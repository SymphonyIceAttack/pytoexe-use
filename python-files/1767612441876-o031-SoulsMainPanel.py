#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================
# Soul's Ultimate Panel v7.1
# skidding this results into malicious software allegations against you.
# .gg/fluidz - discord link to be able to find actual source code

import string
import random
import os
import json
import sys
import time
import math
import base64
import socket
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
import difflib
import ast
import operator
import getpass

ALLOWED_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod
}

def safe_eval(expr):
    def _eval(node):
        if isinstance(node, ast.Num): return node.n
        elif isinstance(node, ast.BinOp): return ALLOWED_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        else: raise ValueError("Unsafe expression")
    return _eval(ast.parse(expr, mode='eval').body)

os.system("")

# =============================
# INFO SECTION DATABASE
# =============================
INFO_ENTRIES = {
"backstory": """
\033[1;34mSoul's Ultimate Panel\033[0m was forged as a \033[1;36mterminal-first toolkit\033[0m designed
for \033[1;33mstylization\033[0m, \033[1;33msimulation\033[0m, and \033[1;33mcreative power\033[0m. What started as a
simple \033[1;32municode experiment\033[0m evolved into a \033[1;35mmulti-section panel\033[0m blending
\033[1;32maesthetic control\033[0m with \033[1;31mmali-style utilities\033[0m. \033[1;36mNo dependencies\033[0m.
\033[1;36mNo fluff\033[0m. Just \033[1;33mrawdogging panels\033[0m.
""",

    "about": """
Soul's Ultimate Panel v7.1
Built in pure Python with a focus on speed, control, and style.
Designed for creators, developers, and terminal enthusiasts.
""",
"rules": """
1. No \033[1;33mSkidding\033[0m.
2. No \033[1;31mlarping as the Creators\033[0m.
3. No \033[1;33mUsing this Panel for Personal Issues\033[0m.
4. No \033[1;33mUsing this Panel to Find IPS\033[0m → \033[1;36mGeo-Location\033[0m (its made to find ports)
5. \033[1;31mNO DDOSING WITHOUT A ACTUAL SERIOUS REASON\033[0m AS IT IS \033[1;31mTRACEABLE BY POLICE\033[0m (for now...)
""",

"credits": """
Core Developer: \033[1;31msoulatm\033[0m
Contributors: \033[1;31msebasxcv\033[0m

Founders: \033[1;34mSoul\033[0m, \033[1;34mSebas\033[0m, \033[1;34mSilly\033[0m 
Co-Owners: \033[1;34mN/A\033[0m
Managers: \033[1;34mN/A\033[0m
Admins: \033[1;34mN/A\033[0m
Moderators: \033[1;34mN/A\033[0m
Trial Staff: \033[1;34mN/A\033[0m 
""",
}  # This final } closes INFO_ENTRIES

# =============================
# COMPLETE CONFIG SYSTEM
# =============================
CONFIG_DIR = Path.home() / ".souls-panel"
CONFIG_FILE = CONFIG_DIR / "config.json"
FONTS_DIR = CONFIG_DIR / "custom_fonts"

for d in [CONFIG_DIR, FONTS_DIR]:
    d.mkdir(exist_ok=True)

def load_config() -> Dict[str, Any]:
    default_config = {
        "last_fonts": ["bold"], "auto_copy": True, "theme": "dark",
        "favorites": [], "history": [], "sound": False
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                default_config.update(config)
        except:
            pass
    return default_config

def save_config(config: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except:
        pass

# =============================
# ELITE UNICODE ENGINE - ALL 20+ FONTS
# =============================
class EliteUnicodeEngine:
    def __init__(self) -> None:
        self.fonts: Dict[str, Dict[str, str]] = {}
        self._init_all_fonts()

    def available_fonts(self) -> List[str]:
        return sorted(self.fonts.keys())

    def fuzzy_search_fonts(self, query: str) -> List[str]:
        all_fonts = self.available_fonts()
        matches = difflib.get_close_matches(query.lower(), [f.lower() for f in all_fonts], n=5, cutoff=0.6)
        return [f for f in all_fonts if f.lower() in [m.lower() for m in matches]]

    def stylize(self, text: str, style: str) -> str:
        style_parts = [s.strip() for s in style.split("+") if s.strip()]
        if not style_parts: return text
        out = text
        for part in style_parts:
            mapping = self.fonts.get(part)
            if mapping:
                out = self._apply_mapping(out, mapping)
        return out

    def suggest_styles(self, text: str) -> List[str]:
        suggestions = []
        length = len(text)
        if length <= 10: suggestions.extend(["bold", "circled", "small_caps"])
        if any(c.isupper() for c in text): suggestions.extend(["full_width"])
        if any(c.isdigit() for c in text): suggestions.extend(["squared"])
        combos = ["bold+sans", "fraktur", "sans+small_caps"]
        suggestions.extend(random.sample(combos, min(2, len(combos))))
        return list(dict.fromkeys(suggestions))[:6]

    def _apply_mapping(self, text: str, mapping: Dict[str, str]) -> str:
        result = []
        for ch in text:
            key = ch.lower() if ch.isalpha() else ch
            mapped = mapping.get(key)
            result.append(mapped if mapped else ch)
        return "".join(result)

    def _make_math_range(self, lower_start: int, upper_start: int) -> Dict[str, str]:
        mapping = {}
        for i, ch in enumerate(string.ascii_lowercase): mapping[ch] = chr(lower_start + i)
        for i, ch in enumerate(string.ascii_uppercase): mapping[ch.lower()] = chr(upper_start + i)
        return mapping

    def _init_all_fonts(self) -> None:
        # MATH FONTS (7)
        self.fonts["bold"] = self._make_math_range(0x1D41A, 0x1D400)
        self.fonts["italic"] = self._make_math_range(0x1D44E, 0x1D434)
        self.fonts["bold_italic"] = self._make_math_range(0x1D482, 0x1D468)
        self.fonts["script"] = self._make_math_range(0x1D4B6, 0x1D49C)
        self.fonts["fraktur"] = self._make_math_range(0x1D51E, 0x1D504)
        self.fonts["double_struck"] = self._make_math_range(0x1D552, 0x1D538)
        self.fonts["monospace"] = self._make_math_range(0x1D68A, 0x1D670)
        # SANS FONTS (4)
        self.fonts["sans"] = self._make_math_range(0x1D5BA, 0x1D5A0)
        self.fonts["sans_bold"] = self._make_math_range(0x1D5EE, 0x1D5D4)
        self.fonts["sans_italic"] = self._make_math_range(0x1D622, 0x1D608)
        self.fonts["sans_bold_italic"] = self._make_math_range(0x1D656, 0x1D63C)
        # SPECIAL FONTS
        self.fonts["small_caps"] = {
            "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ",
            "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ",
            "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ",
            "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"
        }
        # Full Width
        full_width = {}
        for i, ch in enumerate(string.ascii_lowercase): full_width[ch] = chr(0xFF41 + i)
        for i, ch in enumerate(string.ascii_uppercase): full_width[ch.lower()] = chr(0xFF21 + i)
        for i in range(10): full_width[str(i)] = chr(0xFF10 + i)
        self.fonts["full_width"] = full_width
        # Circled
        circled = {c:chr(0x24D0+i) for i,c in enumerate(string.ascii_lowercase)}
        circled["0"] = "⓪"
        for i in range(1, 10): circled[str(i)] = chr(0x2460 + (i - 1))
        self.fonts["circled"] = circled
        # Squared
        base = ["🄰","🄱","🄲","🄳","🄴","🄵","🄶","🄷","🄸","🄹","🄺","🄻","🄼","🄽","🄾","🄿","🅀","🅁","🅂","🅃","🅄","🅅","🅆","🅇","🅈","🅉"]
        self.fonts["squared"] = dict(zip(string.ascii_lowercase, base))
        # Box Drawing
        self.fonts["box"] = {
            "a": "█", "b": "▓", "c": "▒", "d": "░", "e": "▌", "f": "▐",
            "g": "▖", "h": "▗", "i": "▘", "j": "▝", "k": "▞", "l": "▚",
            "m": "▙", "n": "▛", "o": "▜", "p": "▟", "q": "■", "r": "□",
            "s": "▪", "t": "▫", "u": "▣", "v": "▤", "w": "▥", "x": "▦",
            "y": "▧", "z": "▨"
        }
        # Upside Down
        self.fonts["upside_down"] = {
            "a": "ɐ", "b": "q", "c": "ɔ", "d": "p", "e": "ǝ", "f": "ɟ",
            "g": "ƃ", "h": "ɥ", "i": "ᴉ", "j": "ɾ", "k": "ʞ", "l": "ʃ",
            "m": "ɯ", "n": "u", "o": "o", "p": "d", "q": "b", "r": "ɹ",
            "s": "s", "t": "ʇ", "u": "n", "v": "ʌ", "w": "ʍ", "x": "x",
            "y": "ʎ", "z": "z"
        }
        # Leet Speak
        self.fonts["leet"] = {"a":"4","b":"8","e":"3","g":"9","i":"1","l":"1","o":"0","s":"5","t":"7","z":"2"}
        # Mirror
        self.fonts["mirror"] = {"b":"d","d":"b","p":"q","q":"p"}

# =============================
# COMPLETE PURE TOOLS
# =============================
class PureTools:
    @staticmethod
    def random_password(length: int = 16, use_symbols: bool = True, words: bool = False) -> str:
        if words:
            words_list = ["apple", "bear", "cloud", "delta", "eagle", "falcon", "ghost", "hotel"]
            return "-".join(random.choice(words_list) for _ in range(4))
        chars = string.ascii_letters + string.digits
        if use_symbols: chars += "!@#$%^&*()-_=+[]{};:,.?/"
        return "".join(random.choice(chars) for _ in range(length))

    @staticmethod
    def password_strength(password: str) -> Dict[str, Any]:
        length_score = min(len(password) // 4, 4)
        upper = any(c.isupper() for c in password)
        lower = any(c.islower() for c in password)
        digits = any(c.isdigit() for c in password)
        symbols = any(c in "!@#$%^&*()" for c in password)
        score = length_score + upper + lower + digits + symbols
        strength = ["Very Weak", "Weak", "Fair", "Good", "Strong"][min(score, 4)]
        return {"score": score, "strength": strength}

    @staticmethod
    def simple_hash(text: str) -> str:
        h = 0
        for c in text:
            h = (h * 31 + ord(c)) & 0xFFFFFFFF
        return f"{h:08x}"

    @staticmethod
    def simple_calc(expression: str) -> float:
        try:
            return eval(expression.replace('^', '**'), {"__builtins__": {}, "math": math})
        except:
            return 0.0

    @staticmethod
    def create_banner(text: str, width: int = 40) -> str:
        padded = text.center(width-4)
        return f"╔{'═'*(width-2)}╗\n║ {padded} ║\n╚{'═'*(width-2)}╝"

    @staticmethod
    def spinner_task(msg: str, duration: float = 2.0):
        chars = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏⠋'
        for i in range(int(duration * 10)):
            sys.stdout.write(f'\r{chars[i%len(chars)]} {msg} ')
            sys.stdout.flush()
            time.sleep(0.1)
        print(' ' * 50, end='\r')

# =============================
# SYMBOL SETS - NO EMOJIS
# =============================
SYMBOL_SETS = {
    "arrows": "➤➥➦➧➨➩➪➫➬➭➮➯",
    "stars": "★☆✦✧✩✪✫✬✭✮✯",
    "blocks": "█▓▒░▌▐▖▗▘▝▞▚",
    "shapes": "◆◇◈◉◎●○◌◍◐◑◒◓",
    "mixed": "✶✷✸✹✺✻✼✽✾✿❀❁❂",
    "hearts": "♥♦♣♠♡♢♤♧♨",
    "music": "♪♫♬♩♬♭♮♯",
    "weather": "☀☁☂☃☄★☇",
    "geometric": "▣▤▥▦▧▨▩▪▫▬▭▮▯",
    "lines": "─│┌┐└┘├┤┬┴┼╮╯"
}

def generate_symbol_line(length: int, set_name: str) -> str:
    symbols = SYMBOL_SETS.get(set_name, SYMBOL_SETS["mixed"])
    return "".join(symbols[i % len(symbols)] for i in range(length))

# =============================
# STARTUP EFFECTS - PERFECTED
# =============================
def matrix_startup(duration: float = 2.5, width: int = 60) -> None:
    chars = "01█▓▒░"
    end_time = time.time() + duration
    while time.time() < end_time:
        line = "".join(random.choice(chars) for _ in range(width))
        sys.stdout.write("\r" + line)
        sys.stdout.flush()
        time.sleep(0.05)
    sys.stdout.write("\r" + " " * width + "\r")
    sys.stdout.flush()

def type_and_erase(message: str, type_delay: float = 0.06, erase_delay: float = 0.02) -> None:
    for ch in message:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(type_delay)
    time.sleep(0.4)

# =============================
# PASSWORD GATE FUNCTION (with suppression)
# =============================
def password_gate():
    correct_password = "fluidz273"  # Change this password
    max_attempts = 3
    for attempt in range(max_attempts):
        # Suppress stderr temporarily
        with open(os.devnull, 'w') as devnull:
            old_stderr = sys.stderr
            sys.stderr = devnull
            try:
                entered = getpass.getpass("Enter Password:")
            finally:
                sys.stderr = old_stderr
        if entered == correct_password:
            print("\033[92m✔ Access granted!\033[0m")
            return True
        else:
            print("\033[91mWrong password, if you dont know the password - Join the Discord\033[0m")
            if attempt == max_attempts - 1:
                print("\033[1;91m❌ MAX ATTEMPTS - EXITING\033[0m")
                sys.exit(1)
            time.sleep(1)
    return False

# =============================
# MENU FUNCTIONS
# =============================
def print_banner() -> None:
    banner = PureTools.create_banner("Soul's Ultimate Panel v7.1", 50)
    print("\033[93;4m" + "="*60 + "\033[0m")
    print("\033[96m" + banner + "\033[0m")
    print("\033[1;91m         Discord Link - gg/fluidz\033[0m")
    print("\033[95;4m         Credits are in the INFO command        \033[0m")
    print("\033[92m" + "="*60 + "\033[0m")

def print_main_menu() -> None:
    print("""
\033[94mMAIN SECTIONS:\033[0m
  text     → Unicode fonts + suggestions
  sym      → Symbol generator
  tools    → Passwords/hash/calc/banner
  mali     → SOUL'S TOOLS (10+)
  timer    → Countdown timer
  fonts    → List all 20+ fonts
  info     → Project backstory, rules, credits
  config   → Settings menu
  help     → Show this menu
  exit     → Quit

\033[1;94;4m      More Coming Soon!        \033[0m
    """)

def print_hacker_menu() -> None:
    print("""
\033[91mSOUL'S TOOLS SECTION (10+ Commands):\033[0m
  ╔══════════════════════════════════════╗
  ║  base64   → Encode/decode base64     ║
  ║  hex      → Text to hex dump         ║
  ║  crypt    → XOR encrypt/decrypt      ║
  ║  scan     → Port scanner simulator   ║
  ║  net      → Network interface info   ║
  ║  bin      → Binary/hex converter     ║
  ║  art      → ASCII art generator      ║
  ║  ps       → Process list simulator   ║
  ║  qr       → ASCII QR code generator  ║
  ║  matrix   → Matrix rain effect       ║
  ╚══════════════════════════════════════╝
  back       → Return to main menu
    """)

# =============================
# MAIN LOOP - FULLY FUNCTIONAL
# =============================
def startup_sequence():
    """Unified startup: boot → FAST ERASE → matrix → greeting → ERASE"""
    # Run boot sequence
    steps = [
        "\033[1;33mCompiling Resources\033[0m",
        "\033[1;33mResources Compiled → Switching to Panel Resources\033[0m", 
        "\033[1;33mCompiling Panel\033[0m",
        "\033[1;32mPANEL COMPILED ✓\033[0m"
    ]
    boot_lines = []
    for step in steps:
        print(step)
        boot_lines.append(step)
        time.sleep(0.8)
    # Fast erase
    time.sleep(0.5)
    for line in boot_lines:
        for _ in range(len(line) + 10):
            sys.stdout.write("\b \b")
        sys.stdout.flush()
        time.sleep(0.02)
    # Clear screen
    print("\033[2J\033[H", end="", flush=True)
    # Matrix effect
    chars = "01█▓▒░"
    for _ in range(25):
        line = "".join(random.choice(chars) for _ in range(70))
        sys.stdout.write(f"\r\033[1;32m{line}\033[0m")
        sys.stdout.flush()
        time.sleep(0.06)
    sys.stdout.write("\r" + " " * 70 + "\r")
    sys.stdout.flush()
    # Welcome message with type and erase
    welcome_msg = "\033[1;34mWelcome to Soul's Panel, Everything You've Exepected is Here.\033[0m"
    for char in welcome_msg:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.05)
    time.sleep(0.8)
    # Erase message
    for _ in welcome_msg:
        sys.stdout.write("\b \b")
        sys.stdout.flush()
        time.sleep(0.03)
    # Final clear
    print("\033[2J\033[H", end="", flush=True)

# =============================
# MAIN FUNCTION
# =============================
def main():
    # Call password gate first
    password_gate()

    # After successful login, run startup effects
    startup_sequence()
    print_banner()
    print_main_menu()

    while True:
        try:
            cmd = input("\n\033[93mLostSoul> \033[0m").strip().lower()

            if cmd in {"exit", "quit", "q"}:
                print("\033[91mGoodbye!\033[0m")
                break

            if cmd == "help":
                print_main_menu()
                continue

            # INFO SECTION
            if cmd == "info":
                print("Available info topics:", ", ".join(INFO_ENTRIES.keys()))
                topic = input("Topic: ").strip().lower()
                if topic in INFO_ENTRIES:
                    print(f"\n\033[95m=== {topic.upper()} ===\033[0m")
                    print(INFO_ENTRIES[topic])
                else:
                    print("Unknown topic. Try one of:", ", ".join(INFO_ENTRIES.keys()))
                continue

            # HACKER SECTION
            if cmd == "mali":
                while True:
                    print_hacker_menu()
                    subcmd = input("\033[91mMaliSoul> \033[0m").strip().lower()
                    if subcmd in {"back", "main", "exit"}:
                        break
                    elif subcmd == "base64":
                        print("base64: encode | decode")
                        action = input("Action: ").strip().lower()
                        text = input("Text: ").strip()
                        try:
                            if action == "encode":
                                print(base64.b64encode(text.encode()).decode())
                            elif action == "decode":
                                print(base64.b64decode(text.encode()).decode())
                            else:
                                print("Use: encode or decode")
                        except:
                            print("Invalid base64")
                        continue
                    elif subcmd == "hex":
                        text = input("Text/bytes: ").encode()
                        hex_dump = " ".join(f"{b:02x}" for b in text)
                        print(f"Hex: {hex_dump}")
                        print(f"Len: {len(text)} bytes")
                        continue
                    elif subcmd == "crypt":
                        text = input("Text: ").strip()
                        key = input("Key (single char): ").strip() or "s"
                        key_byte = ord(key[0]) if key else ord("s")
                        encrypted = "".join(chr(ord(c) ^ key_byte) for c in text)
                        print(f"XOR encrypted (key={key}): {encrypted}")
                        print(f"Decrypted: {''.join(chr(ord(c) ^ key_byte) for c in encrypted)}")
                        continue
                    elif subcmd == "scan":
                        target = input("Target (127.0.0.1): ") or "127.0.0.1"
                        ports = [22, 80, 443, 8080, 3000, 5000]
                        print(f"Scanning {target}...")
                        tools.spinner_task("Scanning ports")
                        for port in ports:
                            status = random.choice(["OPEN", "CLOSED", "FILTERED"])
                            print(f"{target}:{port} {status}")
                        continue
                    elif subcmd == "net":
                        hostname = socket.gethostname()
                        ip = socket.gethostbyname(hostname)
                        print(f"Hostname: {hostname}")
                        print(f"Local IP: {ip}")
                        print(f"MAC: {':'.join(['%02x' % random.randint(0x00, 0xff) for _ in range(6)])}")
                        continue
                    elif subcmd == "bin":
                        num = input("Number (decimal): ").strip()
                        try:
                            n = int(num)
                            binary = bin(n)[2:].zfill(8)[-32:]
                            print(f"Decimal: {n}")
                            print(f"Binary:  {binary}")
                            print(f"Hex:     {hex(n)}")
                        except:
                            print("Invalid number")
                        continue
                    elif subcmd == "art":
                        chars = "SOULHACKPANEL"
                        print("\n".join(generate_symbol_line(40, "arrows") for _ in range(2)))
                        for i, c in enumerate(chars):
                            print(f"{generate_symbol_line(i*2, 'stars')}{c}{generate_symbol_line(40-i*2, 'blocks')}")
                        print("\n".join(generate_symbol_line(40, "lines") for _ in range(2)))
                        continue
                    elif subcmd == "ps":
                        processes = ["python", "chrome", "firefox", "node", "nginx", "mysql", "redis"]
                        print("PID   CPU   MEM   COMMAND")
                        print("-" * 35)
                        for i, proc in enumerate(processes, 1001):
                            cpu = random.randint(0, 100)
                            mem = random.randint(10, 512)
                            print(f"{i:>4}  {cpu:>3}%  {mem:>3}M  {proc}")
                        continue
                    elif subcmd == "qr":
                        text = input("Text: ")[:20]
                        size = len(text) // 2 + 3
                        border = "█" * size
                        print(border)
                        for _ in range(size-2):
                            print("█" + "░▒▓█"[:size-2] + "█")
                        print(border)
                        print(f"Data: {text}")
                        continue
                    elif subcmd == "matrix":
                        print("Press Ctrl+C to stop Matrix rain...")
                        try:
                            cols = 40
                            drops = [0] * cols
                            while True:
                                line = ""
                                for i in range(cols):
                                    if drops[i] > 0:
                                        char = random.choice("01█▓▒░")
                                        line += char
                                        drops[i] -= 1
                                    else:
                                        if random.random() > 0.95:
                                            drops[i] = random.randint(5, 15)
                                            line += "█"
                                        else:
                                            line += " "
                                print("\r" + line, end="")
                                time.sleep(0.1)
                        except KeyboardInterrupt:
                            print("\nMatrix terminated.")
                        continue
                    print("\nType 'back' to return to main menu")
                print_main_menu()
                continue

            if cmd == "fonts" or cmd == "list":
                fonts_list = engine.available_fonts()[:12]
                print("Fonts:", ", ".join(fonts_list), f"...(+{len(engine.fonts)-12} more)")
                continue

            # TEXT MODE
            if cmd == "text":
                text = input("Enter text: ").strip()
                if not text:
                    print("Try: 'Hello World' or 'SOUL 2026'")
                    continue

                print("Suggestions:", ", ".join(engine.suggest_styles(text)))
                style = input("Style (Enter=bold): ").strip().lower()
                if not style:
                    style = "bold"

                if style not in engine.fonts:
                    matches = engine.fuzzy_search_fonts(style)
                    if matches:
                        print("Did you mean:", ", ".join(matches[:3]) + "?")
                        style = matches[0]

                result = engine.stylize(text, style)
                print(f"\n\033[96m{style.upper()}:\033[0m")
                print(result)
                print("Saved style:", style)
                config["last_fonts"] = style.split("+")
                save_config(config)
                continue

            # SYMBOL MODE
            if cmd == "sym":
                print("Sets:", ", ".join(SYMBOL_SETS.keys()))
                set_name = input("Set: ").strip().lower()
                if set_name not in SYMBOL_SETS:
                    print("Use: arrows, stars, blocks, shapes, hearts, music...")
                    continue
                length = int(input("Length (50): ") or "50")
                line = generate_symbol_line(length, set_name)
                print(f"\n{set_name.upper()} ({length} chars):")
                print(line)
                continue

            # TOOLS MODE
            if cmd == "tools":
                print("Tools: pass | hash | strength | calc | uuid | banner")
                tool = input("Tool: ").strip().lower()

                if tool == "pass":
                    length = int(input("Length (16): ") or "16")
                    pwd = tools.random_password(length)
                    strength = tools.password_strength(pwd)
                    print(f"\n{pwd}")
                    print(f"{strength['strength']} (score: {strength['score']}/9)")

                elif tool == "hash":
                    text = input("Text: ")
                    print("Hash:", tools.simple_hash(text))

                elif tool == "strength":
                    pwd = input("Password: ")
                    strength = tools.password_strength(pwd)
                    print(f"{strength['strength']} (score: {strength['score']}/9)")

                elif tool == "calc":
                    expr = input("Expression: ")
                    try:
                        result = tools.simple_calc(expr)
                        print(f"{expr} = \033[92m{result}\033[0m")
                    except:
                        print("Invalid expression")

                elif tool == "uuid":
                    print("UUID:", ''.join(random.choice(string.hexdigits) for _ in range(8)).upper() + '-' + 
                          ''.join(random.choice(string.hexdigits) for _ in range(4)).upper() + '-' + 
                          ''.join(random.choice(string.hexdigits) for _ in range(4)).upper() + '-' + 
                          ''.join(random.choice(string.hexdigits) for _ in range(4)).upper() + '-' + 
                          ''.join(random.choice(string.hexdigits) for _ in range(12)).upper())

                elif tool == "banner":
                    text = input("Text: ") or "SOULS"
                    print(tools.create_banner(text))
                continue

            # CALCULATOR SHORTCUT
            if cmd.startswith("calc "):
                expr = cmd[5:].strip()
                try:
                    result = tools.simple_calc(expr)
                    print(f"{expr} = \033[92m{result}\033[0m")
                except:
                    print("Invalid expression")
                continue

            # TIMER
            if cmd.startswith("timer "):
                minutes = int(cmd[6:].strip() or input("Minutes: ") or "1")
                print(f"Starting {minutes} minute timer...")
                tools.spinner_task("Counting down")
                for i in range(minutes*60, 0, -1):
                    m, s = divmod(i, 60)
                    sys.stdout.write(f'\r{m:02d}:{s:02d} ')
                    sys.stdout.flush()
                    time.sleep(1)
                print('Time\'s up!')
                continue

            # STATS
            if cmd == "stats":
                print(f"Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Fonts loaded: {len(engine.fonts)}")
                print(f"Config: {CONFIG_FILE}")
                continue

            # CONFIG
            if cmd == "config":
                print("Configuration:")
                print("Auto-copy:", "ON" if config['auto_copy'] else "OFF")
                print("Last fonts:", ", ".join(config.get('last_fonts', ['bold'])))
                config["auto_copy"] = not config["auto_copy"]
                save_config(config)
                print("Settings saved!")
                continue

            print("\nCommands: text | sym | tools | mali | timer | info | help | exit")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

# =============================
# CLI ARGUMENTS
# =============================
def main_args():
    args = sys.argv[1:]

    if "--list" in args or "-l" in args:
        engine = EliteUnicodeEngine()
        print("Available fonts:", ", ".join(engine.available_fonts()))
        return

    if "--text" in args or "-t" in args:
        try:
            text_idx = args.index("--text") + 1 if "--text" in args else args.index("-t") + 1
            text = args[text_idx]
            style_idx = args.index("--style") + 1 if "--style" in args else -1
            style = args[style_idx] if style_idx > 0 else "bold"
            engine = EliteUnicodeEngine()
            result = engine.stylize(text, style)
            print(result)
        except:
            print("Usage: python souls.py --text 'Hello' [--style bold]")
        return

    main()

if __name__ == "__main__":
    main_args()