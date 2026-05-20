import tkinter as tk
from tkinter import scrolledtext, messagebox, font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class BoxPlotWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("Построение ящиков с усами")
        self.root.geometry("800x650")
        self.root.configure(bg='#f0f0f0')

        self.num_boxes = 0
        self.box_data = []
        self.current_step = 0
        self.entries = []

        self.title_font = font.Font(family="Helvetica", size=14, weight="bold")
        self.label_font = font.Font(family="Helvetica", size=10)

        self.main_frame = tk.Frame(root, bg='#f0f0f0')
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.step_frames = []
        self.create_count_frame()
        self.step_frames.append(self.frame_count)

        self.show_step(0)

    # -------------------- ФОРМАТИРОВАНИЕ С ЗАПЯТОЙ --------------------
    @staticmethod
    def format_number(value, precision=4):
        """Возвращает строку с числом, используя запятую как десятичный разделитель."""
        return f"{value:.{precision}f}".replace('.', ',')

    # -------------------- КОНТЕКСТНОЕ МЕНЮ --------------------
    def _add_text_menu(self, widget, enable_cut=True, enable_paste=True):
        def copy():
            try:
                widget.event_generate("<<Copy>>")
            except:
                try:
                    sel = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                    self.root.clipboard_clear()
                    self.root.clipboard_append(sel)
                except:
                    pass
        def cut():
            if enable_cut:
                try:
                    widget.event_generate("<<Cut>>")
                except:
                    try:
                        sel = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                        self.root.clipboard_clear()
                        self.root.clipboard_append(sel)
                        widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    except:
                        pass
        def paste():
            if enable_paste:
                try:
                    text = self.root.clipboard_get()
                    widget.insert(tk.INSERT, text)
                except:
                    pass
        def select_all():
            widget.tag_add('sel', '1.0', 'end-1c')
            widget.mark_set(tk.INSERT, '1.0')
            widget.see('1.0')

        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Копировать", command=copy)
        if enable_cut:
            menu.add_command(label="Вырезать", command=cut)
        if enable_paste:
            menu.add_command(label="Вставить", command=paste)
        menu.add_separator()
        menu.add_command(label="Выделить всё", command=select_all)

        widget.bind("<Button-3>", lambda event: menu.tk_popup(event.x_root, event.y_root))
        widget.bind("<Control-c>", lambda e: copy())
        if enable_cut:
            widget.bind("<Control-x>", lambda e: cut())
        if enable_paste:
            widget.bind("<Control-v>", lambda e: paste())

    # -------------------- ОСНОВНЫЕ ФУНКЦИИ --------------------
    def create_count_frame(self):
        self.frame_count = tk.Frame(self.main_frame, bg='#ffffff', bd=2, relief='groove')
        tk.Label(self.frame_count, text="Сколько ящиков построить?", font=self.title_font,
                 bg='#ffffff').pack(pady=20)
        self.box_count_var = tk.IntVar(value=1)
        frame_buttons = tk.Frame(self.frame_count, bg='#ffffff')
        frame_buttons.pack(pady=10)
        for i in range(1, 5):
            tk.Radiobutton(frame_buttons, text=str(i), variable=self.box_count_var, value=i,
                           bg='#ffffff', font=self.label_font, width=5).pack(side='left', padx=5)
        tk.Button(self.frame_count, text="Далее →", command=self.on_count_next,
                  bg='#4CAF50', fg='white', font=self.label_font, width=15).pack(pady=30)

    def on_count_next(self):
        self.num_boxes = self.box_count_var.get()
        self.create_data_frames()
        self.create_build_frame()
        self.current_step = 1
        self.show_step(1)

    def create_data_frames(self):
        for frame in self.step_frames[1:]:
            if frame in self.step_frames:
                frame.destroy()
        self.step_frames = self.step_frames[:1]
        self.entries.clear()

        for i in range(1, self.num_boxes + 1):
            frame = tk.Frame(self.main_frame, bg='#ffffff', bd=2, relief='groove')
            tk.Label(frame, text=f"Ящик №{i}", font=self.title_font,
                     bg='#ffffff').pack(pady=10)
            tk.Label(frame, text="Название (необязательно):", bg='#ffffff').pack(anchor='w', padx=10)
            name_var = tk.StringVar(value=f"Ящик {i}")
            entry_name = tk.Entry(frame, textvariable=name_var, width=40)
            entry_name.pack(pady=5, padx=10, anchor='w')

            tk.Label(frame, text="Вставьте столбец чисел из Excel (с запятой как десятичный разделитель):",
                     bg='#ffffff', wraplength=600, justify='left').pack(anchor='w', padx=10, pady=(10,0))
            text_area = scrolledtext.ScrolledText(frame, height=12, width=70, wrap='none')
            text_area.pack(pady=10, padx=10, fill='both', expand=True)
            tk.Label(frame, text="Скопируйте столбец из Excel (одна колонка) и вставьте сюда.",
                     bg='#ffffff', fg='gray', font=('Helvetica', 8)).pack(pady=(0,10))

            self._add_text_menu(text_area, enable_cut=True, enable_paste=True)

            self.entries.append({
                'frame': frame,
                'name_var': name_var,
                'text_area': text_area
            })
            self.step_frames.append(frame)

    def create_build_frame(self):
        self.frame_build = tk.Frame(self.main_frame, bg='#ffffff', bd=2, relief='groove')
        tk.Label(self.frame_build, text="Все данные введены", font=self.title_font,
                 bg='#ffffff').pack(pady=20)

        frame_checks = tk.LabelFrame(self.frame_build, text="Выберите показатели для вывода в таблице",
                                     bg='#ffffff', font=self.label_font)
        frame_checks.pack(pady=10, padx=20, fill='x')

        self.all_metrics = [
            ('count', 'Количество'),
            ('mean', 'Среднее'),
            ('median', 'Медиана'),
            ('q1', 'Q1 (25%)'),
            ('q3', 'Q3 (75%)'),
            ('iqr', 'IQR'),
            ('min', 'Минимум'),
            ('max', 'Максимум'),
            ('whisker_low', 'Нижний ус'),
            ('whisker_high', 'Верхний ус'),
            ('outliers', 'Выбросы')
        ]
        self.selected_stats = {}
        row = 0
        col = 0
        for key, label in self.all_metrics:
            var = tk.BooleanVar(value=True)
            self.selected_stats[key] = var
            cb = tk.Checkbutton(frame_checks, text=label, variable=var, bg='#ffffff')
            cb.grid(row=row, column=col, sticky='w', padx=10, pady=2)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        tk.Label(self.frame_build, text="Нажмите кнопку для расчёта и построения графиков",
                 bg='#ffffff', justify='center').pack(pady=10)
        tk.Button(self.frame_build, text="Расчёт", command=self.show_results_window,
                  bg='#FF9800', fg='white', font=self.label_font, width=15).pack(pady=10)
        self.step_frames.append(self.frame_build)

    def parse_column(self, text):
        lines = text.strip().splitlines()
        if not lines:
            return []
        data = []
        for line in lines:
            parts = line.split('\t')
            val_str = None
            for part in parts:
                part = part.strip()
                if part:
                    val_str = part
                    break
            if val_str is None:
                continue
            val_str = val_str.replace(',', '.')
            try:
                data.append(float(val_str))
            except ValueError:
                continue
        return data

    def collect_data(self):
        self.box_data.clear()
        for ent in self.entries:
            name = ent['name_var'].get().strip()
            if not name:
                name = "Ящик"
            raw = ent['text_area'].get("1.0", tk.END)
            numbers = self.parse_column(raw)
            self.box_data.append((name, numbers))

    def calculate_stats(self, data):
        if not data:
            return None
        data_sorted = np.sort(data)
        q1 = np.percentile(data_sorted, 25)
        q3 = np.percentile(data_sorted, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = [x for x in data if x < lower_bound or x > upper_bound]
        non_outliers = [x for x in data if lower_bound <= x <= upper_bound]
        if non_outliers:
            whisker_low = np.min(non_outliers)
            whisker_high = np.max(non_outliers)
        else:
            whisker_low = q1
            whisker_high = q3
        return {
            'count': len(data),
            'mean': np.mean(data),
            'median': np.median(data),
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'min': np.min(data),
            'max': np.max(data),
            'whisker_low': whisker_low,
            'whisker_high': whisker_high,
            'outliers': outliers,
            'data': data
        }

    def generate_stats_table(self):
        self.collect_data()
        valid_indices = [i for i, (_, data) in enumerate(self.box_data) if data]
        if not valid_indices:
            return "Нет данных для отображения."

        headers = [self.box_data[i][0] for i in valid_indices]
        stats_list = [self.calculate_stats(self.box_data[i][1]) for i in valid_indices]

        selected_metrics = [(key, label) for key, label in self.all_metrics if self.selected_stats[key].get()]
        if not selected_metrics:
            return "Не выбрано ни одного показателя."

        lines = []
        header_row = "Показатель\t" + "\t".join(headers)
        lines.append(header_row)

        for key, label in selected_metrics:
            row = [label]
            for stats in stats_list:
                if key == 'outliers':
                    val = stats[key]
                    if val:
                        formatted = [self.format_number(v) for v in val[:5]]
                        if len(val) > 5:
                            val_str = ', '.join(formatted) + f" … и ещё {len(val)-5}"
                        else:
                            val_str = ', '.join(formatted)
                    else:
                        val_str = "нет"
                else:
                    if key == 'count':
                        val_str = str(stats[key])
                    else:
                        val_str = self.format_number(stats[key])
                row.append(val_str)
            lines.append("\t".join(row))

        # Исходные данные
        lines.append("\n" + "="*80)
        lines.append("ИСХОДНЫЕ ДАННЫЕ (списки чисел)")
        lines.append("="*80)
        for i, idx in enumerate(valid_indices):
            name = self.box_data[idx][0]
            data = self.box_data[idx][1]
            data_str = ', '.join(self.format_number(x) for x in data)
            lines.append(f"\n{name}:")
            for j in range(0, len(data_str), 100):
                lines.append(f"  {data_str[j:j+100]}")
        return "\n".join(lines)

    def show_results_window(self):
        self.collect_data()
        valid_data = [(name, data) for name, data in self.box_data if data]
        if not valid_data:
            messagebox.showerror("Ошибка", "Нет данных для построения графика.")
            return

        if not any(self.selected_stats[key].get() for key, _ in self.all_metrics):
            messagebox.showerror("Ошибка", "Выберите хотя бы один показатель.")
            return

        win = tk.Toplevel(self.root)
        win.title("Ящики с усами + таблица данных")
        win.geometry("950x800")

        # График
        fig, ax = plt.subplots(figsize=(8, 4))
        names = [name for name, _ in valid_data]
        data_list = [data for _, data in valid_data]
        ax.boxplot(data_list, labels=names, patch_artist=True,
                   showmeans=True, meanline=True,
                   meanprops={'color': 'blue', 'linestyle': '--', 'linewidth': 1.5},
                   medianprops={'color': 'red', 'linewidth': 2},
                   flierprops={'marker': 'o', 'markerfacecolor': 'gray', 'markersize': 5})
        ax.set_title('Диаграммы "ящик с усами"')
        ax.set_ylabel('Значения')
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10, fill='x')

        # Текстовое поле с таблицей
        frame_text = tk.Frame(win)
        frame_text.pack(fill='both', expand=True, padx=10, pady=10)

        text_area = scrolledtext.ScrolledText(frame_text, wrap='none', font=('Courier', 9), height=18)
        text_area.pack(fill='both', expand=True)

        self._add_text_menu(text_area, enable_cut=False, enable_paste=False)

        table_text = self.generate_stats_table()
        text_area.insert(tk.END, table_text)
        text_area.config(state='normal')

        btn_copy = tk.Button(frame_text, text="Копировать всё (таблица + данные)",
                             command=lambda: self.copy_text(table_text, win),
                             bg='#2196F3', fg='white', font=self.label_font)
        btn_copy.pack(pady=5)

    def copy_text(self, text, window):
        window.clipboard_clear()
        window.clipboard_append(text)
        messagebox.showinfo("Копирование", "Текст скопирован в буфер обмена")

    def show_step(self, step):
        for frame in self.step_frames:
            frame.pack_forget()
        self.step_frames[step].pack(fill='both', expand=True)

        if hasattr(self, 'nav_frame'):
            self.nav_frame.destroy()

        self.nav_frame = tk.Frame(self.root, bg='#f0f0f0')
        self.nav_frame.pack(side='bottom', fill='x', pady=5)

        if step == 0:
            return
        if step < len(self.step_frames)-1:
            tk.Button(self.nav_frame, text="← Назад", command=self.go_back,
                      bg='#9E9E9E', fg='white', width=10).pack(side='left', padx=10, pady=5)
            tk.Button(self.nav_frame, text="Вперёд →", command=self.go_forward,
                      bg='#4CAF50', fg='white', width=10).pack(side='right', padx=10, pady=5)
        elif step == len(self.step_frames)-1:
            tk.Button(self.nav_frame, text="← Назад к редактированию", command=self.go_back_to_edit,
                      bg='#FF9800', fg='white', width=20).pack(side='bottom', pady=10)

    def go_back(self):
        if self.current_step > 1:
            self.current_step -= 1
            self.show_step(self.current_step)

    def go_forward(self):
        if self.current_step < len(self.step_frames)-1:
            self.current_step += 1
            self.show_step(self.current_step)

    def go_back_to_edit(self):
        self.current_step = len(self.step_frames) - 2
        self.show_step(self.current_step)


if __name__ == "__main__":
    root = tk.Tk()
    app = BoxPlotWizard(root)
    root.mainloop()