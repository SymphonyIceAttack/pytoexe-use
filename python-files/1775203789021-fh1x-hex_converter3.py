import struct

def parse_hex(hex_str):
    # убираем пробелы, тире, запятые, 0x
    hex_str = hex_str.replace(" ", "").replace("-", "").replace(",", "").replace("0x","")
    return bytes.fromhex(hex_str)

def reorder(data, order):
    return bytes([data[i] for i in order])

def to_float32(b):
    try:
        return struct.unpack('>f', b)[0]
    except:
        return "err"

def to_float64(b):
    try:
        return struct.unpack('>d', b)[0]
    except:
        return "err"

def to_int32(b, signed=True):
    return int.from_bytes(b, byteorder='big', signed=signed)

def to_int16_pairs(b, signed=True):
    return [
        int.from_bytes(b[0:2], byteorder='big', signed=signed),
        int.from_bytes(b[2:4], byteorder='big', signed=signed)
    ]

def process_block(data):
    variants = {
        "ABCD (Big Endian)": [0,1,2,3],
        "DCBA (Little Endian)": [3,2,1,0],
        "BADC": [1,0,3,2],
        "CDAB": [2,3,0,1],
    }
    results = []
    for name, order in variants.items():
        b = reorder(data, order)
        results.append({
            "Endian": name,
            "HEX": b.hex(" ").upper(),
            "float32": to_float32(b),
            "float64": to_float64(b + b), # float64 берём из повторения 4 байт дважды
            "int32": to_int32(b),
            "int16": to_int16_pairs(b)
        })
    return results

def print_table(results):
    # Выравнивание колонок
    header = f"{'Endian':20} {'HEX':15} {'float32':>15} {'float64':>20} {'int32':>15} {'int16(2x)':>20}"
    print(header)
    print("-"*110)
    for r in results:
        f32 = f"{r['float32']:.6g}" if isinstance(r['float32'], float) else r['float32']
        f64 = f"{r['float64']:.6g}" if isinstance(r['float64'], float) else r['float64']
        i32 = str(r['int32'])
        i16 = str(r['int16'])
        print(f"{r['Endian']:20} {r['HEX']:15} {f32:>15} {f64:>20} {i32:>15} {i16:>20}")

def main():
    print("Консольный HEX конвертер (4 байта за блок). Поддержка ABCD/DCBA/BADC/CDAB")
    print("Поддерживаются разделители: пробел, тире, запятая, 0x. Команды выхода: exit, quit, q")
    while True:
        s = input("\nВведите HEX (или exit): ")
        if s.lower() in ("exit","quit","q"):
            break
        try:
            data_bytes = parse_hex(s)
            if len(data_bytes) % 4 != 0:
                print(f"⚠️ Длина не кратна 4 байтам, остаток будет пропущен")
            for i in range(0, len(data_bytes)-3, 4):
                block = data_bytes[i:i+4]
                print(f"\nБлок {i//4+1}: {block.hex(' ').upper()}")
                results = process_block(block)
                print_table(results)
        except Exception as e:
            print("Ошибка:", e)

if __name__=="__main__":
    main()