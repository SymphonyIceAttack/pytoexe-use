import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image

def select_images():
    """Открывает диалог выбора файлов и возвращает список путей."""
    file_paths = filedialog.askopenfilenames(
        title="Выберите изображения",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
    )
    if file_paths:
        listbox.delete(0, tk.END)
        for path in file_paths:
            listbox.insert(tk.END, os.path.basename(path))
        list_path.set(";".join(file_paths))  # Сохраняем пути, разделённые точкой с запятой
    return file_paths

def stitch_images():
    """Склеивает изображения попарно по горизонтали."""
    image_paths_str = list_path.get()
    if not image_paths_str:
        messagebox.showerror("Ошибка", "Выберите изображения!")
        return
    image_paths = image_paths_str.split(";")  # Разделяем по точке с запятой
    if len(image_paths) % 2 != 0:
        messagebox.showerror("Ошибка", "Выберите чётное количество изображений!")
        return

    output_folder = "stitched_results"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for i in range(0, len(image_paths) - 1, 2):
        img1_path = image_paths[i]
        img2_path = image_paths[i + 1]
        try:
            img1 = Image.open(img1_path)
            img2 = Image.open(img2_path)
            new_width = img1.width + img2.width
            new_height = max(img1.height, img2.height)
            new_image = Image.new('RGB', (new_width, new_height))
            new_image.paste(img1, (0, 0))
            new_image.paste(img2, (img1.width, 0))
            output_path = os.path.join(output_folder, f"stitched_{i//2 + 1}.jpg")
            new_image.save(output_path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обработать {img1_path} и {img2_path}: {e}")
            return

    messagebox.showinfo("Готово", f"Склейка завершена! Результаты в папке {output_folder}")

# Создаём окно
root = tk.Tk()
root.title("Склейка изображений попарно")
root.geometry("500x400")

# Переменная для хранения путей
list_path = tk.StringVar()

# Виджеты
tk.Label(root, text="Выберите изображения (чётное количество):").pack(pady=10)
tk.Button(root, text="Выбрать файлы", command=select_images).pack(pady=5)
listbox = tk.Listbox(root, width=60, height=10)
listbox.pack(pady=10)
tk.Button(root, text="Склеить попарно", command=stitch_images).pack(pady=10)

root.mainloop()
