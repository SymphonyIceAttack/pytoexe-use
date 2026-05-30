import hashlib
import secrets
import base64
import lzma


class QShadowV6:

    # =========================
    # KEY STREAM
    # =========================

    def _keystream_byte(self, key: int, position: int) -> int:
        h = hashlib.sha256(f"{key}:{position}".encode()).digest()
        return h[position % len(h)]

    # =========================
    # MAX COMPRESSION
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
    # ENCODING (COMPACT)
    # =========================

    def _encode(self, data: bytes) -> str:
        return base64.b64encode(data).decode()

    def _decode(self, data: str) -> bytes:
        return base64.b64decode(data.encode())

    # =========================
    # TEXT (OPTIONAL)
    # =========================

    def encrypt_text(self, text: str) -> str:
        key = secrets.randbits(64)

        data = self._compress(text.encode("utf-8"))

        enc = bytearray()
        for i, b in enumerate(data):
            enc.append(b ^ self._keystream_byte(key, i))

        return f"K:{key}:txt|txt|{self._encode(bytes(enc))}"

    def decrypt_text(self, container: str) -> str:
        _, key, payload = container.split(":", 2)
        key = int(key)

        _, _, data = payload.split("|", 2)

        raw = self._decode(data)

        dec = bytearray()
        for i, b in enumerate(raw):
            dec.append(b ^ self._keystream_byte(key, i))

        return self._decompress(bytes(dec)).decode("utf-8")

    # =========================
    # FILE ENCRYPTION (MAIN FEATURE)
    # =========================

    def encrypt_file(self, src: str, dst: str):
        with open(src, "rb") as f:
            raw = f.read()

        key = secrets.randbits(64)

        filename = src.split("/")[-1]
        if "." in filename:
            name, ext = filename.rsplit(".", 1)
        else:
            name, ext = filename, "bin"

        # 1. compress MAX
        compressed = self._compress(raw)

        # 2. encrypt
        enc = bytearray()
        for i, b in enumerate(compressed):
            enc.append(b ^ self._keystream_byte(key, i))

        payload = self._encode(bytes(enc))

        container = f"K:{key}:{name}|{ext}|{payload}"

        with open(dst, "w", encoding="utf-8") as f:
            f.write(container)

    def decrypt_file(self, src: str, dst_folder: str):
        with open(src, "r", encoding="utf-8") as f:
            _, key, payload = f.read().split(":", 2)

        key = int(key)

        name, ext, data = payload.split("|", 2)

        raw = self._decode(data)

        dec = bytearray()
        for i, b in enumerate(raw):
            dec.append(b ^ self._keystream_byte(key, i))

        decompressed = self._decompress(bytes(dec))

        output_path = f"{dst_folder}/{name}.{ext}"

        with open(output_path, "wb") as f:
            f.write(decompressed)

        print(f"Файл восстановлен: {output_path}")

    # =========================
    # MENU (RU)
    # =========================

    def menu(self):
        while True:
            print("==============================")
            print("1. Зашифровать текст")
            print("2. Расшифровать текст")
            print("3. Зашифровать файл")
            print("4. Расшифровать файл")
            print("0. Выход")
            print("==============================")

            c = input("Выбор: ").strip()

            if c == "1":
                text = input("Текст: ")
                print(self.encrypt_text(text))

            elif c == "2":
                data = input("Контейнер: ")
                try:
                    print(self.decrypt_text(data))
                except Exception as e:
                    print("Ошибка:", e)

            elif c == "3":
                src = input("Файл: ")
                dst = input("Куда сохранить (.txt контейнер): ")
                self.encrypt_file(src, dst)
                print("Файл зашифрован")

            elif c == "4":
                src = input("Контейнер файл: ")
                dst = input("Папка для восстановления: ")
                self.decrypt_file(src, dst)

            elif c == "0":
                break

            else:
                print("Неверный ввод")


if __name__ == "__main__":
    QShadowV6().menu()