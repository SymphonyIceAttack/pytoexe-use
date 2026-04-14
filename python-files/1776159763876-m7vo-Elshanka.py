# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

DEFAULT_FONT = ("Arial", 9)
ENTRY_WIDTH = 12

class SettingsWindow:
    """Окно настроек инструмента и смещений"""
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = tk.Toplevel(parent)
        self.window.title("Настройки инструмента и обработки")
        self.window.resizable(False, False)
        self.window.grab_set()

        self.temp_tool_d = tk.StringVar(value=self.app.var_tool_d.get())
        self.temp_cut_depth = tk.StringVar(value=self.app.var_cut_depth.get())
        self.temp_step_down = tk.StringVar(value=self.app.var_step_down.get())
        self.temp_safe_Z = tk.StringVar(value=self.app.var_safe_Z.get())
        self.temp_feed_rapid = tk.StringVar(value=self.app.var_feed_rapid.get())
        self.temp_feed_work = tk.StringVar(value=self.app.var_feed_work.get())
        self.temp_spindle_rpm = tk.StringVar(value=self.app.var_spindle_rpm.get())
        self.temp_offset_x = tk.StringVar(value=self.app.var_offset_x.get())
        self.temp_offset_y = tk.StringVar(value=self.app.var_offset_y.get())
        self.temp_do_outer_cut = tk.BooleanVar(value=self.app.var_do_outer_cut.get())

        self.create_widgets()

    def create_widgets(self):
        frame = tk.LabelFrame(self.window, text="Параметры", padx=10, pady=10, font=DEFAULT_FONT)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        row = 0
        fields = [
            ("Диаметр инструмента, мм:", self.temp_tool_d),
            ("Глубина фрезерования, мм:", self.temp_cut_depth),
            ("Глубина за проход, мм (0=за раз):", self.temp_step_down),
            ("Безопасная высота Z, мм:", self.temp_safe_Z),
            ("Скорость холостого хода, мм/мин:", self.temp_feed_rapid),
            ("Рабочая подача, мм/мин:", self.temp_feed_work),
            ("Обороты шпинделя, об/мин:", self.temp_spindle_rpm),
            ("Смещение по X (Offset X), мм:", self.temp_offset_x),
            ("Смещение по Y (Offset Y), мм:", self.temp_offset_y),
        ]
        for label, var in fields:
            tk.Label(frame, text=label, font=DEFAULT_FONT).grid(row=row, column=0, sticky="e", padx=5, pady=3)
            tk.Entry(frame, textvariable=var, width=ENTRY_WIDTH, font=DEFAULT_FONT).grid(row=row, column=1, sticky="w", padx=5, pady=3)
            row += 1

        tk.Checkbutton(frame, text="Выполнить обрезку заготовки по периметру",
                       variable=self.temp_do_outer_cut, font=DEFAULT_FONT).grid(row=row, column=0, columnspan=2, pady=8)

        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Сохранить", command=self.save, bg="#4CAF50", fg="white",
                  font=DEFAULT_FONT, padx=15, pady=5).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.window.destroy,
                  font=DEFAULT_FONT, padx=15, pady=5).pack(side="left", padx=5)

    def save(self):
        try:
            tool_d = float(self.temp_tool_d.get())
            cut_depth = float(self.temp_cut_depth.get())
            step_down = float(self.temp_step_down.get())
            safe_Z = float(self.temp_safe_Z.get())
            feed_rapid = float(self.temp_feed_rapid.get())
            feed_work = float(self.temp_feed_work.get())
            spindle_rpm = int(self.temp_spindle_rpm.get())
            offset_x = float(self.temp_offset_x.get())
            offset_y = float(self.temp_offset_y.get())
            do_outer_cut = self.temp_do_outer_cut.get()

            if tool_d <= 0 or safe_Z <= 0:
                raise ValueError("Диаметр и безопасная высота должны быть > 0")

            self.app.var_tool_d.set(str(tool_d))
            self.app.var_cut_depth.set(str(cut_depth))
            self.app.var_step_down.set(str(step_down))
            self.app.var_safe_Z.set(str(safe_Z))
            self.app.var_feed_rapid.set(str(feed_rapid))
            self.app.var_feed_work.set(str(feed_work))
            self.app.var_spindle_rpm.set(str(spindle_rpm))
            self.app.var_offset_x.set(str(offset_x))
            self.app.var_offset_y.set(str(offset_y))
            self.app.var_do_outer_cut.set(do_outer_cut)

            self.app.update_canvas()
            self.window.destroy()
        except ValueError as e:
            messagebox.showerror("Ошибка", "Неверные числовые значения: {}".format(e))

class CNCGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор УП для ЧПУ")
        self.root.resizable(False, False)

        # Общие переменные
        self.var_tool_d = tk.StringVar(value="6")
        self.var_cut_depth = tk.StringVar(value="5")
        self.var_step_down = tk.StringVar(value="2")
        self.var_safe_Z = tk.StringVar(value="10")
        self.var_feed_rapid = tk.StringVar(value="1000")
        self.var_feed_work = tk.StringVar(value="500")
        self.var_spindle_rpm = tk.StringVar(value="12000")
        self.var_offset_x = tk.StringVar(value="0")
        self.var_offset_y = tk.StringVar(value="0")
        self.var_do_outer_cut = tk.BooleanVar(value=True)

        # Переменные для вкладки "Маска радиатора"
        self.mask_W = tk.StringVar(value="2000")
        self.mask_H = tk.StringVar(value="500")
        self.mask_L_margin = tk.StringVar(value="100")
        self.mask_R_margin = tk.StringVar(value="100")
        self.mask_M_gap = tk.StringVar(value="100")
        self.mask_H_cut = tk.StringVar(value="30")
        self.mask_output = tk.StringVar()

        # Переменные для вкладки "ФСФ 24"
        self.fsf_W = tk.StringVar(value="2000")
        self.fsf_H = tk.StringVar(value="500")
        self.fsf_cut_W = tk.StringVar(value="400")
        self.fsf_cut_H = tk.StringVar(value="30")
        self.fsf_bottom_margin = tk.StringVar(value="150")
        self.fsf_h_gap = tk.StringVar(value="30")
        self.fsf_v_gap = tk.StringVar(value="100")
        self.fsf_output = tk.StringVar()

        self.current_tab = "mask"
        self.scale_factor = 1.0

        # Отслеживание изменений
        vars_to_trace = [
            self.var_tool_d,
            self.mask_W, self.mask_H, self.mask_L_margin, self.mask_R_margin,
            self.mask_M_gap, self.mask_H_cut,
            self.fsf_W, self.fsf_H, self.fsf_cut_W, self.fsf_cut_H,
            self.fsf_bottom_margin, self.fsf_h_gap, self.fsf_v_gap
        ]
        for var in vars_to_trace:
            var.trace("w", lambda *args: self.update_canvas())

        self.create_widgets()
        self.root.after(100, self.update_canvas)

    def create_widgets(self):
        top_frame = tk.Frame(self.root)
        top_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        btn_settings = tk.Button(top_frame, text="Настройки", command=self.open_settings,
                                 font=DEFAULT_FONT, padx=10, pady=3, bg="#607D8B", fg="white")
        btn_settings.pack(side="left")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Маска радиатора")
        self.create_tab1_widgets()

        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="ФСФ 24")
        self.create_tab2_widgets()

        self.log_text = tk.Text(self.root, height=10, width=80, state="disabled", font=("Courier", 9))
        self.log_text.grid(row=2, column=0, padx=10, pady=5)

    def open_settings(self):
        SettingsWindow(self.root, self)

    def on_tab_changed(self, event):
        tab_id = self.notebook.select()
        tab_name = self.notebook.tab(tab_id, "text")
        self.current_tab = "mask" if tab_name == "Маска радиатора" else "fsf"
        self.scale_factor = 1.0
        self.update_canvas()

    def create_tab1_widgets(self):
        main_frame = tk.Frame(self.tab1)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        left_frame = tk.LabelFrame(main_frame, text="Параметры детали (маска радиатора)", padx=5, pady=5, font=DEFAULT_FONT)
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        row = 0
        fields = [
            ("Ширина заготовки (W), мм:", self.mask_W),
            ("Высота заготовки (H), мм:", self.mask_H),
            ("Левый отступ, мм:", self.mask_L_margin),
            ("Правый отступ, мм:", self.mask_R_margin),
            ("Средний отступ между вырезами, мм:", self.mask_M_gap),
            ("Высота выреза, мм:", self.mask_H_cut),
        ]
        for label, var in fields:
            tk.Label(left_frame, text=label, font=DEFAULT_FONT).grid(row=row, column=0, sticky="e", padx=5, pady=2)
            tk.Entry(left_frame, textvariable=var, width=ENTRY_WIDTH, font=DEFAULT_FONT).grid(row=row, column=1, sticky="w", padx=5, pady=2)
            row += 1

        btn_update = tk.Button(left_frame, text="Обновить схему", command=self.update_canvas,
                               bg="#FFC107", fg="black", font=DEFAULT_FONT, padx=10, pady=3)
        btn_update.grid(row=row, column=0, columnspan=2, pady=8)
        row += 1

        file_frame = tk.LabelFrame(left_frame, text="Выходной файл (.dnc)", padx=5, pady=5, font=DEFAULT_FONT)
        file_frame.grid(row=row, column=0, columnspan=2, pady=8, sticky="ew")
        tk.Entry(file_frame, textvariable=self.mask_output, width=30, font=DEFAULT_FONT).grid(row=0, column=0, padx=5, pady=3)
        tk.Button(file_frame, text="Обзор...", command=lambda: self.browse_output(self.mask_output),
                  font=DEFAULT_FONT, padx=8, pady=2).grid(row=0, column=1, padx=5, pady=3)
        row += 1

        btn_generate = tk.Button(left_frame, text="Сгенерировать G-код (Маска)", command=self.generate_mask,
                                 bg="#4CAF50", fg="white", font=DEFAULT_FONT, padx=15, pady=5)
        btn_generate.grid(row=row, column=0, columnspan=2, pady=15)

        right_frame = tk.LabelFrame(main_frame, text="Схема обработки", padx=5, pady=5, font=DEFAULT_FONT)
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.canvas1 = tk.Canvas(right_frame, width=500, height=350, bg="white")
        self.canvas1.pack(fill="both", expand=True)

        zoom_frame = tk.Frame(right_frame)
        zoom_frame.pack(pady=5)
        tk.Button(zoom_frame, text="-", command=self.zoom_out, font=DEFAULT_FONT, width=3).pack(side="left", padx=2)
        tk.Button(zoom_frame, text="+", command=self.zoom_in, font=DEFAULT_FONT, width=3).pack(side="left", padx=2)
        tk.Button(zoom_frame, text="100%", command=self.zoom_reset, font=DEFAULT_FONT, width=6).pack(side="left", padx=2)

    def create_tab2_widgets(self):
        main_frame = tk.Frame(self.tab2)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        left_frame = tk.LabelFrame(main_frame, text="Параметры детали (ФСФ 24)", padx=5, pady=5, font=DEFAULT_FONT)
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        row = 0
        fields = [
            ("Ширина заготовки (W), мм:", self.fsf_W),
            ("Высота заготовки (H), мм:", self.fsf_H),
            ("Ширина выреза, мм:", self.fsf_cut_W),
            ("Высота выреза, мм:", self.fsf_cut_H),
            ("Отступ снизу, мм:", self.fsf_bottom_margin),
            ("Горизонтальный зазор между вырезами, мм:", self.fsf_h_gap),
            ("Вертикальный зазор между рядами, мм:", self.fsf_v_gap),
        ]
        for label, var in fields:
            tk.Label(left_frame, text=label, font=DEFAULT_FONT).grid(row=row, column=0, sticky="e", padx=5, pady=2)
            tk.Entry(left_frame, textvariable=var, width=ENTRY_WIDTH, font=DEFAULT_FONT).grid(row=row, column=1, sticky="w", padx=5, pady=2)
            row += 1

        btn_update = tk.Button(left_frame, text="Обновить схему", command=self.update_canvas,
                               bg="#FFC107", fg="black", font=DEFAULT_FONT, padx=10, pady=3)
        btn_update.grid(row=row, column=0, columnspan=2, pady=8)
        row += 1

        file_frame = tk.LabelFrame(left_frame, text="Выходной файл (.dnc)", padx=5, pady=5, font=DEFAULT_FONT)
        file_frame.grid(row=row, column=0, columnspan=2, pady=8, sticky="ew")
        tk.Entry(file_frame, textvariable=self.fsf_output, width=30, font=DEFAULT_FONT).grid(row=0, column=0, padx=5, pady=3)
        tk.Button(file_frame, text="Обзор...", command=lambda: self.browse_output(self.fsf_output),
                  font=DEFAULT_FONT, padx=8, pady=2).grid(row=0, column=1, padx=5, pady=3)
        row += 1

        btn_generate = tk.Button(left_frame, text="Сгенерировать G-код (ФСФ 24)", command=self.generate_fsf,
                                 bg="#2196F3", fg="white", font=DEFAULT_FONT, padx=15, pady=5)
        btn_generate.grid(row=row, column=0, columnspan=2, pady=15)

        right_frame = tk.LabelFrame(main_frame, text="Схема обработки", padx=5, pady=5, font=DEFAULT_FONT)
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.canvas2 = tk.Canvas(right_frame, width=500, height=350, bg="white")
        self.canvas2.pack(fill="both", expand=True)

        zoom_frame = tk.Frame(right_frame)
        zoom_frame.pack(pady=5)
        tk.Button(zoom_frame, text="-", command=self.zoom_out, font=DEFAULT_FONT, width=3).pack(side="left", padx=2)
        tk.Button(zoom_frame, text="+", command=self.zoom_in, font=DEFAULT_FONT, width=3).pack(side="left", padx=2)
        tk.Button(zoom_frame, text="100%", command=self.zoom_reset, font=DEFAULT_FONT, width=6).pack(side="left", padx=2)

    def browse_output(self, var):
        filename = filedialog.asksaveasfilename(
            defaultextension=".dnc",
            filetypes=[("Файлы DNC", "*.dnc"), ("Все файлы", "*.*")],
            title="Сохранить управляющую программу как..."
        )
        if filename:
            var.set(filename)

    def zoom_in(self):
        self.scale_factor *= 1.2
        self.update_canvas()

    def zoom_out(self):
        self.scale_factor /= 1.2
        self.update_canvas()

    def zoom_reset(self):
        self.scale_factor = 1.0
        self.update_canvas()

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.root.update()

    def log_gcode(self, gcode_lines):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, "\n".join(gcode_lines) + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.root.update()

    def get_common_params(self):
        try:
            tool_d = float(self.var_tool_d.get())
            cut_depth = float(self.var_cut_depth.get())
            step_down = float(self.var_step_down.get())
            safe_Z = float(self.var_safe_Z.get())
            feed_rapid = float(self.var_feed_rapid.get())
            feed_work = float(self.var_feed_work.get())
            spindle_rpm = int(self.var_spindle_rpm.get())
            offset_x = float(self.var_offset_x.get())
            offset_y = float(self.var_offset_y.get())
            do_outer_cut = self.var_do_outer_cut.get()
            return {
                "tool_d": tool_d, "cut_depth": cut_depth, "step_down": step_down,
                "safe_Z": safe_Z, "feed_rapid": feed_rapid, "feed_work": feed_work,
                "spindle_rpm": spindle_rpm, "offset_x": offset_x, "offset_y": offset_y,
                "do_outer_cut": do_outer_cut
            }
        except ValueError as e:
            raise ValueError("Ошибка в общих параметрах: {}".format(e))

    def calculate_mask_geometry(self, common):
        try:
            W = float(self.mask_W.get())
            H = float(self.mask_H.get())
            L = float(self.mask_L_margin.get())
            R = float(self.mask_R_margin.get())
            M = float(self.mask_M_gap.get())
            H_cut = float(self.mask_H_cut.get())
        except ValueError:
            raise ValueError("Неверные числовые параметры маски")

        tool_d = common["tool_d"]
        radius = tool_d / 2.0

        W_cut = (W - L - R - M) / 2.0
        if W_cut <= 0:
            raise ValueError("Ширина выреза <= 0")

        cut_width_inner = W_cut - tool_d
        cut_height_inner = H_cut - tool_d
        if cut_width_inner <= 0 or cut_height_inner <= 0:
            raise ValueError("Вырез слишком мал для инструмента")

        left_x_min = L
        left_x_max = L + W_cut
        right_x_min = W - R - W_cut
        right_x_max = W - R
        y_min = (H - H_cut) / 2.0
        y_max = (H + H_cut) / 2.0

        left_cut_x_min = left_x_min + radius
        left_cut_x_max = left_x_max - radius
        right_cut_x_min = right_x_min + radius
        right_cut_x_max = right_x_max - radius
        cut_y_min = y_min + radius
        cut_y_max = y_max - radius

        outer_x_min = -radius
        outer_x_max = W + radius
        outer_y_min = -radius
        outer_y_max = H + radius

        return {
            "W": W, "H": H,
            "left_x_min": left_x_min, "left_x_max": left_x_max,
            "right_x_min": right_x_min, "right_x_max": right_x_max,
            "y_min": y_min, "y_max": y_max,
            "left_cut_x_min": left_cut_x_min, "left_cut_x_max": left_cut_x_max,
            "right_cut_x_min": right_cut_x_min, "right_cut_x_max": right_cut_x_max,
            "cut_y_min": cut_y_min, "cut_y_max": cut_y_max,
            "outer_x_min": outer_x_min, "outer_x_max": outer_x_max,
            "outer_y_min": outer_y_min, "outer_y_max": outer_y_max,
            "tool_radius": radius,
            "H_cut": H_cut, "W_cut": W_cut
        }

    def calculate_fsf_geometry(self, common):
        try:
            W = float(self.fsf_W.get())
            H = float(self.fsf_H.get())
            cut_W = float(self.fsf_cut_W.get())
            cut_H = float(self.fsf_cut_H.get())
            bottom = float(self.fsf_bottom_margin.get())
            h_gap = float(self.fsf_h_gap.get())
            v_gap = float(self.fsf_v_gap.get())
        except ValueError:
            raise ValueError("Неверные числовые параметры ФСФ")

        tool_d = common["tool_d"]
        radius = tool_d / 2.0

        block_width = 2 * cut_W + h_gap
        block_height = 2 * cut_H + v_gap

        start_x = (W - block_width) / 2.0
        start_y = bottom

        pockets = []
        for row in range(2):
            y_base = start_y + row * (cut_H + v_gap)
            for col in range(2):
                x_base = start_x + col * (cut_W + h_gap)
                pockets.append({
                    "x_min": x_base,
                    "x_max": x_base + cut_W,
                    "y_min": y_base,
                    "y_max": y_base + cut_H
                })

        for p in pockets:
            p["cut_x_min"] = p["x_min"] + radius
            p["cut_x_max"] = p["x_max"] - radius
            p["cut_y_min"] = p["y_min"] + radius
            p["cut_y_max"] = p["y_max"] - radius

        outer_x_min = -radius
        outer_x_max = W + radius
        outer_y_min = -radius
        outer_y_max = H + radius

        return {
            "W": W, "H": H,
            "pockets": pockets,
            "outer_x_min": outer_x_min, "outer_x_max": outer_x_max,
            "outer_y_min": outer_y_min, "outer_y_max": outer_y_max,
            "tool_radius": radius
        }

    def update_canvas(self, *args):
        self.canvas1.delete("all")
        self.canvas2.delete("all")

        try:
            common = self.get_common_params()
        except ValueError:
            return

        if self.current_tab == "mask":
            try:
                geom = self.calculate_mask_geometry(common)
            except ValueError:
                return
            self.draw_mask(self.canvas1, common, geom)
        else:
            try:
                geom = self.calculate_fsf_geometry(common)
            except ValueError:
                return
            self.draw_fsf(self.canvas2, common, geom)

    def draw_mask(self, canvas, common, geom):
        canvas_w = canvas.winfo_width()
        canvas_h = canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            canvas_w, canvas_h = 500, 350

        margin = 40
        base_scale = min((canvas_w - 2*margin) / geom["W"], (canvas_h - 2*margin) / geom["H"])
        scale = base_scale * self.scale_factor

        def to_canvas(x, y):
            offset_x = (canvas_w - geom["W"] * scale) / 2
            offset_y = (canvas_h - geom["H"] * scale) / 2
            return (offset_x + x * scale, canvas_h - offset_y - y * scale)

        x0, y0 = to_canvas(0, 0)
        x1, y1 = to_canvas(geom["W"], geom["H"])
        canvas.create_rectangle(x0, y0, x1, y1, outline="blue", width=2)

        canvas.create_line(x0, y0-10, x1, y0-10, fill="blue", arrow=tk.BOTH)
        canvas.create_text((x0+x1)/2, y0-15, text="{:.1f}".format(geom['W']), fill="blue", font=("Arial", 8))
        canvas.create_line(x0-10, y0, x0-10, y1, fill="blue", arrow=tk.BOTH)
        canvas.create_text(x0-20, (y0+y1)/2, text="{:.1f}".format(geom['H']), fill="blue", font=("Arial", 8), angle=90)

        if common["do_outer_cut"]:
            ox0, oy0 = to_canvas(geom["outer_x_min"], geom["outer_y_min"])
            ox1, oy1 = to_canvas(geom["outer_x_max"], geom["outer_y_max"])
            canvas.create_rectangle(ox0, oy0, ox1, oy1, outline="red", dash=(4,4))

        lx0, ly0 = to_canvas(geom["left_x_min"], geom["y_min"])
        lx1, ly1 = to_canvas(geom["left_x_max"], geom["y_max"])
        canvas.create_rectangle(lx0, ly0, lx1, ly1, outline="green", width=2)
        w_cut = geom["left_x_max"] - geom["left_x_min"]
        h_cut = geom["y_max"] - geom["y_min"]
        canvas.create_line(lx0, ly0-5, lx1, ly0-5, fill="green", arrow=tk.BOTH)
        canvas.create_text((lx0+lx1)/2, ly0-10, text="{:.1f}".format(w_cut), fill="green", font=("Arial", 7))
        canvas.create_line(lx0-5, ly0, lx0-5, ly1, fill="green", arrow=tk.BOTH)
        canvas.create_text(lx0-12, (ly0+ly1)/2, text="{:.1f}".format(h_cut), fill="green", font=("Arial", 7), angle=90)

        rx0, ry0 = to_canvas(geom["right_x_min"], geom["y_min"])
        rx1, ry1 = to_canvas(geom["right_x_max"], geom["y_max"])
        canvas.create_rectangle(rx0, ry0, rx1, ry1, outline="green", width=2)
        canvas.create_line(rx0, ry0-5, rx1, ry0-5, fill="green", arrow=tk.BOTH)
        canvas.create_text((rx0+rx1)/2, ry0-10, text="{:.1f}".format(w_cut), fill="green", font=("Arial", 7))
        canvas.create_line(rx0-5, ry0, rx0-5, ry1, fill="green", arrow=tk.BOTH)
        canvas.create_text(rx0-12, (ry0+ry1)/2, text="{:.1f}".format(h_cut), fill="green", font=("Arial", 7), angle=90)

        lcx0, lcy0 = to_canvas(geom["left_cut_x_min"], geom["cut_y_min"])
        lcx1, lcy1 = to_canvas(geom["left_cut_x_max"], geom["cut_y_max"])
        canvas.create_rectangle(lcx0, lcy0, lcx1, lcy1, outline="gray", dash=(2,2))

        rcx0, rcy0 = to_canvas(geom["right_cut_x_min"], geom["cut_y_min"])
        rcx1, rcy1 = to_canvas(geom["right_cut_x_max"], geom["cut_y_max"])
        canvas.create_rectangle(rcx0, rcy0, rcx1, rcy1, outline="gray", dash=(2,2))

        canvas.create_text(x0+5, y0+5, text="0,0", anchor="nw", fill="blue", font=("Arial", 8))

    def draw_fsf(self, canvas, common, geom):
        canvas_w = canvas.winfo_width()
        canvas_h = canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            canvas_w, canvas_h = 500, 350

        margin = 40
        base_scale = min((canvas_w - 2*margin) / geom["W"], (canvas_h - 2*margin) / geom["H"])
        scale = base_scale * self.scale_factor

        def to_canvas(x, y):
            offset_x = (canvas_w - geom["W"] * scale) / 2
            offset_y = (canvas_h - geom["H"] * scale) / 2
            return (offset_x + x * scale, canvas_h - offset_y - y * scale)

        x0, y0 = to_canvas(0, 0)
        x1, y1 = to_canvas(geom["W"], geom["H"])
        canvas.create_rectangle(x0, y0, x1, y1, outline="blue", width=2)

        canvas.create_line(x0, y0-10, x1, y0-10, fill="blue", arrow=tk.BOTH)
        canvas.create_text((x0+x1)/2, y0-15, text="{:.1f}".format(geom['W']), fill="blue", font=("Arial", 8))
        canvas.create_line(x0-10, y0, x0-10, y1, fill="blue", arrow=tk.BOTH)
        canvas.create_text(x0-20, (y0+y1)/2, text="{:.1f}".format(geom['H']), fill="blue", font=("Arial", 8), angle=90)

        if common["do_outer_cut"]:
            ox0, oy0 = to_canvas(geom["outer_x_min"], geom["outer_y_min"])
            ox1, oy1 = to_canvas(geom["outer_x_max"], geom["outer_y_max"])
            canvas.create_rectangle(ox0, oy0, ox1, oy1, outline="red", dash=(4,4))

        for i, p in enumerate(geom["pockets"]):
            px0, py0 = to_canvas(p["x_min"], p["y_min"])
            px1, py1 = to_canvas(p["x_max"], p["y_max"])
            canvas.create_rectangle(px0, py0, px1, py1, outline="green", width=2)
            w = p["x_max"] - p["x_min"]
            h = p["y_max"] - p["y_min"]
            canvas.create_line(px0, py0-5, px1, py0-5, fill="green", arrow=tk.BOTH)
            canvas.create_text((px0+px1)/2, py0-10, text="{:.1f}".format(w), fill="green", font=("Arial", 7))
            canvas.create_line(px0-5, py0, px0-5, py1, fill="green", arrow=tk.BOTH)
            canvas.create_text(px0-12, (py0+py1)/2, text="{:.1f}".format(h), fill="green", font=("Arial", 7), angle=90)

            pcx0, pcy0 = to_canvas(p["cut_x_min"], p["cut_y_min"])
            pcx1, pcy1 = to_canvas(p["cut_x_max"], p["cut_y_max"])
            canvas.create_rectangle(pcx0, pcy0, pcx1, pcy1, outline="gray", dash=(2,2))

        canvas.create_text(x0+5, y0+5, text="0,0", anchor="nw", fill="blue", font=("Arial", 8))

    def generate_mask(self):
        try:
            out_file = self.mask_output.get().strip()
            if not out_file:
                raise ValueError("Не указан выходной файл для маски")
            if os.path.exists(out_file):
                if not messagebox.askyesno("Подтверждение", "Файл '{}' уже существует. Перезаписать?".format(out_file)):
                    return
            common = self.get_common_params()
            geom = self.calculate_mask_geometry(common)
            gcode = self._generate_gcode(common, geom, "mask")
            self._save_and_log(gcode, out_file, "mask")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def generate_fsf(self):
        try:
            out_file = self.fsf_output.get().strip()
            if not out_file:
                raise ValueError("Не указан выходной файл для ФСФ")
            if os.path.exists(out_file):
                if not messagebox.askyesno("Подтверждение", "Файл '{}' уже существует. Перезаписать?".format(out_file)):
                    return
            common = self.get_common_params()
            geom = self.calculate_fsf_geometry(common)
            gcode = self._generate_gcode(common, geom, "fsf")
            self._save_and_log(gcode, out_file, "fsf")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _apply_offset(self, x, y, common):
        return x + common["offset_x"], y + common["offset_y"]

    def _generate_gcode(self, common, geom, mode):
        gcode = []
        gcode.append("(Generated by CNC G-code generator - {})".format(mode))
        gcode.append("(Material: {} x {} mm, Tool D={})".format(geom["W"], geom["H"], common["tool_d"]))
        gcode.append("(Offset X={:.3f} Y={:.3f})".format(common["offset_x"], common["offset_y"]))
        gcode.append("G21 G17 G40 G90")
        gcode.append("G0 Z{:.3f}".format(common["safe_Z"]))
        gcode.append("")

        cut_depth = common["cut_depth"]
        step_down = common["step_down"]
        if step_down <= 0:
            steps = [(cut_depth,)]
        else:
            steps = []
            z = 0.0
            while z < cut_depth:
                nz = min(z + step_down, cut_depth)
                steps.append((nz,))
                z = nz

        def fmt_xy(x, y):
            ox, oy = self._apply_offset(x, y, common)
            return "X{:.3f} Y{:.3f}".format(ox, oy)

        if common["do_outer_cut"]:
            gcode.append("(=== OUTER CONTOUR ===)")
            gcode.append("S{} M3".format(common["spindle_rpm"]))
            gcode.append("G0 {}".format(fmt_xy(geom["outer_x_min"], geom["outer_y_min"])))
            gcode.append("G0 Z{:.3f}".format(common["safe_Z"]))
            for step in steps:
                z = -step[0]
                gcode.append("G1 Z{:.3f} F{}".format(z, common["feed_work"]))
                gcode.append("G1 {}".format(fmt_xy(geom["outer_x_max"], geom["outer_y_min"])))
                gcode.append("Y{:.3f}".format(common["offset_y"] + geom["outer_y_max"]))
                gcode.append("X{:.3f}".format(common["offset_x"] + geom["outer_x_min"]))
                gcode.append("Y{:.3f}".format(common["offset_y"] + geom["outer_y_min"]))
                if step != steps[-1]:
                    gcode.append("G0 Z{:.3f}".format(common["safe_Z"]))
            gcode.append("G0 Z{:.3f}".format(common["safe_Z"]))
            gcode.append("")

        def add_pocket(xmin, xmax, ymin, ymax):
            gcode.append("G0 {}".format(fmt_xy(xmin, ymin)))
            gcode.append("G0 Z{:.3f}".format(common["safe_Z"]))
            for step in steps:
                z = -step[0]
                gcode.append("G1 Z{:.3f} F{}".format(z, common["feed_work"]))
                gcode.append("Y{:.3f}".format(common["offset_y"] + ymax))
                gcode.append("X{:.3f}".format(common["offset_x"] + xmax))
                gcode.append("Y{:.3f}".format(common["offset_y"] + ymin))
                gcode.append("X{:.3f}".format(common["offset_x"] + xmin))
                if step != steps[-1]:
                    gcode.append("G0 Z{:.3f}".format(common["safe_Z"]))
            gcode.append("G0 Z{:.3f}".format(common["safe_Z"]))

        if mode == "mask":
            gcode.append("(=== LEFT POCKET ===)")
            add_pocket(geom["left_cut_x_min"], geom["left_cut_x_max"], geom["cut_y_min"], geom["cut_y_max"])
            gcode.append("")
            gcode.append("(=== RIGHT POCKET ===)")
            add_pocket(geom["right_cut_x_min"], geom["right_cut_x_max"], geom["cut_y_min"], geom["cut_y_max"])
        else:
            for i, p in enumerate(geom["pockets"]):
                gcode.append("(=== POCKET {} ===)".format(i+1))
                add_pocket(p["cut_x_min"], p["cut_x_max"], p["cut_y_min"], p["cut_y_max"])
                gcode.append("")

        gcode.append("(=== END ===)")
        gcode.append("G0 Z{:.3f}".format(common["safe_Z"]))
        gcode.append("M5")
        gcode.append("M30")

        return gcode

    def _save_and_log(self, gcode, out_file, mode):
        with open(out_file, 'w') as f:
            f.write('\n'.join(gcode))

        self.log("=== G-код для {} ===".format(mode))
        self.log_gcode(gcode)
        self.log("Файл сохранён: {}".format(out_file))
        messagebox.showinfo("Готово", "Файл сохранён:\n{}".format(out_file))

if __name__ == "__main__":
    root = tk.Tk()
    app = CNCGeneratorApp(root)
    root.bind("<Configure>", lambda e: app.update_canvas())
    root.mainloop()