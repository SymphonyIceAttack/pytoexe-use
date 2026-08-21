import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import math
import re
import os

# ---------- Константы ----------
DEFAULT_INPUT_FILE = "Параметры Маятниковой сварки GSK.txt"
OUTPUT_FILE = "program.txt"

IDX_X = 0
IDX_Y = 1
IDX_Z = 2
IDX_ANGLE = 7

# ---------- Логика генерации ----------
def parse_param_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    movl_line = None
    params = {}
    for line in lines:
        if line.startswith("MOVL"):
            movl_line = line
        elif '=' in line:
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip()
            if "Диаметр" in key:
                params['diameter'] = float(val)
            elif "мм влево" in key:
                params['left'] = float(val)
            elif "мм вправо" in key:
                params['right'] = float(val)
            elif "мм шаг" in key:
                params['step'] = float(val)   # теперь это длина полного цикла
            elif "Начальный угол" in key:
                params['start_angle'] = float(val)
            elif "Конечный угол" in key:
                params['end_angle'] = float(val)
            elif "Ось" in key:
                params['axis'] = val.upper()
            elif "Скорость сварки" in key:
                params['weld_speed'] = float(val)
            elif "Максимальная скорость вращателя" in key:
                params['max_rot_rpm'] = float(val)
    if movl_line is None:
        raise ValueError("Не найдена строка MOVL в файле")
    required = ('diameter','left','right','step','start_angle','end_angle','axis','weld_speed')
    if not all(k in params for k in required):
        missing = [k for k in required if k not in params]
        raise ValueError(f"Не все параметры найдены: {missing}")
    if 'max_rot_rpm' not in params:
        params['max_rot_rpm'] = 20.0
    return movl_line, params

def format_number(v):
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    else:
        return f"{v:.3f}"

def generate_synchronized_commands(movl_template, params):
    match = re.search(r'P\*\(([^)]+)\)', movl_template)
    if not match:
        raise ValueError("Не найден формат P*(...) в строке MOVL")
    numbers_str = match.group(1)
    numbers = [float(x) for x in numbers_str.split(',')]
    suffix = movl_template.split(')', 1)[1]

    D = params['diameter']
    left = params['left']
    right = params['right']
    step_cycle = params['step']        # полный цикл (влево-вправо-влево)
    start_deg = params['start_angle']
    end_deg = params['end_angle']
    axis = params['axis']
    weld_speed = params['weld_speed']
    max_rot_rpm = params['max_rot_rpm']

    if weld_speed <= 0:
        raise ValueError("Скорость сварки должна быть > 0")
    R = D / 2.0
    if R <= 0:
        raise ValueError("Диаметр должен быть > 0")

    max_rot_deg_per_sec = (max_rot_rpm / 60.0) * 360.0
    omega_deg = (weld_speed / R) * (180.0 / math.pi)
    ev_percent = int(round((omega_deg / max_rot_deg_per_sec) * 100))
    if ev_percent > 100:
        ev_percent = 100
    elif ev_percent < 1:
        ev_percent = 1

    actual_speed = weld_speed
    if ev_percent == 100 and weld_speed > (max_rot_deg_per_sec * R * math.pi / 180):
        actual_speed = max_rot_deg_per_sec * R * math.pi / 180

    # Шаг между соседними точками = половина цикла
    step_between = step_cycle / 2.0
    dtheta_deg = math.degrees(step_between / R)
    if dtheta_deg == 0:
        raise ValueError("Шаг не может быть нулевым")
    step_deg = dtheta_deg if end_deg >= start_deg else -dtheta_deg

    angles = []
    theta = start_deg
    while True:
        angles.append(theta)
        if (step_deg > 0 and theta >= end_deg) or (step_deg < 0 and theta <= end_deg):
            break
        theta += step_deg
        if abs(theta) > 1000:
            break

    base_x = numbers[IDX_X]
    base_y = numbers[IDX_Y]
    base_z = numbers[IDX_Z]

    commands = []
    points = []

    for i, theta_deg in enumerate(angles):
        # Чередуем: i=0 -> влево, i=1 -> вправо, i=2 -> влево, и т.д.
        delta = left if i % 2 == 0 else -right
        new_numbers = numbers[:]
        if axis == 'X':
            new_numbers[IDX_X] = base_x + delta
        elif axis == 'Y':
            new_numbers[IDX_Y] = base_y + delta
        elif axis == 'Z':
            new_numbers[IDX_Z] = base_z + delta
        else:
            raise ValueError("Ось должна быть X, Y или Z")
        new_numbers[IDX_ANGLE] = theta_deg

        num_str = ','.join(format_number(v) for v in new_numbers)
        v_int = int(round(actual_speed))
        v_str = str(v_int)

        def repl_v(m):
            return f",V{v_str}"
        new_suffix = re.sub(r',V\s*[\d.]+', repl_v, suffix, count=1)
        def repl_ev(m):
            return f",EV{ev_percent}"
        new_suffix = re.sub(r',EV\s*[\d.]+', repl_ev, new_suffix, count=1)

        cmd = f"MOVL P*({num_str}){new_suffix}"
        commands.append(cmd)

        x = new_numbers[IDX_X]
        y = new_numbers[IDX_Y]
        points.append((x, y))

    total_distance = 0.0
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i+1]
        dx = x2 - x1
        dy = y2 - y1
        total_distance += math.hypot(dx, dy)

    time_seconds = total_distance / actual_speed if actual_speed > 0 else 0
    return commands, time_seconds, actual_speed, ev_percent, total_distance


# ---------- GUI Класс ----------
class WeldApp:
    def __init__(self, root):
        self.root = root
        root.title("Генератор маятниковой сварки GSK")
        root.geometry("1200x780")

        self.params = {}
        self.movl_line = ""

        self.create_widgets()

        if not os.path.exists(DEFAULT_INPUT_FILE):
            self.create_default_file()
            self.output_text.insert(tk.END, f"✅ Создан файл {DEFAULT_INPUT_FILE} с параметрами по умолчанию.\n")
            self.output_text.see(tk.END)

        try:
            self.load_from_file()
        except Exception as e:
            self.output_text.insert(tk.END, f"⚠️ Не удалось загрузить файл: {e}\n")
            self.output_text.see(tk.END)

    def create_widgets(self):
        frame_inputs = tk.LabelFrame(self.root, text="Параметры сварки", padx=10, pady=10)
        frame_inputs.pack(fill="x", padx=10, pady=5)
        frame_inputs.columnconfigure(0, weight=1)

        param_list = [
            ("Диаметр", "diameter", "мм", 1.0),
            ("мм влево", "left", "мм", 0.1),
            ("мм вправо", "right", "мм", 0.1),
            ("мм шаг (цикл)", "step", "мм", 0.1),
            ("Начальный угол", "start_angle", "град", 1.0),
            ("Конечный угол", "end_angle", "град", 1.0),
            ("Скорость сварки", "weld_speed", "мм/с", 1.0),
            ("Макс. скор. вращателя", "max_rot_rpm", "об/мин", 1.0)
        ]

        self.entries = {}
        self.var_axis = tk.StringVar(value="Y")

        for idx, (label, key, unit, step) in enumerate(param_list):
            row_frame = tk.Frame(frame_inputs)
            row_frame.grid(row=idx, column=0, sticky="ew", pady=2)

            lbl = tk.Label(row_frame, text=label, width=20, anchor="w")
            lbl.pack(side="left", padx=(0,5))

            entry = tk.Entry(row_frame, width=8)
            entry.pack(side="left")
            self.entries[key] = entry

            lbl_unit = tk.Label(row_frame, text=unit, width=8, anchor="w")
            lbl_unit.pack(side="left", padx=(2,5))

            btn_minus = tk.Button(row_frame, text="-1", width=3,
                                  command=lambda e=entry, st=step: self.step_entry(e, -st))
            btn_minus.pack(side="left", padx=2)

            btn_plus = tk.Button(row_frame, text="+1", width=3,
                                 command=lambda e=entry, st=step: self.step_entry(e, st))
            btn_plus.pack(side="left", padx=2)

        row_axis = tk.Frame(frame_inputs)
        row_axis.grid(row=len(param_list), column=0, sticky="ew", pady=2)

        lbl_axis = tk.Label(row_axis, text="Ось (X/Y/Z)", width=20, anchor="w")
        lbl_axis.pack(side="left", padx=(0,5))

        combo_axis = ttk.Combobox(row_axis, values=["X", "Y", "Z"], textvariable=self.var_axis, width=8)
        combo_axis.pack(side="left")

        row_movl = tk.Frame(frame_inputs)
        row_movl.grid(row=len(param_list)+1, column=0, sticky="ew", pady=5)

        lbl_movl = tk.Label(row_movl, text="MOVL строка:", width=10, anchor="w")
        lbl_movl.pack(side="left", padx=(0,5))

        btn_clear_movl = tk.Button(row_movl, text="Стереть", command=self.clear_movl)
        btn_clear_movl.pack(side="left", padx=5)

        self.movl_entry = tk.Entry(row_movl, width=120)
        self.movl_entry.pack(side="left", fill="x", expand=True, padx=5)

        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(fill="x", padx=10, pady=5)

        btn_load = tk.Button(frame_buttons, text="Загрузить из файла", command=self.load_from_file)
        btn_load.pack(side="left", padx=5)

        btn_save = tk.Button(frame_buttons, text="Сохранить параметры", command=self.save_to_file)
        btn_save.pack(side="left", padx=5)

        btn_generate = tk.Button(frame_buttons, text="Сгенерировать программу", command=self.generate)
        btn_generate.pack(side="left", padx=5)

        btn_clear = tk.Button(frame_buttons, text="Очистить вывод", command=self.clear_output)
        btn_clear.pack(side="left", padx=5)

        btn_scheme = tk.Button(frame_buttons, text="Показать схему", command=self.show_scheme)
        btn_scheme.pack(side="left", padx=5)

        frame_output = tk.LabelFrame(self.root, text="Результат", padx=10, pady=10)
        frame_output.pack(fill="both", expand=True, padx=10, pady=5)

        self.output_text = scrolledtext.ScrolledText(frame_output, wrap=tk.WORD, height=20)
        self.output_text.pack(fill="both", expand=True)

    def step_entry(self, entry, delta):
        try:
            current = float(entry.get())
            new_val = current + delta
            if abs(new_val - round(new_val)) < 1e-9:
                entry.delete(0, tk.END)
                entry.insert(0, str(int(round(new_val))))
            else:
                entry.delete(0, tk.END)
                entry.insert(0, f"{new_val:.3f}".rstrip('0').rstrip('.'))
        except ValueError:
            pass

    def clear_movl(self):
        self.movl_entry.delete(0, tk.END)

    def create_default_file(self):
        default_content = """MOVL P*(22.557167,21.523677,36.303437,-74.299167,14.754652,12.513619,-74.998623,-6.944225,1,1,843.011269,-35.840060,91.207866,-176.729358,24.790600,126.829622) ,V150 ,Z0 ,E2 ,EV5 ;

"Введите параметры сварки:"
Диаметр = 312
мм влево = 1
мм вправо = 1
мм шаг (цикл) = 4
Начальный угол = -10
Конечный угол = 350
Ось = Y
Скорость сварки = 15
Максимальная скорость вращателя (об/мин) = 20
"""
        with open(DEFAULT_INPUT_FILE, "w", encoding="utf-8") as f:
            f.write(default_content)

    def load_from_file(self):
        if not os.path.exists(DEFAULT_INPUT_FILE):
            messagebox.showwarning("Файл не найден", f"Файл {DEFAULT_INPUT_FILE} не найден.\nСоздайте его или введите параметры вручную.")
            return
        try:
            movl_line, params = parse_param_file(DEFAULT_INPUT_FILE)
            self.movl_line = movl_line
            self.movl_entry.delete(0, tk.END)
            self.movl_entry.insert(0, movl_line)
            self.params = params
            for key, val in params.items():
                if key == "axis":
                    self.var_axis.set(val)
                elif key in self.entries:
                    self.entries[key].delete(0, tk.END)
                    if abs(val - round(val)) < 1e-9:
                        self.entries[key].insert(0, str(int(round(val))))
                    else:
                        self.entries[key].insert(0, f"{val:.3f}".rstrip('0').rstrip('.'))
            self.output_text.insert(tk.END, f"✅ Загружены параметры из {DEFAULT_INPUT_FILE}\n")
            self.output_text.see(tk.END)
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", str(e))

    def save_to_file(self):
        try:
            params = {}
            for key, entry in self.entries.items():
                val_str = entry.get().strip()
                if not val_str:
                    raise ValueError(f"Поле {key} не заполнено")
                params[key] = float(val_str)
            params['axis'] = self.var_axis.get().upper()
            if params['axis'] not in ('X','Y','Z'):
                raise ValueError("Ось должна быть X, Y или Z")

            movl_str = self.movl_entry.get().strip()
            if not movl_str:
                raise ValueError("Строка MOVL не может быть пустой.")
            if not movl_str.startswith("MOVL"):
                raise ValueError("Строка должна начинаться с 'MOVL'.")

            lines = []
            lines.append(movl_str)
            lines.append("")
            lines.append("\"Введите параметры сварки:\"")
            mapping = {
                "diameter": "Диаметр",
                "left": "мм влево",
                "right": "мм вправо",
                "step": "мм шаг (цикл)",
                "start_angle": "Начальный угол",
                "end_angle": "Конечный угол",
                "axis": "Ось",
                "weld_speed": "Скорость сварки",
                "max_rot_rpm": "Максимальная скорость вращателя (об/мин)"
            }
            for key, label in mapping.items():
                if key in params:
                    val = params[key]
                    if key == "axis":
                        lines.append(f"{label} = {val}")
                    else:
                        if abs(val - round(val)) < 1e-9:
                            lines.append(f"{label} = {int(round(val))}")
                        else:
                            lines.append(f"{label} = {val:.3f}".rstrip('0').rstrip('.'))
            with open(DEFAULT_INPUT_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            self.output_text.insert(tk.END, f"✅ Параметры сохранены в {DEFAULT_INPUT_FILE}\n")
            self.output_text.see(tk.END)
            self.params = params
            self.movl_line = movl_str
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))

    def generate(self):
        try:
            params = {}
            for key, entry in self.entries.items():
                val_str = entry.get().strip()
                if not val_str:
                    raise ValueError(f"Поле {key} не заполнено")
                params[key] = float(val_str)
            params['axis'] = self.var_axis.get().upper()
            if params['axis'] not in ('X','Y','Z'):
                raise ValueError("Ось должна быть X, Y или Z")

            movl_str = self.movl_entry.get().strip()
            if not movl_str:
                raise ValueError("Строка MOVL не может быть пустой.")
            if not movl_str.startswith("MOVL"):
                raise ValueError("Строка должна начинаться с 'MOVL'.")

            commands, time_sec, speed, ev, dist = generate_synchronized_commands(movl_str, params)

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                for cmd in commands:
                    f.write(cmd + "\n")

            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"✅ Сгенерировано {len(commands)} команд.\n")
            self.output_text.insert(tk.END, f"Файл сохранён: {OUTPUT_FILE}\n")
            self.output_text.insert(tk.END, f"Время: {time_sec:.2f} сек, скорость: {int(round(speed))} мм/с, EV: {ev}%\n\n")
            self.output_text.insert(tk.END, "Первые 5 команд:\n")
            for cmd in commands[:5]:
                self.output_text.insert(tk.END, cmd + "\n")
            self.output_text.see(tk.END)

        except Exception as e:
            messagebox.showerror("Ошибка генерации", str(e))

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

    def show_scheme(self):
        """Открывает окно со схемой: слева вид сверху, справа развёртка с 3 циклами."""
        try:
            diam = float(self.entries['diameter'].get()) if self.entries['diameter'].get() else 312
            left = float(self.entries['left'].get()) if self.entries['left'].get() else 1
            right = float(self.entries['right'].get()) if self.entries['right'].get() else 1
            step_cycle = float(self.entries['step'].get()) if self.entries['step'].get() else 4
            start = float(self.entries['start_angle'].get()) if self.entries['start_angle'].get() else -10
            end = float(self.entries['end_angle'].get()) if self.entries['end_angle'].get() else 350
        except:
            diam, left, right, step_cycle, start, end = 312, 1, 1, 4, -10, 350

        scheme_win = tk.Toplevel(self.root)
        scheme_win.title("Схема параметров сварки (вид сверху и развёртка)")
        scheme_win.geometry("1100x600")
        scheme_win.resizable(False, False)

        # Левый canvas - вид сверху
        left_canvas = tk.Canvas(scheme_win, width=550, height=550, bg='white', highlightthickness=1, highlightbackground='gray')
        left_canvas.pack(side='left', padx=10, pady=10)

        # Правый canvas - развёртка с прокруткой
        right_frame = tk.Frame(scheme_win, width=550, height=550)
        right_frame.pack(side='right', padx=10, pady=10)
        right_frame.pack_propagate(False)

        right_canvas = tk.Canvas(right_frame, bg='white', highlightthickness=1, highlightbackground='gray')
        h_scroll = tk.Scrollbar(right_frame, orient='horizontal', command=right_canvas.xview)
        v_scroll = tk.Scrollbar(right_frame, orient='vertical', command=right_canvas.yview)
        right_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        right_canvas.pack(side='top', fill='both', expand=True)
        h_scroll.pack(side='bottom', fill='x')
        v_scroll.pack(side='right', fill='y')

        # ---- Вид сверху (левый canvas) ----
        cx, cy = 275, 275
        pixel_radius = min(200, diam * 0.6) if diam > 0 else 150

        left_canvas.create_oval(cx - pixel_radius, cy - pixel_radius,
                                cx + pixel_radius, cy + pixel_radius,
                                outline='blue', width=2)
        left_canvas.create_line(cx - pixel_radius, cy + pixel_radius + 20,
                                cx + pixel_radius, cy + pixel_radius + 20,
                                arrow='both')
        left_canvas.create_text(cx, cy + pixel_radius + 40, text=f"Диаметр = {diam} мм", font=('Arial', 10))

        start_rad = math.radians(start)
        end_rad = math.radians(end)
        if end < start:
            end_rad += 2 * math.pi
        extent = math.degrees(end_rad - start_rad)
        if extent < 0:
            extent += 360

        left_canvas.create_arc(cx - pixel_radius, cy - pixel_radius,
                               cx + pixel_radius, cy + pixel_radius,
                               start=start, extent=extent,
                               outline='red', width=4, style='arc')

        sx = cx + pixel_radius * math.cos(math.radians(start))
        sy = cy - pixel_radius * math.sin(math.radians(start))
        left_canvas.create_line(cx, cy, sx, sy, fill='green', dash=(4,2))
        left_canvas.create_text(sx + 15, sy - 15, text="Начало", fill='green', font=('Arial', 9))

        end_actual = end if end >= start else end + 360
        ex = cx + pixel_radius * math.cos(math.radians(end_actual))
        ey = cy - pixel_radius * math.sin(math.radians(end_actual))
        left_canvas.create_line(cx, cy, ex, ey, fill='orange', dash=(4,2))
        left_canvas.create_text(ex + 15, ey - 15, text="Конец", fill='orange', font=('Arial', 9))

        left_canvas.create_text(cx + pixel_radius * 0.5, cy - 30,
                                text=f"Угол: {start}° → {end}°", font=('Arial', 10))

        # Шаг на дуге (отметим один цикл = два шага)
        mid_angle = (start + end) / 2 if end >= start else (start + end + 360) / 2
        if diam > 0:
            # Угол, соответствующий половине цикла (половина шага) для отображения расстояния между точками
            step_between = step_cycle / 2.0
            step_angle_deg = math.degrees(step_between / (diam/2))
        else:
            step_angle_deg = 1
        # Отметим расстояние между двумя соседними точками (половина цикла)
        angle1 = mid_angle - step_angle_deg/2
        angle2 = mid_angle + step_angle_deg/2
        a1 = math.radians(angle1)
        a2 = math.radians(angle2)
        px1 = cx + pixel_radius * math.cos(a1)
        py1 = cy - pixel_radius * math.sin(a1)
        px2 = cx + pixel_radius * math.cos(a2)
        py2 = cy - pixel_radius * math.sin(a2)
        left_canvas.create_line(px1, py1, px2, py2, fill='brown', width=3)
        left_canvas.create_text((px1+px2)/2, (py1+py2)/2 - 20, text=f"шаг (цикл) = {step_cycle} мм", fill='brown', font=('Arial', 9))
        # Дополнительно подпишем половину цикла
        left_canvas.create_text((px1+px2)/2, (py1+py2)/2 + 20, text=f"половина = {step_between:.1f} мм", fill='brown', font=('Arial', 8))

        left_canvas.create_text(275, 520, text="Вид сверху", font=('Arial', 12, 'bold'))

        # ---- Развёртка (правый canvas) ----
        num_cycles = 3
        total_length = num_cycles * step_cycle

        # Масштаб: 5 пикселей на 1 мм
        scale = 5
        canvas_width = total_length * scale + 100
        canvas_height = 400
        right_canvas.config(scrollregion=(0, 0, canvas_width, canvas_height), width=550, height=550)

        margin = 50
        x0 = margin
        y0 = 50
        y1 = y0 + 300
        mid_y = (y0 + y1)//2

        right_canvas.create_rectangle(x0, y0, x0 + total_length*scale, y1, outline='black', width=1)
        right_canvas.create_text(x0 + total_length*scale/2, y0 - 10, text=f"Развёртка (3 цикла = {total_length:.1f} мм)", font=('Arial', 10))

        # Оси
        right_canvas.create_line(x0, mid_y, x0 + total_length*scale, mid_y, fill='gray', dash=(4,2))
        right_canvas.create_text(x0 + total_length*scale + 10, mid_y, text="длина дуги (мм)", font=('Arial', 8))
        right_canvas.create_line(x0 + total_length*scale/2, y0, x0 + total_length*scale/2, y1, fill='gray', dash=(4,2))
        right_canvas.create_text(x0 + total_length*scale/2, y0-5, text="амплитуда", font=('Arial', 8))

        # Точки: всего 7 точек (начало + 6 шагов, где каждый шаг = половина цикла)
        num_points = num_cycles * 2 + 1
        points = []
        amp_scale = 50  # пикселей на 1 мм амплитуды
        max_amp = max(left, right)
        if max_amp == 0:
            max_amp = 1

        step_between = step_cycle / 2.0
        for i in range(num_points):
            arc_pos = i * step_between
            x = x0 + arc_pos * scale
            if i % 2 == 0:
                amp = -left
            else:
                amp = right
            amp_px = amp * amp_scale
            y = mid_y - amp_px
            points.append((x, y))

        # Траектория
        for i in range(len(points)-1):
            right_canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill='purple', width=2)

        # Начало и конец
        if points:
            right_canvas.create_text(points[0][0]-15, points[0][1]-5, text="Начало", fill='green', font=('Arial', 8))
            right_canvas.create_text(points[-1][0]+15, points[-1][1]-5, text="Конец", fill='orange', font=('Arial', 8))

        # Амплитуда
        if len(points) > 1:
            x_amp, y_amp = points[1]
            right_canvas.create_line(x_amp, mid_y, x_amp, y_amp, fill='purple', dash=(3,2), arrow='both')
            if y_amp < mid_y:
                right_canvas.create_text(x_amp + 15, (mid_y + y_amp)//2, text=f"вправо {right} мм", fill='purple', font=('Arial', 8))
            else:
                right_canvas.create_text(x_amp - 15, (mid_y + y_amp)//2, text=f"влево {left} мм", fill='purple', font=('Arial', 8))

        # Шаг (цикл) – покажем расстояние между двумя соседними точками (половина цикла) и полный цикл
        if len(points) >= 2:
            x1_step, y1_step = points[0]
            x2_step, y2_step = points[1]
            right_canvas.create_line(x1_step, y1+10, x2_step, y1+10, arrow='both', fill='brown')
            right_canvas.create_text((x1_step+x2_step)/2, y1+25, text=f"половина цикла\n{step_between:.1f} мм", fill='brown', font=('Arial', 8))

        # Отметим полный цикл (два шага)
        if len(points) >= 3:
            x1_cycle, _ = points[0]
            x3_cycle, _ = points[2]
            right_canvas.create_line(x1_cycle, y1+40, x3_cycle, y1+40, arrow='both', fill='brown')
            right_canvas.create_text((x1_cycle+x3_cycle)/2, y1+55, text=f"цикл = {step_cycle} мм", fill='brown', font=('Arial', 8))

        # Подписи длины дуги
        right_canvas.create_text(x0-5, y1-5, text="0", anchor='e', font=('Arial', 8))
        right_canvas.create_text(x0 + total_length*scale + 5, y1-5, text=f"{total_length:.1f}", anchor='w', font=('Arial', 8))
        # Отметки циклов
        for i in range(1, num_cycles+1):
            x_pos = x0 + i * step_cycle * scale
            right_canvas.create_line(x_pos, y0, x_pos, y1, fill='gray', dash=(1,1))
            right_canvas.create_text(x_pos, y1+5, text=f"цикл {i}", font=('Arial', 8))

        right_canvas.create_text(x0 + total_length*scale/2, 500, text="Развёртка (3 цикла, реальный масштаб 5 пикс/мм)", font=('Arial', 12, 'bold'))

        # Кнопка закрыть
        btn_close = tk.Button(scheme_win, text="Закрыть", command=scheme_win.destroy)
        btn_close.pack(side='bottom', pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = WeldApp(root)
    root.mainloop()