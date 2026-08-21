#!/usr/bin/env python3
"""
xworm_interactive.py  —  XWorm Config Decryptor
Requires: pip install pycryptodome
"""

import base64
import hashlib
import shutil
import sys
import time

try:
    from Crypto.Cipher import AES
except ImportError:
    print("Missing dependency. Run:  pip install pycryptodome")
    sys.exit(1)

if sys.platform == "win32":
    import os
    os.system("")

RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"

def rgb(r, g, b): return f"\033[38;2;{r};{g};{b}m"
def bgr(r, g, b): return f"\033[48;2;{r};{g};{b}m"

C1 = rgb(0,   255, 255)
C2 = rgb(0,   220, 255)
C3 = rgb(0,   190, 255)
C4 = rgb(0,   160, 255)
C5 = rgb(0,   130, 240)
C6 = rgb(0,   100, 220)
GRADIENT = [C1, C2, C3, C4, C5, C6]

GREEN  = rgb(80,  255, 140)
RED    = rgb(255, 90,  90)
YELLOW = rgb(255, 210, 90)
GREY   = rgb(100, 120, 130)
DGREY  = rgb(50,  65,  75)

BANNER = [
    r" ██████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗ ",
    r"██╔════╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗",
    r"██║     ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝",
    r"██║     ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗",
    r"╚██████╗██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║",
    r" ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ",
]


def W():
    return min(shutil.get_terminal_size(fallback=(90, 24)).columns, 92)

def center(text, width):
    return " " * max((width - len(text)) // 2, 0) + text

def hline(w, left="─", mid="─", right="─", col=C4):
    inner = mid * (w - 2)
    return f"{col}{left}{inner}{right}{RESET}"

def box_line(text_visible, text_styled, w, col=C4):
    inner_w = w - 4
    pad = max(inner_w - len(text_visible), 0)
    lp = pad // 2
    rp = pad - lp
    return f"{col}│{RESET} {' '*lp}{text_styled}{' '*rp} {col}│{RESET}"


def print_banner():
    w = W()
    sys.stdout.write("\n")

    top    = f"{C4}╭{'─'*(w-2)}╮{RESET}"
    bottom = f"{C4}╰{'─'*(w-2)}╯{RESET}"

    print(top)
    for i, line in enumerate(BANNER):
        col = GRADIENT[i % len(GRADIENT)]
        print(box_line(line, f"{col}{BOLD}{line}{RESET}", w))

    # blank separator row
    print(box_line("", "", w))

    subtitle_v = "XWorm Interactive Config Decryptor   v1.0"
    subtitle_s = f"{C2}{BOLD}XWorm Interactive Config Decryptor{RESET}   {DIM}{GREY}v1.0{RESET}"
    print(box_line(subtitle_v, subtitle_s, w))

    tag_v = "Static analysis  •  No file execution  •  No network"
    tag_s = f"{DGREY}{tag_v}{RESET}"
    print(box_line(tag_v, tag_s, w))

    print(bottom)
    sys.stdout.write("\n")


def tag_ok():   return f"{GREEN}{BOLD}[OK]{RESET} "
def tag_err():  return f"{RED}{BOLD}[ERR]{RESET} "
def tag_warn(): return f"{YELLOW}{BOLD}[!]{RESET}  "
def tag_info(): return f"{C2}{BOLD}[i]{RESET}  "

def prompt_input(label):
    arrow = f"{C3}{BOLD}❯{RESET}"
    lbl   = f"{C4}{label}{RESET}"
    return input(f"{arrow} {lbl} ").strip()


def loading_bar(msg="Decrypting", steps=12, delay=0.025):
    w = W()
    bar_w = 20
    for i in range(steps + 1):
        filled = int(bar_w * i / steps)
        bar = "█" * filled + "░" * (bar_w - filled)
        pct = int(100 * i / steps)
        line = f"\r{C2}{BOLD}{msg}...{RESET} {C4}[{bar}]{RESET} {GREY}{pct}%{RESET} "
        sys.stdout.write(line)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(f"\r{' ' * (len(msg) + bar_w + 20)}\r")
    sys.stdout.flush()


def derive_key(mutex: str) -> bytes:
    digest = hashlib.md5(mutex.encode("utf-8")).digest()
    key = bytearray(32)
    key[0:16] = digest
    key[15:31] = digest
    return bytes(key)


def decrypt(encoded: str, mutex: str) -> str:
    key = derive_key(mutex)
    raw = base64.b64decode(encoded.strip(), validate=True)
    if not raw or len(raw) % AES.block_size:
        raise ValueError(f"Bad ciphertext length ({len(raw)} bytes) — paste the full base64 value")
    dec = AES.new(key, AES.MODE_ECB).decrypt(raw)
    pad = dec[-1]
    if pad < 1 or pad > AES.block_size or dec[-pad:] != bytes([pad]) * pad:
        raise ValueError("Wrong Mutex or not XWorm data (invalid PKCS7 padding)")
    return dec[:-pad].decode("utf-8")


SECRET_FIELDS = {"key", "aes", "aeskey", "encryptionkey"}

def classify(value: str) -> tuple[str, str]:
    """Returns (label_hint, color) based on the decoded content."""
    v = value.lower()
    if any(x in v for x in [".", ":", "//", "ddns", "ngrok", "onion"]):
        return ("HOST", C1)
    if value.isdigit() and 1 <= int(value) <= 65535:
        return ("PORT", YELLOW)
    if "xworm" in v or "xrat" in v:
        return ("VERSION", C3)
    if value.startswith("<") and value.endswith(">"):
        return ("DELIMITER", GREY)
    if ".exe" in v or ".bat" in v or ".vbs" in v:
        return ("FILENAME", YELLOW)
    return ("VALUE", GREEN)


def main():
    print_banner()

    mutex = prompt_input("Enter Mutex:")
    while not mutex:
        print(f"{tag_warn()}{YELLOW}Mutex cannot be empty.{RESET}")
        mutex = prompt_input("Enter Mutex:")

    print(f"\n{tag_ok()}{C4}Mutex set:{RESET} {DIM}{GREY}{mutex}{RESET}")
    print(f"{DGREY}  Paste any encrypted field below — one at a time.")
    print(f"  Commands: {BOLD}!mutex{RESET}{DGREY} = change Mutex   {BOLD}!quit{RESET}{DGREY} = exit{RESET}\n")

    w = W()
    print(f"{C6}{'─' * w}{RESET}")

    count_ok  = 0
    count_err = 0

    while True:
        try:
            text = prompt_input("Enter text to decrypt:")
        except (EOFError, KeyboardInterrupt):
            break

        if not text:
            continue

        cmd = text.lower().strip()
        if cmd in ("!quit", "!exit", "exit", "quit"):
            break
        if cmd == "!mutex":
            mutex = prompt_input("Enter new Mutex:")
            print(f"{tag_ok()}{C4}Mutex updated.{RESET}\n")
            continue

        # Tiny loading effect so it feels like it's doing real crypto work.
        loading_bar("Decrypting", steps=10, delay=0.018)

        try:
            result = decrypt(text, mutex)
            count_ok += 1

            # Special-case: if the field looks like it might be a KEY/secret
            if any(k in text[:5].lower() for k in ["job", "jOb"]):
                label, col = "KEY", RED
            else:
                label, col = classify(result)

            if label == "KEY":
                print(f"{tag_ok()}{col}{BOLD}[{label}]{RESET}  {RED}[DETECTED - REDACTED]{RESET}")
            else:
                print(f"{tag_ok()}{col}{BOLD}[{label}]{RESET}  {GREEN}{BOLD}{result}{RESET}")

        except Exception as exc:
            count_err += 1
            print(f"{tag_err()}{RED}{exc}{RESET}")

        print()

    # Summary on exit
    print(f"\n{C6}{'─' * w}{RESET}")
    print(f"{tag_info()}{GREY}Session ended —{RESET} "
          f"{GREEN}{count_ok} decrypted{RESET}  "
          f"{RED}{count_err} failed{RESET}\n")


if __name__ == "__main__":
    main()
