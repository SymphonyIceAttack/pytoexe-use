#!/usr/bin/env python3
import sys
import os
import argparse
import secrets
import string
import csv
import base64
import hashlib
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Optional import for AES encryption
try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Random import get_random_bytes
    AES_AVAILABLE = True
except ImportError:
    AES_AVAILABLE = False

# ---------------------------- Character Sets ----------------------------
ARABIC_LETTERS = 'ءابتثجحخدذرزسشصضطظعغفقكلمنهوي'
CHINESE_CHARACTERS = '的一是了我不人在他有这中大国年着那和要她出也得里后自以会家可下而过天去能对小多然于心学么之都好看起发当没成只如事把还用第样道想作种开美总从无情己面最女但现前些所同日手又行意动方期它头经长儿回位分爱老因很给名法间斯知世什两次使身者被高已亲其进此话常与活正感'
JAPANESE_HIRAGANA = 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'
JAPANESE_KATAKANA = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン'
KOREAN_HANGUL = '가나다라마바사아자차카타파하'
RUSSIAN_CYRILLIC = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'

COMMON_WORDS = [
    "apple", "banana", "cherry", "dragon", "eagle", "forest", "guitar", "harbor", "island", "jungle",
    "knight", "lemon", "mango", "nectar", "orange", "panda", "queen", "rocket", "silver", "turtle",
    "umbrella", "violet", "walrus", "xenon", "yacht", "zebra", "anchor", "breeze", "castle", "desert",
    "emerald", "falcon", "galaxy", "hammer", "icicle", "jigsaw", "kayak", "lantern", "magnet", "nebula",
    "octopus", "palace", "quartz", "rainbow", "sunset", "tornado", "unicorn", "valley", "window", "oxygen"
]

AMBIGUOUS_CHARS = 'il1Lo0O'

# ---------------------------- AES Helpers ----------------------------
def derive_aes_key(master_pwd, salt):
    return PBKDF2(master_pwd, salt, dkLen=32, count=100000)

def aes_encrypt(plaintext, master_pwd):
    salt = get_random_bytes(16)
    key = derive_aes_key(master_pwd, salt)
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pad_len = 16 - len(plaintext) % 16
    padded = plaintext + chr(pad_len) * pad_len
    ciphertext = cipher.encrypt(padded.encode())
    return base64.b64encode(salt + iv + ciphertext).decode()

def aes_decrypt(encrypted, master_pwd):
    data = base64.b64decode(encrypted)
    salt, iv, ciphertext = data[:16], data[16:32], data[32:]
    key = derive_aes_key(master_pwd, salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = cipher.decrypt(ciphertext).decode()
    pad_len = ord(padded[-1])
    return padded[:-pad_len]

# ---------------------------- CLI Mode ----------------------------
def cli_mode():
    parser = argparse.ArgumentParser(description='E4P Password Generator - CLI mode')
    parser.add_argument('--length', type=int, default=12, help='Password length (4-64)')
    parser.add_argument('--no-lower', action='store_true', help='Exclude lowercase')
    parser.add_argument('--no-upper', action='store_true', help='Exclude uppercase')
    parser.add_argument('--no-digits', action='store_true', help='Exclude digits')
    parser.add_argument('--no-symbols', action='store_true', help='Exclude symbols')
    parser.add_argument('--arabic', action='store_true', help='Include Arabic letters')
    parser.add_argument('--chinese', action='store_true', help='Include Chinese characters')
    parser.add_argument('--japanese', action='store_true', help='Include Japanese characters')
    parser.add_argument('--korean', action='store_true', help='Include Korean characters')
    parser.add_argument('--russian', action='store_true', help='Include Russian characters')
    parser.add_argument('--passphrase', action='store_true', help='Generate passphrase instead')
    parser.add_argument('--words', type=int, default=4, help='Number of words in passphrase')
    parser.add_argument('--separator', default='-', help='Separator for passphrase')
    parser.add_argument('--no-ambiguous', action='store_true', help='Avoid ambiguous characters')
    parser.add_argument('--no-repeat', action='store_true', help='Avoid repeating characters >2 in a row')
    args = parser.parse_args()

    if args.passphrase:
        words = [secrets.choice(COMMON_WORDS) for _ in range(args.words)]
        password = args.separator.join(words)
        print(password)
        return

    pool = ''
    mandatory = []
    # Helper to add characters with weight 3 for digits and symbols
    def add_chars(chars, weight=1):
        nonlocal pool, mandatory
        filtered = chars
        if args.no_ambiguous:
            filtered = ''.join(c for c in filtered if c not in AMBIGUOUS_CHARS)
        if filtered:
            pool += filtered * weight
            mandatory.append(secrets.choice(filtered))

    if not args.no_lower:
        add_chars(string.ascii_lowercase, weight=1)
    if not args.no_upper:
        add_chars(string.ascii_uppercase, weight=1)
    if not args.no_digits:
        add_chars(string.digits, weight=3)          # أرقام وزن 3
    if not args.no_symbols:
        add_chars("!@#$%^&*()_+-=[]{}|;:,.<>?/~", weight=3)  # رموز وزن 3
    if args.arabic:
        add_chars(ARABIC_LETTERS, weight=1)
    if args.chinese:
        add_chars(CHINESE_CHARACTERS, weight=1)
    if args.japanese:
        add_chars(JAPANESE_HIRAGANA + JAPANESE_KATAKANA, weight=1)
    if args.korean:
        add_chars(KOREAN_HANGUL, weight=1)
    if args.russian:
        add_chars(RUSSIAN_CYRILLIC, weight=1)

    if not pool:
        print("Error: At least one character set must be enabled.")
        sys.exit(1)

    remaining = args.length - len(mandatory)
    if remaining < 0:
        print(f"Error: Length too short (min {len(mandatory)}).")
        sys.exit(1)

    password_chars = mandatory + [secrets.choice(pool) for _ in range(remaining)]
    secrets.SystemRandom().shuffle(password_chars)
    password = ''.join(password_chars)

    if args.no_repeat:
        filtered = []
        i = 0
        while i < len(password):
            c = password[i]
            count = 1
            while i+count < len(password) and password[i+count] == c:
                count += 1
            filtered.extend([c] * min(count, 2))
            i += count
        password = ''.join(filtered)

    print(password)

# ---------------------------- GUI Application ----------------------------
class E4PApp:
    def __init__(self, root):
        self.root = root
        self.root.title("E4P")
        self.root.geometry("520x680")
        self.root.resizable(False, False)
        self.root.configure(bg='#2b2b2b')

        # Colors (dark theme fixed)
        self.colors = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'entry_bg': '#3c3c3c',
            'entry_fg': '#ffffff',
            'btn_bg': '#4CAF50',
            'btn_fg': 'white',
            'listbox_bg': '#3c3c3c',
            'listbox_fg': '#ffffff',
            'scale_trough': '#555555'
        }

        self.master_key = None
        self.password_history = []
        self.clipboard_timer = None

        self.create_widgets()
        self.load_or_set_master()

        # Keyboard shortcuts
        self.root.bind('<Control-g>', lambda e: self.generate_password())
        self.root.bind('<Control-c>', lambda e: self.copy_to_clipboard() if self.root.focus_get() != self.result_entry else None)

    def load_or_set_master(self):
        if not AES_AVAILABLE:
            messagebox.showinfo("Encryption", "Install pycryptodome for encrypted storage.\nSaving as plaintext.")
            return
        ans = messagebox.askyesno("Master Password", "Set a master password for encrypted storage?")
        if ans:
            pwd = simpledialog.askstring("Master Password", "Enter master password:", show='*')
            if pwd:
                self.master_key = pwd
                messagebox.showinfo("Master Password", "Master password set.")

    def create_widgets(self):
        main = tk.Frame(self.root, bg=self.colors['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        tk.Label(main, text="E4P - Ultimate Password Generator", font=("Arial", 14, "bold"),
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=5)

        # Presets
        pf = tk.Frame(main, bg=self.colors['bg'])
        pf.pack(pady=5, fill=tk.X)
        tk.Label(pf, text="Presets:", font=("Arial", 10), bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.preset_var = tk.StringVar(value="Custom")
        self.preset_combo = ttk.Combobox(pf, textvariable=self.preset_var,
                                         values=["Custom", "High Security (20)", "Simple (8)",
                                                 "Passphrase (4 words)", "Arabic Mix", "Chinese Mix",
                                                 "Japanese Mix", "Korean Mix", "Russian Mix"],
                                         state="readonly", width=22)
        self.preset_combo.pack(side=tk.LEFT, padx=5)
        self.preset_combo.bind('<<ComboboxSelected>>', self.apply_preset)

        # Mode
        mf = tk.Frame(main, bg=self.colors['bg'])
        mf.pack(pady=5, fill=tk.X)
        tk.Label(mf, text="Mode:", font=("Arial", 10), bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="Random")
        self.mode_combo = ttk.Combobox(mf, textvariable=self.mode_var,
                                       values=["Random", "Passphrase", "Pattern"], state="readonly", width=15)
        self.mode_combo.pack(side=tk.LEFT, padx=5)
        self.mode_combo.bind('<<ComboboxSelected>>', self.update_mode_ui)

        # Pattern (hidden)
        self.pattern_frame = tk.Frame(main, bg=self.colors['bg'])
        tk.Label(self.pattern_frame, text="Pattern (w=word,d=digit,s=symbol,c=char):",
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.pattern_var = tk.StringVar(value="wwds")
        self.pattern_entry = tk.Entry(self.pattern_frame, textvariable=self.pattern_var, width=15,
                                      bg=self.colors['entry_bg'], fg=self.colors['entry_fg'])
        self.pattern_entry.pack(side=tk.LEFT)

        # Passphrase separator/words
        self.sep_frame = tk.Frame(main, bg=self.colors['bg'])
        tk.Label(self.sep_frame, text="Separator:", bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.sep_var = tk.StringVar(value="-")
        self.sep_entry = tk.Entry(self.sep_frame, textvariable=self.sep_var, width=5,
                                  bg=self.colors['entry_bg'], fg=self.colors['entry_fg'])
        self.sep_entry.pack(side=tk.LEFT)
        tk.Label(self.sep_frame, text="Words:", bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.word_count_var = tk.IntVar(value=4)
        self.word_spin = tk.Spinbox(self.sep_frame, from_=2, to=10, textvariable=self.word_count_var,
                                    width=3, bg=self.colors['entry_bg'], fg=self.colors['entry_fg'],
                                    buttonbackground=self.colors['entry_bg'])
        self.word_spin.pack(side=tk.LEFT)

        # Length
        lf = tk.Frame(main, bg=self.colors['bg'])
        lf.pack(pady=5, fill=tk.X)
        tk.Label(lf, text="Length:", font=("Arial", 10), bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.length_var = tk.IntVar(value=12)
        self.length_scale = tk.Scale(lf, from_=4, to=64, orient=tk.HORIZONTAL, variable=self.length_var,
                                     length=150, bg=self.colors['bg'], fg=self.colors['fg'],
                                     troughcolor=self.colors['scale_trough'], highlightthickness=0)
        self.length_scale.pack(side=tk.LEFT)
        tk.Label(lf, textvariable=self.length_var, width=2, font=("Arial", 10),
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)

        # Character types
        opt_frame = tk.LabelFrame(main, text="Character Types", font=("Arial", 10, "bold"),
                                  bg=self.colors['bg'], fg=self.colors['fg'], padx=10, pady=5)
        opt_frame.pack(pady=5, fill=tk.X, padx=5)

        cb = {'bg': self.colors['bg'], 'fg': self.colors['fg'], 'selectcolor': self.colors['bg'],
              'activebackground': self.colors['bg'], 'activeforeground': self.colors['fg'], 'font': ("Arial", 9)}

        cbf = tk.Frame(opt_frame, bg=self.colors['bg'])
        cbf.pack()
        left = tk.Frame(cbf, bg=self.colors['bg']); left.pack(side=tk.LEFT, padx=10)
        right = tk.Frame(cbf, bg=self.colors['bg']); right.pack(side=tk.LEFT, padx=10)

        self.use_lower = tk.BooleanVar(value=True)
        self.use_upper = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)
        self.use_arabic = tk.BooleanVar(value=False)
        self.use_chinese = tk.BooleanVar(value=False)
        self.use_japanese = tk.BooleanVar(value=False)
        self.use_korean = tk.BooleanVar(value=False)
        self.use_russian = tk.BooleanVar(value=False)
        self.avoid_ambiguous = tk.BooleanVar(value=False)
        self.no_repeat = tk.BooleanVar(value=False)
        self.no_history = tk.BooleanVar(value=False)

        tk.Checkbutton(left, text="Lowercase (a-z)", variable=self.use_lower, **cb).pack(anchor="w")
        tk.Checkbutton(left, text="Uppercase (A-Z)", variable=self.use_upper, **cb).pack(anchor="w")
        tk.Checkbutton(left, text="Digits (0-9)", variable=self.use_digits, **cb).pack(anchor="w")
        tk.Checkbutton(left, text="Symbols (!@#$...)", variable=self.use_symbols, **cb).pack(anchor="w")
        tk.Checkbutton(right, text="Arabic (ابت...)", variable=self.use_arabic, **cb).pack(anchor="w")
        tk.Checkbutton(right, text="Chinese (的一...)", variable=self.use_chinese, **cb).pack(anchor="w")
        tk.Checkbutton(right, text="Japanese (あア...)", variable=self.use_japanese, **cb).pack(anchor="w")
        tk.Checkbutton(right, text="Korean (가나...)", variable=self.use_korean, **cb).pack(anchor="w")
        tk.Checkbutton(right, text="Russian (абв...)", variable=self.use_russian, **cb).pack(anchor="w")
        tk.Checkbutton(right, text="Avoid Ambiguous", variable=self.avoid_ambiguous, **cb).pack(anchor="w")
        tk.Checkbutton(right, text="No repeat >2 row", variable=self.no_repeat, **cb).pack(anchor="w")
        tk.Checkbutton(right, text="Don't save in history", variable=self.no_history, **cb).pack(anchor="w")

        # Show/Auto-copy row
        ef = tk.Frame(main, bg=self.colors['bg'])
        ef.pack(pady=5, fill=tk.X)
        self.show_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ef, text="Show Password", variable=self.show_var, command=self.toggle_show, **cb).pack(side=tk.LEFT, padx=5)
        self.auto_copy_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ef, text="Auto-copy", variable=self.auto_copy_var, **cb).pack(side=tk.LEFT, padx=5)

        # Buttons
        bf = tk.Frame(main, bg=self.colors['bg'])
        bf.pack(pady=5)
        tk.Button(bf, text="Generate 🔐", command=self.generate_password,
                  font=("Arial", 11, "bold"), bg=self.colors['btn_bg'], fg=self.colors['btn_fg']).pack(side=tk.LEFT, padx=3)
        tk.Button(bf, text="Regenerate 🔄", command=self.generate_password,
                  font=("Arial", 11, "bold"), bg='#2196F3', fg='white').pack(side=tk.LEFT, padx=3)
        tk.Button(bf, text="Export 📤", command=self.export_passwords,
                  font=("Arial", 10), bg='#FF9800', fg='black').pack(side=tk.LEFT, padx=3)

        # Result + Copy
        rf = tk.Frame(main, bg=self.colors['bg'])
        rf.pack(pady=5)
        self.result_var = tk.StringVar()
        self.result_entry = tk.Entry(rf, textvariable=self.result_var, font=("Courier", 13),
                                     justify="center", state="normal", width=30,
                                     bg=self.colors['entry_bg'], fg=self.colors['entry_fg'],
                                     insertbackground=self.colors['fg'], show='*')
        self.result_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(rf, text="Copy 📋", command=self.copy_to_clipboard,
                  font=("Arial", 10), bg='#555555', fg='white').pack(side=tk.LEFT)

        # Strength bar
        sf = tk.Frame(main, bg=self.colors['bg'])
        sf.pack(pady=5, fill=tk.X)
        tk.Label(sf, text="Strength:", font=("Arial", 10), bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.strength_canvas = tk.Canvas(sf, width=200, height=20, bg=self.colors['bg'], highlightthickness=0)
        self.strength_canvas.pack(side=tk.LEFT, padx=5)
        self.strength_rect = self.strength_canvas.create_rectangle(0, 0, 0, 20, fill='grey', outline='')

        # History
        hf = tk.LabelFrame(main, text="History (last 5)", font=("Arial", 9),
                           bg=self.colors['bg'], fg=self.colors['fg'], padx=5, pady=5)
        hf.pack(pady=5, fill=tk.BOTH, expand=True, padx=5)
        self.history_listbox = tk.Listbox(hf, height=5, bg=self.colors['listbox_bg'], fg=self.colors['listbox_fg'],
                                          selectbackground='#4CAF50')
        self.history_listbox.pack(fill=tk.BOTH, expand=True)
        tk.Button(hf, text="Copy Selected", command=self.copy_history_selection,
                  font=("Arial", 9), bg='#555555', fg='white').pack(pady=2)

        # Save
        svf = tk.LabelFrame(main, text="Save to Encrypted File", font=("Arial", 9),
                            bg=self.colors['bg'], fg=self.colors['fg'], padx=5, pady=5)
        svf.pack(pady=5, fill=tk.X, padx=5)
        tk.Label(svf, text="Site/Username:", bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.site_var = tk.StringVar()
        self.site_entry = tk.Entry(svf, textvariable=self.site_var, width=20,
                                   bg=self.colors['entry_bg'], fg=self.colors['entry_fg'])
        self.site_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(svf, text="💾 Save", command=self.save_password,
                  font=("Arial", 9), bg='#FF9800', fg='black').pack(side=tk.LEFT, padx=5)

    def toggle_show(self):
        self.result_entry.configure(show='' if self.show_var.get() else '*')

    def update_mode_ui(self, event=None):
        mode = self.mode_var.get()
        if mode == "Random":
            self.length_scale.configure(state=tk.NORMAL)
            self.pattern_frame.pack_forget()
            self.sep_frame.pack_forget()
        elif mode == "Passphrase":
            self.length_scale.configure(state=tk.DISABLED)
            self.pattern_frame.pack_forget()
            self.sep_frame.pack(pady=5, before=self.strength_canvas.master)
        elif mode == "Pattern":
            self.length_scale.configure(state=tk.DISABLED)
            self.pattern_frame.pack(pady=5, before=self.strength_canvas.master)
            self.sep_frame.pack_forget()

    def apply_preset(self, event=None):
        preset = self.preset_var.get()
        self.mode_var.set("Random")
        self.update_mode_ui()
        # Reset all
        self.use_lower.set(False); self.use_upper.set(False); self.use_digits.set(False)
        self.use_symbols.set(False); self.use_arabic.set(False); self.use_chinese.set(False)
        self.use_japanese.set(False); self.use_korean.set(False); self.use_russian.set(False)
        self.avoid_ambiguous.set(False); self.no_repeat.set(False)

        if "High Security" in preset:
            self.length_var.set(20)
            self.use_lower.set(True); self.use_upper.set(True); self.use_digits.set(True); self.use_symbols.set(True)
            self.no_repeat.set(True)
        elif "Simple" in preset:
            self.length_var.set(8)
            self.use_lower.set(True); self.use_upper.set(True)
        elif "Passphrase" in preset:
            self.mode_var.set("Passphrase")
            self.update_mode_ui()
            self.word_count_var.set(4); self.sep_var.set("-")
        elif "Arabic Mix" in preset:
            self.length_var.set(12); self.use_lower.set(True); self.use_upper.set(True); self.use_digits.set(True); self.use_arabic.set(True)
        elif "Chinese Mix" in preset:
            self.length_var.set(12); self.use_lower.set(True); self.use_upper.set(True); self.use_digits.set(True); self.use_chinese.set(True)
        elif "Japanese Mix" in preset:
            self.length_var.set(12); self.use_lower.set(True); self.use_upper.set(True); self.use_digits.set(True); self.use_japanese.set(True)
        elif "Korean Mix" in preset:
            self.length_var.set(12); self.use_lower.set(True); self.use_upper.set(True); self.use_digits.set(True); self.use_korean.set(True)
        elif "Russian Mix" in preset:
            self.length_var.set(12); self.use_lower.set(True); self.use_upper.set(True); self.use_digits.set(True); self.use_russian.set(True)

    def build_pool_mandatory(self):
        pool = ""
        mandatory = []
        # دالة لإضافة نوع مع وزن (weight)
        def add(chars, weight=1):
            nonlocal pool, mandatory
            filtered = chars
            if self.avoid_ambiguous.get():
                filtered = ''.join(c for c in filtered if c not in AMBIGUOUS_CHARS)
            if filtered:
                pool += filtered * weight          # وزن 3 للأرقام والرموز
                mandatory.append(secrets.choice(filtered))

        add(string.ascii_lowercase, weight=1)
        add(string.ascii_uppercase, weight=1)
        add(string.digits, weight=3)                # أرقام وزن 3
        add("!@#$%^&*()_+-=[]{}|;:,.<>?/~", weight=3)  # رموز وزن 3
        add(ARABIC_LETTERS, weight=1)
        add(CHINESE_CHARACTERS, weight=1)
        add(JAPANESE_HIRAGANA + JAPANESE_KATAKANA, weight=1)
        add(KOREAN_HANGUL, weight=1)
        add(RUSSIAN_CYRILLIC, weight=1)
        return pool, mandatory

    def generate_password(self):
        mode = self.mode_var.get()
        if mode == "Random":
            pwd = self.generate_random()
        elif mode == "Passphrase":
            pwd = self.generate_passphrase()
        elif mode == "Pattern":
            pwd = self.generate_pattern()
        else:
            messagebox.showerror("Error", "Unknown mode"); return

        if pwd:
            self.result_var.set(pwd)
            self.toggle_show()
            if not self.no_history.get():
                self.add_to_history(pwd)
            self.update_strength_bar(pwd)
            if self.auto_copy_var.get():
                self.copy_to_clipboard(silent=True)
                self.schedule_clipboard_clear()

    def generate_random(self):
        length = self.length_var.get()
        pool, mandatory = self.build_pool_mandatory()
        if not pool:
            messagebox.showwarning("Warning", "Select at least one character type."); return None
        remaining = length - len(mandatory)
        if remaining < 0:
            messagebox.showerror("Error", f"Length too short (min {len(mandatory)})."); return None
        chars = mandatory + [secrets.choice(pool) for _ in range(remaining)]
        secrets.SystemRandom().shuffle(chars)
        password = ''.join(chars)
        if self.no_repeat.get():
            password = self.filter_no_repeat(password)
        return password

    def generate_passphrase(self):
        words = [secrets.choice(COMMON_WORDS) for _ in range(self.word_count_var.get())]
        return self.sep_var.get().join(words)

    def generate_pattern(self):
        pattern = self.pattern_var.get()
        result = []
        for ch in pattern:
            if ch == 'w': result.append(secrets.choice(COMMON_WORDS))
            elif ch == 'd':
                digs = string.digits
                if self.avoid_ambiguous.get(): digs = ''.join(c for c in digs if c not in AMBIGUOUS_CHARS)
                result.append(secrets.choice(digs))
            elif ch == 's':
                syms = "!@#$%^&*()_+-=[]{}|;:,.<>?/~"
                if self.avoid_ambiguous.get(): syms = ''.join(c for c in syms if c not in AMBIGUOUS_CHARS)
                result.append(secrets.choice(syms))
            elif ch == 'c':
                pool, _ = self.build_pool_mandatory()
                result.append(secrets.choice(pool) if pool else 'c')
            else:
                result.append(ch)
        password = ''.join(result)
        if self.no_repeat.get():
            password = self.filter_no_repeat(password)
        return password

    def filter_no_repeat(self, text):
        filtered = []; i = 0
        while i < len(text):
            c = text[i]; count = 1
            while i+count < len(text) and text[i+count] == c: count += 1
            filtered.extend([c] * min(count, 2)); i += count
        return ''.join(filtered)

    def update_strength_bar(self, password):
        length = len(password)
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~" for c in password)
        has_other = any((not c.isalnum() and c not in string.printable[:95]) for c in password)
        variety = sum([has_lower, has_upper, has_digit, has_symbol, has_other])

        if length >= 16 and variety >= 5: score, color = 100, '#00C853'
        elif length >= 12 and variety >= 4: score, color = 75, '#64DD17'
        elif length >= 8 and variety >= 3: score, color = 50, '#FFD600'
        elif length >= 6 and variety >= 2: score, color = 25, '#FF9100'
        else: score, color = 10, '#FF1744'

        fill_width = int(200 * score / 100)
        self.strength_canvas.coords(self.strength_rect, 0, 0, fill_width, 20)
        self.strength_canvas.itemconfig(self.strength_rect, fill=color)

    def add_to_history(self, pwd):
        if pwd not in self.password_history:
            self.password_history.insert(0, pwd)
            if len(self.password_history) > 5: self.password_history.pop()
        self.refresh_history_display()

    def refresh_history_display(self):
        self.history_listbox.delete(0, tk.END)
        for p in self.password_history:
            self.history_listbox.insert(tk.END, p)

    def copy_history_selection(self):
        sel = self.history_listbox.curselection()
        if sel:
            pwd = self.history_listbox.get(sel[0])
            self.root.clipboard_clear(); self.root.clipboard_append(pwd)
            self.schedule_clipboard_clear()
            self.show_toast("Copied from history.")

    def copy_to_clipboard(self, silent=False):
        pwd = self.result_var.get()
        if pwd:
            self.root.clipboard_clear(); self.root.clipboard_append(pwd)
            if not silent:
                self.schedule_clipboard_clear()
                self.show_toast("Copied!")

    def schedule_clipboard_clear(self):
        if self.clipboard_timer: self.root.after_cancel(self.clipboard_timer)
        self.clipboard_timer = self.root.after(30000, self.clear_clipboard)

    def clear_clipboard(self):
        try: self.root.clipboard_clear()
        except: pass
        self.clipboard_timer = None

    def export_passwords(self):
        fmt = simpledialog.askstring("Export Format", "Choose format: keepass, bitwarden, or csv")
        if not fmt: return
        fmt = fmt.lower().strip()
        if fmt not in ['keepass', 'bitwarden', 'csv']:
            messagebox.showerror("Error", "Invalid format."); return
        if not os.path.exists("passwords.csv"):
            messagebox.showwarning("Export", "No saved passwords found."); return
        try:
            with open("passwords.csv", "r", encoding="utf-8") as f:
                reader = csv.reader(f); rows = list(reader)
            if len(rows) < 2:
                messagebox.showinfo("Export", "No entries."); return
            export_name = f"export_{fmt}.csv"
            with open(export_name, "w", newline='', encoding='utf-8') as out:
                writer = csv.writer(out)
                if fmt == "keepass":
                    writer.writerow(["Title", "URL", "Username", "Password"])
                    for row in rows[1:]:
                        site, enc = row[0], row[1]
                        pwd = aes_decrypt(enc, self.master_key) if (AES_AVAILABLE and self.master_key) else enc
                        writer.writerow([site, "", site, pwd])
                elif fmt == "bitwarden":
                    writer.writerow(["folder", "favorite", "type", "name", "notes", "fields", "reprompt",
                                     "login_uri", "login_username", "login_password", "login_totp"])
                    for row in rows[1:]:
                        site, enc = row[0], row[1]
                        pwd = aes_decrypt(enc, self.master_key) if (AES_AVAILABLE and self.master_key) else enc
                        writer.writerow(["", "", "login", site, "", "", "", "", site, pwd, ""])
                else:  # plain csv
                    writer.writerow(["site", "password"])
                    for row in rows[1:]:
                        site, enc = row[0], row[1]
                        pwd = aes_decrypt(enc, self.master_key) if (AES_AVAILABLE and self.master_key) else enc
                        writer.writerow([site, pwd])
            messagebox.showinfo("Export", f"Exported to {export_name}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def save_password(self):
        pwd = self.result_var.get()
        site = self.site_var.get().strip()
        if not pwd or not site:
            messagebox.showwarning("Warning", "Generate password and enter site."); return
        encrypted = pwd
        if AES_AVAILABLE and self.master_key:
            try: encrypted = aes_encrypt(pwd, self.master_key)
            except Exception as e: messagebox.showerror("Encryption Error", str(e)); return
        file_exists = os.path.isfile("passwords.csv")
        with open("passwords.csv", "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists: writer.writerow(["site", "encrypted_password"])
            writer.writerow([site, encrypted])
        self.show_toast("Saved!")

    def show_toast(self, msg):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.geometry(f"+{self.root.winfo_x()+50}+{self.root.winfo_y()+50}")
        toast.configure(bg='black')
        tk.Label(toast, text=msg, fg='white', bg='black', font=("Arial", 10), padx=10, pady=5).pack()
        toast.after(2000, toast.destroy)

# ---------------------------- Entry Point ----------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli_mode()
    else:
        root = tk.Tk()
        app = E4PApp(root)
        root.mainloop()