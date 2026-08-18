import sys
import re
import struct
from pathlib import Path, PureWindowsPath
from PIL import Image

UNIT = 20
INVALID = re.compile(r'[<>:"/\\|?*]')


def sanitize(name):
    return INVALID.sub("_", name).strip()


def pause():
    try:
        input("\nPress Enter to exit...")
    except (EOFError, KeyboardInterrupt):
        pass


def parse_bfd(data):
    if len(data) < 3:
        return []

    version, count = struct.unpack_from("<BH", data, 0)
    pos = 3

    if pos < len(data) and data[pos] == 0 and pos + 1 < len(data) and data[pos + 1] == 0x75:
        pos += 1

    entries = []
    for _ in range(count):
        end = data.find(b"\x00", pos)
        if end == -1:
            break
        path = data[pos:end].decode("utf-8", "replace")
        pos = end + 1

        if pos + 28 > len(data):
            break

        w, h = struct.unpack_from("<HH", data, pos)
        ca, cb = struct.unpack_from("<ii", data, pos + 20)
        pos += 28

        rotated = cb > 0
        if rotated:
            y = -ca // UNIT
            right = cb // UNIT
            crop_w = h
            crop_h = w
            x = right - crop_w
        else:
            x = -ca // UNIT
            y = -cb // UNIT
            crop_w = w
            crop_h = h

        entries.append({
            "path": path, "w": w, "h": h,
            "x": x, "y": y, "crop_w": crop_w, "crop_h": crop_h,
            "rot": rotated,
        })

    return entries


def make_output_path(root, virtual_path):
    p = PureWindowsPath(virtual_path)
    parts = []
    for part in p.parts:
        if p.drive and part == p.drive:
            continue
        clean = sanitize(part)
        if clean in ("", ".", ".."):
            continue
        parts.append(clean)
    if not parts:
        parts = ["unnamed.png"]
    return root.joinpath(*parts)


def rotate_ccw(icon):
    try:
        return icon.transpose(Image.Transpose.ROTATE_90)
    except AttributeError:
        return icon.transpose(Image.ROTATE_90)


def extract_atlas(bfd_path, png_path, out_dir):
    try:
        data = bfd_path.read_bytes()
        atlas = Image.open(png_path).convert("RGBA")
    except Exception as e:
        print(f"  ERROR opening {bfd_path.name} / {png_path.name}: {e}")
        return 0

    atlas_w, atlas_h = atlas.size
    entries = parse_bfd(data)
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted = 0
    for e in entries:
        x, y = e["x"], e["y"]
        cw, ch = e["crop_w"], e["crop_h"]

        if x < 0 or y < 0 or x + cw > atlas_w or y + ch > atlas_h:
            print(f"  skip (out of bounds): {e['path']}")
            continue

        icon = atlas.crop((x, y, x + cw, y + ch))
        if e["rot"]:
            icon = rotate_ccw(icon)

        out_path = make_output_path(out_dir, e["path"])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        icon.save(out_path, "PNG")
        extracted += 1

    print(f"  {bfd_path.name}: {extracted}/{len(entries)} icons -> {out_dir}")
    return extracted


def main():
    if len(sys.argv) < 2:
        print("Drag & drop a folder onto this script (it should contain .bfd + .png pairs).")
        print("Or run:  extract.py <folder>")
        pause()
        return

    folder = Path(sys.argv[1].strip().strip('"'))

    if not folder.is_dir():
        print(f"Not a folder: {folder}")
        pause()
        return

    bfd_files = sorted(folder.glob("*.bfd"))
    if not bfd_files:
        print(f"No .bfd files found in: {folder}")
        pause()
        return

    output_root = folder.parent / (folder.name + "_extracted")

    print(f"Input : {folder}")
    print(f"Output: {output_root}")
    print()

    total = 0
    for bfd in bfd_files:
        png = bfd.with_suffix(".png")
        if not png.exists():
            print(f"  skip {bfd.name}: no matching {bfd.stem}.png")
            continue
        total += extract_atlas(bfd, png, output_root / sanitize(bfd.stem))

    print()
    print(f"Done. Total icons extracted: {total}")
    pause()


if __name__ == "__main__":
    main()