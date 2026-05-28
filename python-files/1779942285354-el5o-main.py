import tkinter as tk
from tkinter import filedialog, messagebox
import os
import math

# ================== НАСТРОЙКИ ==================

ARC_STEP = 5.0
CIRCLE_STEP = 10.0
ELLIPSE_STEP = 5.0
SPLINE_SAMPLES = 80

# ================== ГЕОМЕТРИЧЕСКИЕ УТИЛИТЫ ==================

def arc_to_points(cx, cy, r, sa, ea, step=ARC_STEP):
    pts = []
    sa = sa % 360
    ea = ea % 360
    if ea <= sa:
        ea += 360
    a = sa
    while a < ea - 1e-9:
        rad = math.radians(a)
        pts.append([cx + r * math.cos(rad), cy + r * math.sin(rad)])
        a += step
    rad = math.radians(ea)
    pts.append([cx + r * math.cos(rad), cy + r * math.sin(rad)])
    return pts

def circle_to_points(cx, cy, r, step=CIRCLE_STEP):
    pts = []
    a = 0
    while a < 360 - 1e-9:
        rad = math.radians(a)
        pts.append([cx + r * math.cos(rad), cy + r * math.sin(rad)])
        a += step
    pts.append([cx + r, cy])
    return pts

def ellipse_to_points(cx, cy, mx, my, ratio, sa, ea, step=ELLIPSE_STEP):
    mag = math.hypot(mx, my)
    if mag == 0:
        return []
    ux, uy = mx / mag, my / mag
    vx, vy = -uy, ux
    a = mag
    b = mag * ratio
    pts = []
    sa = sa % 360
    ea = ea % 360
    if ea <= sa:
        ea += 360
    ang = sa
    while ang < ea - 1e-9:
        t = math.radians(ang)
        x = cx + a * math.cos(t) * ux + b * math.sin(t) * vx
        y = cy + a * math.cos(t) * uy + b * math.sin(t) * vy
        pts.append([x, y])
        ang += step
    t = math.radians(ea)
    pts.append([
        cx + a * math.cos(t) * ux + b * math.sin(t) * vx,
        cy + a * math.cos(t) * uy + b * math.sin(t) * vy
    ])
    return pts

# ================== SPLINE ==================

def bspline_basis(i, k, t, knots):
    if k == 0:
        return 1.0 if knots[i] <= t < knots[i+1] else 0.0
    d1 = knots[i+k] - knots[i]
    d2 = knots[i+k+1] - knots[i+1]
    a = ((t - knots[i]) / d1 * bspline_basis(i, k-1, t, knots)) if d1 else 0
    b = ((knots[i+k+1] - t) / d2 * bspline_basis(i+1, k-1, t, knots)) if d2 else 0
    return a + b

def bspline_point(ctrl, deg, knots, t):
    x = y = 0
    n = len(ctrl) - 1
    for i in range(n+1):
        b = bspline_basis(i, deg, t, knots)
        x += b * ctrl[i][0]
        y += b * ctrl[i][1]
    return [x, y]

def spline_to_points(ctrl, deg=3, samples=SPLINE_SAMPLES):
    if not ctrl:
        return []
    n = len(ctrl) - 1
    k = deg
    m = n + k + 1
    knots = [0]*(k+1)
    interior = m - 2*(k+1) + 1
    if interior > 0:
        step = 1/(interior+1)
        for i in range(interior):
            knots.append((i+1)*step)
    knots += [1]*(k+1)
    pts = []
    t0 = knots[k]
    t1 = knots[-k-1]
    for i in range(samples):
        t = t0 + (t1 - t0) * (i/(samples-1))
        pts.append(bspline_point(ctrl, deg, knots, t))
    return pts

# ================== ПАРСЕР DXF ==================

def parse_dxf_with_blocks(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [ln.rstrip("\n\r") for ln in f]

    n = len(lines)
    blocks = {}
    inserts = []  # <--- ГРУППИРОВКА ПО INSERT

    # ---------- PASS 1: BLOCKS ----------
    i = 0
    while i + 3 < n:
        if (lines[i].strip() == "0" and lines[i+1].strip() == "SECTION"
            and lines[i+2].strip() == "2" and lines[i+3].strip() == "BLOCKS"):
            j = i + 4
            while j + 1 < n:
                if lines[j].strip() == "0" and lines[j+1].strip() == "ENDSEC":
                    break

                if lines[j].strip() == "0" and lines[j+1].strip() == "BLOCK":
                    k = j + 2
                    name = None
                    while k + 1 < n:
                        gc = lines[k].strip()
                        gv = lines[k+1].strip()
                        if gc == "0":
                            break
                        if gc == "2" and name is None:
                            name = gv
                        k += 2

                    ents = []
                    p = k
                    while p + 1 < n:
                        if lines[p].strip() == "0" and lines[p+1].strip() == "ENDBLK":
                            p += 2
                            break
                        if lines[p].strip() == "0":
                            etype = lines[p+1].strip()
                            if etype in ("LINE", "LWPOLYLINE", "SPLINE", "ARC", "CIRCLE", "ELLIPSE"):
                                raw = {}
                                q = p + 2
                                while q + 1 < n:
                                    gc = lines[q].strip()
                                    gv = lines[q+1].strip()
                                    if gc == "0":
                                        break
                                    if gc in raw:
                                        if isinstance(raw[gc], list):
                                            raw[gc].append(gv)
                                        else:
                                            raw[gc] = [raw[gc], gv]
                                    else:
                                        raw[gc] = gv
                                    q += 2
                                ents.append({"type": etype, "raw": raw})
                                p = q
                            else:
                                q = p + 2
                                while q + 1 < n:
                                    if lines[q].strip() == "0":
                                        break
                                    q += 2
                                p = q
                        else:
                            p += 2

                    if name and ents:
                        blocks[name] = ents

                    j = p
                    continue

                j += 2
            i = j
        else:
            i += 2

    # ---------- PASS 2: ENTITIES ----------
    def raw_to_points(etype, raw):
        if etype == "LINE":
            x1 = float(raw.get("10", 0))
            y1 = float(raw.get("20", 0))
            x2 = float(raw.get("11", x1))
            y2 = float(raw.get("21", y1))
            return [[x1, y1], [x2, y2]]

        if etype == "LWPOLYLINE":
            xs = raw.get("10")
            ys = raw.get("20")
            pts = []
            if isinstance(xs, list):
                for a, b in zip(xs, ys):
                    pts.append([float(a), float(b)])
            elif xs is not None and ys is not None:
                pts.append([float(xs), float(ys)])
            return pts

        if etype == "SPLINE":
            ctrl = []
            xs = raw.get("10")
            ys = raw.get("20")
            if isinstance(xs, list):
                for a, b in zip(xs, ys):
                    ctrl.append([float(a), float(b)])
            elif xs is not None and ys is not None:
                ctrl.append([float(xs), float(ys)])
            return spline_to_points(ctrl)

        if etype == "ARC":
            cx = float(raw.get("10", 0))
            cy = float(raw.get("20", 0))
            r = float(raw.get("40", 0))
            sa = float(raw.get("50", 0))
            ea = float(raw.get("51", 0))
            return arc_to_points(cx, cy, r, sa, ea)

        if etype == "CIRCLE":
            cx = float(raw.get("10", 0))
            cy = float(raw.get("20", 0))
            r = float(raw.get("40", 0))
            return circle_to_points(cx, cy, r)

        if etype == "ELLIPSE":
            cx = float(raw.get("10", 0))
            cy = float(raw.get("20", 0))
            mx = float(raw.get("11", 0))
            my = float(raw.get("21", 0))
            ratio = float(raw.get("40", 1))
            sa = float(raw.get("41", 0))
            ea = float(raw.get("42", 360))
            return ellipse_to_points(cx, cy, mx, my, ratio, sa, ea)

        return []

    i = 0
    while i + 3 < n:
        if (lines[i].strip() == "0" and lines[i+1].strip() == "SECTION"
            and lines[i+2].strip() == "2" and lines[i+3].strip() == "ENTITIES"):
            j = i + 4
            while j + 1 < n:
                if lines[j].strip() == "0" and lines[j+1].strip() == "ENDSEC":
                    break

                if lines[j].strip() == "0":
                    etype = lines[j+1].strip()
                    raw = {}
                    k = j + 2
                    while k + 1 < n:
                        gc = lines[k].strip()
                        gv = lines[k+1].strip()
                        if gc == "0":
                            break
                        if gc in raw:
                            if isinstance(raw[gc], list):
                                raw[gc].append(gv)
                            else:
                                raw[gc] = [raw[gc], gv]
                        else:
                            raw[gc] = gv
                        k += 2

                    if etype == "INSERT":
                        inserts.append(raw)

                    j = k
                    continue

                j += 2
            break
        i += 2

    # ---------- РАЗВОРАЧИВАЕМ INSERT → BLOCK ----------
    details = []

    for ins in inserts:
        bname = ins.get("2")
        if isinstance(bname, list):
            bname = bname[0]

        bx = float(ins.get("10", 0))
        by = float(ins.get("20", 0))
        rot = float(ins.get("50", 0))
        sx = float(ins.get("41", 1))
        sy = float(ins.get("42", 1))

        cosr = math.cos(math.radians(rot))
        sinr = math.sin(math.radians(rot))

        if bname not in blocks:
            continue

        contours = []

        for ent in blocks[bname]:
            pts_local = raw_to_points(ent["type"], ent["raw"])
            if not pts_local:
                continue

            pts_world = []
            for x, y in pts_local:
                x *= sx
                y *= sy
                xr = x * cosr - y * sinr
                yr = x * sinr + y * cosr
                xr += bx
                yr += by
                pts_world.append([xr, yr])

            contours.append(pts_world)

        details.append(contours)

    return details

# ================== РАСПОЗНАВАНИЕ КОНТУРОВ ==================

def classify_contour(pts):
    """OUTER / HOLE / CONTOUR"""
    if len(pts) < 3:
        return "CONTOUR"

    x0, y0 = pts[0]
    x1, y1 = pts[-1]

    closed = (abs(x0 - x1) < 1e-3 and abs(y0 - y1) < 1e-3)

    if not closed:
        return "CONTOUR"

    # площадь
    area = 0
    for i in range(len(pts)-1):
        x1, y1 = pts[i]
        x2, y2 = pts[i+1]
        area += x1*y2 - x2*y1
    area = abs(area) / 2

    if area < 2000:
        return "HOLE"
    return "OUTER"

# ================== G-CODE ==================

def save_nc(details, out_path):
    lines = []
    lines.append("G21")
    lines.append("G90")
    lines.append("F2000\n")

    detail_id = 1

    for contours in details:
        if not contours:
            continue

        # локальный ноль = первая точка первого контура
        x0, y0 = contours[0][0]

        lines.append("; ============================================")
        lines.append(f"; =============== DETAIL {detail_id} ====================")
        lines.append(f"; X0 = 0 , Y0 = 0")
        lines.append("; ============================================\n")

        hole_id = 1
        contour_id = 1

        for pts in contours:

            # --- отсечение аномального скачка ---
            segs = []
            for i in range(1, len(pts)):
                dx = pts[i][0] - pts[i-1][0]
                dy = pts[i][1] - pts[i-1][1]
                segs.append(math.hypot(dx, dy))

            if segs:
                avg = sum(segs) / len(segs)
                HARD = 500
                FACT = 5
                cut = len(pts)
                for i, d in enumerate(segs):
                    if d > HARD or (avg > 0 and d > FACT * avg):
                        cut = i + 1
                        break
                pts = pts[:cut]

            if len(pts) < 2:
                continue

            # --- классификация ---
            kind = classify_contour(pts)

            if kind == "HOLE":
                name = f"HOLE {hole_id}"
                hole_id += 1
            elif kind == "OUTER":
                name = "OUTER CONTOUR"
            else:
                name = f"CONTOUR {contour_id}"
                contour_id += 1

            lines.append(f"; --- {name} ---")

            # локальный ноль
            lines.append("G0 X0 Y0")
            lines.append("M03")

            for x, y in pts[1:]:
                dx = x - x0
                dy = y - y0
                lines.append(f"G1 X{dx:.3f} Y{dy:.3f}")

            lines.append("M05\n")

        detail_id += 1

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# ================== GUI ==================

def select_dxf():
    p = filedialog.askopenfilename(filetypes=[("DXF files","*.dxf")])
    if p:
        dxf_var.set(p)

def run_convert():
    path = dxf_var.get().strip()
    if not path:
        messagebox.showerror("Ошибка", "Выберите DXF")
        return

    out_nc = os.path.splitext(path)[0] + "_gcode.nc"

    try:
        details = parse_dxf_with_blocks(path)
        save_nc(details, out_nc)
        messagebox.showinfo("Готово", f"G‑code сохранён:\n{out_nc}")
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

def main():
    global dxf_var
    root = tk.Tk()
    root.title("DXF → G‑CODE (группировка, распознавание)")
    root.geometry("520x200")

    dxf_var = tk.StringVar()

    tk.Label(root, text="DXF файл:").pack()
    tk.Entry(root, textvariable=dxf_var, width=60).pack(pady=5)
    tk.Button(root, text="Обзор", command=select_dxf).pack()

    tk.Button(root, text="Конвертировать", command=run_convert, height=2).pack(pady=15)

    root.mainloop()

if __name__ == "__main__":
    main()
