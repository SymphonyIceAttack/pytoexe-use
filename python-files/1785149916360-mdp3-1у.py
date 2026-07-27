import os
import sys
import re
import subprocess
import threading
import socket
import ctypes
import platform
from tkinter import Tk, Frame, Button, Label, Text, Scrollbar, END, messagebox, filedialog, StringVar
from tkinter.font import Font
import requests

# ------------------------------------------------------------
# 1. Проверка и запрос прав администратора
# ------------------------------------------------------------
def is_admin():
    """Возвращает True, если процесс запущен с правами администратора."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def run_as_admin():
    """Перезапускает текущий скрипт с правами администратора."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)

# При старте: если не админ — перезапускаем
if not is_admin():
    run_as_admin()

# ------------------------------------------------------------
# 2. Вспомогательные функции сбора данных
# ------------------------------------------------------------
def run_wmic(command: str) -> str:
    """Выполняет wmic команду и возвращает очищенное значение или сообщение об ошибке."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        if proc.returncode != 0:
            return "[ОШИБКА]"
        # wmic выводит заголовок, пустую строку, значение
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        # Ожидаем минимум две строки: заголовок и значение
        if len(lines) >= 2:
            # Значение обычно в последней непустой строке
            value = lines[-1]
            return value if value else "[НЕ ДОСТУПНО]"
        return "[НЕ ДОСТУПНО]"
    except subprocess.TimeoutExpired:
        return "[ОШИБКА]"
    except Exception as e:
        return f"[ОШИБКА: {e}]"

def get_mac_addresses() -> list:
    """Возвращает список MAC-адресов активных сетевых адаптеров."""
    try:
        proc = subprocess.run(
            "getmac /v /fo list",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        if proc.returncode != 0:
            return ["[ОШИБКА]"]
        output = proc.stdout
        # Разбиваем на блоки по разделителю (пустая строка)
        blocks = re.split(r'\n\s*\n', output)
        macs = []
        for block in blocks:
            # Пропускаем блоки без Media State или Physical Address
            if 'Physical Address:' not in block:
                continue
            # Проверяем состояние подключения: если нет disconnected, считаем активным
            media_match = re.search(r'Media State:\s*(.+)', block, re.IGNORECASE)
            if media_match and 'disconnected' in media_match.group(1).lower():
                continue
            # Извлекаем физический адрес
            addr_match = re.search(r'Physical Address:\s*([0-9A-Fa-f\-]{17})', block)
            if addr_match:
                macs.append(addr_match.group(1).upper())
        return macs if macs else ["[НЕ ДОСТУПНО]"]
    except Exception as e:
        return [f"[ОШИБКА: {e}]"]

def get_local_ip() -> str:
    """Определяет локальный IP-адрес через UDP-соединение."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "[НЕ ДОСТУПНО]"

def get_external_ip() -> str:
    """Получает внешний IP-адрес через веб-сервисы с таймаутом 5 сек."""
    services = [
        ("https://api.ipify.org", None),
        ("https://ifconfig.me/ip", None),
    ]
    for url, _ in services:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                ip = resp.text.strip()
                if re.match(r'^\d{1,3}(?:\.\d{1,3}){3}$', ip):
                    return ip
        except requests.exceptions.Timeout:
            continue
        except Exception:
            continue
    return "[НЕТ ИНТЕРНЕТА]"

def clean_hex(raw_string: str) -> str:
    """Оставляет только шестнадцатеричные символы (0-9, A-F, a-f)."""
    return ''.join(ch for ch in raw_string if ch in '0123456789ABCDEFabcdef')

# ------------------------------------------------------------
# 3. Основная логика сбора данных
# ------------------------------------------------------------
def gather_all_info():
    """Собирает все данные и возвращает словарь с ключами, включая готовый HWID."""
    info = {}

    # 1. Имя компьютера
    info['computer_name'] = platform.node()
    # 2. Имя пользователя
    try:
        info['user_name'] = os.getlogin()
    except Exception:
        info['user_name'] = "[НЕ ДОСТУПНО]"

    # 3. UUID материнской платы
    uuid = run_wmic("wmic csproduct get UUID")
    info['uuid'] = uuid

    # 4. ID процессора
    processor_id = run_wmic("wmic cpu get ProcessorId")
    info['processor_id'] = processor_id

    # 5. Серийный номер основного диска
    disk_serial = run_wmic("wmic diskdrive get SerialNumber")
    info['disk_serial'] = disk_serial.strip()  # может содержать пробелы

    # 6. Серийный номер материнской платы
    board_serial = run_wmic("wmic baseboard get SerialNumber")
    info['board_serial'] = board_serial.strip()

    # 7. MAC-адреса активных адаптеров
    macs = get_mac_addresses()
    info['macs'] = macs

    # 8. Локальный IP
    info['local_ip'] = get_local_ip()

    # 9. Внешний IP
    info['external_ip'] = get_external_ip()

    # Формирование HWID: конкатенация пунктов 3-7, очистка от не-hex символов
    raw_hwid = uuid + processor_id + disk_serial + board_serial + ''.join(macs)
    info['hwid'] = clean_hex(raw_hwid)

    return info

# ------------------------------------------------------------
# 4. Графический интерфейс
# ------------------------------------------------------------
class HWIDApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("HWID Collector (Администратор)")
        self.root.geometry("700x600")
        self.root.minsize(600, 400)

        # Данные
        self.data = None
        self.gathering = False

        # Шрифт для вывода
        self.text_font = Font(family="Courier New", size=10)

        # Верхняя панель управления
        control_frame = Frame(root)
        control_frame.pack(fill='x', padx=5, pady=5)

        self.refresh_btn = Button(control_frame, text="Обновить данные", command=self.start_gathering)
        self.refresh_btn.pack(side='left', padx=5)

        self.copy_hwid_btn = Button(control_frame, text="Копировать HWID", command=self.copy_hwid)
        self.copy_hwid_btn.pack(side='left', padx=5)

        self.export_btn = Button(control_frame, text="Экспорт", command=self.export_data)
        self.export_btn.pack(side='left', padx=5)

        # Индикатор статуса
        self.status_var = StringVar()
        self.status_var.set("Сбор данных...")
        status_label = Label(control_frame, textvariable=self.status_var, bd=1, relief='sunken', anchor='w')
        status_label.pack(side='right', fill='x', expand=True, padx=5)

        # Текстовое поле с прокруткой
        text_frame = Frame(root)
        text_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.output_text = Text(text_frame, wrap='none', font=self.text_font)
        scrollbar_y = Scrollbar(text_frame, orient='vertical', command=self.output_text.yview)
        scrollbar_x = Scrollbar(root, orient='horizontal', command=self.output_text.xview)

        self.output_text.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.output_text.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.pack(fill='x')

        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Запускаем сбор данных при старте
        self.root.after(100, self.start_gathering)

    def start_gathering(self):
        """Запускает сбор данных в отдельном потоке."""
        if self.gathering:
            return
        self.gathering = True
        self.refresh_btn.config(state='disabled')
        self.status_var.set("Сбор данных...")
        self.output_text.delete(1.0, END)
        self.output_text.insert(END, "Пожалуйста, подождите...\n")

        # Поток для сбора
        thread = threading.Thread(target=self._gather_thread, daemon=True)
        thread.start()

    def _gather_thread(self):
        """Фоновый сбор данных."""
        try:
            data = gather_all_info()
            self.root.after(0, self._display_data, data)
        except Exception as e:
            self.root.after(0, self._display_error, str(e))
        finally:
            self.gathering = False
            self.root.after(0, self._enable_ui)

    def _display_data(self, data):
        """Отображает собранные данные в текстовом поле."""
        self.data = data
        self.status_var.set("Готово")
        self.output_text.delete(1.0, END)

        # Форматирование вывода
        lines = []
        lines.append("=" * 60)
        lines.append(f"Имя компьютера: {data['computer_name']}")
        lines.append(f"Имя пользователя: {data['user_name']}")
        lines.append("=" * 60)
        lines.append("")
        lines.append("[1] UUID материнской платы:")
        lines.append(str(data['uuid']))
        lines.append("")
        lines.append("[2] ID процессора:")
        lines.append(str(data['processor_id']))
        lines.append("")
        lines.append("[3] Серийный номер диска:")
        lines.append(str(data['disk_serial']))
        lines.append("")
        lines.append("[4] Серийный номер материнской платы:")
        lines.append(str(data['board_serial']))
        lines.append("")
        lines.append("[5] MAC-адреса:")
        for mac in data['macs']:
            lines.append(mac)
        lines.append("")
        lines.append("[6] IP-адреса:")
        lines.append(f"  Локальный IP: {data['local_ip']}")
        lines.append(f"  Внешний IP:   {data['external_ip']}")
        lines.append("")
        lines.append("=" * 60)
        lines.append(f"HWID: {data['hwid']}")
        lines.append("=" * 60)

        self.output_text.insert(END, "\n".join(lines))

    def _display_error(self, msg):
        self.status_var.set("Ошибка")
        self.output_text.delete(1.0, END)
        self.output_text.insert(END, f"Критическая ошибка при сборе данных:\n{msg}")

    def _enable_ui(self):
        self.refresh_btn.config(state='normal')

    def copy_hwid(self):
        """Копирует итоговый HWID в буфер обмена."""
        if not self.data or 'hwid' not in self.data:
            messagebox.showwarning("Нет данных", "Сначала выполните сбор данных.")
            return
        hwid = self.data['hwid']
        self.root.clipboard_clear()
        self.root.clipboard_append(hwid)
        self.status_var.set(f"HWID скопирован: {hwid[:40]}...")
        messagebox.showinfo("Готово", "HWID скопирован в буфер обмена.")

    def export_data(self):
        """Сохраняет весь вывод в текстовый файл."""
        if not self.data:
            messagebox.showwarning("Нет данных", "Сначала выполните сбор данных.")
            return
        content = self.output_text.get(1.0, END)
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
            title="Сохранить отчёт"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_var.set(f"Экспортировано: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

# ------------------------------------------------------------
# 5. Запуск приложения
# ------------------------------------------------------------
if __name__ == "__main__":
    root = Tk()
    app = HWIDApp(root)
    root.mainloop()