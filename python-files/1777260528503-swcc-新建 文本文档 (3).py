import sys, os, re
from elftools.elf.elffile import ELFFile

def rc4(key: bytes, data: bytes) -> bytes:
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    i = j = 0
    out = bytearray()
    for b in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) % 256]
        out.append(b ^ k)
    return bytes(out)

def main():
    print("=== SHC 脚本解密工具 定制Win版 ===")
    if len(sys.argv) < 2:
        print("用法：把 .sh.x 文件拖拽到本程序")
        input("回车退出...")
        return
    fp = sys.argv[1]
    with open(fp, "rb") as f:
        raw = f.read()
    key_find = re.search(rb'\x00[\x20-\xff]{6,36}\x00', raw)
    if not key_find:
        print("未找到密钥！")
        input()
        return
    key = key_find.group(0).strip(b"\x00")
    dec = rc4(key, raw)
    pos = dec.find(b"#!/")
    if pos != -1:
        dec = dec[pos:]
    out_name = os.path.splitext(fp)[0] + "_解密完成.sh"
    with open(out_name, "wb") as f:
        f.write(dec)
    print(f"✅ 解密成功！\n输出文件：{out_name}")
    input("\n回车关闭...")

if __name__ == "__main__":
    main()