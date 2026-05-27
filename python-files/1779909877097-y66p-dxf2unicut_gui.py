import ezdxf
import math
import tkinter as tk
from tkinter import filedialog, messagebox

def arc_to_points(center, radius, start_angle, end_angle, ccw=True, segments=32):
    pts = []
    if not ccw:
        start_angle, end_angle = end_angle, start_angle
    for i in range(segments + 1):
        a = math.radians(start_angle + (end_angle - start_angle) * i / segments)
        x = center[0] + radius * math.cos(a)
        y = center[1] + radius * math.sin(a)
        pts.append((x, y))
    return pts

def load_dxf_ordered(filename):
    doc = ezdxf.readfile(filename)
    msp = doc.modelspace()

    ordered_paths = []

    for e in msp:
        if e.dxftype() == "LINE":
            ordered_paths.append([(e.dxf.start.x, e.dxf.start.y),
                                  (e.dxf.end.x, e.dxf.end.y)])

        elif e.dxftype() == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points()]
            if e.closed:
                pts.append(pts[0])
            ordered_paths.append(pts)

        elif e.dxftype() == "CIRCLE":
            center = (e.dxf.center.x, e.dxf.center.y)
            r = e.dxf.radius
            pts = arc_to_points(center, r, 0, 360)
            ordered_paths.append(pts)

        elif e.dxftype() == "ARC":
            center = (e.dxf.center.x, e.dxf.center.y)
            r = e.dxf.radius
            pts = arc_to_points(center, r, e.dxf.start_angle, e.dxf.end_angle,
                                ccw=(e.dxf.end_angle > e.dxf.start_angle))
            ordered_paths.append(pts)

    return ordered_paths


def generate_unicut(paths):
    g = []
    g.append("G90")
    g.append("G21")
    g.append("")

    for i, contour in enumerate(paths, 1):
        g.append(f"; ===== Контур {i} =====")
        x0, y0 = contour[0]
        g.append(f"G0 X{x0:.3f} Y{y0:.3f}")

        for x, y in contour[1:]:
            g.append(f"G1 X{x:.3f} Y{y:.3f}")

        g.append("")

    return "\n".join(g)


def select_file():
    filename = filedialog.askopenfilename(
        title="Выберите DXF",
        filetypes=[("DXF files", "*.dxf")]
    )
    if filename:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, filename)


def convert():
    filename = entry_path.get()
    if not filename:
        messagebox.showerror("Ошибка", "Выберите DXF файл")
        return

    try:
        paths = load_dxf_ordered(filename)
        gcode = generate_unicut(paths)

        outname = filename.rsplit(".", 1)[0] + "_unicut.nc"
        with open(outname, "w") as f:
            f.write(gcode)

        messagebox.showinfo("Готово", f"G‑code сохранён:\n{outname}")

    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


# === GUI ===
root = tk.Tk()
root.title("DXF → UniCut G‑code Converter")
root.geometry("500x150")

label = tk.Label(root, text="DXF файл:")
label.pack(pady=5)

entry_path = tk.Entry(root, width=60)
entry_path.pack()

btn_select = tk.Button(root, text="Выбрать файл", command=select_file)
btn_select.pack(pady=5)

btn_convert = tk.Button(root, text="Сгенерировать G‑code", command=convert)
btn_convert.pack(pady=10)

root.mainloop()
