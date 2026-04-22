import tkinter as tk
from tkinter import messagebox
import threading
import time
import random
import sys
import os
import ctypes

# Глобальный флаг для остановки
stop_prank = False

def emergency_exit():
    """Следит за нажатием Enter для выхода"""
    global stop_prank
    input()
    stop_prank = True

def block_alt_f4():
    """Блокирует Alt+F4 (чтобы нельзя было закрыть окна этим способом)"""
    def on_close():
        pass  # Ничего не делаем, окно не закрывается
    
    return on_close

def popup_blitz():
    """Шквал окон - до 10 в секунду"""
    global stop_prank
    
    scary_messages = [
        "⚠️ КРИТИЧЕСКАЯ ОШИБКА! ⚠️",
        "💀 ВАШ ПК ЗАРАЖЕН! 💀",
        "🔥 ДАННЫЕ УДАЛЯЮТСЯ... (ШУЧУ) 🔥",
        "👻 ВАС ВЗЛОМАЛИ! 👻",
        "🤖 СИСТЕМА ЗАХВАЧЕНА! 🤖",
        "💣 ВИРУС-МСТИТЕЛЬ АКТИВИРОВАН! 💣",
        "🎯 ВЫ - ЖЕРТВА ПРАНКА! 🎯",
        "⚡ 100% ЗАГРУЗКИ ЦП⚡",
        "🔒 ДОСТУП ЗАБЛОКИРОВАН! 🔒",
        "💰 ПЛАТИТЕ БИТКОИНЫ! 💰",
        "📀 ФОРМАТИРОВАНИЕ ДИСКА C: 📀",
        "🕹️ ДОБРО ПОЖАЛОВАТЬ В МАТРИЦУ! 🕹️",
        "🎪 КОМПЬЮТЕРНЫЙ ЦИРК ПРИЕХАЛ! 🎪",
        "🐍 ЗМЕЙ ПИТОН УКУСИЛ ПК! 🐍",
        "🤪 ТЫ ДУРАЧОК, ЧТО НАЖАЛ! 🤪",
        "💥 ВЗРЫВ ЧЕРЕЗ 5 СЕКУНД... 💥",
        "🎲 ТЫ ПРОИГРАЛ В ЛОТЕРЕЮ! 🎲",р
        "📢  ЭТО ВИРУС! 📢"
    ]
    
    while not stop_prank:
        for _ in range(10):  # Создаём по 5 окон за раз
            if stop_prank:
                break
            
            def create_window():
                if stop_prank:
                    return
                
                root = tk.Tk()
                root.title("🔴🔴🔴 СИСТЕМА ЗАХВАЧЕНА 🔴🔴🔴")
                
                # Делаем окно поверх всех и полноэкранным? Не надо, это бесит
                root.attributes('-topmost', True)
                
                # Блокируем закрытие через крестик
                root.protocol("WM_DELETE_WINDOW", lambda: None)
                
                msg = random.choice(scary_messages)
                
                # Красный фон
                label = tk.Label(root, text=msg, font=("Arial", 20, "bold"), 
                                fg="red", bg="black", pady=30, padx=30)
                label.pack(fill="both", expand=True)
                
                # Кнопка не закрывает окно, а создаёт новое!
                def fake_button():
                    threading.Thread(target=create_window, daemon=True).start()
                
                button = tk.Button(root, text="❌ ЗАКРЫТЬ (НЕ РАБОТАЕТ) ❌", 
                                 command=fake_button, font=("Arial", 12), 
                                 bg="red", fg="white")
                button.pack(pady=20)
                
                # Случайный размер окна
                width = random.randint(300, 600)
                height = random.randint(150, 300)
                root.geometry(f"{width}x{height}")
                
                # Случайная позиция
                x_pos = random.randint(0, 800)
                y_pos = random.randint(0, 600)
                root.geometry(f"+{x_pos}+{y_pos}")
                
                # Автоматическое закрытие через 3 секунды (чтобы не перегружать)
                root.after(3000, root.destroy)
                
                root.mainloop()
            
            threading.Thread(target=create_window, daemon=True).start()
            time.sleep(0.05)  # Очень быстрый запуск окон
        
        time.sleep(0.3)  # Небольшая пауза перед следующей волной

def endless_message_boxes():
    """Бесконечные messagebox'ы (их нельзя игнорировать)"""
    global stop_prank
    
    errors = [
        "SYSTEM FAILURE",
        "MEMORY CORRUPTED",
        "VIRUS DETECTED",
        "HACKER ATTACK",
        "DATA LOST",
        "FATAL ERROR",
        "SYSTEM SHUTDOWN",
        "CRITICAL ALERT"
    ]
    
    while not stop_prank:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        msg = random.choice(errors)
        messagebox.showerror(f"⚠️ {msg} ⚠️", 
                            f"ОШИБКА #{random.randint(1000, 9999)}: {msg}\n\n"
                            f"Ваш компьютер находится под атакой!\n"
                            f"НЕ ЗАКРЫВАЙТЕ ЭТО ОКНО!\n\n"
                            f"(Это просто пранк, всё в порядке)")
        
        root.destroy()
        time.sleep(0.2)

def mouse_jitter():
    """Агрессивное дёрганье мыши"""
    while not stop_prank:
        for _ in range(100):
            if stop_prank:
                break
            x = random.randint(-25, 25)
            y = random.randint(-25, 25)
            ctypes.windll.user32.mouse_event(0x0001, x, y, 0, 0)
            time.sleep(0.01)
        time.sleep(1)  # Пауза

def keyboard_jammer():
    """Имитация нажатий клавиш (пишет страшные сообщения)"""
    import ctypes
    from ctypes import wintypes
    
    # Коды клавиш
    KEYEVENTF_KEYDOWN = 0x0000
    KEYEVENTF_KEYUP = 0x0002
    
    messages_to_type = [
        "VIRUS ACTIVATED",
        "YOUR PC IS DEAD",
        "HAHA PRANK",
        "RUN WHILE YOU CAN",
        "SYSTEM HACKED"
    ]
    
    while not stop_prank:
        msg = random.choice(messages_to_type)
        for char in msg:
            if stop_prank:
                break
            # Симулируем ввод (работает в блокноте/чате)
            for ch in char:
                ctypes.windll.user32.keybd_event(ord(ch.upper()), 0, KEYEVENTF_KEYDOWN, 0)
                time.sleep(0.05)
                ctypes.windll.user32.keybd_event(ord(ch.upper()), 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(0x20, 0, KEYEVENTF_KEYDOWN, 0)  # Пробел
            ctypes.windll.user32.keybd_event(0x20, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.1)
        time.sleep(3)

def fake_bsod():
    """Фальшивый синий экран смерти"""
    while not stop_prank:
        time.sleep(15)  # Каждые 15 секунд
        if stop_prank:
            break
        
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(bg='blue')
        
        # Блокируем закрытие
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        text = tk.Label(root, text="""
    ⚠️  КРИТИЧЕСКАЯ ОШИБКА  ⚠️
    
    Ваш компьютер столкнулся с проблемой
    и должен быть перезагружен.
    
    Ошибка: PRANK_VIRUS_DETECTED
    
    Что делать?
    1. Нажмите Enter в консоли (где запущен скрипт)
    2. Наслаждайтесь пранком
    3. Не паникуйте, это просто шутка!
    
    Для выхода: нажмите Enter в окне консоли
        """, font=("Consolas", 18, "bold"), fg="white", bg="blue")
        text.pack(expand=True)
        
        root.after(5000, root.destroy)  # Закроется через 5 сек
        root.mainloop()

def reverse_mouse():
    """Инвертирует движение мыши (влево-вправо меняются местами)"""
    # Это сложно реализовать без драйвера, сделаем более простую версию
    while not stop_prank:
        # Внезапно уводим мышь в угол
        time.sleep(random.randint(3, 8))
        if stop_prank:
            break
        ctypes.windll.user32.SetCursorPos(random.randint(0, 500), random.randint(0, 500))
        time.sleep(0.5)

def console_rain():
    """Консольный дождь из символов"""
    chars = "!@#$%^&*()_+{}|:<>?~`"
    while not stop_prank:
        line = "".join(random.choice(chars) for _ in range(50))
        print(f"\033[91m{line}\033[0m")  # Красный цвет в терминале
        time.sleep(0.05)

def beep_attack():
    """Атака звуковыми сигналами"""
    while not stop_prank:
        for freq in [1000, 2000, 1500, 2500, 800]:
            if stop_prank:
                break
            try:
                import winsound
                winsound.Beep(freq, 100)
            except:
                pass
            time.sleep(0.1)
        time.sleep(2)

# ЗАПУСК - МГНОВЕННЫЙ И ЖЁСТКИЙ
if __name__ == "__main__":
    # Сначала проверяем права
    try:
        # Скрываем консоль (опционально, чтобы было страшнее)
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.ShowWindow(hwnd, 0)  # Скрываем консоль
    except:
        pass
    
    # Предупреждение на весь экран
    splash = tk.Tk()
    splash.attributes('-fullscreen', True)
    splash.attributes('-topmost', True)
    splash.configure(bg='black')
    
    warning_text = tk.Label(splash, text="""
    
    ⚠️⚠️⚠️  ВНИМАНИЕ!  ⚠️⚠️⚠️
    
    ПРАНК АКТИВИРОВАН В ЖЁСТКОМ РЕЖИМЕ
    
    - Окна будут появляться сотнями
    - Мышь будет сходить с ума
    - Будут звуковые эффекты
    - И многое другое...
    
    ДЛЯ ОСТАНОВКИ:
    Нажмите ENTER в окне консоли (оно скрыто, но активно)
    Или нажмите Ctrl+C в консоли
    
    ПРИЯТНОГО ВЕСЕЛЬЯ! 😈
    """, font=("Arial", 24, "bold"), fg="red", bg="black")
    warning_text.pack(expand=True)
    
    splash.after(3000, splash.destroy)  # Показываем 3 секунды
    splash.mainloop()
    
    # Показываем консоль обратно
    try:
        ctypes.windll.user32.ShowWindow(hwnd, 5)
    except:
        pass
    
    print("=" * 60)
    print("🔴🔴🔴 ЖЁСТКИЙ ПРАНК АКТИВИРОВАН! 🔴🔴🔴")
    print("Для остановки нажми ENTER в этом окне")
    print("Если перестанет отвечать - зажми Enter на 5 секунд")
    print("=" * 60)
    print()
    
    # Запускаем ВСЕ эффекты одновременном ш к 
    threads = [
        threading.Thread(target=popup_blitz, daemon=True),
        threading.Thread(target=endless_message_boxes, daemon=True),
        threading.Thread(target=mouse_jitter, daemon=True),
        threading.Thread(target=keyboard_jammer, daemon=True),
        threading.Thread(target=fake_bsod, daemon=True),
        threading.Thread(target=reverse_mouse, daemon=True),
        threading.Thread(target=console_rain, daemon=True),
        threading.Thread(target=beep_attack, daemon=True)
    ]
    
    for t in threads:
        t.start()
    
    # Ждём нажатия Enter
    try:
        emergency_exit()
    except:
        pass
    
    print("\n✅✅✅ Пранк остановлен! ✅✅✅")
    print("Надеюсь, было весело (или страшно)!")
    time.sleep(2)