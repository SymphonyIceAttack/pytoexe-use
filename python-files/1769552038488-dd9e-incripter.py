import os
import subprocess
import threading
import base64
import hashlib
import tempfile
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import traceback
import time
import sys

# ================= DEPENDENCY CHECK =================
HAS_CRYPTO = True
try:
    from cryptography.fernet import Fernet
except ImportError:
    HAS_CRYPTO = False

# ================= CONFIG =================
APKTOOL_EXE = r"C:\Users\louis\Downloads\APK_Toolkit_v1.5\APK Toolkit v1.5\ApkToolkit.exe"
APKSIGNER = "apksigner"  # Ensure apksigner is in PATH
CRASH_LOG_FILE = os.path.join(os.path.expanduser("~"), "apk_encryptor_crash.log")

# ================= CRASH HANDLER =================
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        return
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    with open(CRASH_LOG_FILE, "a") as f:
        f.write(f"\n==== CRASH: {time.strftime('%Y-%m-%d %H:%M:%S')} ====\n")
        f.write(error_msg)
    try:
        messagebox.showerror("Unexpected Error", f"An error occurred!\nCheck crash log:\n{CRASH_LOG_FILE}")
    except:
        print(f"An error occurred! See {CRASH_LOG_FILE}")

sys.excepthook = handle_exception

def safe_thread(func, *args, **kwargs):
    def wrapper():
        try:
            func(*args, **kwargs)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            handle_exception(exc_type, exc_value, exc_traceback)
    threading.Thread(target=wrapper, daemon=True).start()

# ================= ENCRYPTION =================
def generate_key(password: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def encrypt_file(file_path: str, key: bytes):
    try:
        if not os.path.isfile(file_path): raise FileNotFoundError(f"File not found: {file_path}")
        if not os.access(file_path, os.R_OK): raise PermissionError(f"No read permission: {file_path}")
        if not os.access(file_path, os.W_OK):
            try: os.chmod(file_path, 0o600)
            except: pass
        fernet = Fernet(key)
        with open(file_path, 'rb') as f: data = f.read()
        with open(file_path, 'wb') as f: f.write(fernet.encrypt(data))
        log(f"Encrypted: {file_path}", "green")
    except Exception as e:
        log(f"Skipped: {file_path} | {e}", "orange")

def decrypt_file(file_path: str, key: bytes):
    try:
        if not os.path.isfile(file_path): raise FileNotFoundError(f"File not found: {file_path}")
        fernet = Fernet(key)
        with open(file_path, 'rb') as f: data = f.read()
        with open(file_path, 'wb') as f: f.write(fernet.decrypt(data))
        log(f"Decrypted: {file_path}", "blue")
    except Exception as e:
        log(f"Failed to decrypt: {file_path} | {e}", "orange")

def deep_encrypt(folder_path: str, password: str, decrypt=False):
    key = generate_key(password)
    ENCRYPT_EXTENSIONS = ('.assets', '.unity3d', '.resource', '.png', '.jpg', '.dat', '.so', '.txt', '.metadata')
    EXCLUDE_FOLDERS = ('smali', 'smali_classes2', 'smali_classes3', 'META-INF', 'res')
    EXCLUDE_FILES = ('AndroidManifest.xml', 'resources.arsc')
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_FOLDERS]
        for file in files:
            if file in EXCLUDE_FILES: continue
            if file.lower().endswith(ENCRYPT_EXTENSIONS):
                path = os.path.join(root, file)
                decrypt_file(path, key) if decrypt else encrypt_file(path, key)

def encrypt_single_file(password: str, file_path: str):
    encrypt_file(file_path, generate_key(password))

def decrypt_single_file(password: str, file_path: str):
    decrypt_file(file_path, generate_key(password))

# ================= APK PROCESS =================
def process_apk(apk_path, password, callback, decrypt=False):
    try:
        if not os.path.exists(apk_path): raise FileNotFoundError("APK file not found")
        base = os.path.splitext(os.path.basename(apk_path))[0]
        temp_dir = tempfile.mkdtemp(prefix=f"{base}_decompiled_")
        out_apk = os.path.join(os.path.expanduser("~"), f"{base}_{'decrypted' if decrypt else 'protected'}.apk")

        update_status("🛠 Decompiling APK...")
        subprocess.run([APKTOOL_EXE, "d", "-f", apk_path, "-o", temp_dir], check=True)

        update_status(f"{'Decrypting' if decrypt else 'Encrypting'} files...")
        deep_encrypt(temp_dir, password, decrypt=decrypt)

        update_status("🔧 Rebuilding APK...")
        subprocess.run([APKTOOL_EXE, "b", temp_dir, "-o", out_apk], check=True)

        signed_apk = auto_sign_apk(out_apk)

        shutil.rmtree(temp_dir, ignore_errors=True)
        callback(True, f"APK processed and signed:\n{signed_apk}")
    except subprocess.CalledProcessError as e:
        callback(False, f"APKTool error or path issue: {e}")
    except Exception as e:
        callback(False, f"Error: {e}")

# ================= AUTO SIGN =================
def auto_sign_apk(apk_path):
    signed_apk = apk_path.replace(".apk", "_signed.apk")
    debug_keystore = os.path.join(os.path.expanduser("~"), ".android", "debug.keystore")
    if not os.path.exists(debug_keystore):
        os.makedirs(os.path.dirname(debug_keystore), exist_ok=True)
        subprocess.run([
            "keytool", "-genkey", "-v",
            "-keystore", debug_keystore,
            "-storepass", "android",
            "-alias", "androiddebugkey",
            "-keypass", "android",
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
            "-dname", "CN=Android Debug,O=Android,C=US"
        ], check=True)
    subprocess.run([
        APKSIGNER, "sign",
        "--ks", debug_keystore,
        "--ks-pass", "pass:android",
        "--key-pass", "pass:android",
        "--out", signed_apk,
        apk_path
    ], check=True)
    log(f"APK signed: {signed_apk}", "green")
    return signed_apk

# ================= LOGGING =================
def log(message, color="white"):
    def append_log():
        txt_log.configure(state="normal")
        txt_log.insert(tk.END, message + "\n", ("color",))
        txt_log.tag_config("color", foreground=color)
        txt_log.see(tk.END)
        txt_log.configure(state="disabled")
    root.after(0, append_log)

def update_status(message, fg="white"):
    def update():
        status_bar.config(text=message, fg=fg)
    root.after(0, update)

# ================= GUI =================
root = tk.Tk()
root.title("APK & Unity Encryptor / Decryptor")
root.geometry("780x580")
root.configure(bg="#2b2b2b")

apk_path = tk.StringVar()
asset_path = tk.StringVar()
password = tk.StringVar()

# --- GUI FUNCTIONS ---
def browse_apk():
    p = filedialog.askopenfilename(filetypes=[("APK Files", "*.apk")])
    if p: apk_path.set(p)

def browse_asset():
    p = filedialog.askopenfilename(filetypes=[("Encryptable Files", "*.unity3d *.dat *.so *.metadata *.txt")])
    if p: asset_path.set(p)

def start_apk_encrypt():
    if not apk_path.get() or not password.get(): update_status("❌ APK and password required!", "red"); return
    btn_apk_encrypt.config(state="disabled"); btn_apk_decrypt.config(state="disabled")
    safe_thread(process_apk, apk_path.get(), password.get(), done, False)

def start_apk_decrypt():
    if not apk_path.get() or not password.get(): update_status("❌ APK and password required!", "red"); return
    btn_apk_encrypt.config(state="disabled"); btn_apk_decrypt.config(state="disabled")
    safe_thread(process_apk, apk_path.get(), password.get(), done, True)

def start_asset_encrypt():
    if not asset_path.get() or not password.get(): update_status("❌ File and password required!", "red"); return
    safe_thread(encrypt_single_file, password.get(), asset_path.get())

def start_asset_decrypt():
    if not asset_path.get() or not password.get(): update_status("❌ File and password required!", "red"); return
    safe_thread(decrypt_single_file, password.get(), asset_path.get())

def done(success, msg):
    btn_apk_encrypt.config(state="normal"); btn_apk_decrypt.config(state="normal")
    update_status(f"{'✅' if success else '❌'} {msg}", "green" if success else "red")
    messagebox.showinfo("Info", msg) if success else messagebox.showerror("Error", msg)

# --- Tabs ---
tabs = ttk.Notebook(root)
tab_apk = tk.Frame(tabs, bg="#2ecc71")
tab_file = tk.Frame(tabs, bg="#9b59b6")
tabs.add(tab_apk, text="APK Encryption")
tabs.add(tab_file, text="Single File")
tabs.pack(expand=1, fill="both")

# --- APK tab ---
tk.Label(tab_apk, text="Select APK:", bg="#2ecc71", fg="white").pack(anchor="w", padx=10, pady=4)
tk.Entry(tab_apk, textvariable=apk_path, width=80).pack(padx=10)
tk.Button(tab_apk, text="Browse APK", command=browse_apk, bg="#27ae60", fg="white").pack(pady=4)
tk.Label(tab_apk, text="Encryption Password:", bg="#2ecc71", fg="white").pack(anchor="w", padx=10, pady=4)
tk.Entry(tab_apk, textvariable=password, show="*", width=50).pack(padx=10)
btn_apk_encrypt = tk.Button(tab_apk, text="Encrypt APK", bg="#2c3e50", fg="white", width=20, height=2, command=start_apk_encrypt)
btn_apk_encrypt.pack(pady=6)
btn_apk_decrypt = tk.Button(tab_apk, text="Decrypt APK", bg="#34495e", fg="white", width=20, height=2, command=start_apk_decrypt)
btn_apk_decrypt.pack(pady=2)

# --- Single file tab ---
tk.Label(tab_file, text="Select File (.dat/.so/.unity3d/.metadata/.txt):", bg="#9b59b6", fg="white").pack(anchor="w", padx=10, pady=4)
tk.Entry(tab_file, textvariable=asset_path, width=80).pack(padx=10)
tk.Button(tab_file, text="Browse File", command=browse_asset, bg="#8e44ad", fg="white").pack(pady=4)
tk.Label(tab_file, text="Encryption Password:", bg="#9b59b6", fg="white").pack(anchor="w", padx=10, pady=4)
tk.Entry(tab_file, textvariable=password, show="*", width=50).pack(padx=10)
tk.Button(tab_file, text="Encrypt File", bg="#27ae60", fg="white", width=25, height=2, command=start_asset_encrypt).pack(pady=4)
tk.Button(tab_file, text="Decrypt File", bg="#8e44ad", fg="white", width=25, height=2, command=start_asset_decrypt).pack(pady=2)

# --- Log output ---
log_frame = tk.LabelFrame(root, text="Log Output", bg="#3b3b3b", fg="white", padx=6, pady=6)
log_frame.pack(fill="both", expand=True, padx=10, pady=6)
txt_log = scrolledtext.ScrolledText(log_frame, state="disabled", height=12, bg="#1e1e1e", fg="white")
txt_log.pack(fill="both", expand=True)

# --- Status bar ---
status_bar = tk.Label(root, text="Ready. Enter files and password.", bg="#2b2b2b", fg="white", anchor="w")
status_bar.pack(fill="x", padx=10, pady=4)

# --- Credits ---
tk.Label(root, text="Credits: LimeVR & ChatGPT", bg="#2b2b2b", fg="gray", font=("Arial", 10, "italic")).pack(side="bottom", pady=4)

# Disable buttons if missing cryptography
if not HAS_CRYPTO:
    btn_apk_encrypt.config(state="disabled")
    btn_apk_decrypt.config(state="disabled")
    update_status("Missing dependency: cryptography module.", "red")

root.mainloop()
