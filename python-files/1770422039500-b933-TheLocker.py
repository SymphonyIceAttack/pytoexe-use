import os
import hashlib
import uuid
import shutil
from Crypto.Cipher import AES
from keyauth import api
import atexit
import sys, os
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

# -----------------------------
# CONFIG - KeyAuth values
# -----------------------------
KEYAUTH_NAME = "Games Locker"
KEYAUTH_OWNERID = "Zf4tbR9qfQ"
KEYAUTH_SECRET = "42fc3a7f46af178aa0465c08e33b2e2efdf1155d9361f423ba05275b77f5b3e3"
KEYAUTH_VERSION = "1.0"

ENCRYPTED_FOLDER = "encrypted_files"  # folder with all .enc files

# -----------------------------
# OUTPUT FOLDERS - developer chooses
# -----------------------------
LUA_OUTPUT_FOLDER = "C:\Program Files (x86)\Steam\config\stplug-in"          # CHANGE THIS to where you want LUA files
MANIFEST_OUTPUT_FOLDER = "C:\Program Files (x86)\Steam\config\depotcache"  # CHANGE THIS to where you want MANIFEST files

# -----------------------------
# Initialize KeyAuth
# -----------------------------
keyauthapp = api(
    name=KEYAUTH_NAME,
    ownerid=KEYAUTH_OWNERID,
    secret=KEYAUTH_SECRET,
    version=KEYAUTH_VERSION
)

# -----------------------------
# HWID function
# -----------------------------
def get_hwid():
    return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()

# -----------------------------
# AES decryption helpers
# -----------------------------
def unpad(data):
    return data[:-data[-1]]

def decrypt_file(enc_path, out_path, key):
    key_bytes = hashlib.sha256(key.encode()).digest()
    with open(enc_path, "rb") as f:
        iv = f.read(16)
        data = f.read()
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(data))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(decrypted)

# -----------------------------
# Auto-delete decrypted folders on exit (optional)
# -----------------------------
folders_to_cleanup = [LUA_OUTPUT_FOLDER, MANIFEST_OUTPUT_FOLDER]

def cleanup():
    for folder in folders_to_cleanup:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)
            print(f"🗑️ {folder} removed.")

# Uncomment next line if you want auto-delete
atexit.register(cleanup)

# -----------------------------
# MAIN PROGRAM
# -----------------------------
def main():
    license_key = input("Enter your activation key: ").strip()

    # Authenticate online
    keyauthapp.license(license_key)
    if not keyauthapp.response.success:
        print("❌ Invalid or already used key!")
        return

    print("✅ Key accepted! Decrypting files automatically...")

    # Decrypt files
    for file in os.listdir(ENCRYPTED_FOLDER):
        enc_path = os.path.join(ENCRYPTED_FOLDER, file)

        # Route files based on type
        if file.lower().endswith(".lua.enc"):
            out_path = os.path.join(LUA_OUTPUT_FOLDER, file.replace(".enc", ""))
        elif file.lower().endswith(".manifest.enc"):
            out_path = os.path.join(MANIFEST_OUTPUT_FOLDER, file.replace(".enc", ""))
        else:
            continue

        decrypt_file(enc_path, out_path, license_key)

    print("✅ Files decrypted successfully!")
    print(f"LUA files → {LUA_OUTPUT_FOLDER}")
    print(f"MANIFEST files → {MANIFEST_OUTPUT_FOLDER}")

if __name__ == "__main__":
    main()

