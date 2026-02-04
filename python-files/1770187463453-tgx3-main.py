import tkinter as tk
from tkinter import ttk


class CompactPriceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Компактный прайс-лист")
        self.root.geometry("1500x320")
        self.root.resizable(False, False)

        # Цветовая схема
        self.bg_color = "#000000"
        self.header_color = "#FFD700"  # золотой
        self.hall_color = "#333333"
        self.text_color = "#FFFFFF"
        self.odd_row = "#1A1A1A"
        self.even_row = "#262626"

        # Данные из картинки (с временем)
        self.prices = {
            "STANDARD (3060, 165Hz, 27\")": {
                "будни": {
                    "1ч": "80 ₽ (08-14хуй)\n150 ₽ (04-17)\n175 ₽ (17-04)",
                    "3ч(Недоступен 20-01)": "410 ₽ (04-17)\n470 ₽ (17-04)",
                    "5ч": "620 ₽ (04-17)\n720 ₽ (17-04)",
                    "ночь": "810 ₽ (23-11)"
                },
                "выходные": {
                    "1ч": "90 ₽ (08-14)\n175 ₽ (04-17)\n200 ₽ (17-04)",
                    "3ч(Недоступен 20-01)": "470 ₽ (04-17)\n540 ₽ (17-04)",
                    "5ч": "720 ₽ (04-17)\n820 ₽ (17-04)",
                    "ночь": "950 ₽ (23-11)"
                }
            },
            "STANDARD PRO (4060Ti, 280Hz, 27\")": {
                "будни": {
                    "1ч": "85 ₽ (08-14)\n160 ₽ (04-17)\n185 ₽ (17-04)",
                    "3ч(Недоступен 20-01)": "430 ₽ (04-17)\n500 ₽ (17-04)",
                    "5ч": "660 ₽ (04-17)\n760 ₽ (17-04)",
                    "ночь": "860 ₽ (23-11)"
                },
                "выходные": {
                    "1ч": "95 ₽ (08-14)\n185 ₽ (04-17)\n215 ₽ (17-04)",
                    "3ч(Недоступен 20-01)": "500 ₽ (04-17)\n580 ₽ (17-04)",
                    "5ч": "760 ₽ (04-17)\n880 ₽ (17-04)",
                    "ночь": "1000 ₽ (23-11)"
                }
            },
            "BOOTCAMP PRO (4070, 280Hz, 27\")": {
                "будни": {
                    "1ч": "95 ₽ (08-14)\n195 ₽ (04-17)\n225 ₽ (17-04)",
                    "3ч(Недоступен 20-01)": "530 ₽ (04-17)\n610 ₽ (17-04)",
                    "5ч": "800 ₽ (04-17)\n920 ₽ (17-04)",
                    "ночь": "1050 ₽ (23-11)"
                },
                "выходные": {
                    "1ч": "100 ₽ (08-14)\n225 ₽ (04-17)\n260 ₽ (17-04)",
                    "3ч(Недоступен 20-01)": "610 ₽ (04-17)\n700 ₽ (17-04)",
                    "5ч": "920 ₽ (04-17)\n1070 ₽ (17-04)",
                    "ночь": "1220 ₽ (23-11)"
                }
            },
            "АРЕНДА ТВ (65'', до 2 чел.)": {
                "будни": {
                    "1ч": "345 ₽ (04-17)\n395 ₽ (17-04)",
                    "3ч(Недоступен 20-01)": "780 ₽ (04-17)\n890 ₽ (17-04)",
                    "5ч": "1210 ₽ (04-17)\n1380 ₽ (17-04)",
                    "ночь": "1860 ₽ (23-11)"
                },
                "выходные": {
                    "1ч": "395 ₽ (04-17)\n455 ₽ (17-04)",
                    "3ч(Недоступен 20-01)": "890 ₽ (04-17)\n1020 ₽ (17-04)",
                    "5ч": "1380 ₽ (04-17)\n1590 ₽ (17-04)",
                    "ночь": "2130 ₽ (23-11)"
                }
            }
        }

        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()

        # Настройка стилей
        style.configure("TNotebook", background=self.bg_color)
        style.configure("TNotebook.Tab",
                        background=self.hall_color,
                        foreground=self.text_color,
                        padding=[10, 5],
                        font=('Helvetica', 9, 'bold'))
        style.map("TNotebook.Tab",
                  background=[("selected", self.header_color)],
                  foreground=[("selected", "#000000")])

        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel",
                        background=self.bg_color,
                        foreground=self.text_color,
                        font=('Helvetica', 8))

        # Создаем Notebook для вкладок
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладки
        frame_weekdays = ttk.Frame(notebook)
        frame_weekends = ttk.Frame(notebook)

        notebook.add(frame_weekdays, text="Будни")
        notebook.add(frame_weekends, text="Выходные")

        self.create_day_table(frame_weekdays, "будни")
        self.create_day_table(frame_weekends, "выходные")

    def create_day_table(self, parent, day_type):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Заголовки
        row = 0
        tariffs = ["1ч", "3ч(Недоступен 20-01)", "5ч", "ночь"]

        # Заголовки столбцов
        tk.Label(main_frame, text="Зал",
                 bg=self.header_color, fg="#000000",
                 font=('Helvetica', 9, 'bold')).grid(row=row, column=0, sticky="ew", padx=1, pady=1)

        for col, tariff in enumerate(tariffs, start=1):
            tk.Label(main_frame, text=tariff,
                     bg=self.header_color, fg="#000000",
                     font=('Helvetica', 9, 'bold')).grid(row=row, column=col, sticky="ew", padx=1, pady=1)

        row += 1

        # Данные
        for hall_idx, (hall_name, days_data) in enumerate(self.prices.items()):
            row_color = self.even_row if hall_idx % 2 else self.odd_row

            tk.Label(main_frame, text=hall_name,
                     bg=self.hall_color, fg=self.text_color,
                     font=('Helvetica', 9, 'bold')).grid(
                row=row, column=0, sticky="nsew", padx=1, pady=1)

            for col, tariff in enumerate(tariffs, start=1):
                tk.Label(main_frame, text=days_data[day_type][tariff],
                         bg=row_color, fg=self.text_color, justify="center").grid(
                    row=row, column=col, sticky="nsew", padx=1, pady=1)

            row += 1

        # Настройка размеров
        for col in range(1 + len(tariffs)):
            main_frame.columnconfigure(col, weight=1)

        for r in range(row):
            main_frame.rowconfigure(r, weight=1)


if __name__ == "__main__":
    root = tk.Tk()
    app = CompactPriceApp(root)
    root.attributes('-topmost', True)
    root.mainloop()
