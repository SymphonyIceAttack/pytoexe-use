import math
import tkinter as tk
from tkinter import filedialog, messagebox

# ============================================================
# ======================= DXF PARSER ==========================
# ============================================================

def parse_dxf(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [l.rstrip('\n') for l in f]

    entities = []
    in_entities = False
    current = None
    i = 0

    while i < len(lines):
        code = lines[i].strip()
        value = lines[i+1].strip() if i+1 < len(lines) else ''
        i += 2

        if code == '0' and value == 'SECTION':
            if lines[i].strip() == '2' and lines[i+1].strip() == 'ENTITIES':
                in_entities = True
            continue

        if code == '0' and value == 'ENDSEC':
            in_entities = False
            continue

        if not in_entities:
            continue

        if code == '0':
            if current:
                entities.append(current)
            current = {'type': value, 'data': {}}
        else:
            current['data'].setdefault(code, []).append(value)

    if current:
        entities.append(current)

    return entities


def get(d, code, default=0.0):
    return float(d.get(code, [default])[0])


# ============================================================
# ======================= GEOMETRY ============================
# ============================================================

def rotate_point(x, y, angle_deg):
    ang = math.radians(angle_deg)
    ca = math.cos(ang)
    sa = math.sin(ang)
    xr = x * ca - y * sa
    yr = x * sa + y * ca
    return xr, yr


def rotate_entities(entities, angle_deg):
    new_ents = []
    for e in entities:
        d = e['data']
        t = e['type']
        new_e = {'type': t, 'data': {}}

        if t == 'CIRCLE':
            cx = get(d, '10')
            cy = get(d, '20')
            cx2, cy2 = rotate_point(cx, cy, angle_deg)
            new_e['data']['10'] = [str(cx2)]
            new_e['data']['20'] = [str(cy2)]
            new_e['data']['40'] = d['40']

        elif t == 'LWPOLYLINE':
            xs = d.get('10', [])
            ys = d.get('20', [])
            new_xs = []
            new_ys = []
            for x, y in zip(xs, ys):
                xr, yr = rotate_point(float(x), float(y), angle_deg)
                new_xs.append(str(xr))
                new_ys.append(str(yr))
            new_e['data']['10'] = new_xs
            new_e['data']['20'] = new_ys
            new_e['data']['70'] = d.get('70', ['0'])

        new_ents.append(new_e)

    return new_ents


def circle_to_polygon(cx, cy, r, r_factor=1.0, n=8):
    pts = []
    R = r * r_factor
    for i in range(n):
        ang = 2 * math.pi * i / n
        x = cx + R * math.cos(ang)
        y = cy + R * math.sin(ang)
        pts.append((x, y))
    pts.append(pts[0])
    return pts


def get_detail_bbox(entities):
    xs = []
    ys = []
    for e in entities:
        d = e['data']
        if e['type'] == 'CIRCLE':
            cx = get(d, '10')
            cy = get(d, '20')
            r  = get(d, '40')
            xs += [cx-r, cx+r]
            ys += [cy-r, cy+r]
        elif e['type'] == 'LWPOLYLINE':
            for x in d.get('10', []):
                xs.append(float(x))
            for y in d.get('20', []):
                ys.append(float(y))
    return min(xs), min(ys), max(xs), max(ys)


# ============================================================
# ======================= G-CODE GEN ==========================
# ============================================================

def generate_detail(entities, dx, dy, idx, r_factor=1.0):
    g = []
    g.append(f"; ===== DETAIL {idx} at X{dx}, Y{dy} =====")

    hole_id = 1
    poly_id = 1

    for e in entities:
        t = e['type']
        d = e['data']

        if t == 'CIRCLE':
            cx = get(d, '10') + dx
            cy = get(d, '20') + dy
            r  = get(d, '40')

            pts = circle_to_polygon(cx, cy, r, r_factor=r_factor, n=8)

            g.append(f"; --- HOLE {hole_id} ---")
            hole_id += 1

            x0, y0 = pts[0]
            g.append(f"G0 X{x0:.3f} Y{y0:.3f}")
            g.append("M03")
            for (x, y) in pts[1:]:
                g.append(f"G1 X{x:.3f} Y{y:.3f}")
            g.append("M05")
            g.append("")

        elif t == 'LWPOLYLINE':
            xs = d.get('10', [])
            ys = d.get('20', [])
            closed = d.get('70', ['0'])[0] == '1'

            g.append(f"; --- OUTER CONTOUR {poly_id} ---")
            poly_id += 1

            x0 = float(xs[0]) + dx
            y0 = float(ys[0]) + dy

            g.append(f"G0 X{x0:.3f} Y{y0:.3f}")
            g.append("M03")

            for i in range(1, len(xs)):
                x = float(xs[i]) + dx
                y = float(ys[i]) + dy
                g.append(f"G1 X{x:.3f} Y{y:.3f}")

            if closed:
                g.append(f"G1 X{x0:.3f} Y{y0:.3f}")

            g.append("M05")
            g.append("")

    return g


# ============================================================
# ======================= NESTING =============================
# ============================================================

def generate_gcode(dxf_path, out_path, sheetW, sheetH, count, gapX, gapY, r_factor):

    ents = parse_dxf(dxf_path)

    # ---------- выбираем лучший угол ----------
    angles = [0, 90, 180, 270]
    best_angle = 0
    best_fit = 0

    for ang in angles:
        ents_rot = rotate_entities(ents, ang)
        x0, y0, x1, y1 = get_detail_bbox(ents_rot)
        w = x1 - x0
        h = y1 - y0

        countX = int((sheetW + gapX) // (w + gapX))
        countY = int((sheetH + gapY) // (h + gapY))
        fit = countX * countY

        if fit >= count:
            best_angle = ang
            break

        if fit > best_fit:
            best_fit = fit
            best_angle = ang

    ents = rotate_entities(ents, best_angle)

    # ---------- bounding box ----------
    x0, y0, x1, y1 = get_detail_bbox(ents)
    detailW = x1 - x0
    detailH = y1 - y0

    # ---------- раскладка ----------
    countX = int((sheetW + gapX) // (detailW + gapX))
    countY = int((sheetH + gapY) // (detailH + gapY))

    positions = []
    for iy in range(countY):
        for ix in range(countX):
            positions.append((
                ix * (detailW + gapX),
                iy * (detailH + gapY)
            ))

    positions = positions[:count]

    # ---------- G-code ----------
    g = []
    g.append("G21")
    g.append("G90")
    g.append("F2000")
    g.append(f"; ROTATION = {best_angle} degrees")
    g.append("")

    for idx, (dx, dy) in enumerate(positions, start=1):
        g.extend(generate_detail(ents, dx, dy, idx, r_factor=r_factor))

    g.append("M30")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(g))


# ============================================================
# ======================= GUI ================================
# ============================================================

def run_gui():
    root = tk.Tk()
    root.title("Nesting Postprocessor GUI")
    root.geometry("420x420")

    # DXF file
    tk.Label(root, text="DXF файл:").pack()
    dxf_entry = tk.Entry(root, width=40)
    dxf_entry.pack()

    def choose_dxf():
        path = filedialog.askopenfilename(filetypes=[("DXF files", "*.dxf")])
        if path and path.lower().endswith(".dxf"):
            dxf_entry.delete(0, tk.END)
            dxf_entry.insert(0, path)
        else:
            messagebox.showwarning("Внимание", "DXF файл не выбран.")

    tk.Button(root, text="Выбрать DXF", command=choose_dxf).pack()

    # Sheet size
    tk.Label(root, text="Ширина листа (мм):").pack()
    sheetW_entry = tk.Entry(root)
    sheetW_entry.insert(0, "1200")
    sheetW_entry.pack()

    tk.Label(root, text="Высота листа (мм):").pack()
    sheetH_entry = tk.Entry(root)
    sheetH_entry.insert(0, "600")
    sheetH_entry.pack()

    # Count
    tk.Label(root, text="Количество деталей:").pack()
    count_entry = tk.Entry(root)
    count_entry.insert(0, "4")
    count_entry.pack()

    # Gaps
    tk.Label(root, text="Зазор X (мм):").pack()
    gapX_entry = tk.Entry(root)
    gapX_entry.insert(0, "10")
    gapX_entry.pack()

    tk.Label(root, text="Зазор Y (мм):").pack()
    gapY_entry = tk.Entry(root)
    gapY_entry.insert(0, "10")
    gapY_entry.pack()

    # r_factor
    tk.Label(root, text="Коэффициент радиуса отверстий:").pack()
    r_entry = tk.Entry(root)
    r_entry.insert(0, "0.875")
    r_entry.pack()

    # Output
    tk.Label(root, text="Имя выходного файла:").pack()
    out_entry = tk.Entry(root)
    out_entry.insert(0, "output.nc")
    out_entry.pack()

    def run_post():
        try:
            dxf = dxf_entry.get()
            if not dxf or not dxf.lower().endswith(".dxf"):
                messagebox.showerror("Ошибка", "Выберите DXF файл.")
                return

            sheetW = float(sheetW_entry.get())
            sheetH = float(sheetH_entry.get())
            count = int(count_entry.get())
            gapX = float(gapX_entry.get())
            gapY = float(gapY_entry.get())
            r_factor = float(r_entry.get())
            out_file = out_entry.get()

            generate_gcode(dxf, out_file, sheetW, sheetH, count, gapX, gapY, r_factor)

            messagebox.showinfo("Готово", f"G‑код сохранён в {out_file}")

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    tk.Button(root, text="Сгенерировать G‑код", command=run_post, bg="lightgreen").pack(pady=10)

    root.mainloop()


# Запуск GUI
if __name__ == "__main__":
    run_gui()
