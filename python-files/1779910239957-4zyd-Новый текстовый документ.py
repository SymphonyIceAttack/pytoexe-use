import sys

def parse_dxf_lines(filename):
    lines = []
    with open(filename, "r") as f:
        data = f.readlines()

    i = 0
    while i < len(data):
        code = data[i].strip()
        if code == "0" and data[i+1].strip() == "LINE":
            x1 = y1 = x2 = y2 = None
            i += 2
            while i < len(data):
                c = data[i].strip()
                v = data[i+1].strip()
                if c == "10": x1 = float(v)
                elif c == "20": y1 = float(v)
                elif c == "11": x2 = float(v)
                elif c == "21": y2 = float(v)
                elif c == "0": break
                i += 2
            if None not in (x1, y1, x2, y2):
                lines.append([(x1, y1), (x2, y2)])
        else:
            i += 1
    return lines


def generate_gcode(paths):
    g = []
    g.append("G90")
    g.append("G21")
    g.append("")

    for i, seg in enumerate(paths, 1):
        g.append(f"; ===== LINE {i} =====")
        (x1, y1), (x2, y2) = seg
        g.append(f"G0 X{x1:.3f} Y{y1:.3f}")
        g.append(f"G1 X{x2:.3f} Y{y2:.3f}")
        g.append("")

    return "\n".join(g)


def main():
    if len(sys.argv) < 2:
        print("Использование: dxf2gcode.exe input.dxf")
        return

    filename = sys.argv[1]
    paths = parse_dxf_lines(filename)
    gcode = generate_gcode(paths)

    outname = filename.rsplit(".", 1)[0] + "_unicut.nc"
    with open(outname, "w") as f:
        f.write(gcode)

    print("Готово! Файл сохранён:", outname)


if __name__ == "__main__":
    main()
