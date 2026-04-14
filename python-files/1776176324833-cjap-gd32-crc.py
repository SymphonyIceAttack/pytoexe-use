import sys

def crc32_gd32(data: bytes) -> int:
    poly = 0x04C11DB7
    crc = 0xFFFFFFFF
    length = len(data)
    idx = 0

    while idx < length:
        chunk = bytearray(4)
        for i in range(4):
            if idx + i < length:
                chunk[i] = data[idx + i]
        
        value = (chunk[3] << 24) | (chunk[2] << 16) | (chunk[1] << 8) | chunk[0]

        crc ^= value
        for _ in range(32):
            if crc & 0x80000000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFFFFFF

        idx += 4

    return (~crc) & 0xFFFFFFFF

def main():
    if len(sys.argv) < 2:
        print("==============================================")
        print("       GD32F450 CRC32 计算工具")
        print("   使用方法：把 bin 文件拖到本工具上")
        print("==============================================")
        input("按回车退出")
        return

    fname = sys.argv[1]
    with open(fname, "rb") as f:
        d = f.read()
    
    crc = crc32_gd32(d)
    print("======================================")
    print(f"文件: {fname}")
    print(f"长度: {len(d)} 字节")
    print(f"GD32 CRC32 = 0x{crc:08X}")
    print("======================================")
    input("完成！按回车退出")

if __name__ == "__main__":
    main()