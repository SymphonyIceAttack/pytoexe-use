import mouse
import threading
import time
import keyboard

# Флаг для отслеживания состояния ПКМ
rbutton_pressed = False

def check_rbutton():
    global rbutton_pressed
    mouse.on_button(callback, args=('right',), buttons=('right'), types=('down', 'up'))

def callback(event):
    global rbutton_pressed
    if event.event_type == 'down':
        rbutton_pressed = True
    elif event.event_type == 'up':
        if rbutton_pressed:
            rbutton_pressed = False
            # Ждем 1 мс
            time.sleep(0.001)
            # Зажимаем ЛКМ на 2 секунды в отдельном потоке
            threading.Thread(target=hold_lmb, daemon=True).start()

def hold_lmb():
    mouse.press(button='left')
    time.sleep(2)
    mouse.release(button='left')

if __name__ == "__main__":
    print("Скрипт запущен. Зажми и отпусти ПКМ...")
    print("Для выхода нажми 'q'")
    
    # Запускаем проверку ПКМ в отдельном потоке
    thread = threading.Thread(target=check_rbutton, daemon=True)
    thread.start()
    
    # Ждем нажатия 'q' для выхода
    keyboard.wait('q')
    print("Выход...")