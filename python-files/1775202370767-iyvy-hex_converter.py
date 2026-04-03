import struct

def parse_hex(hex_str):
    hex_str = hex_str.replace(" ", "").replace("0x", "")
    return bytes.fromhex(hex_str)

def reorder(data, order):
    return bytes([data[i] for i in order])

def to_float(b):
    try:
        return struct.unpack('>f', b)[0]
    except:
        return None

def to_int32(b):
    return int.from_bytes(b, byteorder='big', signed=True)

def to_int16_pairs(b):
    return [
        int.from_bytes(b[0:2], byteorder='big', signed=True),
        int.from_bytes(b[2:4], byteorder='big', signed=True)
    ]

def process(data):
    if len(data) != 4:
        print("❌ Нужно ровно 4 байта (8 hex символов)")
        return

    variants = {
        "ABCD (Big Endian)": [0,1,2,3],
        "DCBA (Little Endian)": [3,2,1,0],
        "BADC (Mid-Big)": [1,0,3,2],
        "CDAB (Mid-Little)": [2,3,0,1],
    }

    for name, order in variants.items():
        b = reorder(data, order)

        f = to_float(b)
        i32 = to_int32(b)
        i16 = to_int16_pairs(b)

        print(f"\n{name}")
        print(f"  HEX: {b.hex(' ').upper()}")
        print(f"  float32: {f}")
        print(f"  int32:   {i32}")
        print(f"  int16:   {i16}")

if __name__ == "__main__":
    while True:
        s = input("\nВведите HEX (например: 41 20 00 00): ")
        try:
            data = parse_hex(s)
            process(data)
        except Exception as e:
            print("Ошибка:", e)