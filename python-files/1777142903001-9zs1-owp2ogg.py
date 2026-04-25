import os

def convert_owp_to_ogg():
    BUFSIZE = 1024  # 缓冲区大小
    xor_key = 0x39  # 异或运算的密钥

    input_directory = "."
    output_directory = "."

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for filename in os.listdir(input_directory):
        if filename.endswith(".owp"):
            filepath = os.path.join(input_directory, filename)
            outfilename = os.path.join(output_directory, os.path.splitext(filename)[0] + ".ogg")
            print(f"Opening... {outfilename}")

            try:
                with open(filepath, "rb") as fp, open(outfilename, "wb") as fpo:
                    while True:
                        buf = fp.read(BUFSIZE)
                        if not buf:
                            break
                        buf = bytearray(buf)
                        for j in range(len(buf)):
                            buf[j] ^= xor_key
                        fpo.write(buf)
            except IOError as e:
                print(f"Cannot open: {outfilename}\n{e}")
                continue

            print(f"Complete: {filename}\n")

if __name__ == "__main__":
    convert_owp_to_ogg()
