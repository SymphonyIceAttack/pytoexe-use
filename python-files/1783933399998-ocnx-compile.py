import tkinter as tk
from tkinter import filedialog
import py_compile
import os

def compile_file():
    file_path = filedialog.askopenfilename(title="файл для компиляции", filetypes=[("Python files", "*.py")])
    if file_path:
        try:
            py_compile.compile(file_path)
            print(f"{file_path} успешно скомпилирован.")
        except Exception as e:
            print(f"ошибка файла {file_path}: {e}")

root = tk.Tk()
root.title("компилятор")
compile_button = tk.Button(root, text="выбрать", command=compile_file)
compile_button.pack(pady=20)
root.mainloop()
