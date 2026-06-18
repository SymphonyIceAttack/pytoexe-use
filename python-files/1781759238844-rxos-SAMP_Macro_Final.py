import os
import sys
import time
import ctypes
import random
import threading
import configparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import customtkinter as ctk
from tkinter import messagebox
from ctypes import wintypes

# Используем клавиатуру, а мышь пишем на чистом WinAPI (как в AHK)
import keyboard

# --- НАСТРОЙКА АДМИН-ПРАВ ---
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

KERNEL32 = ctypes.windll.kernel32
USER32 = ctypes.windll.user32

# --- ЖЕСТКОЕ ОПРЕДЕЛЕНИЕ ТИПОВ ДЛЯ 64-БИТНЫХ СИСТЕМ (ФИКС OVERFLOW) ---
USER32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
USER32.DefWindowProcW.restype = wintypes.LPARAM

USER32.GetRawInputData.argtypes = [ctypes.c_void_p, wintypes.UINT, ctypes.c_void_p, wintypes.PUINT, wintypes.UINT]
USER32.GetRawInputData.restype = wintypes.UINT

# --- СТРУКТУРЫ WINAPI ДЛЯ RAW INPUT ---
class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [("dwType", wintypes.DWORD), ("dwSize", wintypes.DWORD), ("hDevice", wintypes.HANDLE), ("wParam", wintypes.WPARAM)]

class RAWMOUSE(ctypes.Structure):
    _fields_ = [("usFlags", wintypes.USHORT), ("ulButtons", wintypes.ULONG), ("ulRawButtons", wintypes.ULONG),
                ("lLastX", wintypes.LONG), ("lLastY", wintypes.LONG), ("ulExtraInformation", wintypes.ULONG)]

class RAWINPUT(ctypes.Structure):
    _fields_ = [("header", RAWINPUTHEADER), ("mouse", RAWMOUSE)]

class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [("usUsagePage", wintypes.USHORT), ("usUsage", wintypes.USHORT), ("dwFlags", wintypes.DWORD), ("hwndTarget", wintypes.HWND)]

# Объявляем тип для CALLBACK-функции оконной процедуры с правильными типами данных
WNDPROC = ctypes.WINFUNCTYPE(wintypes.LPARAM, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

# Правильная структура WNDCLASSW с валидными типами из wintypes
class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HANDLE),          
        ("hCursor", wintypes.HANDLE),        
        ("hbrBackground", wintypes.HANDLE),   
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR)
    ]

class SAMacroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SA Macro - Raw Input Engine")
        self.geometry("450x660")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Файлы
        self.profiles_file = "profiles.txt"
        self.vk_token_file = "vk_settings.txt"
        self.ini_file = os.path.join(os.path.dirname(__file__), "teleport_positions.ini")

        # Состояние
        self.macro_data = []
        self.is_recording = False
        self.is_playing = False
        self.start_time = 0
        self.is_looping = False
        self.block_hook = False

        self.tp_slots = {i: {"X": 0.0, "Y": 0.0, "Z": 0.0} for i in range(1, 5)}

        # Настройка стабильной сессии запросов ВК (фикс ошибок "депрессии к миссии")
        self.http_session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        self.http_session.mount("https://", HTTPAdapter(max_retries=retries))

        self.init_data_files()
        self.load_positions_from_ini()

        # Интерфейс
        self.lbl_info = ctk.CTkLabel(self, text="J - Сброс камеры | F9 - Запись | F10 - Стоп\nF11 - Старт | F12 - Стоп макроса\nСохранить: Alt + 4/5/6/7 | ТП: Нажать 4/5/6/7")
        self.lbl_info.pack(pady=10)

        self.check_loop = ctk.CTkCheckBox(self, text="Зациклить воспроизведение", command=self.update_loop_status)
        self.check_loop.pack(anchor="w", padx=30, pady=4)

        self.check_x = ctk.CTkCheckBox(self, text="Записывать ось X (Влево / Вправо)", command=lambda: self.notify_checkbox_change("Запись оси X", self.check_x.get()))
        self.check_x.pack(anchor="w", padx=30, pady=4)
        self.check_x.select()

        self.check_y = ctk.CTkCheckBox(self, text="Записывать ось Y (Вверх / Вниз)", command=lambda: self.notify_checkbox_change("Запись оси Y", self.check_y.get()))
        self.check_y.pack(anchor="w", padx=30, pady=4)
        self.check_y.select()

        self.check_cam = ctk.CTkCheckBox(self, text="Сбросить камеру (старт/новый круг)", command=lambda: self.notify_checkbox_change("Сброс камеры", self.check_cam.get()))
        self.check_cam.pack(anchor="w", padx=30, pady=4)
        self.check_cam.select()

        self.check_tp = ctk.CTkCheckBox(self, text="Включить Телепорт", command=lambda: self.notify_checkbox_change("Функция Телепорта", self.check_tp.get()))
        self.check_tp.pack(anchor="w", padx=30, pady=4)
        self.check_tp.select()

        self.lbl_vk = ctk.CTkLabel(self, text="--- НАСТРОЙКИ VK ---", text_color="blue", font=ctk.CTkFont(weight="bold"))
        self.lbl_vk.pack(anchor="w", padx=30, pady=(10, 2))

        self.check_vk = ctk.CTkCheckBox(self, text="Включить уведомления ВК", command=self.save_vk_config_now)
        self.check_vk.pack(anchor="w", padx=30, pady=4)
        if self.vk_settings["enabled"]: self.check_vk.select()

        self.entry_token = ctk.CTkEntry(self, width=390, placeholder_text="Токен")
        self.entry_token.pack(pady=2)
        self.entry_token.insert(0, self.vk_settings["token"])
        self.entry_token.bind("<FocusOut>", lambda e: self.save_vk_config_now())

        self.vk_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.vk_frame.pack(fill="x", padx=30, pady=2)
        
        self.entry_vk_id = ctk.CTkEntry(self.vk_frame, width=280, placeholder_text="Ваш VK ID")
        self.entry_vk_id.pack(side="left")
        self.entry_vk_id.insert(0, self.vk_settings["id"])
        self.entry_vk_id.bind("<FocusOut>", lambda e: self.save_vk_config_now())

        self.btn_vk_test = ctk.CTkButton(self.vk_frame, text="Тест", width=100, command=self.test_vk_connection)
        self.btn_vk_test.pack(side="right")

        self.combo_profiles = ctk.CTkComboBox(self, width=390, values=self.profile_array)
        self.combo_profiles.pack(pady=10)

        self.add_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.add_frame.pack(fill="x", padx=30, pady=2)

        self.entry_new_profile = ctk.CTkEntry(self.add_frame, width=280, placeholder_text="Название новой работы")
        self.entry_new_profile.pack(side="left")

        self.btn_add = ctk.CTkButton(self.add_frame, text="+", width=100, command=self.add_custom_profile)
        self.btn_add.pack(side="right")

        self.file_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.file_frame.pack(fill="x", padx=30, pady=15)

        self.btn_save = ctk.CTkButton(self.file_frame, text="Сохранить", width=185, command=self.save_macro_to_file)
        self.btn_save.pack(side="left")

        self.btn_load = ctk.CTkButton(self.file_frame, text="Загрузить", width=185, command=self.load_macro_from_file)
        self.btn_load.pack(side="right")

        self.lbl_status = ctk.CTkLabel(self, text="Статус: Ожидание", text_color="gray", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_status.pack(pady=5)

        # Хук клавиатуры
        keyboard.hook(self.global_key_callback)

        # Регистрация Raw Input для мыши
        self.setup_raw_input()

        self.send_vk_message("🚀 Макрос-бот запущен и готов к работе!")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def is_samp_active(self):
        hwnd = USER32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(512)
        USER32.GetWindowTextW(hwnd, buf, 512)
        return any(x in buf.value for x in ["GTA:SA", "Grand Theft Auto", "GTA:SA:MP"])

    # --- ИНИЦИАЛИЗАЦИЯ ИНСТРУМЕНТА RAW INPUT ---
    def setup_raw_input(self):
        def create_hidden_window():
            def wnd_proc(hwnd, msg, wparam, lparam):
                if msg == 0x00FF: # WM_INPUT
                    self.process_raw_input_message(lparam)
                return USER32.DefWindowProcW(hwnd, msg, wparam, lparam)

            wc_name = ctypes.create_unicode_buffer("RawInputWindow")
            self._proc_ref = WNDPROC(wnd_proc) # Защита от Garbage Collector
            
            class_struct = WNDCLASSW()
            class_struct.lpfnWndProc = self._proc_ref
            class_struct.lpszClassName = wc_name.value
            class_struct.hInstance = KERNEL32.GetModuleHandleW(None)
            
            USER32.RegisterClassW(ctypes.byref(class_struct))
            hwnd = USER32.CreateWindowExW(0, wc_name.value, wc_name.value, 0, 0, 0, 0, 0, 0, 0, None, None)
            
            rid = RAWINPUTDEVICE()
            rid.usUsagePage = 1  
            rid.usUsage = 2      
            rid.dwFlags = 0x00000100  # RIDEV_INPUTSINK
            rid.hwndTarget = hwnd
            USER32.RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(rid))

            msg = wintypes.MSG()
            while USER32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
                USER32.TranslateMessage(ctypes.byref(msg))
                USER32.DispatchMessageW(ctypes.byref(msg))

        threading.Thread(target=create_hidden_window, daemon=True).start()

    # --- ИСПРАВЛЕННЫЙ ЗАХВАТ МЫШИ (ДВИЖЕНИЯ + КЛИКИ ЛКМ И ПКМ) ---
    def process_raw_input_message(self, lparam):
        if not self.is_recording or self.block_hook or not self.is_samp_active():
            return

        size = wintypes.UINT()
        USER32.GetRawInputData(ctypes.c_void_p(lparam), 0x10000003, None, ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER))
        
        if size.value > 0:
            raw = RAWINPUT()
            USER32.GetRawInputData(ctypes.c_void_p(lparam), 0x10000003, ctypes.byref(raw), ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER))
            
            if raw.header.dwType == 0: # RIM_TYPEMOUSE
                flags = raw.mouse.ulButtons
                cur_t = (time.perf_counter() - self.start_time) * 1000
                
                # Проверяем клики ЛКМ (0x0001 - Нажата, 0x0002 - Отпущена)
                if flags & 0x0001: self.macro_data.append({"t": cur_t, "type": "K", "key": "lbutton", "state": "D"})
                if flags & 0x0002: self.macro_data.append({"t": cur_t, "type": "K", "key": "lbutton", "state": "U"})
                
                # Проверяем клики ПКМ (0x0004 - Нажата, 0x0008 - Отпущена)
                if flags & 0x0004: self.macro_data.append({"t": cur_t, "type": "K", "key": "rbutton", "state": "D"})
                if flags & 0x0008: self.macro_data.append({"t": cur_t, "type": "K", "key": "rbutton", "state": "U"})
                
                # Считываем движение осей мыши
                dx = raw.mouse.lLastX if self.check_x.get() else 0
                dy = raw.mouse.lLastY if self.check_y.get() else 0
                
                if dx != 0 or dy != 0:
                    self.macro_data.append({"t": cur_t, "type": "M", "x": dx, "y": dy})

    # --- ОБРАБОТКА ХОТКЕЕВ КЛАВИАТУРЫ ---
    def global_key_callback(self, event):
        if not self.is_samp_active(): return
        key_name = event.name.lower()
        is_down = (event.event_type == "down")

        if is_down:
            if key_name == "j": self.center_camera_3d()
            elif key_name == "f9": self.toggle_recording(True)
            elif key_name == "f10": self.toggle_recording(False)
            elif key_name == "f11":
                if not self.is_playing: threading.Thread(target=self.play_macro, daemon=True).start()
            elif key_name == "f12": self.stop_playback()

        if self.check_tp.get() and key_name in ["4", "5", "6", "7"]:
            slot = int(key_name) - 3
            alt_pressed = keyboard.is_pressed('alt')
            if is_down:
                if alt_pressed:
                    if self.save_current_position(slot):
                        KERNEL32.Beep(700 + (slot * 200), 150)
                        if self.is_recording:
                            self.macro_data.append({"t": (time.perf_counter() - self.start_time)*1000, "type": "K", "key": f"s{slot}", "state": "D"})
                else:
                    if self.teleport_to_saved_position(slot):
                        KERNEL32.Beep(400 + (slot * 100), 150)
                        if self.is_recording:
                            self.macro_data.append({"t": (time.perf_counter() - self.start_time)*1000, "type": "K", "key": f"t{slot}", "state": "D"})
            return

        if self.is_recording and not self.block_hook:
            if key_name not in ["f9", "f10", "f11", "f12", "j", "alt"]:
                cur_t = (time.perf_counter() - self.start_time) * 1000
                state_str = "D" if is_down else "U"
                if len(self.macro_data) > 0 and self.macro_data[-1]["type"] == "K" and self.macro_data[-1]["key"] == key_name and self.macro_data[-1]["state"] == state_str:
                    return
                self.macro_data.append({"t": cur_t, "type": "K", "key": key_name, "state": state_str})

    # --- ВОСПРОИЗВЕДЕНИЕ ---
    def move_mouse_relative(self, dx, dy):
        USER32.mouse_event(0x0001, int(dx), int(dy), 0, 0)

    def simulate_key(self, key_str, state):
        if key_str == "lbutton": USER32.mouse_event(0x0002 if state == "D" else 0x0004, 0, 0, 0, 0)
        elif key_str == "rbutton": USER32.mouse_event(0x0008 if state == "D" else 0x0010, 0, 0, 0, 0)
        elif key_str == "mbutton": USER32.mouse_event(0x0020 if state == "D" else 0x0040, 0, 0, 0, 0)
        else:
            try:
                if state == "D": keyboard.press(key_str)
                else: keyboard.release(key_str)
            except: pass

    def native_center_camera(self):
        self.block_hook = True
        self.move_mouse_relative(0, 10000)
        time.sleep(0.05)
        self.move_mouse_relative(0, -2500)
        time.sleep(0.05)
        self.block_hook = False

    def center_camera_3d(self):
        if self.is_playing or self.is_recording: return
        self.native_center_camera()

    def toggle_recording(self, start):
        if start and not self.is_recording:
            if self.check_cam.get():
                self.update_status_ui("ПОДГОТОВКА...", "orange")
                self.native_center_camera()
                time.sleep(0.2)
            self.is_recording = True
            self.macro_data = []
            self.start_time = time.perf_counter()
            self.update_status_ui("ЗАПИСЬ...", "red")
            self.send_vk_message(f"🔴 Начата запись нового макроса: {self.combo_profiles.get()}")
            KERNEL32.Beep(850, 200)
        elif not start and self.is_recording:
            self.is_recording = False
            self.update_status_ui("Записано", "green")
            self.send_vk_message(f"✅ Запись завершена! Действий: {len(self.macro_data)}")
            KERNEL32.Beep(550, 200)

    def play_macro(self):
        if len(self.macro_data) == 0: return
        self.is_playing = True
        self.update_status_ui("ВОСПРОИЗВЕДЕНИЕ", "blue")
        self.send_vk_message(f"▶️ Запущено воспроизведение макроса [{self.combo_profiles.get()}]")
        
        ctypes.windll.winmm.timeBeginPeriod(1)
        lap_counter = 0
        was_aborted = False

        while self.is_playing:
            lap_counter += 1
            if self.is_looping: self.send_vk_message(f"🔄 Начат круг №{lap_counter}")
            if self.check_cam.get():
                self.native_center_camera()
                time.sleep(0.2)

            start_time_ticks = time.perf_counter() * 1000

            for e in self.macro_data:
                if not self.is_playing:
                    was_aborted = True
                    break

                target_time = start_time_ticks + e["t"]
                while (time.perf_counter() * 1000) < target_time:
                    diff = target_time - (time.perf_counter() * 1000)
                    if diff > 2: time.sleep(0.001)

                if e["type"] == "K":
                    low_key = e["key"]
                    if low_key in ["s1", "t1", "s2", "t2", "s3", "t3", "s4", "t4"]:
                        if self.check_tp.get():
                            slot = int(low_key[1])
                            if low_key[0] == "s": self.save_current_position(slot)
                            else: self.teleport_to_saved_position(slot)
                        continue
                    self.simulate_key(low_key, e["state"])
                else:
                    self.move_mouse_relative(e["x"], e["y"])

            if not self.is_looping or was_aborted: break

        ctypes.windll.winmm.timeEndPeriod(1)
        self.release_all_keys()
        self.is_playing = False
        self.update_status_ui("Готов", "gray")

    def stop_playback(self):
        self.is_playing = False
        self.update_status_ui("Прервано", "orange")

    def release_all_keys(self):
        for key in ["w","a","s","d","space","shift","ctrl"]:
            try: keyboard.release(key)
            except: pass
        USER32.mouse_event(0x0004, 0, 0, 0, 0)
        USER32.mouse_event(0x0010, 0, 0, 0, 0)

    # --- РАБОТА С ПАМЯТЬЮ И INI (ТЕЛЕПОРТ) ---
    def get_gta_process_handle(self):
        hwnd = USER32.FindWindowW("Grand Theft Auto San Andreas", None)
        if not hwnd: hwnd = USER32.FindWindowW(None, "GTA:SA:MP")
        if not hwnd: return None
        pid = ctypes.c_ulong()
        USER32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return KERNEL32.OpenProcess(0x1F0FFF, False, pid.value)

    def save_current_position(self, slot):
        h_proc = self.get_gta_process_handle()
        if not h_proc: return False
        try:
            base_ptr = ctypes.c_ulong()
            KERNEL32.ReadProcessMemory(h_proc, 0xB7CD98, ctypes.byref(base_ptr), 4, None)
            struct_ptr = ctypes.c_ulong()
            KERNEL32.ReadProcessMemory(h_proc, base_ptr.value + 0x14, ctypes.byref(struct_ptr), 4, None)

            x, y, z = ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
            KERNEL32.ReadProcessMemory(h_proc, struct_ptr.value + 0x30, ctypes.byref(x), 4, None)
            KERNEL32.ReadProcessMemory(h_proc, struct_ptr.value + 0x34, ctypes.byref(y), 4, None)
            KERNEL32.ReadProcessMemory(h_proc, struct_ptr.value + 0x38, ctypes.byref(z), 4, None)

            self.tp_slots[slot] = {"X": x.value, "Y": y.value, "Z": z.value}
            
            cfg = configparser.ConfigParser()
            if os.path.exists(self.ini_file): cfg.read(self.ini_file)
            sect = f"Slot{slot}"
            if not cfg.has_section(sect): cfg.add_section(sect)
            cfg.set(sect, "X", str(x.value))
            cfg.set(sect, "Y", str(y.value))
            cfg.set(sect, "Z", str(z.value))
            with open(self.ini_file, "w") as f: cfg.write(f)
            return True
        except: return False
        finally: KERNEL32.CloseHandle(h_proc)

    def teleport_to_saved_position(self, slot):
        pos = self.tp_slots[slot]
        if pos["X"] == 0.0 and pos["Y"] == 0.0: return False
        h_proc = self.get_gta_process_handle()
        if not h_proc: return False
        try:
            base_ptr = ctypes.c_ulong()
            KERNEL32.ReadProcessMemory(h_proc, 0xB7CD98, ctypes.byref(base_ptr), 4, None)
            struct_ptr = ctypes.c_ulong()
            KERNEL32.ReadProcessMemory(h_proc, base_ptr.value + 0x14, ctypes.byref(struct_ptr), 4, None)

            x, y, z = ctypes.c_float(pos["X"]), ctypes.c_float(pos["Y"]), ctypes.c_float(pos["Z"] + 0.2)
            KERNEL32.WriteProcessMemory(h_proc, struct_ptr.value + 0x30, ctypes.byref(x), 4, None)
            KERNEL32.WriteProcessMemory(h_proc, struct_ptr.value + 0x34, ctypes.byref(y), 4, None)
            KERNEL32.WriteProcessMemory(h_proc, struct_ptr.value + 0x38, ctypes.byref(z), 4, None)
            return True
        except: return False
        finally: KERNEL32.CloseHandle(h_proc)

    def load_positions_from_ini(self):
        if not os.path.exists(self.ini_file): return
        try:
            cfg = configparser.ConfigParser()
            cfg.read(self.ini_file)
            for slot in range(1, 5):
                sect = f"Slot{slot}"
                if cfg.has_section(sect):
                    self.tp_slots[slot]["X"] = float(cfg.get(sect, "X", fallback=0.0))
                    self.tp_slots[slot]["Y"] = float(cfg.get(sect, "Y", fallback=0.0))
                    self.tp_slots[slot]["Z"] = float(cfg.get(sect, "Z", fallback=0.0))
        except: pass

    # --- ВК, ПРОФИЛИ И СОХРАНЕНИЯ ---
    def init_data_files(self):
        if not os.path.exists(self.profiles_file):
            with open(self.profiles_file, "w", encoding="utf-8") as f: f.write("Общий\nШахта\nФерма\nЗавод")
        with open(self.profiles_file, "r", encoding="utf-8") as f:
            self.profile_array = [line.strip() for line in f if line.strip()]

        self.vk_settings = {"enabled": 0, "token": "", "id": ""}
        if os.path.exists(self.vk_token_file):
            with open(self.vk_token_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f]
                if len(lines) >= 3: self.vk_settings = {"enabled": int(lines[0]), "token": lines[1], "id": lines[2]}

    def save_vk_config_now(self):
        try:
            with open(self.vk_token_file, "w", encoding="utf-8") as f:
                f.write(f"{1 if self.check_vk.get() else 0}\n{self.entry_token.get().strip()}\n{self.entry_vk_id.get().strip()}")
        except: pass

    def notify_checkbox_change(self, name, val):
        status = "ВКЛЮЧЕНА" if val == 1 else "ВЫКЛЮЧЕНА"
        self.send_vk_message(f"⚙️ Изменение настроек: {name} теперь {status}")

    def update_loop_status(self):
        self.is_looping = self.check_loop.get()
        self.notify_checkbox_change("Зацикленное воспроизведение", self.is_looping)

    def on_close(self):
        self.send_vk_message("🛑 Макрос-бот закрыт или завершил работу. До связи!", sync=True)
        self.save_vk_config_now()
        self.destroy()

    def send_vk_message(self, msg, sync=False):
        if not self.check_vk.get(): return
        token = self.entry_token.get().strip()
        peer_id = self.entry_vk_id.get().strip()
        if not token or not peer_id: return

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*"
        }

        def _async():
            try: 
                self.http_session.post(
                    "https://api.vk.com/method/messages.send", 
                    data={
                        "access_token": token, 
                        "peer_id": peer_id, 
                        "message": msg, 
                        "random_id": random.randint(1, 2147483647), 
                        "v": "5.131"
                    }, 
                    headers=headers,
                    timeout=5
                )
            except: 
                pass

        if sync: _async()
        else: threading.Thread(target=_async, daemon=True).start()

    def test_vk_connection(self):
        self.save_vk_config_now()
        token = self.entry_token.get().strip()
        peer_id = self.entry_vk_id.get().strip()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            r = self.http_session.post(
                "https://api.vk.com/method/messages.send", 
                data={
                    "access_token": token, 
                    "peer_id": peer_id, 
                    "message": "🔔 Тест пройден! Соединение стабильно.", 
                    "random_id": random.randint(1, 2147483647), 
                    "v": "5.131"
                }, 
                headers=headers,
                timeout=5
            ).json()
            if "error" in r: messagebox.showerror("Ошибка VK API", str(r["error"]))
            else: messagebox.showinfo("Успех", "Тестовое уведомление успешно отправлено в VK!")
        except Exception as e: 
            messagebox.showerror("Ошибка сети", "Не удалось достучаться до серверов VK. Проверь интернет или токен!")

    def add_custom_profile(self):
        name = self.entry_new_profile.get().strip()
        if name and name not in self.profile_array:
            self.profile_array.append(name)
            with open(self.profiles_file, "a", encoding="utf-8") as f: f.write(f"\n{name}")
            self.combo_profiles.configure(values=self.profile_array)
        self.combo_profiles.set(name)
        self.entry_new_profile.delete(0, 'end')

    def save_macro_to_file(self):
        if not self.macro_data: return
        filename = f"macro_{self.combo_profiles.get()}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for e in self.macro_data:
                if e["type"] == "K": f.write(f"K,{e['t']},{e['key']},{e['state']}\n")
                else: f.write(f"M,{e['t']},{e['x']},{e['y']}\n")
        messagebox.showinfo("Успех", f"Сохранено: {filename}")

    # --- ИСПРАВЛЕННАЯ ПРОВЕРКА СУЩЕСТВОВАНИЯ КОНФИГА ---
    def load_macro_from_file(self):
        current_profile = self.combo_profiles.get()
        filename = f"macro_{current_profile}.txt"
        
        if not os.path.exists(filename):
            self.update_status_ui(f"ОШИБКА: Конфиг не найден!", "red")
            return
            
        self.macro_data = []
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    p = line.strip().split(",")
                    if p[0] == "K": self.macro_data.append({"type": "K", "t": float(p[1]), "key": p[2], "state": p[3]})
                    elif p[0] == "M": self.macro_data.append({"type": "M", "t": float(p[1]), "x": int(p[2]), "y": int(p[3])})
            self.update_status_ui(f"Загружен: {current_profile}", "green")
        except Exception as e:
            self.update_status_ui("Ошибка чтения файла!", "red")

    def update_status_ui(self, text, color="gray"): self.lbl_status.configure(text=f"Статус: {text}", text_color=color)

if __name__ == "__main__":
    app = SAMacroApp()
    app.mainloop()