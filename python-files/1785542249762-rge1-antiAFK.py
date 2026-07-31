import pyautogui
import time
import threading
import tkinter as tk
from tkinter import ttk
import ctypes
from ctypes import wintypes
import sys

# Отключаем безопасные задержки pyautogui
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# Windows API для SendInput (для GTA 5)
INPUT_KEYBOARD = 1
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Скан-коды клавиш для DirectInput (работает в GTA 5)
SCAN_CODES = {
    'd': 0x20,
    'a': 0x1E,
    'i': 0x17,
    'f2': 0x3C,
    'up': 0xC8,  # Стрелка вверх
}

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION)
    ]

def send_key_scan(scan_code, press=True):
    inputs = (INPUT * 1)()
    inputs[0].type = INPUT_KEYBOARD
    inputs[0].union.ki.wScan = scan_code
    inputs[0].union.ki.dwFlags = KEYEVENTF_SCANCODE | (KEYEVENTF_KEYDOWN if press else KEYEVENTF_KEYUP)
    inputs[0].union.ki.time = 0
    inputs[0].union.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inputs), ctypes.sizeof(INPUT))

def press_key(key):
    scan_code = SCAN_CODES.get(key.lower())
    if scan_code:
        send_key_scan(scan_code, True)
        time.sleep(0.05)
        send_key_scan(scan_code, False)
        time.sleep(0.05)
        return True
    return False

def hold_key(key, duration):
    scan_code = SCAN_CODES.get(key.lower())
    if scan_code:
        send_key_scan(scan_code, True)
        time.sleep(duration)
        send_key_scan(scan_code, False)
        return True
    return False

# Базовые действия
actions = [
    (1, "Ожидание", "wait", "", 15),
    (2, "Зажатие D", "hold", "D", 0.5),
    (3, "Ожидание", "wait_pause", "", 30),
    (4, "Зажатие A", "hold", "A", 0.5),
    (5, "Ожидание", "wait_pause", "", 30),
    (6, "Нажатие I", "press", "I", 0),
    (7, "Ожидание", "wait_pause", "", 30),
    (8, "Нажатие I (2)", "press", "I", 0),
    (9, "Ожидание", "wait_pause", "", 30),
    (10, "Нажатие F2", "press", "F2", 0),
    (11, "Ожидание", "wait_pause", "", 30),
    (12, "Нажатие F2 (2)", "press", "F2", 0),
    (13, "Ожидание", "wait_pause", "", 30),
    (14, "Стрелка вверх", "press", "up", 0),
    (15, "Ожидание", "wait_pause", "", 30),
    (16, "Стрелка вверх (2)", "press", "up", 0),
]

# Настройки регулируемых пауз
wait_pauses = {
    3: 30,   # После D
    5: 30,   # После A
    7: 30,   # После I
    9: 30,   # После I2
    11: 30,  # После F2
    13: 30,  # После F2 (2) - перед стрелкой
    15: 30,  # После первой стрелки
}

# Глобальные переменные
running = False
current_action = "Ожидание"
next_action_text = "Нажмите СТАРТ"
time_to_next = 0
loop_count = 0
start_time_program = None

def format_time(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def update_timer():
    global start_time_program
    while running:
        if start_time_program:
            elapsed = time.time() - start_time_program
            timer_var.set(format_time(elapsed))
        time.sleep(0.1)

def update_status():
    try:
        status_var.set(current_action)
        next_action_var.set(next_action_text)
        if time_to_next > 0:
            time_next_var.set(f"{time_to_next:.1f}с")
        else:
            time_next_var.set("---")
        loops_var.set(str(loop_count))
        root.update_idletasks()
    except:
        pass

def wait_with_live_display(seconds, next_act_name):
    global time_to_next, next_action_text
    next_action_text = f"➡️ {next_act_name}"
    for i in range(int(seconds * 10), -1, -1):
        if not running:
            return False
        time_to_next = i / 10
        update_status()
        time.sleep(0.1)
    time_to_next = 0
    update_status()
    return True

def execute_single_cycle():
    global running, current_action, next_action_text, time_to_next
    
    for i, (step, name, act_type, key, default_delay) in enumerate(actions):
        if not running:
            return False
        
        if act_type == "wait_pause":
            wait_time = wait_pauses.get(step, default_delay)
        elif act_type == "wait":
            wait_time = default_delay
        else:
            wait_time = 0
        
        next_name = actions[i + 1][1] if i + 1 < len(actions) else "Новый цикл"
        
        current_action = f"▶️ {name}"
        next_action_text = f"➡️ {next_name}"
        update_status()
        
        if act_type == "wait" or act_type == "wait_pause":
            if wait_time > 0:
                if not wait_with_live_display(wait_time, next_name):
                    return False
        elif act_type == "press":
            press_key(key)
        elif act_type == "hold":
            hold_key(key, default_delay)
    
    return True

def main_loop():
    global running, loop_count, current_action
    cycle_num = 0
    while running:
        cycle_num += 1
        loop_count = cycle_num
        update_status()
        
        print(f"\n{'='*40}")
        print(f"🔄 ЦИКЛ {cycle_num}")
        print(f"{'='*40}")
        
        if not execute_single_cycle():
            break
        
        print(f"✅ ЦИКЛ {cycle_num} ЗАВЕРШЁН")
        
        if running:
            for i in range(20, -1, -1):
                if not running:
                    break
                time_to_next = i / 10
                current_action = f"⏸️ Пауза (цикл #{cycle_num})"
                next_action_text = "🔄 Новый цикл"
                update_status()
                time.sleep(0.1)
    
    current_action = "⏹️ Стоп"
    next_action_text = "---"
    time_to_next = 0
    update_status()

def start_sequence():
    global running, start_time_program, loop_count
    if running:
        return
    running = True
    loop_count = 0
    start_time_program = time.time()
    timer_thread = threading.Thread(target=update_timer, daemon=True)
    timer_thread.start()
    main_thread = threading.Thread(target=main_loop, daemon=True)
    main_thread.start()
    start_btn.config(state=tk.DISABLED)
    stop_btn.config(state=tk.NORMAL)

def stop_sequence():
    global running
    running = False
    start_btn.config(state=tk.NORMAL)
    stop_btn.config(state=tk.DISABLED)

def update_wait_pause(step, value):
    wait_pauses[step] = value

# GUI
root = tk.Tk()
root.title("GTA5 Macro")
root.geometry("500x650")
root.resizable(False, False)

# Canvas с прокруткой
canvas = tk.Canvas(root)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

main_frame = scrollable_frame

# Переменные
status_var = tk.StringVar(value="Ожидание")
next_action_var = tk.StringVar(value="Нажмите СТАРТ")
time_next_var = tk.StringVar(value="---")
timer_var = tk.StringVar(value="00:00")
loops_var = tk.StringVar(value="0")

# Таймер
timer_frame = ttk.LabelFrame(main_frame, text="⏱️ Время работы", padding=5)
timer_frame.pack(fill=tk.X, pady=5, padx=5)

timer_label = ttk.Label(timer_frame, textvariable=timer_var, font=("Arial", 24, "bold"), foreground="green")
timer_label.pack(pady=3)

# Предупреждение
warning_frame = ttk.LabelFrame(main_frame, text="⚠️ Важно", padding=5)
warning_frame.pack(fill=tk.X, pady=5, padx=5)

ttk.Label(warning_frame, text="Админ → GTA5 активно → Оконный режим", 
          foreground="red", font=("Arial", 8)).pack(anchor="w")

# Статус
status_frame = ttk.LabelFrame(main_frame, text="📊 Статус", padding=5)
status_frame.pack(fill=tk.X, pady=5, padx=5)

ttk.Label(status_frame, text="Действие:", font=("Arial", 8, "bold")).grid(row=0, column=0, sticky="w")
ttk.Label(status_frame, textvariable=status_var, foreground="blue", font=("Arial", 8)).grid(row=0, column=1, sticky="w", padx=5)

ttk.Label(status_frame, text="Следующее:", font=("Arial", 8, "bold")).grid(row=1, column=0, sticky="w")
ttk.Label(status_frame, textvariable=next_action_var, foreground="orange", font=("Arial", 8)).grid(row=1, column=1, sticky="w", padx=5)

ttk.Label(status_frame, text="Через:", font=("Arial", 8, "bold")).grid(row=2, column=0, sticky="w")
ttk.Label(status_frame, textvariable=time_next_var, foreground="red", font=("Arial", 10, "bold")).grid(row=2, column=1, sticky="w", padx=5)

ttk.Label(status_frame, text="Циклов:", font=("Arial", 8, "bold")).grid(row=3, column=0, sticky="w")
ttk.Label(status_frame, textvariable=loops_var, foreground="purple", font=("Arial", 10, "bold")).grid(row=3, column=1, sticky="w", padx=5)

# Настройка пауз
settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Настройка пауз (шаг 5с, без лимита)", padding=5)
settings_frame.pack(fill=tk.X, pady=5, padx=5)

row = 0
for step, name in [(3, "После D"), (5, "После A"), (7, "После I (1)"), (9, "После I (2)"), 
                   (11, "После F2 (1)"), (13, "После F2 (2)"), (15, "После стрелки (1)")]:
    ttk.Label(settings_frame, text=name, font=("Arial", 8)).grid(row=row, column=0, padx=3, pady=2, sticky="w")
    
    var = tk.IntVar(value=wait_pauses[step])
    spinbox = ttk.Spinbox(settings_frame, from_=0, to=999999, increment=5, textvariable=var, width=8)
    spinbox.grid(row=row, column=1, padx=3, pady=2)
    
    btn = ttk.Button(settings_frame, text="✅", command=lambda s=step, v=var: update_wait_pause(s, v.get()), width=2)
    btn.grid(row=row, column=2, padx=3, pady=2)
    
    row += 1

# Список действий
seq_frame = ttk.LabelFrame(main_frame, text="📋 Последовательность", padding=5)
seq_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

text_frame = ttk.Frame(seq_frame)
text_frame.pack(fill=tk.BOTH, expand=True)

sequence_text = tk.Text(text_frame, height=18, width=55, font=("Consolas", 8))
scrollbar_text = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=sequence_text.yview)
sequence_text.configure(yscrollcommand=scrollbar_text.set)

scrollbar_text.pack(side=tk.RIGHT, fill=tk.Y)
sequence_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

seq_text = """┌──┬─────────────────┬────────────┬──────────┐
│# │Действие         │Тип         │Длит-ть   │
├──┼─────────────────┼────────────┼──────────┤
│1 │Ожидание         │Пауза       │15 сек    │
│2 │D                │Зажатие     │0.5 сек   │
│3 │Ожидание         │Пауза       │⚙️ 30 сек │
│4 │A                │Зажатие     │0.5 сек   │
│5 │Ожидание         │Пауза       │⚙️ 30 сек │
│6 │I                │Нажатие     │0 сек     │
│7 │Ожидание         │Пауза       │⚙️ 30 сек │
│8 │I (2)            │Нажатие     │0 сек     │
│9 │Ожидание         │Пауза       │⚙️ 30 сек │
│10│F2               │Нажатие     │0 сек     │
│11│Ожидание         │Пауза       │⚙️ 30 сек │
│12│F2 (2)           │Нажатие     │0 сек     │
│13│Ожидание         │Пауза       │⚙️ 30 сек │
│14│Стрелка вверх    │Нажатие     │0 сек     │
│15│Ожидание         │Пауза       │⚙️ 30 сек │
│16│Стрелка вверх (2)│Нажатие     │0 сек     │
└──┴─────────────────┴────────────┴──────────┘

⚙️ = регулируется в настройках выше (шаг 5с, без лимита)
🔄 Бесконечный цикл (пауза между циклами 2с)"""

sequence_text.insert(tk.END, seq_text)
sequence_text.config(state=tk.DISABLED)

# Кнопки
button_frame = ttk.Frame(main_frame)
button_frame.pack(fill=tk.X, pady=10, padx=5)

start_btn = ttk.Button(button_frame, text="▶ СТАРТ", command=start_sequence, width=12)
start_btn.pack(side=tk.LEFT, padx=3)

stop_btn = ttk.Button(button_frame, text="⏹ СТОП", command=stop_sequence, width=12, state=tk.DISABLED)
stop_btn.pack(side=tk.LEFT, padx=3)

exit_btn = ttk.Button(button_frame, text="✖ ВЫХОД", command=root.destroy, width=12)
exit_btn.pack(side=tk.LEFT, padx=3)

root.mainloop()