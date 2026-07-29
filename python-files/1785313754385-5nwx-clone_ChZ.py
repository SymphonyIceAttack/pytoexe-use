# Скачать python по адресу https://www.python.org/downloads/
# При установке python поставить галочку (выбрать YES) на запрос "add python to PATH"
# Перед запуском скрипта запустить из командной строки pip install pywin32 для установки драйвера для принтера
# В настройках программы указать имя принтера, так как он называется в панели управления.



import tkinter as tk
from tkinter import messagebox
import win32print
import json
import os

class LabelPrinterApp:
    def process_barcode(self, event):
        raw_barcode = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if not raw_barcode: return

        try:
            dpi_factor = 23.6 
            x_dots = int(float(self.config.get('offset_x', 5.0)) * dpi_factor)
            y_dots = int(float(self.config.get('offset_y', 5.0)) * dpi_factor)
            scale = int(self.config.get('dm_scale', 4))
            width_mm = self.config.get('width', 50.0)
            height_mm = self.config.get('height', 30.0)

            formatted_data = raw_barcode.replace("91", "\x1d91").replace("92", "\x1d92")

            cmd_start = (f"SIZE {width_mm} mm, {height_mm} mm\nGAP 3 mm, 0\nCLS\n"
                         f"DMATRIX {x_dots},{y_dots},400,400,x{scale},")
            cmd_end = "\nPRINT 1,1\n"
            full_cmd = cmd_start.encode('utf-8') + b'"' + formatted_data.encode('utf-8') + b'"' + cmd_end.encode('utf-8')

            # Отправка через Windows Spooler
            printer_name = self.config.get("ip", "TSC TX610")
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Label", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, full_cmd)
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)

        except Exception as e:
            messagebox.showerror("Ошибка печати", f"Не удалось отправить данные на '{self.config.get('ip')}':\n{e}")

    def load_config(self):
        default = {"ip": "TSC TX610", "width": 50.0, "height": 30.0, "dm_scale": 4, "offset_x": 5.0, "offset_y": 5.0}
        if not os.path.exists("config.json"): return default
        try:
            with open("config.json", "r") as f: return {**default, **json.load(f)}
        except: return default

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Настройки")
        fields = [("Имя принтера:", "ip"), ("Ширина(мм):", "width"), ("Высота(мм):", "height"), 
                  ("Масштаб(2-9):", "dm_scale"), ("Отступ X:", "offset_x"), ("Отступ Y:", "offset_y")]
        entries = {}
        for text, key in fields:
            tk.Label(win, text=text).pack()
            e = tk.Entry(win)
            e.insert(0, str(self.config.get(key, "")))
            e.pack()
            entries[key] = e
        def save():
            try:
                self.config = {k: (float(e.get().replace(",", ".")) if k != "ip" else e.get().strip()) for k, e in entries.items()}
                with open("config.json", "w") as f: json.dump(self.config, f)
                win.destroy()
            except Exception as e: messagebox.showerror("Ошибка", f"{e}")
        tk.Button(win, text="Сохранить", command=save).pack()

    def __init__(self, root):
        self.root = root
        self.root.title("Печать марок")
        self.config = self.load_config()
        tk.Label(root, text="Сканируйте марку ЧЗ:").pack(pady=10)
        self.entry = tk.Entry(root, width=40)
        self.entry.pack(pady=5)
        self.entry.bind('<Return>', self.process_barcode)
        self.entry.focus_set()
        tk.Button(root, text="Настройки принтера", command=self.open_settings).pack(pady=10)

root = tk.Tk()
app = LabelPrinterApp(root)
root.mainloop()