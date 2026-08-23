import customtkinter as ctk
import json
import os
from tkinter import messagebox

class SeriesTracker:
    def __init__(self):
        self.data_file = "series_data.json"
        self.series_list = []
        
        # Настройка темы
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Создание главного окна
        self.root = ctk.CTk()
        self.root.title("Трекер серий - Сезон 8")
        self.root.geometry("600x700")
        self.root.configure(fg_color="#1a1a1a")
        
        self.load_data()
        self.create_widgets()
        
    def create_widgets(self):
        # Заголовок
        title = ctk.CTkLabel(
            self.root, 
            text="📺 Трекер серий", 
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#ffffff"
        )
        title.pack(pady=20)
        
        # Форма ввода
        input_frame = ctk.CTkFrame(self.root, fg_color="#2a2a2a", corner_radius=10)
        input_frame.pack(pady=10, padx=20, fill="x")
        
        # Название серии
        ctk.CTkLabel(
            input_frame, 
            text="Название серии:",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.name_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Введите название серии",
            width=400,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.name_entry.pack(padx=20, pady=(0, 15))
        
        # Номер серии
        ctk.CTkLabel(
            input_frame, 
            text="Номер серии:",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).pack(anchor="w", padx=20, pady=(0, 5))
        
        self.number_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Введите номер серии",
            width=400,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.number_entry.pack(padx=20, pady=(0, 15))
        
        # Сезон (всегда 8)
        ctk.CTkLabel(
            input_frame,
            text="Сезон: 8",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4a9eff"
        ).pack(pady=(0, 15))
        
        # Кнопка добавления
        add_btn = ctk.CTkButton(
            input_frame,
            text="➕ Добавить серию",
            command=self.add_series,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4a9eff",
            hover_color="#3a8eef"
        )
        add_btn.pack(pady=(0, 20))
        
        # Список серий
        list_frame = ctk.CTkFrame(self.root, fg_color="#2a2a2a", corner_radius=10)
        list_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(
            list_frame,
            text="Список серий:",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Scrollable frame для списка
        self.scrollable_frame = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="#1a1a1a",
            corner_radius=5
        )
        self.scrollable_frame.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        
        # Статистика
        self.stats_label = ctk.CTkLabel(
            self.root,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.stats_label.pack(pady=10)
        
        self.update_display()
        
    def add_series(self):
        name = self.name_entry.get().strip()
        number = self.number_entry.get().strip()
        
        if not name or not number:
            messagebox.showwarning("Ошибка", "Заполните все поля!")
            return
            
        try:
            number = int(number)
        except ValueError:
            messagebox.showwarning("Ошибка", "Номер серии должен быть числом!")
            return
        
        series = {
            "name": name,
            "number": number,
            "season": 8
        }
        
        self.series_list.append(series)
        self.save_data()
        self.update_display()
        
        # Очистка полей
        self.name_entry.delete(0, "end")
        self.number_entry.delete(0, "end")
        
    def delete_series(self, index):
        if messagebox.askyesno("Подтверждение", "Удалить эту серию?"):
            self.series_list.pop(index)
            self.save_data()
            self.update_display()
        
    def update_display(self):
        # Очистка списка
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.series_list:
            empty_label = ctk.CTkLabel(
                self.scrollable_frame,
                text="Нет добавленных серий",
                font=ctk.CTkFont(size=14),
                text_color="#666666"
            )
            empty_label.pack(pady=40)
        else:
            # Сортировка по номеру серии
            sorted_list = sorted(self.series_list, key=lambda x: x["number"])
            
            for idx, series in enumerate(sorted_list):
                item_frame = ctk.CTkFrame(
                    self.scrollable_frame,
                    fg_color="#2a2a2a",
                    corner_radius=8
                )
                item_frame.pack(fill="x", pady=5, padx=10)
                
                # Информация о серии
                info_text = f"Серия {series['number']} • Сезон {series['season']}"
                info_label = ctk.CTkLabel(
                    item_frame,
                    text=info_text,
                    font=ctk.CTkFont(size=11),
                    text_color="#4a9eff"
                )
                info_label.pack(anchor="w", padx=15, pady=(10, 2))
                
                name_label = ctk.CTkLabel(
                    item_frame,
                    text=series["name"],
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color="#ffffff"
                )
                name_label.pack(anchor="w", padx=15, pady=(0, 10))
                
                # Кнопка удаления
                delete_btn = ctk.CTkButton(
                    item_frame,
                    text="🗑️",
                    width=35,
                    height=35,
                    command=lambda i=self.series_list.index(series): self.delete_series(i),
                    fg_color="#ff4a4a",
                    hover_color="#ff3a3a"
                )
                delete_btn.place(relx=1.0, rely=0.5, anchor="e", x=-15)
        
        # Обновление статистики
        self.stats_label.configure(
            text=f"Всего серий: {len(self.series_list)} • Сезон 8"
        )
        
    def save_data(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.series_list, f, ensure_ascii=False, indent=2)
            
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.series_list = json.load(f)
            except:
                self.series_list = []
                
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SeriesTracker()
    app.run()