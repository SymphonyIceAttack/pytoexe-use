"""
PUBG TCP Reset Utility с трей-иконкой
- Windows only, желательно запуск от имени администратора.
- Зависимости: psutil, pystray, pillow, keyboard
pip install psutil pystray pillow keyboard
"""

import ctypes, struct, socket, psutil, threading, logging, json, os, re, pystray, time, keyboard
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw

# -------------------- Конфигурация --------------------
PROC_NAME = "TslGame.exe"
LOG_FILE = "pubg_reset.log"
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "button_color": "#ff4444",
    "text_color": "white",
    "button_text": "Reset",
    "width": 50,
    "height": 25,
    "x": 50,
    "y": 50,
    "movable": True
}

PUBG_PATTERNS = [
    r"\b(13\.)", r"\b(15\.)", r"\b(18\.)", r"\b(3\.)",
    r"amazonaws\.com", r"cloudfront\.net", r"pubg", r"tencent"
]

# -------------------- Windows IP Helper API --------------------
AF_INET = 2
ERROR_INSUFFICIENT_BUFFER = 122
MIB_TCP_STATE_DELETE_TCB = 12

iphlpapi = ctypes.WinDLL('iphlpapi')
kernel32 = ctypes.WinDLL('kernel32')

DWORD = ctypes.c_uint32

class MIB_TCPROW_OWNER_PID(ctypes.Structure):
    _fields_ = [
        ("dwState", DWORD),
        ("dwLocalAddr", DWORD),
        ("dwLocalPort", DWORD),
        ("dwRemoteAddr", DWORD),
        ("dwRemotePort", DWORD),
        ("dwOwningPid", DWORD)
    ]

GetExtendedTcpTable = iphlpapi.GetExtendedTcpTable
GetExtendedTcpTable.argtypes = [ctypes.c_void_p, ctypes.POINTER(DWORD), ctypes.c_bool, DWORD, DWORD, DWORD]
GetExtendedTcpTable.restype = DWORD

SetTcpEntry = iphlpapi.SetTcpEntry
SetTcpEntry.argtypes = [ctypes.POINTER(MIB_TCPROW_OWNER_PID)]
SetTcpEntry.restype = DWORD

# -------------------- Helpers --------------------
def dword_to_ip(dw):
    return socket.inet_ntoa(struct.pack("<I", dw))

def dword_port_to_int(dw_port):
    p1 = dw_port & 0xFFFF
    p2 = (dw_port >> 16) & 0xFFFF
    try:
        p3 = socket.ntohs(dw_port & 0xFFFF)
    except Exception:
        p3 = p1
    for p in (p1, p2, p3):
        if 0 < p <= 65535:
            return p
    return p1

def get_all_tcp_connections():
    TCP_TABLE_OWNER_PID_ALL = 5
    size = DWORD(0)
    res = GetExtendedTcpTable(None, ctypes.byref(size), False, AF_INET, TCP_TABLE_OWNER_PID_ALL, 0)
    if res not in (0, ERROR_INSUFFICIENT_BUFFER):
        raise OSError(f"GetExtendedTcpTable initial call failed: {res}")

    buf = ctypes.create_string_buffer(size.value)
    res = GetExtendedTcpTable(buf, ctypes.byref(size), False, AF_INET, TCP_TABLE_OWNER_PID_ALL, 0)
    if res != 0:
        raise OSError(f"GetExtendedTcpTable failed: {res}")

    dwNum = struct.unpack_from("I", buf.raw, 0)[0]
    entries = []
    offset = ctypes.sizeof(DWORD)
    row_size = ctypes.sizeof(MIB_TCPROW_OWNER_PID)
    for i in range(dwNum):
        row_buf = buf.raw[offset: offset + row_size]
        row = MIB_TCPROW_OWNER_PID.from_buffer_copy(row_buf)
        entries.append(row)
        offset += row_size
    return entries

def is_pubg_ip(ip):
    for pattern in PUBG_PATTERNS:
        if re.search(pattern, ip):
            return True
    return False

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

# -------------------- Reset logic --------------------
def reset_pubg_connections(logger):
    pids = []
    for proc in psutil.process_iter(['name','pid']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == PROC_NAME.lower():
                pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not pids:
        logger.info("[-] Процесс PUBG (TslGame.exe) не найден.")
        return

    logger.info(f"[+] Найдены PID'ы PUBG: {', '.join(map(str,pids))}")

    try:
        rows = get_all_tcp_connections()
    except Exception as e:
        logger.error(f"[!] Ошибка получения таблицы TCP: {e}")
        return

    matches = []
    for r in rows:
        if r.dwOwningPid in pids:
            local_ip = dword_to_ip(r.dwLocalAddr)
            remote_ip = dword_to_ip(r.dwRemoteAddr)
            local_port = dword_port_to_int(r.dwLocalPort)
            remote_port = dword_port_to_int(r.dwRemotePort)
            matches.append( (r, local_ip, local_port, remote_ip, remote_port) )

    if not matches:
        logger.info("[-] Активных TCP-соединений PUBG не найдено.")
        return

    logger.info(f"[+] Найдено {len(matches)} соединений PUBG. Попытка сброса...")
    succeeded = 0
    for (row, l_ip, l_port, r_ip, r_port) in matches:
        logger.info(f"    -> {l_ip}:{l_port} -> {r_ip}:{r_port} (pid={row.dwOwningPid})")
        to_delete = MIB_TCPROW_OWNER_PID()
        to_delete.dwState = MIB_TCP_STATE_DELETE_TCB
        to_delete.dwLocalAddr = row.dwLocalAddr
        to_delete.dwLocalPort = row.dwLocalPort
        to_delete.dwRemoteAddr = row.dwRemoteAddr
        to_delete.dwRemotePort = row.dwRemotePort
        to_delete.dwOwningPid = row.dwOwningPid

        try:
            res = SetTcpEntry(ctypes.byref(to_delete))
            if res == 0:
                logger.info("      [OK] сброшено.")
                succeeded += 1
            else:
                logger.warning(f"      [ERR] SetTcpEntry -> код {res}")
        except Exception as e:
            logger.error(f"      [ERR] Исключение при SetTcpEntry: {e}")

    logger.info(f"[+] Завершено. Успешно сброшено: {succeeded}/{len(matches)}")

# -------------------- GUI --------------------
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.see(tk.END)
        self.text_widget.after(0, append)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            if k not in cfg:
                cfg[k] = v
        return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

class FloatingButton(tk.Toplevel):
    def __init__(self, master, on_click, config):
        super().__init__(master)
        self.on_click = on_click
        self.config_data = config
        self.movable = config["movable"]

        self.overrideredirect(True)
        self.geometry(f"{config['width']}x{config['height']}+{config['x']}+{config['y']}")
        self.attributes("-topmost", True)
        self.configure(bg="#222")

        self.btn = tk.Button(
            self,
            text=config["button_text"],
            command=self.handle_click,
            font=("Segoe UI", 12, "bold"),
            bg=config["button_color"],
            fg=config["text_color"],
            relief="flat",
            activebackground="#cc3333",
            activeforeground="white",
            cursor="hand2"
        )
        self.btn.pack(expand=True, fill="both", padx=3, pady=3)

        self._drag_data = {"x": 0, "y": 0}

        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)

        self.protocol("WM_DELETE_WINDOW", self.hide)

    def handle_click(self):
        self.on_click()

    def hide(self):
        self.withdraw()

    def show(self):
        self.deiconify()
        self.lift()

    def start_drag(self, event):
        if not self.movable:
            return
        self._drag_data["x"] = event.x_root - self.winfo_x()
        self._drag_data["y"] = event.y_root - self.winfo_y()

    def do_drag(self, event):
        if not self.movable:
            return
        x = event.x_root - self._drag_data["x"]
        y = event.y_root - self._drag_data["y"]
        self.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        if not self.movable:
            return
        self.config_data["x"] = self.winfo_x()
        self.config_data["y"] = self.winfo_y()
        save_config(self.config_data)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("PUBG Reset TCP Connections")
        self.root.geometry("650x400")
        self.config = load_config()
        self.create_widgets()
        self.create_tray_icon()
        self.delay = 30  # задержка между нажатием кномки сброса соединений в секундах
        self.last_time = time.monotonic() - 30
        
        # Регистрируем горячую клавишу F8
        self.setup_hotkey()

    def setup_hotkey(self):
        """Настройка глобальной горячей клавиши F8"""
        try:
            # Регистрируем глобальный хоткей F8
            keyboard.add_hotkey('f8', self.hotkey_callback)
            self.logger.info("[+] Горячая клавиша F8 зарегистрирована (глобально)")
        except Exception as e:
            self.logger.error(f"[!] Ошибка регистрации F8: {e}")
            # Если не получилось с глобальным, делаем локальный бинд
            self.root.bind('<F8>', lambda e: self.reset_pubg())
            self.logger.info("[+] Используется локальный бинд F8 (только когда окно активно)")

    def hotkey_callback(self):
        """Callback для горячей клавиши"""
        try:
            # Используем after для безопасного вызова из другого потока
            self.root.after(0, self.reset_pubg)
        except Exception as e:
            print(f"Error in hotkey callback: {e}")

    def create_tray_icon(self):
        # Иконка для трей
        image = Image.new('RGB', (64, 64), color=(255, 0, 0))
        d = ImageDraw.Draw(image)
        d.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
        menu = pystray.Menu(
            pystray.MenuItem('Показать окно', lambda : self.show_window()),
            pystray.MenuItem('Выход', lambda : self.exit_app())
        )
        self.tray_icon = pystray.Icon("PUBGReset", image, "PUBG Reset", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def exit_app(self):
        try:
            # Очищаем хоткеи
            keyboard.unhook_all()
        except:
            pass
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.root.after(0, self.root.destroy)

    def create_widgets(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="PUBG TCP Reset Utility", font=("Segoe UI", 14, "bold")).pack(pady=5)

        # Информация о горячей клавише
        hotkey_frame = ttk.Frame(frame)
        hotkey_frame.pack(pady=2)
        tk.Label(hotkey_frame, text="Горячая клавиша: ", font=("Segoe UI", 10)).pack(side="left")
        tk.Label(hotkey_frame, text="F8", font=("Segoe UI", 10, "bold"), fg="green").pack(side="left")
        tk.Label(hotkey_frame, text=" (глобально)", font=("Segoe UI", 10)).pack(side="left")

        tk.Button(
            frame, text="⟳ Разорвать соединения PUBG", font=("Segoe UI", 12),
            bg="#ff4444", fg="white", relief="flat", command=self.reset_pubg
        ).pack(pady=5)

        settings = ttk.LabelFrame(frame, text="Настройки кнопки")
        settings.pack(fill="x", pady=5)

        tk.Label(settings, text="Цвет кнопки:").grid(row=0, column=0, sticky="e")
        self.button_color = tk.Entry(settings, width=10)
        self.button_color.insert(0, self.config["button_color"])
        self.button_color.grid(row=0, column=1, padx=5)

        tk.Label(settings, text="Цвет текста:").grid(row=0, column=2, sticky="e")
        self.text_color = tk.Entry(settings, width=10)
        self.text_color.insert(0, self.config["text_color"])
        self.text_color.grid(row=0, column=3, padx=5)

        tk.Label(settings, text="Текст:").grid(row=1, column=0, sticky="e")
        self.text_entry = tk.Entry(settings, width=10)
        self.text_entry.insert(0, self.config["button_text"])
        self.text_entry.grid(row=1, column=1, padx=5)

        tk.Label(settings, text="Ширина:").grid(row=1, column=2, sticky="e")
        self.width_entry = tk.Entry(settings, width=5)
        self.width_entry.insert(0, self.config["width"])
        self.width_entry.grid(row=1, column=3, padx=5)

        tk.Label(settings, text="Высота:").grid(row=2, column=2, sticky="e")
        self.height_entry = tk.Entry(settings, width=5)
        self.height_entry.insert(0, self.config["height"])
        self.height_entry.grid(row=2, column=3, padx=5)

        self.movable_var = tk.BooleanVar(value=self.config["movable"])
        tk.Checkbutton(settings, text="Разрешить перетаскивание", variable=self.movable_var).grid(
            row=2, column=0, columnspan=2, sticky="w"
        )

        tk.Button(settings, text="💾 Сохранить", command=self.save_settings).grid(row=3, column=0, columnspan=4, pady=5)

        tk.Label(frame, text="Логи:").pack(anchor="w")
        self.log_text = tk.Text(frame, height=10, bg="#111", fg="#0f0", insertbackground="#0f0")
        self.log_text.pack(fill="both", expand=True, pady=5)

        self.logger = logging.getLogger("PUBGReset")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = []
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        self.logger.addHandler(file_handler)
        self.logger.addHandler(TextHandler(self.log_text))

        self.create_floating()

    def reset_pubg(self):
        now = time.monotonic()
        if now - self.last_time >= self.delay:
            threading.Thread(target=self._reset_thread, daemon=True).start()
            self.last_time = now
        else:
            p = str(abs(int(now - self.last_time - self.delay)))
            self.logger.warning("Вы сможете нажать кнопку через " + p + " секунд.")

    def _reset_thread(self):
        if not is_admin():
            self.logger.warning("Рекомендуется запускать программу от имени администратора для корректной работы SetTcpEntry.")
        try:
            reset_pubg_connections(self.logger)
        except Exception as e:
            self.logger.error(f"Исключение в reset: {e}")

    def save_settings(self):
        self.config["button_color"] = self.button_color.get()
        self.config["text_color"] = self.text_color.get()
        self.config["button_text"] = self.text_entry.get()
        self.config["width"] = int(self.width_entry.get())
        self.config["height"] = int(self.height_entry.get())
        self.config["movable"] = self.movable_var.get()
        save_config(self.config)

        if hasattr(self, "floating") and self.floating:
            self.floating.btn.configure(
                text=self.config["button_text"],
                bg=self.config["button_color"],
                fg=self.config["text_color"]
            )
            self.floating.geometry(f"{self.config['width']}x{self.config['height']}+{self.config['x']}+{self.config['y']}")
            self.floating.movable = self.config["movable"]

        messagebox.showinfo("Настройки", "Настройки сохранены.")

    def create_floating(self):
        if hasattr(self, "floating") and self.floating:
            try:
                self.floating.destroy()
            except Exception:
                pass
        self.floating = FloatingButton(self.root, on_click=self.reset_pubg, config=self.config)

    def on_close(self):
        # При закрытии окна прячем в трей
        self.root.withdraw()

def main():
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
