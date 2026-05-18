import sys
import json
import random
import time
import threading
import requests
from datetime import datetime
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox

# --- ОСНОВНОЙ КЛАСС ПРИЛОЖЕНИЯ ---
class VKGiftSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VK Gift Sender")
        self.root.geometry("650x700")
        self.root.minsize(600, 600)

        # Флаг для остановки процесса отправки
        self.is_running = False
        self.stop_event = threading.Event()

        # --- Переменные для полей ввода ---
        self.token_var = StringVar()
        self.user_id_var = StringVar()
        self.balance_var = IntVar(value=26787)
        self.max_gifts_var = IntVar(value=23)
        self.sleep_seconds_var = IntVar(value=10)
        self.gift_ids_var = StringVar(value="1778,1776,1775,1774,1773,1770,1768,1766,1765,1763,1761,1758,1757,1742,1740,1735,1733,1731,1730,1729,1727,1725,1720,1719,1693,1692,1691,1690,1689,1688,1687,1686,1685,1684,1671,1665,1663,1661,1659,1658,1657,1656,1650,1649,1648,1647,1646,1645,1642")

        # --- Интерфейс ---
        self._create_widgets()
        self._update_log("✅ Приложение запущено. Введите данные и нажмите 'Старт'.")

        # Загружаем сохраненные настройки
        self._load_settings()

    # --- СОЗДАНИЕ ГРАФИЧЕСКИХ ЭЛЕМЕНТОВ ---
    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=BOTH, expand=True)

        # 1. Настройки VK
        ttk.Label(main_frame, text="🔑 VK Токен:").grid(row=0, column=0, sticky=W, pady=2)
        token_entry = ttk.Entry(main_frame, textvariable=self.token_var, width=60, show="*")
        token_entry.grid(row=0, column=1, sticky=EW, pady=2, padx=5)

        ttk.Label(main_frame, text="👤 User ID:").grid(row=1, column=0, sticky=W, pady=2)
        ttk.Entry(main_frame, textvariable=self.user_id_var, width=60).grid(row=1, column=1, sticky=EW, pady=2, padx=5)

        # 2. Основные настройки
        ttk.Label(main_frame, text="📊 Баланс (голосов):").grid(row=2, column=0, sticky=W, pady=2)
        ttk.Spinbox(main_frame, from_=0, to=1000000, textvariable=self.balance_var, width=15).grid(row=2, column=1, sticky=W, pady=2, padx=5)

        ttk.Label(main_frame, text="🎁 Макс. подарков:").grid(row=3, column=0, sticky=W, pady=2)
        ttk.Spinbox(main_frame, from_=1, to=500, textvariable=self.max_gifts_var, width=15).grid(row=3, column=1, sticky=W, pady=2, padx=5)

        ttk.Label(main_frame, text="⏱️ Пауза между подарками (сек):").grid(row=4, column=0, sticky=W, pady=2)
        ttk.Spinbox(main_frame, from_=1, to=60, textvariable=self.sleep_seconds_var, width=15).grid(row=4, column=1, sticky=W, pady=2, padx=5)

        ttk.Label(main_frame, text="📜 ID подарков (через запятую):").grid(row=5, column=0, sticky=NW, pady=2)
        gift_ids_scroll = scrolledtext.ScrolledText(main_frame, height=5, wrap=WORD)
        gift_ids_scroll.grid(row=5, column=1, sticky=EW, pady=2, padx=5)
        gift_ids_scroll.insert("1.0", self.gift_ids_var.get())

        # 3. Кнопки управления
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=15)

        self.start_stop_btn = ttk.Button(btn_frame, text="🚀 СТАРТ", command=self._start_sending, width=15)
        self.start_stop_btn.pack(side=LEFT, padx=10)

        ttk.Button(btn_frame, text="💾 Сохранить настройки", command=self._save_settings, width=20).pack(side=LEFT, padx=10)

        # 4. Лог событий
        ttk.Label(main_frame, text="📃 ЛОГ ПРОГРАММЫ:").grid(row=7, column=0, sticky=W, pady=(10,0))
        self.log_area = scrolledtext.ScrolledText(main_frame, height=18, state=DISABLED, wrap=WORD)
        self.log_area.grid(row=8, column=0, columnspan=2, sticky=NSEW, pady=5)

        # Настройка Grid
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(8, weight=1)

    # --- ЛОГИРОВАНИЕ ---
    def _update_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[{timestamp}] {message}\n"
        self.log_area.config(state=NORMAL)
        self.log_area.insert(END, full_msg)
        self.log_area.see(END)
        self.log_area.config(state=DISABLED)
        self.root.update_idletasks()

    # --- ЗАГРУЗКА/СОХРАНЕНИЕ НАСТРОЕК ---
    def _save_settings(self):
        gift_ids = self.gift_ids_var.get()
        self.gift_ids_var.set(gift_ids)
        settings = {
            "token": self.token_var.get(),
            "user_id": self.user_id_var.get(),
            "balance": self.balance_var.get(),
            "max_gifts": self.max_gifts_var.get(),
            "sleep_seconds": self.sleep_seconds_var.get(),
            "gift_ids": self.gift_ids_var.get()
        }
        try:
            with open("vk_gift_sender_settings.json", "w") as f:
                json.dump(settings, f)
            self._update_log("💾 Настройки сохранены.")
        except Exception as e:
            self._update_log(f"❌ Ошибка сохранения настроек: {e}")

    def _load_settings(self):
        try:
            with open("vk_gift_sender_settings.json", "r") as f:
                settings = json.load(f)
            self.token_var.set(settings.get("token", ""))
            self.user_id_var.set(settings.get("user_id", ""))
            self.balance_var.set(settings.get("balance", 26787))
            self.max_gifts_var.set(settings.get("max_gifts", 23))
            self.sleep_seconds_var.set(settings.get("sleep_seconds", 10))
            self.gift_ids_var.set(settings.get("gift_ids", ""))
            self._update_log("⚙️ Настройки загружены.")
        except FileNotFoundError:
            pass
        except Exception as e:
            self._update_log(f"⚠️ Ошибка загрузки настроек: {e}")

    # --- ПОЛУЧЕНИЕ ЦЕН ПОДАРКОВ ---
    def _get_gift_prices(self, token):
        try:
            url = "https://api.vk.com/method/gifts.get"
            params = {
                "access_token": token,
                "v": "5.199"
            }
            response = requests.get(url, params=params)
            data = response.json()
            if "error" in data:
                self._update_log(f"❌ VK Ошибка: {data['error']['error_msg']}")
                return None
            prices = {}
            for gift in data["response"]["items"]:
                prices[gift["id"]] = gift["price"]
            return prices
        except Exception as e:
            self._update_log(f"❌ Ошибка запроса к VK API: {e}")
            return None

    # --- ОТПРАВКА ПОДАРКА ---
    def _send_gift(self, token, user_id, gift_id):
        try:
            url = "https://api.vk.com/method/gifts.send"
            guid = random.randint(1000000000, 2147483647)
            params = {
                "access_token": token,
                "user_ids": user_id,
                "gift_id": gift_id,
                "guid": guid,
                "v": "5.199"
            }
            response = requests.post(url, data=params)
            data = response.json()
            if "error" in data:
                self._update_log(f"❌ VK ошибка при отправке: {data['error']['error_msg']}")
                return False
            return True
        except Exception as e:
            self._update_log(f"❌ Ошибка сети: {e}")
            return False

    # --- ФУНКЦИЯ ЗАПУСКА ПРОЦЕССА В ПОТОКЕ ---
    def _start_sending(self):
        if self.is_running:
            # Запрос на остановку
            self._update_log("🛑 Запрошена остановка процесса...")
            self.stop_event.set()
            return

        # --- Проверка данных перед стартом ---
        token = self.token_var.get().strip()
        user_id = self.user_id_var.get().strip()
        if not token or not user_id:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните токен и User ID!")
            return

        gift_ids_str = self.gift_ids_var.get()
        if not gift_ids_str:
            messagebox.showerror("Ошибка", "Список ID подарков не может быть пустым!")
            return

        # Парсим ID подарков
        gift_ids_list = []
        for part in gift_ids_str.replace(" ", "").split(","):
            if part.isdigit():
                gift_ids_list.append(int(part))

        if not gift_ids_list:
            messagebox.showerror("Ошибка", "Не удалось распознать ID подарков!")
            return

        # --- Запускаем процесс в фоновом потоке ---
        self.is_running = True
        self.stop_event.clear()
        self.start_stop_btn.config(text="🛑 СТОП")
        self._update_log("▶️ Запуск процесса...")
        threading.Thread(target=self._sending_process, args=(token, user_id, gift_ids_list), daemon=True).start()

    # --- ОСНОВНОЙ ПРОЦЕСС ОТПРАВКИ ---
    def _sending_process(self, token, user_id, gift_ids_list):
        try:
            # Получаем цены
            self._update_log("📦 Получаем список и цены подарков...")
            prices = self._get_gift_prices(token)
            if prices is None:
                self._update_log("❌ Не удалось получить данные о подарках. Проверьте токен и интернет.")
                return

            sent_count = 0
            spent_votes = 0
            current_balance = self.balance_var.get()
            index = 0
            total_gifts = len(gift_ids_list)
            max_gifts = self.max_gifts_var.get()

            while sent_count < max_gifts and current_balance > 0 and not self.stop_event.is_set():
                gift_id = gift_ids_list[index % total_gifts]

                # Проверка цены
                if gift_id not in prices:
                    self._update_log(f"⚠️ Нет данных о цене подарка {gift_id}. Пропуск.")
                elif prices[gift_id] != 1:
                    self._update_log(f"⏭️ Пропуск подарка {gift_id} (цена = {prices[gift_id]} голосов).")
                else:
                    self._update_log(f"🎁 Отправляю подарок {gift_id} (цена 1 голос)...")
                    success = self._send_gift(token, user_id, gift_id)

                    if success:
                        sent_count += 1
                        spent_votes += 1
                        current_balance -= 1
                        self._update_log(f"✅ Подарок {gift_id} отправлен! (Отправлено: {sent_count}/{max_gifts})")
                    else:
                        self._update_log(f"❌ Не удалось отправить подарок {gift_id}")

                # Переход к следующему ID
                index += 1
                if index >= total_gifts:
                    index = 0
                    self._update_log("🔄 Достигнут конец списка, начинаем новый круг.")

                # Пауза (с возможностью прерывания)
                for _ in range(self.sleep_seconds_var.get()):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)

            # Итог
            if sent_count == max_gifts:
                self._update_log(f"🏁 Цель достигнута! Отправлено {max_gifts} подарков. Потрачено {spent_votes} голосов.")
            elif current_balance <= 0:
                self._update_log(f"🚫 Не хватает голосов! Отправлено {sent_count} из {max_gifts} подарков.")
            elif self.stop_event.is_set():
                self._update_log(f"🛑 Остановлено пользователем. Отправлено {sent_count} подарков.")

            # Обновляем баланс в интерфейсе
            self.balance_var.set(current_balance)

        except Exception as e:
            self._update_log(f"💥 Критическая ошибка в процессе: {e}")
        finally:
            self._start_stop_btn.config(text="🚀 СТАРТ")
            self.is_running = False
            self._update_log("⏹️ Процесс завершён.")

# --- ТОЧКА ВХОДА ---
if __name__ == "__main__":
    root = Tk()
    app = VKGiftSenderApp(root)
    root.mainloop()