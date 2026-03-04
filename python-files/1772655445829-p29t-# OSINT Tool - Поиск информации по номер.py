import ctypes
import random
import time
import winsound
import threading

# Подключаем системные библиотеки Windows
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

def glitch_screen():
    """Инвертирует цвета на экране (эффект негатива)"""
    hdc = user32.GetDC(0)
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)
    
    while True:
        # Инвертируем случайный прямоугольник на экране
        x = random.randint(0, sw)
        y = random.randint(0, sh)
        w = random.randint(100, 500)
        h = random.randint(100, 500)
        
        gdi32.BitBlt(hdc, x, y, w, h, hdc, x, y, 0x550009) # NOTSRCCOPY (инверсия)
        time.sleep(0.1)

def shake_mouse():
    """Заставляет курсор мыши дрожать"""
    while True:
        x, y = random.randint(-5, 5), random.randint(-5, 5)
        user32.SetCursorPos(user32.GetCursorPos()[0] + x, user32.GetCursorPos()[1] + y)
        time.sleep(0.01)

def annoying_beeps():
    """Воспроизводит случайные системные звуки"""
    while True:
        winsound.Beep(random.randint(400, 2000), 100)
        time.sleep(random.random())

def main_prank():
    print("ВНИМАНИЕ: Пранк запущен!")
    print("Чтобы остановить: нажми Ctrl+Alt+Del и заверши процесс python.exe")
    
    # Запускаем все эффекты в разных потоках
    threading.Thread(target=glitch_screen, daemon=True).start()
    threading.Thread(target=shake_mouse, daemon=True).start()
    threading.Thread(target=annoying_beeps, daemon=True).start()

    # Основной цикл, чтобы программа не закрылась сразу
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Пранк остановлен.")

if __name__ == "__main__":
    # Запрашиваем подтверждение, чтобы не запустить случайно
    answer = input("Ты уверен, что хочешь запустить визуальные эффекты? (y/n): ")
    if answer.lower() == 'y':
        main_prank()