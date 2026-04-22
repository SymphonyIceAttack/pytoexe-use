import tkinter as tk
from tkinter import messagebox
import threading
import time
import random
import sys
import os

# Глобальный флаг для остановки
stop_prank = False

def emergency_exit():
    """Следит за нажатием Enter для выхода"""
    global stop_prank
    input()
    stop_prank = True

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
        "⚡ 100% ЗАГРУЗКИ ЦП ⚡",
        "🔒 ДОСТУП ЗАБЛОКИРОВАН! 🔒",
        "💰 ПЛАТИТЕ БИТКОИНЫ! (ШУТКА) 💰",
        "📀 ФОРМАТИРОВАНИЕ ДИСКА C: 📀",
        "🕹️ ДОБРО ПОЖАЛОВАТЬ В МАТРИЦУ! 🕹️",
        "🎪 КОМПЬЮТЕРНЫЙ ЦИРК ПРИЕХАЛ! 🎪",
        "🐍 ЗМЕЙ ПИТОН УКУСИЛ ПК! 🐍",
        "🤪 ТЫ ДУРАЧОК, ЧТО НАЖАЛ! 🤪",
        "💥 ВЗРЫВ ЧЕРЕЗ 5 СЕКУНД... 💥",
        "🎲 ТЫ ПРОИГРАЛ В ЛОТЕРЕЮ! 🎲",
        "📢 ВНИМАНИЕ! ЭТО НЕ ВИРУС! АХАХА 📢",
        "😈 ТЕБЯ ПРАНКАНУЛИ! 😈",
        "🎉 СЮРПРИЗ! 🎉",
        "🤡 КТО ТУТ ГЛУПЫЙ? 🤡"
    ]
    
    while not stop_prank:
        # Создаём несколько окон подряд
        for _ in range(3):
            if stop_prank:
                break
            
            # Создаём окно
            root = tk.Tk()
            root.title("🔴🔴🔴 ВНИМАНИЕ 🔴🔴🔴")
            
            # Делаем окно поверх всех
            root.attributes('-topmost', True)
            
            # Случайное сообщение
            msg = random.choice(scary_messages)
            
            # Красный фон и большой текст
            label = tk.Label(root, text=msg, font=("Arial", 16, "bold"), 
                           fg="red", bg="black", pady=30, padx=30)
            label.pack(fill="both", expand=True)
            
            # Кнопка закрытия
            def close_window(w):
                w.destroy()
            
            button = tk.Button(root, text="ЗАКРЫТЬ", 
                             command=lambda w=root: close_window(w),
                             font=("Arial", 12), bg="gray", fg="white")
            button.pack(pady=10)
            
            # Случайный размер и позиция
            width = random.randint(300, 500)
            height = random.randint(150, 250)
            x_pos = random.randint(0, 500)
            y_pos = random.randint(0, 300)
            root.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
            
            # Запускаем окно
            root.mainloop()
            
            time.sleep(0.1)
        
        time.sleep(0.5)

def endless_message_boxes():
    """Бесконечные messagebox'ы"""
    global stop_prank
    
    while not stop_prank:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        error_num = random.randint(1000, 9999)
        messagebox.showerror(
            f"⚠️ СИСТЕМНАЯ ОШИБКА {error_num} ⚠️",
            f"Произошла критическая ошибка #{error_num}\n\n"
            f"Ваш компьютер находится под атакой!\n"
            f"(Это просто пранк, всё в порядке)\n\n"
            f"Для выхода нажмите Enter в консоли"
        )
        
        root.destroy()
        time.sleep(0.3)

def console_spam():
    """Спамит в консоль страшными сообщениями"""
    global stop_prank
    
    spam_texts = [
        "[!] ВИРУС ОБНАРУЖЕН [!]",
        "[!] СИСТЕМА ЗАХВАЧЕНА [!]",
        "[!] ДАННЫЕ ШИФРУЮТСЯ... [!]",
        "[!] НЕ ВЫКЛЮЧАЙТЕ КОМПЬЮТЕР [!]",
        "[!] ВАС ВЗЛОМАЛИ [!]",
        "[!] ЭТО ПРОСТО ПРАНК :) [!]",
        "[!] НАЖМИТЕ ENTER ДЛЯ ВЫХОДА [!]",
        "[!] ХА-ХА-ХА [!]",
        "[!] ТЫ ПОПАЛСЯ [!]",
        "[!] ЗАБАВНО, ПРАВДА? [!]"
    ]
    
    while not stop_prank:
        print("=" * 50)
        print(random.choice(spam_texts))
        print("=" * 50)
        time.sleep(1)

def fake_bsod():
    """Фальшивый синий экран смерти"""
    global stop_prank
    
    while not stop_prank:
        time.sleep(12)  # Каждые 12 секунд
        if stop_prank:
            break
        
        root = tk.Toplevel()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(bg='#0000AA')  # Синий цвет как в BSOD
        
        # Блокируем закрытие через крестик
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Белый текст
        text_frame = tk.Frame(root, bg='#0000AA')
        text_frame.pack(expand=True, fill='both')
        
        bsod_text = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                    ⚠️  КРИТИЧЕСКАЯ ОШИБКА  ⚠️               ║
║                                                              ║
║   Ваш компьютер столкнулся с проблемой                       ║
║   и должен быть перезагружен.                                ║
║                                                              ║
║   Ошибка: PRANK_VIRUS_DETECTED                               ║
║                                                              ║
║   Что делать?                                                ║
║   умри                                    ║
║                                                              ║
║   Для выхода: нажмите Enter в окне командной строки          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        
        label = tk.Label(text_frame, text=bsod_text, font=("Consolas", 16, "bold"),
                        fg="white", bg="#0000AA", justify="left")
        label.pack(expand=True)
        
        # Автоматическое закрытие через 6 секунд
        root.after(6000, root.destroy)
        
        root.mainloop()

def blinking_windows():
    """Мерцающие окна счётчика"""
    global stop_prank
    
    while not stop_prank:
        time.sleep(5)
        if stop_prank:
            break
        
        root = tk.Tk()
        root.title("⚠️ СЧЁТЧИК ⚠️")
        root.attributes('-topmost', True)
        root.configure(bg='black')
        
        for i in range(10, 0, -1):
            if stop_prank:
                break
            
            # Очищаем окно
            for widget in root.winfo_children():
                widget.destroy()
            
            # Показываем цифру
            label = tk.Label(root, text=str(i), font=("Arial", 72, "bold"),
                           fg="red", bg="black")
            label.pack(expand=True, padx=50, pady=50)
            
            sublabel = tk.Label(root, text=f"До взлома: {i} сек...", 
                              font=("Arial", 14), fg="white", bg="black")
            sublabel.pack()
            
            root.geometry("300x200")
            root.eval('tk::PlaceWindow . center')
            root.update()
            
            time.sleep(1)
        
        if not stop_prank:
            # Финальное сообщение
            for widget in root.winfo_children():
                widget.destroy()
            
            final_label = tk.Label(root, text="💥 БУМ! 💥\n(шучу)", 
                                  font=("Arial", 24, "bold"),
                                  fg="red", bg="black")
            final_label.pack(expand=True)
            root.update()
            time.sleep(2)
        
        root.destroy()

# ============================================
# ЗАПУСК
# ============================================
if __name__ == "__main__":
    # Показываем предупреждение
    splash = tk.Tk()
    splash.title("ПРЕДУПРЕЖДЕНИЕ")
    splash.attributes('-topmost', True)
    splash.geometry("500x300")
    splash.configure(bg='black')
    
    warning_text = """
    ⚠️⚠️⚠️ ВНИМАНИЕ! ⚠️⚠️⚠️
    
    СЕЙЧАС НАЧНЁТСЯ ПРАНК
    
    - Будут появляться страшные окна
    - Фальшивый синий экран смерти
    - И другие приколы
    
    ДЛЯ ОСТАНОВКИ:
    Нажмите ENTER в окне консоли
    
    ПРИЯТНОГО ВЕСЕЛЬЯ! 😈
    """
    
    label = tk.Label(splash, text=warning_text, font=("Arial", 12, "bold"),
                    fg="red", bg="black", justify="center")
    label.pack(expand=True)
    
    def start_prank():
        splash.destroy()
        print("=" * 60)
        print("🔴🔴🔴 ПРАНК АКТИВИРОВАН! 🔴🔴🔴")
        print("Для остановки нажми ENTER в этом окне")
        print("=" * 60)
        print()
        
        # Запускаем все потоки
        threading.Thread(target=popup_blitz, daemon=True).start()
        threading.Thread(target=endless_message_boxes, daemon=True).start()
        threading.Thread(target=console_spam, daemon=True).start()
        threading.Thread(target=fake_bsod, daemon=True).start()
        threading.Thread(target=blinking_windows, daemon=True).start()
        
        # Ждём нажатия Enter
        emergency_exit()
        
        print("\n✅✅✅ Пранк остановлен! ✅✅✅")
        print("Надеюсь, было весело!")
        time.sleep(2)
    
    # Кнопка старта
    btn = tk.Button(splash, text="ЗАПУСТИТЬ ПРАНК", command=start_prank,
                   font=("Arial", 14, "bold"), bg="red", fg="white")
    btn.pack(pady=20)
    
    splash.mainloop()