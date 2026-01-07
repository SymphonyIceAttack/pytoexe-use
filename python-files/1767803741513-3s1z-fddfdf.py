import pyautogui
import tkinter as tk
from tkinter import ttk
from PIL import ImageGrab
import time

# --- Глобальные переменные ---
region = None
running = False
colors_to_find = []

def select_region():
    global region
    print("Выделите область через 3 секунды...")
    time.sleep(3)
    # Используем pyautogui.screenshot() и вручную выделяем область
    x1, y1 = pyautogui.position()
    print(f"Нажмите в левый верхний угол области: ({x1}, {y1})")
    input("Нажмите Enter после того, как выделите область...")
    x2, y2 = pyautogui.position()
    print(f"Нажмите в правый нижний угол области: ({x2}, {y2})")
    region = (x1, y1, x2 - x1, y2 - y1)
    print(f"Область: {region}")
    label_status.config(text=f"Область: {region}")

def add_color():
    hex_code = entry_color.get().strip()
    if hex_code and hex_code.startswith("#") and len(hex_code) == 7:
        if hex_code not in colors_to_find:
            colors_to_find.append(hex_code)
            update_colors_list()
            entry_color.delete(0, tk.END)
    else:
        print("Некорректный HEX-код. Пример: #FF0000")

def remove_color(hex_code):
    if hex_code in colors_to_find:
        colors_to_find.remove(hex_code)
        update_colors_list()

def update_colors_list():
    for widget in frame_colors.winfo_children():
        widget.destroy()

    for color in colors_to_find:
        frame = tk.Frame(frame_colors)
        frame.pack(fill="x", pady=2)

        label_color = tk.Label(frame, text=color, bg=color, width=10, height=1)
        label_color.pack(side="left")

        btn_remove = tk.Button(frame, text="Удалить", command=lambda c=color: remove_color(c))
        btn_remove.pack(side="right")

def start_searching():
    global running
    if not colors_to_find:
        print("Нет цветов для поиска!")
        return
    running = True
    btn_start.config(state="disabled")
    btn_stop.config(state="normal")
    search_loop()

def stop_searching():
    global running
    running = False
    btn_start.config(state="normal")
    btn_stop.config(state="disabled")

def search_loop():
    if not running or region is None:
        return

    # Скриншот области
    screenshot = ImageGrab.grab(bbox=(
        region[0],
        region[1],
        region[0] + region[2],
        region[1] + region[3]
    ))
    screenshot = screenshot.convert("RGB")

    found = False
    for x in range(screenshot.width):
        for y in range(screenshot.height):
            r, g, b = screenshot.getpixel((x, y))
            hex_color = f"#{r:02X}{g:02X}{b:02X}"
            if hex_color in colors_to_find:
                # Найден цвет! Нажимаем ЛКМ
                click_x = region[0] + x
                click_y = region[1] + y
                pyautogui.click(click_x, click_y)
                print(f"Цвет {hex_color} найден! Нажатие ЛКМ в ({click_x}, {click_y})")
                found = True
                break
        if found:
            break

    if not found:
        print("Цвет не найден в области.")

    root.after(500, search_loop)  # Проверка каждые 500 мс

# --- Интерфейс ---
root = tk.Tk()
root.title("Отслеживание цвета на экране")

# Ввод HEX-кода
frame_input = tk.Frame(root)
frame_input.pack(pady=10)

tk.Label(frame_input, text="HEX-код цвета:").pack(side="left")
entry_color = tk.Entry(frame_input)
entry_color.pack(side="left", padx=5)
btn_add_color = tk.Button(frame_input, text="Добавить цвет", command=add_color)
btn_add_color.pack(side="left", padx=5)

# Список цветов
frame_colors_label = tk.Label(root, text="Цвета для поиска:")
frame_colors_label.pack(pady=(10, 0))

frame_colors = tk.Frame(root)
frame_colors.pack(fill="x", padx=10)

# Управление
btn_select = tk.Button(root, text="Выбрать область", command=select_region)
btn_select.pack(pady=5)

label_status = tk.Label(root, text="Область не выбрана")
label_status.pack(pady=5)

btn_start = tk.Button(root, text="Начать отслеживание", command=start_searching)
btn_start.pack(pady=5)

btn_stop = tk.Button(root, text="Остановить", command=stop_searching, state="disabled")
btn_stop.pack(pady=5)

root.mainloop()