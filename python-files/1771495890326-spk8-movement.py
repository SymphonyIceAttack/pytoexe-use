import time
from pynput import keyboard, mouse
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Инициализация данных для хранения времени нажатий
a_press_times = []
d_press_times = []
click_press_times = []

# Флаг для управления состоянием программы
running = False

# Функция для обработки нажатий клавиш
def on_press(key):
    if running:
        if key == keyboard.KeyCode.from_char('a'):
            a_press_times.append(time.time())
        elif key == keyboard.KeyCode.from_char('d'):
            d_press_times.append(time.time())

# Функция для обработки нажатий кнопок мыши
def on_click(x, y, button, pressed):
    if running and pressed:
        click_press_times.append(time.time())

# Функция для обработки горячих клавиш
def on_hotkey():
    global running
    running = not running
    if running:
        print("Программа запущена.")
    else:
        print("Программа остановлена.")

# Настройка горячих клавиш
hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('<shift>+<enter>'),
    on_hotkey
)

# Запуск слушателей клавиатуры и мыши
listener_keyboard = keyboard.Listener(on_press=on_press)
listener_mouse = mouse.Listener(on_click=on_click)
listener_keyboard.start()
listener_mouse.start()

# Настройка графика
fig, ax = plt.subplots()
ax.set_xlabel('Time (s)')
ax.set_ylabel('Event')
ax.set_title('Key and Mouse Click Events')

# Функция для обновления графика
def update(frame):
    ax.clear()
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Event')
    ax.set_title('Key and Mouse Click Events')
    
    if running:
        # Преобразование времени в секунды
        a_times = [t - a_press_times[0] for t in a_press_times]
        d_times = [t - d_press_times[0] for t in d_press_times]
        click_times = [t - click_press_times[0] for t in click_press_times]
        
        # Построение графика
        ax.bar(a_times, [1]*len(a_times), width=0.1, color='red', label='A Key')
        ax.bar(d_times, [1]*len(d_times), width=0.1, color='blue', label='D Key')
        ax.bar(click_times, [1]*len(click_times), width=0.1, color='orange', label='Click')
        
        ax.legend()
        ax.set_xlim(0, max(a_times + d_times + click_times) + 1)

# Анимация графика
ani = animation.FuncAnimation(fig, update, interval=100)

# Отображение графика
plt.show()

# Остановка слушателей
listener_keyboard.stop()
listener_mouse.stop()