import hashlib
import secrets
import base64
import lzma
import struct
import os


class QShadowV7:

    # =========================
    # KEY STREAM
    # =========================

    def _keystream_byte(self, key: int, pos: int) -> int:
        h = hashlib.sha256(f"{key}:{pos}".encode()).digest()
        return h[pos % len(h)]

    # =========================
    # COMPRESSION
    # =========================

    def _compress(self, data: bytes) -> bytes:
        return lzma.compress(
            data,
            format=lzma.FORMAT_XZ,
            preset=9 | lzma.PRESET_EXTREME
        )

    def _decompress(self, data: bytes) -> bytes:
        return lzma.decompress(data)

    # =========================
    # ENCODING
    # =========================

    def _encode(self, data: bytes) -> str:
        return base64.b64encode(data).decode()

    def _decode(self, data: str) -> bytes:
        return base64.b64decode(data.encode())

    # =========================
    # TEXT
    # =========================

    def encrypt_text(self, text: str) -> str:
        key = secrets.randbits(64)
        compressed = self._compress(text.encode("utf-8"))

        enc = bytearray()
        for i, b in enumerate(compressed):
            enc.append(b ^ self._keystream_byte(key, i))

        return f"{key}:{self._encode(bytes(enc))}"

    def decrypt_text(self, container: str) -> str:
        key_str, payload = container.split(":", 1)
        key = int(key_str)

        data = self._decode(payload)

        dec = bytearray()
        for i, b in enumerate(data):
            dec.append(b ^ self._keystream_byte(key, i))

        return self._decompress(bytes(dec)).decode("utf-8")

    # =========================
    # FILES (HIDDEN METADATA)
    # =========================

    def encrypt_file(self, src: str, dst: str):
        with open(src, "rb") as f:
            raw = f.read()

        key = secrets.randbits(64)

        filename = os.path.basename(src)

        if "." in filename:
            name, ext = filename.rsplit(".", 1)
        else:
            name, ext = filename, "bin"

        name_b = name.encode()
        ext_b = ext.encode()

        header = (
            struct.pack("B", len(name_b)) +
            name_b +
            struct.pack("B", len(ext_b)) +
            ext_b
        )

        combined = header + raw
        compressed = self._compress(combined)

        enc = bytearray()
        for i, b in enumerate(compressed):
            enc.append(b ^ self._keystream_byte(key, i))

        payload = self._encode(bytes(enc))

        container = f"{key}:{payload}"

        with open(dst, "w", encoding="utf-8") as f:
            f.write(container)

    def decrypt_file(self, src: str, dst_folder: str):
        with open(src, "r", encoding="utf-8") as f:
            key_str, payload = f.read().split(":", 1)

        key = int(key_str)

        data = self._decode(payload)

        dec = bytearray()
        for i, b in enumerate(data):
            dec.append(b ^ self._keystream_byte(key, i))

        decompressed = self._decompress(bytes(dec))

        name_len = decompressed[0]
        name = decompressed[1:1 + name_len].decode()

        ext_pos = 1 + name_len
        ext_len = decompressed[ext_pos]

        ext = decompressed[ext_pos + 1:ext_pos + 1 + ext_len].decode()

        file_start = ext_pos + 1 + ext_len
        file_data = decompressed[file_start:]

        out_path = os.path.join(dst_folder, f"{name}.{ext}")

        with open(out_path, "wb") as f:
            f.write(file_data)

        print(f"[✓] Файл восстановлен: {out_path}")


    # =========================
    # TERMINAL UI
    # =========================

    def run(self):
        while True:
            print("=" * 40)
            print("1. Зашифровать текст")
            print("2. Расшифровать текст")
            print("3. Зашифровать файл")
            print("4. Расшифровать файл")
            print("0. Выход")
            print("=" * 40)

            choice = input("Выберите опцию: ").strip()

            # TEXT ENC
            if choice == "1":
                text = input("Введите текст:\n> ")
                result = self.encrypt_text(text)
                print("\n🔐 Результат:")
                print(result)

            # TEXT DEC
            elif choice == "2":
                data = input("Введите контейнер:\n> ")
                try:
                    print("\n🔓 Результат:")
                    print(self.decrypt_text(data))
                except Exception as e:
                    print("Ошибка:", e)

            # FILE ENC
            elif choice == "3":
                src = input("Путь к файлу: ")
                dst = input("Куда сохранить (.txt контейнер): ")

                try:
                    self.encrypt_file(src, dst)
                    print("[✓] Файл зашифрован")
                except Exception as e:
                    print("Ошибка:", e)

            # FILE DEC
            elif choice == "4":
                src = input("Путь к контейнеру: ")
                dst = input("Папка для восстановления: ")

                try:
                    self.decrypt_file(src, dst)
                except Exception as e:
                    print("Ошибка:", e)

            # EXIT
            elif choice == "0":
                print("Выход...")
                break

            else:
                print("Неверный выбор")


# =========================
# RUN
# =========================

if __name__ == "__main__":
    QShadowV7().run()