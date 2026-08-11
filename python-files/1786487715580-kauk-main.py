import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import csv
import xlwt
import os


class AeroApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Аэрология (Управление мышью)")
        self.geometry("1000x850")

        self.plot_mode = 'D'
        self.rows = []
        self.rows2 = []
        self.is_compare_mode = False

        self.x_min, self.x_max = 0, 360
        self.y_min, self.y_max = 0, 30
        self.shift = 180
        self.pan_start = None
        self.click_start_pos = None

        self.points_on_screen = []
        self.entry_widget = None

        self.setup_ui()
        self.update_ui()

    def setup_ui(self):
        top = tk.Frame(self)
        top.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(top, text="Открыть файл 1", command=self.load_file).pack(side=tk.LEFT)
        tk.Button(top, text="Таблица/График", command=self.toggle_view).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Сохр. TAE", command=self.save_tae).pack(side=tk.LEFT)
        tk.Button(top, text="Сохр. XLS", command=self.save_xls).pack(side=tk.LEFT)

        self.main_area = tk.Frame(self)
        self.main_area.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(self.main_area)
        left.pack(fill=tk.Y, side=tk.LEFT, padx=5)
        self.btn_mode = tk.Button(left, text="Режим: Направление (D)", command=self.toggle_mode)
        self.btn_mode.pack(fill=tk.X)
        tk.Button(left, text="Сбросить вид", command=self.reset_view).pack(fill=tk.X, pady=5)

        self.canvas = tk.Canvas(self.main_area, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.canvas.bind("<Configure>", lambda e: self.draw_graph())

        # ЛКМ - только клик для добавления точки
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # ПКМ - удаление точки
        self.canvas.bind("<Button-3>", self.on_right_click)

        # Колёсико (средняя кнопка) - зажать и тащить для перемещения графика
        self.canvas.bind("<Button-2>", self.on_middle_click)
        self.canvas.bind("<B2-Motion>", self.on_middle_drag)

        # Прокрутка колёсика - зум
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Button-4>", self.on_scroll)
        self.canvas.bind("<Button-5>", self.on_scroll)

        self.canvas.bind("<Motion>", self.on_motion)

        self.tree = ttk.Treeview(self.main_area, columns=("H", "P", "T", "U", "D", "V", "TD"), show="headings")
        for col in ("H", "P", "T", "U", "D", "V", "TD"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<ButtonPress-2>", self.on_tree_scroll_start)
        self.tree.bind("<B2-Motion>", self.on_tree_scroll_drag)

        bottom = tk.Frame(self)
        bottom.pack(fill=tk.X, padx=5, pady=5)

        self.shift_frame = tk.Frame(bottom)
        self.shift_frame.pack(side=tk.LEFT, padx=20)
        self.btn_left = tk.Button(self.shift_frame, text="← Сдвиг влево (-5°)", command=lambda: self.change_shift(-5))
        self.btn_left.pack(side=tk.LEFT)
        self.shift_label = tk.Label(self.shift_frame, text="Центр: 360°", font=("Arial", 10, "bold"))
        self.shift_label.pack(side=tk.LEFT, padx=10)
        self.btn_right = tk.Button(self.shift_frame, text="Сдвиг вправо (+5°) →", command=lambda: self.change_shift(5))
        self.btn_right.pack(side=tk.LEFT)

        self.btn_compare = tk.Button(bottom, text="Режим сравнения", command=self.toggle_compare_mode)
        self.btn_compare.pack(side=tk.RIGHT, padx=10)

    def toggle_view(self):
        if self.tree.winfo_ismapped():
            self.tree.pack_forget()
            self.canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
            self.draw_graph()
        else:
            self.canvas.pack_forget()
            self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
            self.update_table()

    def toggle_mode(self):
        self.plot_mode = 'V' if self.plot_mode == 'D' else 'D'
        if self.plot_mode == 'V':
            self.btn_mode.config(text="Режим: Скорость (V)")
            self.shift_frame.pack_forget()
            self.x_min, self.x_max = 0, 50
        else:
            self.btn_mode.config(text="Режим: Направление (D)")
            self.shift_frame.pack(side=tk.LEFT, padx=20)
            self.change_shift(0)
        self.draw_graph()

    def change_shift(self, val):
        self.shift = (self.shift + val) % 360
        if self.plot_mode == 'D':
            self.x_min, self.x_max = self.shift, self.shift + 360
            center_deg = (self.shift + 180) % 360
            self.shift_label.config(text="Центр: {}°".format(center_deg))
        self.draw_graph()

    def reset_view(self):
        self.y_min, self.y_max = 0, 30
        self.change_shift(0)

    def toggle_compare_mode(self):
        if self.is_compare_mode:
            self.is_compare_mode = False
            self.rows2 = []
            self.btn_compare.config(text="Режим сравнения", bg="#f0f0f0", fg="black")
            self.draw_graph()
        else:
            self.is_compare_mode = True
            self.rows2 = []
            self.btn_compare.config(text="Выйти из сравнения", bg="#5a1e28", fg="white")
            self.draw_graph()

    def load_second_file_from_path(self, path):
        lines = self.read_file(path)
        if lines is None: return
        self.rows2 = self.parse_aero_text(lines)
        if self.rows2:
            self.draw_graph()
        else:
            messagebox.showwarning("Ошибка", "Не удалось загрузить 2-й файл или он пуст")

    def read_file(self, path):
        try:
            f = open(path, 'r', encoding='cp1251')
            lines = f.readlines()
            f.close()
            return lines
        except UnicodeDecodeError:
            try:
                f = open(path, 'r', encoding='utf-8')
                lines = f.readlines()
                f.close()
                return lines
            except Exception as e:
                messagebox.showerror("Ошибка чтения", "Не удалось прочитать файл:\n{}".format(e))
                return None
        except Exception as e:
            messagebox.showerror("Ошибка доступа", "Нет прав или файл недоступен:\n{}".format(e))
            return None

    def parse_aero_text(self, lines):
        rows = []
        header = False
        for line in lines:
            s = line.strip()
            if not s: continue
            if "H" in s and "P" in s and "T" in s and "D" in s:
                header = True
                continue
            if not header: continue
            parts = s.split()
            marker = None
            if parts[0] in ['ИП', 'T', 'U', 'TU', 'П', 'НГТ', 'ИПТ']:
                marker = parts[0]
                parts = parts[1:]
            if len(parts) < 2: continue
            try:
                row = {'marker': marker, 'H': float(parts[0].replace(',', '.')),
                       'P': float(parts[1].replace(',', '.')) if len(parts) > 1 else None}
                if len(parts) == 5:
                    row['T'] = float(parts[2].replace(',', '.'))
                    row['U'] = float(parts[3].replace(',', '.'))
                    row['TD'] = float(parts[4].replace(',', '.'))
                elif len(parts) == 7:
                    row['T'] = float(parts[2].replace(',', '.'))
                    row['U'] = float(parts[3].replace(',', '.'))
                    row['D'] = float(parts[4].replace(',', '.'))
                    row['V'] = float(parts[5].replace(',', '.'))
                    row['TD'] = float(parts[6].replace(',', '.'))
                rows.append(row)
            except:
                continue
        return rows

    def load_file(self):
        home = os.path.expanduser('~')
        init_dir = os.path.join(home, 'Рабочий стол', 'Tae3')
        if not os.path.exists(init_dir): init_dir = home
        path = filedialog.askopenfilename(initialdir=init_dir,
                                          filetypes=[("TAE", "*.TAE *.TAE3 *.txt"), ("All", "*.*")])
        if path: self.load_file_from_path(path)

    def load_file_from_path(self, path):
        lines = self.read_file(path)
        if lines is None: return
        self.rows = self.parse_aero_text(lines)
        self.update_ui()

    def update_ui(self):
        if self.tree.winfo_ismapped():
            self.update_table()
        else:
            self.draw_graph()

    def update_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for r in self.rows:
            vals = [r.get(k, '') if r.get(k) is not None else '' for k in ['H', 'P', 'T', 'U', 'D', 'V', 'TD']]
            self.tree.insert("", tk.END, values=vals)

    def on_tree_double_click(self, event):
        if self.entry_widget:
            self.entry_widget.destroy()

        region = self.tree.identify("x", event.x, event.y)
        if region != "cell":
            return

        col = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item or not col:
            return

        x, y, width, height = self.tree.bbox(item, col)

        self.entry_widget = tk.Entry(self.tree)
        self.entry_widget.place(x=x, y=y, width=width, height=height)

        current_val = self.tree.set(item, col)
        self.entry_widget.insert(0, current_val)
        self.entry_widget.focus_set()

        self.entry_widget.bind("<Return>", lambda e: self.save_edit(item, col))
        self.entry_widget.bind("<FocusOut>", lambda e: self.save_edit(item, col))

    def save_edit(self, item, col):
        new_val = self.entry_widget.get()
        self.entry_widget.destroy()
        self.entry_widget = None

        row_idx = self.tree.index(item)
        col_idx = int(col.replace('#', '')) - 1
        keys = ['H', 'P', 'T', 'U', 'D', 'V', 'TD']
        key = keys[col_idx]

        try:
            if new_val.strip() == '':
                val = None
            else:
                val = float(str(new_val).replace(',', '.'))
            self.rows[row_idx][key] = val
            self.tree.set(item, col, new_val)
            self.draw_graph()
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат числа")
            self.update_table()

    def on_tree_scroll_start(self, event):
        self.tree.scan_mark(event.x, event.y)

    def on_tree_scroll_drag(self, event):
        self.tree.scan_dragto(event.x, event.y, gain=1)

    def get_canvas_coords(self, data_x, data_y):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height() - 25
        if w <= 0 or h <= 0: return 0, 0

        dx = self.x_max - self.x_min
        if dx == 0: dx = 1.0
        dy = self.y_max - self.y_min
        if dy == 0: dy = 1.0

        cx = (data_x - self.x_min) / dx * w
        cy = h - (data_y - self.y_min) / dy * h
        return cx, cy

    def get_data_coords(self, cx, cy):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height() - 25
        if w <= 0 or h <= 0: return 0, 0

        dx = self.x_max - self.x_min
        if dx == 0: dx = 1.0
        dy = self.y_max - self.y_min
        if dy == 0: dy = 1.0

        data_x = self.x_min + (cx / w) * dx
        data_y = self.y_min + ((h - cy) / h) * dy
        return data_x, data_y

    def is_straight_point(self, pts, i, v_range, h_range):
        if i == 0 or i >= len(pts) - 1: return False
        v1_x = (pts[i][0] - pts[i - 1][0]) / v_range
        v1_y = (pts[i][1] - pts[i - 1][1]) / h_range
        len1 = math.hypot(v1_x, v1_y)
        v2_x = (pts[i + 1][0] - pts[i][0]) / v_range
        v2_y = (pts[i + 1][1] - pts[i][1]) / h_range
        len2 = math.hypot(v2_x, v2_y)
        if len1 > 0 and len2 > 0:
            dot_product = max(-1.0, min(1.0, (v1_x * v2_x + v1_y * v2_y) / (len1 * len2)))
            angle_deg = math.degrees(math.acos(dot_product))
            if angle_deg < 1.5: return True
        return False

    def calculate_nice_step(self, val_range, max_ticks=10):
        if val_range <= 0: return 1.0
        rough_step = val_range / max_ticks
        mag = 10 ** math.floor(math.log10(rough_step))
        norm = rough_step / mag
        if norm < 1.5:
            step = 1
        elif norm < 3:
            step = 2
        elif norm < 7:
            step = 5
        else:
            step = 10
        return step * mag

    def draw_graph(self):
        if self.tree.winfo_ismapped(): return
        self.canvas.delete("all")
        self.points_on_screen = []

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        x_range = self.x_max - self.x_min
        y_range = self.y_max - self.y_min
        x_step = self.calculate_nice_step(x_range)
        y_step = self.calculate_nice_step(y_range)

        if x_step >= 1:
            x_fmt = "{:.0f}"
        elif x_step >= 0.1:
            x_fmt = "{:.1f}"
        else:
            x_fmt = "{:.2f}"

        if y_step >= 1:
            y_fmt = "{:.0f}"
        elif y_step >= 0.1:
            y_fmt = "{:.1f}"
        else:
            y_fmt = "{:.2f}"

        start_x = math.ceil(self.x_min / x_step) * x_step
        for x in self.arange(start_x, self.x_max, x_step):
            if x < self.x_min: continue
            cx, _ = self.get_canvas_coords(x, 0)
            self.canvas.create_line(cx, 0, cx, h - 25, fill="#eee")
            val = x % 360 if self.plot_mode == 'D' else x
            label = x_fmt.format(val)
            if self.plot_mode == 'D': label += "°"
            self.canvas.create_text(cx, h - 10, text=label, fill="black")

        start_y = math.ceil(self.y_min / y_step) * y_step
        for y in self.arange(start_y, self.y_max, y_step):
            if y < self.y_min: continue
            _, cy = self.get_canvas_coords(0, y)
            self.canvas.create_line(0, cy, w, cy, fill="#eee")
            self.canvas.create_text(20, cy, text=y_fmt.format(y) + "км", fill="black", anchor=tk.W)

        self.canvas.create_line(0, h - 25, w, h - 25, fill="black")
        self.canvas.create_line(1, 0, 1, h - 25, fill="black")

        self.draw_dataset(self.rows, "blue", "red", True, "Файл 1")
        if self.is_compare_mode and self.rows2:
            self.draw_dataset(self.rows2, "#ff7f0e", "#2ca02c", False, "Файл 2")

        if self.is_compare_mode and not self.rows2:
            self.canvas.create_rectangle(0, 0, w, h, fill="black", stipple="gray50")
            self.canvas.create_text(w // 2, h // 2, text="Откройте 2-й файл кнопкой", fill="white",
                                    font=("Arial", 16, "bold"))

    def arange(self, start, stop, step):
        val = start
        while val < stop:
            yield val
            val += step

    def draw_dataset(self, rows, color_normal, color_straight, is_main_file, label):
        pts = []
        for r in rows:
            if r.get('H') is None: continue
            val = r.get('D') if self.plot_mode == 'D' else r.get('V')
            if val is None: continue
            if self.plot_mode == 'D' and val < self.shift: val += 360
            pts.append((val, r['H']))

        if len(pts) < 1: return

        h_vals = [p[1] for p in pts]
        v_vals = [p[0] for p in pts]
        h_range = (max(h_vals) - min(h_vals)) if max(h_vals) != min(h_vals) else 1.0
        v_range = (max(v_vals) - min(v_vals)) if max(v_vals) != min(v_vals) else 1.0

        if len(pts) > 1:
            line_coords = []
            for x, y in pts:
                cx, cy = self.get_canvas_coords(x, y)
                line_coords.extend([cx, cy])
            self.canvas.create_line(line_coords, fill=color_normal, width=2, dash=() if is_main_file else (4, 2))

        for i, (x, y) in enumerate(pts):
            is_str = self.is_straight_point(pts, i, v_range, h_range)
            color = color_straight if is_str else color_normal
            cx, cy = self.get_canvas_coords(x, y)
            self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=color, outline="black")

            self.points_on_screen.append({'x': cx, 'y': cy, 'val': x, 'h': y, 'p': r.get('P'), 'label': label})

    def on_motion(self, event):
        closest_pt = None
        min_dist = float('inf')

        for pt in self.points_on_screen:
            dist = math.hypot(pt['x'] - event.x, pt['y'] - event.y)
            if dist < min_dist and dist < 10:
                min_dist = dist
                closest_pt = pt

        if closest_pt:
            p_val = "—" if closest_pt['p'] is None else "{:.1f} гПа".format(closest_pt['p'])
            if self.plot_mode == 'D':
                real_val = closest_pt['val'] % 360
                val_str = "D: {:.1f}°".format(real_val)
            else:
                val_str = "V: {:.1f} м/с".format(closest_pt['val'])

            text = "[{}]\n{}\nH: {:.2f} км\nP: {}".format(closest_pt['label'], val_str, closest_pt['h'], p_val)

            self.canvas.delete("tooltip")
            x, y = event.x, event.y
            text_id = self.canvas.create_text(x + 15, y + 15, text=text, fill="black", anchor=tk.NW, tags="tooltip")
            bbox = self.canvas.bbox(text_id)
            if bbox:
                self.canvas.create_rectangle(bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2, fill="yellow",
                                             outline="black", tags="tooltip")
                self.canvas.tag_raise(text_id)
        else:
            self.canvas.delete("tooltip")

    def on_left_click(self, event):
        if self.is_compare_mode and not self.rows2: return
        self.click_start_pos = (event.x, event.y)

    def on_release(self, event):
        if self.click_start_pos and abs(event.x - self.click_start_pos[0]) < 5 and abs(
                event.y - self.click_start_pos[1]) < 5:
            dx, dy = self.get_data_coords(event.x, event.y)
            new_row = {'marker': '', 'H': dy, 'P': 1000.0, 'T': None, 'U': None, 'D': None, 'V': None, 'TD': None}
            if self.plot_mode == 'D':
                new_row['D'] = dx % 360
            else:
                new_row['V'] = max(0.0, dx)
            self.rows.append(new_row)
            self.rows.sort(key=lambda r: r['H'] if r['H'] is not None else 0)
            self.update_ui()
        self.click_start_pos = None

    def on_middle_click(self, event):
        if self.is_compare_mode and not self.rows2: return
        self.pan_start = (event.x, event.y)
        self.pan_xlim = (self.x_min, self.x_max)
        self.pan_ylim = (self.y_min, self.y_max)

    def on_middle_drag(self, event):
        if self.is_compare_mode and not self.rows2: return
        if self.pan_start:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height() - 25
            if w <= 0 or h <= 0: return

            dx_pix = event.x - self.pan_start[0]
            dy_pix = event.y - self.pan_start[1]

            dx_val = self.pan_xlim[1] - self.pan_xlim[0]
            if dx_val == 0: dx_val = 1.0
            dy_val = self.pan_ylim[1] - self.pan_ylim[0]
            if dy_val == 0: dy_val = 1.0

            dx_data = (dx_pix / w) * dx_val
            dy_data = (dy_pix / h) * dy_val

            self.x_min = self.pan_xlim[0] - dx_data
            self.x_max = self.pan_xlim[1] - dx_data
            self.y_min = self.pan_ylim[0] + dy_data
            self.y_max = self.pan_ylim[1] + dy_data
            self.draw_graph()

    def on_right_click(self, event):
        if self.is_compare_mode and not self.rows2: return
        dx, dy = self.get_data_coords(event.x, event.y)
        closest = None
        min_dist = float('inf')
        for i, r in enumerate(self.rows):
            if r.get('H') is None: continue
            val = r.get('D') if self.plot_mode == 'D' else r.get('V')
            if val is None: continue
            if self.plot_mode == 'D' and val < self.shift: val += 360
            dist = math.hypot(val - dx, r['H'] - dy)
            if dist < min_dist:
                min_dist = dist
                closest = i
        if closest is not None and min_dist < 2.0:
            self.rows.pop(closest)
            self.update_ui()

    def on_scroll(self, event):
        if self.is_compare_mode and not self.rows2: return

        if event.num == 4 or event.delta > 0:
            scale = 1.1
        elif event.num == 5 or event.delta < 0:
            scale = 1 / 1.1
        else:
            return

        mx, my = self.get_data_coords(event.x, event.y)
        self.x_min = mx - (mx - self.x_min) * scale
        self.x_max = mx + (self.x_max - mx) * scale
        self.y_min = my - (my - self.y_min) * scale
        self.y_max = my + (self.y_max - my) * scale
        self.draw_graph()

    def save_tae(self):
        path = filedialog.asksaveasfilename(defaultextension=".TAE", filetypes=[("TAE", "*.TAE")])
        if not path: return
        f = open(path, 'w', encoding='cp1251')
        f.write("      H       P       T       U       D       V     \n")
        for r in self.rows:
            def fmt(v, l, fl):
                if v is None: return " " * l
                return ("{:." + str(l) + "f}").format(v) if fl else str(v).rjust(l)

            line = "  {}  {}   0.0    0.0  {}  {}     0\n".format(fmt(r['H'], 6, 3), fmt(r['P'], 6, 1),
                                                                  fmt(r['D'], 6, 1), fmt(r['V'], 6, 1))
            f.write(line)
        f.close()
        messagebox.showinfo("OK", "Сохранено")

    def save_xls(self):
        path = filedialog.asksaveasfilename(defaultextension=".xls", filetypes=[("Excel", "*.xls")])
        if not path: return
        wb = xlwt.Workbook(encoding='cp1251')
        ws = wb.add_sheet('Профиль')
        for c, h in enumerate(['H', 'P', 'T', 'U', 'D', 'V', 'TD']):
            ws.write(0, c, h)
        for i, r in enumerate(self.rows):
            for c, k in enumerate(['H', 'P', 'T', 'U', 'D', 'V', 'TD']):
                v = r.get(k)
                if v is not None: ws.write(i + 1, c, v)
        wb.save(path)
        messagebox.showinfo("OK", "Сохранено")


if __name__ == '__main__':
    app = AeroApp()
    app.mainloop()