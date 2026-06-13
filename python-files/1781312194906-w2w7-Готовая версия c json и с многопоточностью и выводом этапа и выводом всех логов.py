import telnetlib
import time
import re
import json
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading

# ------------------- Конфигурация -------------------
CACHE_FILE = "switch_models.json"
IDLE_TIMEOUT = 180  # секунд бездействия

# ------------------- Кэш моделей -------------------
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

switch_cache = load_cache()

# ------------------- Управление соединениями -------------------
connections = {}
connections_lock = threading.Lock()

def close_connection(ip_suffix):
    with connections_lock:
        if ip_suffix in connections:
            try:
                connections[ip_suffix]['tn'].close()
            except:
                pass
            del connections[ip_suffix]

def close_all_idle_connections():
    now = time.time()
    with connections_lock:
        to_close = [ip for ip, data in connections.items()
                    if now - data['last_used'] > IDLE_TIMEOUT]
        for ip in to_close:
            try:
                connections[ip]['tn'].close()
            except:
                pass
            del connections[ip]

def cleanup_thread():
    while True:
        time.sleep(30)
        close_all_idle_connections()

threading.Thread(target=cleanup_thread, daemon=True).start()

# ------------------- Telnet-функции -------------------
def send_command(tn, command, timeout=30, line_timeout=2):
    """
    Отправляет команду, обрабатывает --More--, читает до #.
    timeout - общий таймаут на всю команду (сек)
    line_timeout - таймаут на чтение одной строки (сек)
    """
    tn.write(command.encode('ascii') + b"\n")
    output = b""
    start = time.time()
    while True:
        try:
            line = tn.read_until(b"\n", timeout=line_timeout)
            if not line:
                if time.time() - start > timeout:
                    break
                continue
            output += line
            if b"--More--" in line:
                tn.write(b" \n")
                continue
            if output.rstrip().endswith(b"#"):
                output = output.rstrip()[:-1]
                break
        except EOFError:
            break
        if time.time() - start > timeout:
            break
    tn.read_very_eager()
    return output.decode('ascii', errors='ignore').strip()

def connect_and_auth(ip_suffix, status_callback=None):
    ip = f"10.61.{ip_suffix}"
    if status_callback:
        status_callback(f"Подключение к {ip}...")
    tn = telnetlib.Telnet(ip, 23, timeout=5)
    if status_callback:
        status_callback("Ожидание login...")
    tn.read_until(b"login: ", timeout=3)
    tn.write(b"tp_1ltp\n")
    if status_callback:
        status_callback("Отправка логина...")
    tn.read_until(b"Password: ", timeout=3)
    tn.write(b"7AW_)t6HE6\n")
    if status_callback:
        status_callback("Отправка пароля...")
    tn.read_until(b"#", timeout=5)
    tn.write(b"terminal length 0\n")
    tn.read_until(b"#", timeout=2)
    tn.write(b"\n")
    time.sleep(0.1)
    tn.read_very_eager()
    if status_callback:
        status_callback("Аутентификация завершена")
    return tn

def get_switch_model(tn, ip_suffix, status_callback=None):
    global switch_cache
    if ip_suffix in switch_cache:
        if status_callback:
            status_callback(f"Модель для {ip_suffix} взята из кэша: {switch_cache[ip_suffix]}")
        return switch_cache[ip_suffix]

    if status_callback:
        status_callback("Определение модели через show version...")
    version_output = send_command(tn, "show version", timeout=8)
    if re.search(r'SNR-S2982G-8T', version_output, re.IGNORECASE):
        model = 'SNR'
    elif re.search(r'ISCOM2110', version_output, re.IGNORECASE):
        model = 'ISCOM2110'
    else:
        model = 'unknown'
    switch_cache[ip_suffix] = model
    save_cache(switch_cache)
    if status_callback:
        status_callback(f"Модель определена: {model}")
    return model

def get_connection(ip_suffix, status_callback=None):
    with connections_lock:
        now = time.time()
        if ip_suffix in connections:
            conn = connections[ip_suffix]
            try:
                conn['tn'].write(b"\n")
                conn['tn'].read_very_eager()
                conn['last_used'] = now
                if status_callback:
                    status_callback(f"Используем существующее соединение для {ip_suffix}")
                return conn['tn'], conn['model']
            except:
                if status_callback:
                    status_callback(f"Соединение для {ip_suffix} разорвано, создаём новое")
                del connections[ip_suffix]

        if status_callback:
            status_callback(f"Создаём новое соединение для {ip_suffix}")
        tn = connect_and_auth(ip_suffix, status_callback)
        model = get_switch_model(tn, ip_suffix, status_callback)
        connections[ip_suffix] = {
            'tn': tn,
            'last_used': now,
            'model': model
        }
        return tn, model

def execute_command(ip_suffix, port, vlan, command_key, status_callback=None):
    try:
        tn, model = get_connection(ip_suffix, status_callback)
        if model == 'unknown':
            raise Exception("Не удалось определить модель коммутатора")

        if model == 'SNR':
            cmd_map = {
                'link': f"show interface ethernet 1/0/{port}",
                'mac_port': f"show mac-address-table interface ethernet 1/0/{port}",
                'mac_vlan': f"show mac-address-table vlan {vlan}" if vlan else "show mac-address-table vlan",
                'traffic': f"show interface ethernet 1/0/{port} detail",
                'all_links': "sh int e status",
                'log': "show log"
            }
        else:  # ISCOM2110
            cmd_map = {
                'link': f"sh int port {port}",
                'mac_port': f"show mac-address-table l2-address port {port}",
                'mac_vlan': (f"show mac-address-table l2-address vlan {vlan}"
                             if vlan else "show mac-address-table l2-address vlan"),
                'traffic': f"show interface port {port} statistics dynamic detai",
                'all_links': None,
                'log': f'show logging file'
            }
            if command_key == 'all_links':
                return "Команда не поддерживается для ISCOM2110"

        cmd = cmd_map.get(command_key)
        if not cmd:
            return "Неизвестная команда"

        if status_callback:
            status_callback(f"Выполнение команды: {cmd[:50]}...")

        # Увеличиваем таймаут для логов
        if command_key == 'log':
            output = send_command(tn, cmd, timeout=90, line_timeout=3)
        else:
            output = send_command(tn, cmd, timeout=30, line_timeout=2)

        with connections_lock:
            if ip_suffix in connections:
                connections[ip_suffix]['last_used'] = time.time()

        return output

    except Exception as e:
        close_connection(ip_suffix)
        return f"Ошибка: {str(e)}"

# ------------------- GUI -------------------
class NetToolGUI:
    def __init__(self, root):
        self.root = root
        root.title("Кудимыч")
        root.geometry("950x750")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=5)

        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill='both', expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Параметры подключения", padding=10)
        input_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(input_frame, text="Суффикс IP (10.61.X):")\
            .grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.ip_entry = ttk.Entry(input_frame, width=15)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Номер порта (1/0/7 -> 7):")\
            .grid(row=0, column=2, sticky='e', padx=5, pady=5)
        self.port_entry = ttk.Entry(input_frame, width=10)
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="VLAN (для MAC по VLAN):")\
            .grid(row=0, column=4, sticky='e', padx=5, pady=5)
        self.vlan_entry = ttk.Entry(input_frame, width=10)
        self.vlan_entry.grid(row=0, column=5, padx=5, pady=5)

        self.exit_btn = ttk.Button(input_frame, text="🏠", width=3,
                                   command=self.exit_switch)
        self.exit_btn.grid(row=0, column=6, padx=10, pady=5)

        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)

        buttons = [
            ("📡 Статус линка", "link"),
            ("🔌 MAC на порту", "mac_port"),
            ("🌐 MAC по VLAN", "mac_vlan"),
            ("📊 Трафик порта", "traffic"),
            ("🔗 Все линки", "all_links"),
            ("📜 Логи порта", "log")
        ]

        for text, key in buttons:
            btn = ttk.Button(btn_frame, text=text, width=18,
                             command=lambda k=key: self.start_command(k))
            btn.pack(side='left', padx=5, pady=5)

        self.output = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            background='#1e1e1e',
            foreground='#d4d4d4',
            insertbackground='white'
        )
        self.output.pack(fill='both', expand=True, pady=10)

        self.status = ttk.Label(main_frame, text="Готов", relief='sunken', anchor='w')
        self.status.pack(fill='x')

    @staticmethod
    def is_valid_ip_suffix(s):
        return bool(re.match(r'^\d{1,3}\.\d{1,3}$', s.strip()))

    def exit_switch(self):
        ip_suffix = self.ip_entry.get().strip()
        if not self.is_valid_ip_suffix(ip_suffix):
            messagebox.showerror("Ошибка", "Неверный формат IP")
            return
        close_connection(ip_suffix)
        self.status.config(text="Соединение закрыто")
        self.output.insert(tk.END, f"\n[!] Соединение с {ip_suffix} закрыто\n")
        self.output.see(tk.END)

    def start_command(self, command_key):
        ip_suffix = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        vlan = self.vlan_entry.get().strip()

        if not self.is_valid_ip_suffix(ip_suffix):
            messagebox.showerror("Ошибка",
                                 "Неверный формат суффикса IP.\n"
                                 "Используйте формат: цифры.цифры (например, 4.111)")
            return
        if command_key in ['link', 'mac_port', 'traffic', 'log'] and not port:
            messagebox.showwarning("Ошибка", "Введите номер порта")
            return
        if command_key == 'mac_vlan' and not vlan:
            vlan = None

        self.status.config(text=f"Выполняется {command_key}...")
        self.output.insert(tk.END, f"\n{'='*60}\n➡️ {command_key}\n")
        self.output.see(tk.END)

        thread = threading.Thread(target=self._run_command_thread,
                                  args=(ip_suffix, port, vlan, command_key),
                                  daemon=True)
        thread.start()

    def _status_callback(self, message):
        self.root.after(0, lambda: self.output.insert(tk.END, f"  [*] {message}\n"))
        self.root.after(0, lambda: self.output.see(tk.END))

    def _run_command_thread(self, ip_suffix, port, vlan, command_key):
        result = execute_command(ip_suffix, port, vlan, command_key,
                                 status_callback=self._status_callback)
        self.root.after(0, self._show_result, result)

    def _show_result(self, result):
        self.output.insert(tk.END, result + "\n" + "="*60 + "\n")
        self.output.see(tk.END)
        self.status.config(text="Готов")

if __name__ == "__main__":
    root = tk.Tk()
    app = NetToolGUI(root)
    root.mainloop()