import psutil
import tkinter as tk
from tkinter import ttk

def get_size(bytes, suffix="B"):
    """Конвертирует байты в читаемый формат (KB, MB, GB и т. д.)"""
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

class MemoryMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Монитор памяти")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Создаём основной фрейм
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Заголовок для RAM
        ttk.Label(main_frame, text="ОПЕРАТИВНАЯ ПАМЯТЬ (RAM)",
                  font=("Arial", 12, "bold")).grid(row=0, column=0,
                  columnspan=2, pady=(0, 10), sticky=tk.W)

        # Метки для RAM
        self.ram_total_label = ttk.Label(main_frame, text="Всего: ")
        self.ram_total_label.grid(row=1, column=0, sticky=tk.W, pady=2)

        self.ram_used_label = ttk.Label(main_frame, text="Используется: ")
        self.ram_used_label.grid(row=2, column=0, sticky=tk.W, pady=2)

        self.ram_free_label = ttk.Label(main_frame, text="Свободно: ")
        self.ram_free_label.grid(row=3, column=0, sticky=tk.W, pady=2)

        self.ram_percent_label = ttk.Label(main_frame, text="Использование: ")
        self.ram_percent_label.grid(row=4, column=0, sticky=tk.W, pady=2)

        # Прогрессбар для RAM
        self.ram_progress = ttk.Progressbar(main_frame, orient="horizontal",
                                        length=300, mode="determinate")
        self.ram_progress.grid(row=5, column=0, columnspan=2, pady=10)

        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=6, column=0,
                columnspan=2, sticky=(tk.W, tk.E), pady=20)

        # Заголовок для ROM
        ttk.Label(main_frame, text="ПОСТОЯННАЯ ПАМЯТЬ (ROM)",
                  font=("Arial", 12, "bold")).grid(row=7, column=0,
                  columnspan=2, pady=(0, 10), sticky=tk.W)

        # Treeview для отображения разделов диска
        columns = ("Раздел", "Всего", "Используется", "Свободно", "Использование")
        self.disk_tree = ttk.Treeview(main_frame, columns=columns,
                                     show="headings", height=8)

        for col in columns:
            self.disk_tree.heading(col, text=col)
            self.disk_tree.column(col, width=100)

        self.disk_tree.grid(row=8, column=0, columnspan=2, pady=5)

        # Полоса прокрутки для Treeview
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL,
                               command=self.disk_tree.yview)
        scrollbar.grid(row=8, column=2, sticky=(tk.N, tk.S))
        self.disk_tree.configure(yscrollcommand=scrollbar.set)

        # Кнопка обновления
        refresh_button = ttk.Button(main_frame, text="Обновить",
                              command=self.update_memory_info)
        refresh_button.grid(row=9, column=0, columnspan=2, pady=15)

        # Автоматическое обновление при запуске
        self.update_memory_info()

    def update_memory_info(self):
        """Обновляет информацию о памяти"""
        # Обновляем информацию о RAM
        ram = psutil.virtual_memory()
        self.ram_total_label.config(text=f"Всего: {get_size(ram.total)}")
        self.ram_used_label.config(text=f"Используется: {get_size(ram.used)}")
        self.ram_free_label.config(text=f"Свободно: {get_size(ram.available)}")
        self.ram_percent_label.config(text=f"Использование: {ram.percent}%")
        self.ram_progress['value'] = ram.percent

        # Очищаем и обновляем информацию о ROM
        for item in self.disk_tree.get_children():
            self.disk_tree.delete(item)

        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                self.disk_tree.insert("", "end", values=(
                    partition.device,
            get_size(usage.total),
            get_size(usage.used),
            get_size(usage.free),
            f"{usage.percent}%"
                ))
            except PermissionError:
                self.disk_tree.insert("", "end", values=(
                    partition.device, "—", "—", "—", "Нет доступа"
                ))

def main():
    root = tk.Tk()
    app = MemoryMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
