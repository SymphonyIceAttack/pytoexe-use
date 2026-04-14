import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import json
from threading import Thread

# ------------------------------------------------------------
# Базовый класс для API устройств
# ------------------------------------------------------------
class DeviceAPI:
    name = "Базовое устройство"

    @staticmethod
    def open_lock(host, username, password, **kwargs):
        raise NotImplementedError


class BewardAPI(DeviceAPI):
    name = "Beward DKS20210"

    @staticmethod
    def open_lock(host, username, password, **kwargs):
        url = f"{host.rstrip('/')}/cgi-bin/intercom_cgi?action=maindoor"
        try:
            resp = requests.get(url, auth=HTTPDigestAuth(username, password), timeout=10)
            if resp.status_code == 200:
                return True, f"Успешно! Ответ: {resp.text[:200]}"
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            return False, f"Исключение: {str(e)}"


class BAS_APIToken(DeviceAPI):
    """BAS AA-12B через предварительный логин (токен)"""
    name = "BAS AA-12B (Token)"

    @staticmethod
    def open_lock(host, username, password, login_url=None, open_url=None, **kwargs):
        host = host.rstrip('/')
        login_url = login_url or "/api/v1/login"
        open_url = open_url or "/api/v1/access/general/lock/open/remote/accepted/0"
        full_login = f"{host}{login_url}"
        full_open = f"{host}{open_url}"

        try:
            # Логин
            resp_login = requests.post(full_login, json={"username": username, "password": password}, timeout=10)
            if resp_login.status_code != 200:
                return False, f"Логин {resp_login.status_code} - {resp_login.text[:200]}"

            data = resp_login.json()
            token = data.get('token') or data.get('access_token')
            if not token:
                return False, f"Токен не найден: {data}"

            # Открытие замка
            headers = {"Authorization": f"Bearer {token}"}
            resp_open = requests.post(full_open, headers=headers, timeout=10)
            if resp_open.status_code in (200, 201, 204):
                return True, f"Замок открыт! Ответ: {resp_open.text[:200]}"
            return False, f"Ошибка открытия {resp_open.status_code}: {resp_open.text[:200]}"
        except Exception as e:
            return False, f"Исключение: {str(e)}"


class BAS_DirectBasic(DeviceAPI):
    """BAS AA-12B: прямая Basic-аутентификация на open_lock_api_point"""
    name = "BAS AA-12B (Direct Basic)"

    @staticmethod
    def open_lock(host, username, password, open_url=None, **kwargs):
        host = host.rstrip('/')
        open_url = open_url or "/api/v1/access/general/lock/open/remote/accepted/0"
        full_url = f"{host}{open_url}"
        try:
            resp = requests.post(full_url, auth=HTTPBasicAuth(username, password), timeout=10)
            if resp.status_code in (200, 201, 204):
                return True, f"Успешно! Код {resp.status_code}"
            # Пробуем GET, если POST не сработал
            resp2 = requests.get(full_url, auth=HTTPBasicAuth(username, password), timeout=10)
            if resp2.status_code in (200, 201, 204):
                return True, f"Успешно (GET)! Код {resp2.status_code}"
            return False, f"Ошибка {resp.status_code} (POST) / {resp2.status_code} (GET): {resp.text[:100]}"
        except Exception as e:
            return False, f"Исключение: {str(e)}"


class AkuvoxAPI(DeviceAPI):
    name = "Akuvox-X915S"

    @staticmethod
    def open_lock(host, username, password, **kwargs):
        # password здесь = secret_key
        host = host.rstrip('/')
        url = f"{host}/api/"
        try:
            params = {"key": password}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                return True, f"Успешно (параметр key)! Ответ: {resp.text[:200]}"
            headers = {"X-Secret-Key": password}
            resp2 = requests.get(url, headers=headers, timeout=10)
            if resp2.status_code == 200:
                return True, f"Успешно (заголовок)! Ответ: {resp2.text[:200]}"
            return False, f"Ошибка: {resp.status_code} / {resp2.status_code}"
        except Exception as e:
            return False, f"Исключение: {str(e)}"


# ------------------------------------------------------------
# GUI с возможностью редактирования эндпоинтов
# ------------------------------------------------------------
class DoorControlApp:
    def __init__(self, root):
        self.root = root
        root.title("Управление замками домофона (расширенное)")
        root.geometry("800x700")

        # Устройства и их классы
        self.device_classes = {
            "Beward DKS20210": BewardAPI,
            "BAS AA-12B (Token)": BAS_APIToken,
            "BAS AA-12B (Direct Basic)": BAS_DirectBasic,
            "Akuvox-X915S": AkuvoxAPI,
        }
        self.current_device = tk.StringVar(value="BAS AA-12B (Direct Basic)")

        # Переменные
        self.host_var = tk.StringVar(value="http://11.24.4.9")
        self.username_var = tk.StringVar(value="admin")
        self.password_var = tk.StringVar(value="")
        self.login_url_var = tk.StringVar(value="/api/v1/login")
        self.open_url_var = tk.StringVar(value="/api/v1/access/general/lock/open/remote/accepted/0")
        self.show_advanced = tk.BooleanVar(value=False)

        self.create_widgets()

    def create_widgets(self):
        # Основные параметры
        main_frame = ttk.LabelFrame(self.root, text="Параметры подключения", padding=10)
        main_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(main_frame, text="Host address:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(main_frame, textvariable=self.host_var, width=60).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Username:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(main_frame, textvariable=self.username_var, width=60).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Password / Secret key:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(main_frame, textvariable=self.password_var, width=60, show="*").grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Тип устройства:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        device_combo = ttk.Combobox(main_frame, textvariable=self.current_device,
                                    values=list(self.device_classes.keys()), state="readonly", width=57)
        device_combo.grid(row=3, column=1, padx=5, pady=5)
        device_combo.bind("<<ComboboxSelected>>", self.on_device_change)

        # Расширенные настройки (API пути)
        self.advanced_frame = ttk.LabelFrame(self.root, text="Расширенные настройки API (для BAS и Akuvox)", padding=10)
        self.advanced_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(self.advanced_frame, text="Login URL (если нужен):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.login_entry = ttk.Entry(self.advanced_frame, textvariable=self.login_url_var, width=60)
        self.login_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(self.advanced_frame, text="Open lock URL:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.open_entry = ttk.Entry(self.advanced_frame, textvariable=self.open_url_var, width=60)
        self.open_entry.grid(row=1, column=1, padx=5, pady=2)

        self.advanced_frame.pack_forget()  # сначала скрыто

        # Чекбокс показать расширенные
        self.show_adv_cb = ttk.Checkbutton(self.root, text="Показать расширенные настройки (URLы API)",
                                           variable=self.show_advanced, command=self.toggle_advanced)
        self.show_adv_cb.pack(anchor="w", padx=10, pady=2)

        # Кнопка действия
        self.action_btn = ttk.Button(self.root, text="Дёрнуть!", command=self.on_open_lock)
        self.action_btn.pack(pady=10)

        # Лог
        log_frame = ttk.LabelFrame(self.root, text="Результат выполнения", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill="both", expand=True)

        # Информация
        info = ("Совет: Для BAS AA-12B попробуйте режим 'Direct Basic' – он отправляет запрос прямо на Open lock URL с Basic-аутентификацией.\n"
                "Если не работает, уточните реальные пути API в веб-интерфейсе домофона (F12 -> Network).")
        ttk.Label(self.root, text=info, foreground="gray", justify="left").pack(fill="x", padx=10, pady=5)

        self.on_device_change()

    def toggle_advanced(self):
        if self.show_advanced.get():
            self.advanced_frame.pack(fill="x", padx=10, pady=5, before=self.show_adv_cb)
        else:
            self.advanced_frame.pack_forget()

    def on_device_change(self, event=None):
        dev = self.current_device.get()
        if "BAS" in dev:
            # Для BAS показываем актуальные URL (можно менять)
            self.login_entry.config(state="normal")
            self.open_entry.config(state="normal")
            if "Token" in dev:
                self.login_url_var.set("/api/v1/login")
                self.open_url_var.set("/api/v1/access/general/lock/open/remote/accepted/0")
            else:
                self.login_url_var.set("(не используется)")
                self.open_url_var.set("/api/v1/access/general/lock/open/remote/accepted/0")
        elif dev == "Akuvox-X915S":
            self.login_entry.config(state="disabled")
            self.open_entry.config(state="normal")
            self.open_url_var.set("/api/")
        else:  # Beward
            self.login_entry.config(state="disabled")
            self.open_entry.config(state="disabled")
            self.login_url_var.set("")
            self.open_url_var.set("")

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def on_open_lock(self):
        self.action_btn.config(state="disabled", text="Выполняется...")
        Thread(target=self._open_lock_thread, daemon=True).start()

    def _open_lock_thread(self):
        host = self.host_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        device_name = self.current_device.get()
        device_class = self.device_classes.get(device_name)

        if not host:
            self.show_error("Введите host address")
            return

        self.log(f"▶ Попытка открыть замок для {device_name}")
        self.log(f"  Host: {host}")
        self.log(f"  Username: {username if username else '(пусто)'}")
        self.log(f"  Password: {'*' * len(password) if password else '(пусто)'}")

        extra = {}
        if "BAS" in device_name:
            extra["login_url"] = self.login_url_var.get().strip() if "Token" in device_name else None
            extra["open_url"] = self.open_url_var.get().strip()
            self.log(f"  Login URL: {extra['login_url']}")
            self.log(f"  Open URL: {extra['open_url']}")
        elif device_name == "Akuvox-X915S":
            extra["open_url"] = self.open_url_var.get().strip()

        try:
            success, msg = device_class.open_lock(host, username, password, **extra)
        except Exception as e:
            success, msg = False, f"Критическая ошибка: {str(e)}"

        if success:
            self.log(f"✅ {msg}")
            messagebox.showinfo("Успех", msg)
        else:
            self.log(f"❌ Ошибка: {msg}")
            messagebox.showerror("Ошибка", msg)

        self.root.after(0, lambda: self.action_btn.config(state="normal", text="Дёрнуть!"))

    def show_error(self, text):
        messagebox.showerror("Ошибка ввода", text)
        self.action_btn.config(state="normal", text="Дёрнуть!")


if __name__ == "__main__":
    root = tk.Tk()
    app = DoorControlApp(root)
    root.mainloop()