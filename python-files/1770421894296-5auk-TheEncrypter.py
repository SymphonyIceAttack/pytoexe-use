import os
import hashlib
from Crypto.Cipher import AES

# -----------------------------
# CONFIG - developer chooses
# -----------------------------
SOURCE_FOLDER = "to_encrypt"      # folder with your original files
OUTPUT_FOLDER = "encrypted_files" # folder for encrypted files

# -----------------------------
# Helper functions
# -----------------------------
def pad(data):
    padding_len = AES.block_size - len(data) % AES.block_size
    return data + bytes([padding_len]) * padding_len

def encrypt_file(input_path, output_path, key):
    key_bytes = hashlib.sha256(key.encode()).digest()  # convert key to 32 bytes
    cipher = AES.new(key_bytes, AES.MODE_CBC)
    with open(input_path, "rb") as f:
        data = f.read()
    ciphertext = cipher.encrypt(pad(data))
    # Save IV + ciphertext
    with open(output_path, "wb") as f:
        f.write(cipher.iv + ciphertext)

# -----------------------------
# MAIN PROGRAM
# -----------------------------
def main():
    # Ask for the key at runtime
    encryption_key = input("Enter the encryption key to use: ").strip()
    if not encryption_key:
        print("❌ No key entered. Exiting.")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Encrypt all .lua and .manifest files
    for file in os.listdir(SOURCE_FOLDER):
        full_path = os.path.join(SOURCE_FOLDER, file)
        if os.path.isfile(full_path):
            if file.lower().endswith(".lua") or file.lower().endswith(".manifest"):
                out_file = file + ".enc"
                out_path = os.path.join(OUTPUT_FOLDER, out_file)
                encrypt_file(full_path, out_path, encryption_key)
                print(f"Encrypted {file} → {out_file}")
            else:
                continue

    print(f"\n✅ All files encrypted! Output folder: {OUTPUT_FOLDER}")

if __name__ == "__main__":
    main()
