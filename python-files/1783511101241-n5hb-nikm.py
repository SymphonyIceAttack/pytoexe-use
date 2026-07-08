from PIL import Image
import zlib
import sys
import os

# -----------------------------
# .nikm FORMAT (v1.0)
# -----------------------------
# MAGIC:       "NIKM" (4 bytes)
# VERSION:     0x01   (1 byte)
# WIDTH:       2 bytes (big-endian)
# HEIGHT:      2 bytes (big-endian)
# CHANNELS:    0x03 (RGB)
# COMPRESSION: 0x01 (zlib)
# DATA_SIZE:   4 bytes (big-endian)
# DATA:        compressed pixel bytes
# -----------------------------


def convert_to_nikm(input_path):
    """Convert PNG/JPG/JPEG/JFIF → .nikm"""
    img = Image.open(input_path).convert("RGB")
    width, height = img.size
    pixel_bytes = img.tobytes()

    # Medium compression
    compressed = zlib.compress(pixel_bytes, level=6)

    # Output filename
    base, _ = os.path.splitext(input_path)
    output_path = base + ".nikm"

    with open(output_path, "wb") as f:
        f.write(b"NIKM")                     # magic
        f.write(b"\x01")                     # version
        f.write(width.to_bytes(2, "big"))
        f.write(height.to_bytes(2, "big"))
        f.write(b"\x03")                     # RGB
        f.write(b"\x01")                     # compression = zlib
        f.write(len(compressed).to_bytes(4, "big"))
        f.write(compressed)

    print(f"Converted → {output_path}")


def view_nikm(path):
    """View a .nikm image"""
    with open(path, "rb") as f:
        magic = f.read(4)
        if magic != b"NIKM":
            raise ValueError("Not a .nikm file")

        version = f.read(1)
        width = int.from_bytes(f.read(2), "big")
        height = int.from_bytes(f.read(2), "big")
        channels = f.read(1)
        compression = f.read(1)
        size = int.from_bytes(f.read(4), "big")
        data = f.read(size)

    # Decompress pixel data
    pixels = zlib.decompress(data)

    # Rebuild image
    img = Image.frombytes("RGB", (width, height), pixels)
    img.show()


# -----------------------------
# COMMAND HANDLING
# -----------------------------
# Usage:
#   python nikm.py convert image.png
#   python nikm.py view image.nikm
# -----------------------------

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python nikm.py convert <imagefile>")
        print("  python nikm.py view <nikmfile>")
        sys.exit(1)

    command = sys.argv[1]
    file_path = sys.argv[2]

    if command == "convert":
        convert_to_nikm(file_path)
    elif command == "view":
        view_nikm(file_path)
    else:
        print("Unknown command. Use 'convert' or 'view'.")
