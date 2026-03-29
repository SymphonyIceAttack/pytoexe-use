"""
RE4 Master Editor v1.0.0
========================
Unified RE4 modding suite — single file.
All modules embedded.

Folder structure next to EXE:
  RE4 MASTER EDITOR/
    RE4 CODE MANAGER/
      the_codes/  the_files/  Profiles/  Modified files/
    OSD EDITOR/
    CNS EDITOR/
    SND EDITOR/
    AEV OPTION EDITOR/
    MDT COLOR EDITOR/
    ROOM INIT EDITOR/
    AVL EDITOR/
"""

import sys
import os
import re
import json
import ctypes
import struct
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.scrolledtext as scrolledtext
from tkinter import filedialog, messagebox, colorchooser

# ── hide console ──────────────────────────────────────────────────────────────
def _hide_console():
    try:
        if sys.platform.startswith("win"):
            ctypes.windll.user32.ShowWindow(
                ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass
_hide_console()

# ── root path ─────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    _ROOT = os.path.dirname(sys.executable)
else:
    _ROOT = os.path.dirname(os.path.abspath(__file__))

MASTER_DIR = os.path.join(_ROOT, "RE4 MASTER EDITOR")

# ── master settings ───────────────────────────────────────────────────────────
_MSETTINGS_FILE = os.path.join(MASTER_DIR, "master_settings.json")

def load_master_settings():
    d = {"lang": "en", "remember_exe": True, "last_exe": ""}
    if os.path.isfile(_MSETTINGS_FILE):
        try:
            with open(_MSETTINGS_FILE, encoding="utf-8") as f:
                d.update(json.load(f))
        except Exception:
            pass
    return d

def save_master_settings(s):
    try:
        os.makedirs(os.path.dirname(_MSETTINGS_FILE), exist_ok=True)
        with open(_MSETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

MASTER_SETTINGS = load_master_settings()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1: RE4 CODE MANAGER (embedded from main.py)
# ═════════════════════════════════════════════════════════════════════════════
# The following section contains the full RE4 Code Manager.
# BASE_DIR is overridden to point to RE4 MASTER EDITOR/RE4 CODE MANAGER/


# Override BASE_DIR for master editor context
def _get_base_dir():
    return os.path.join(MASTER_DIR, "RE4 CODE MANAGER")

"""
RE4 Code Manager
=====================
Main application entry point.
Reads code definitions from the_codes/codes_info.json
Reads hex patch data  from the_codes/codes_data.json
"""

# [merged: import sys]
# [merged: import os]
# [merged: import json]
# [merged: import ctypes]
# [merged: import tkinter as tk]
# [merged: from tkinter import filedialog, messagebox]


# ── paths ────────────────────────────────────────────────────────────────────
def _get_base_dir():
    """
    Get the base directory for RE4 Code Manager.
    Works correctly both as .py script and as embedded module in RE4 Master Editor.
    Priority:
    1. If __MASTER_BASE__ is set (embedded mode) — use that
    2. If running as EXE — use directory of EXE
    3. Otherwise — use directory of this script
    """
    # embedded mode: master editor passes the base dir
    master_base = globals().get("__MASTER_BASE__", None)
    if master_base:
        return os.path.join(master_base, "RE4 MASTER EDITOR", "RE4 CODE MANAGER")
    # running as EXE
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        # check if we're inside RE4 MASTER EDITOR structure
        parent = os.path.dirname(exe_dir)
        if os.path.basename(exe_dir).upper() == "RE4 CODE MANAGER":
            return exe_dir
        return exe_dir
    # running as .py
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR     = _get_base_dir()
CODES_DIR    = os.path.join(BASE_DIR, "the_codes")
INFO_FILE    = os.path.join(CODES_DIR, "codes_info.json")
DATA_FILE    = os.path.join(CODES_DIR, "codes_data.json")
ORIG_FILE    = os.path.join(CODES_DIR, "bio4_original.exe")
PROFILES_DIR = os.path.join(BASE_DIR, "Profiles")
MOD_DIR      = os.path.join(BASE_DIR, "Modified files")
FILES_DIR    = os.path.join(BASE_DIR, "the_files")
LOG_FILE     = os.path.join(FILES_DIR, "patch_log.txt")

# ── language ─────────────────────────────────────────────────────────────────
CURRENT_LANG = MASTER_SETTINGS.get("lang", "en")  # synced from master settings

def t(ar_text, en_text):
    return en_text if CURRENT_LANG == "en" else ar_text


def write_log(action, code_name, exe_path="", details=""):
    """Append a formatted entry to patch_log.txt."""
    from datetime import datetime
    try:
        os.makedirs(FILES_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write("=" * 60 + "\n")
            f.write(f"Time   : {ts}\n")
            f.write(f"Action : {action}\n")
            f.write(f"Code   : {code_name}\n")
            if exe_path:
                f.write(f"EXE    : {exe_path}\n")
            if details:
                for line in details.strip().splitlines():
                    f.write(f"         {line}\n")
            f.write("\n")
    except Exception:
        pass


def build_log_details(code_id, codes_data, backup=None):
    """Build details string showing offsets and before/after bytes for log."""
    entry = codes_data.get(code_id, {})
    lines = []
    patches = []
    if "variants" in entry:
        for v in entry["variants"].values():
            patches += v.get("patches", [])
    else:
        patches = entry.get("patches", [])

    backup_code = (backup or {}).get(code_id, {})

    for p in patches:
        ptype = p.get("type", "")
        if ptype == "find_replace":
            fb = p.get("find", "")[:32] + ("..." if len(p.get("find","")) > 32 else "")
            rb = p.get("replace", "")[:32] + ("..." if len(p.get("replace","")) > 32 else "")
            lines.append(f"Type   : find_replace")
            lines.append(f"Before : {fb}")
            lines.append(f"After  : {rb}")
        elif ptype in ("offset_paste", "offset_replace"):
            off = p.get("offset", "")
            nb  = p.get("bytes", "")[:32] + ("..." if len(p.get("bytes","")) > 32 else "")
            key = off.upper().lstrip("0") or "0"
            ob  = backup_code.get(key, "")
            lines.append(f"Offset : {off}")
            if ob:
                lines.append(f"Before : {ob}")
            lines.append(f"After  : {nb}")
    return "\n".join(lines)


# ── colors ───────────────────────────────────────────────────────────────────
BG_MAIN    = "#0d0d0d"
BG_PANEL   = "#111111"
BG_SIDEBAR = "#0a0a0a"
BG_ROW     = "#141414"
BG_ROW_ON  = "#0d1a0d"
BG_ROW_LK  = "#0d0d0d"
BG_ROW_SEL = "#1a1a0a"
BG_HEADER  = "#0f0c00"
BG_TOPBAR  = "#0f0c00"
BG_PATHBAR = "#111111"
BG_NOTICE  = "#1a1200"
BG_STATUS  = "#0a0a0a"
BG_APPLY   = "#0a1a0a"

ACCENT     = "#e8c060"
ACCENT2    = "#ffd060"
GREEN      = "#7aff7a"
RED_SOFT   = "#ff9090"
ORANGE     = "#e8b860"
MUTED      = "#888888"
TEXT_MAIN  = "#e0d0b0"
TEXT_DIM   = "#aaaaaa"
TEXT_LOCK  = "#666666"
BORDER     = "#4a4a2a"
BORDER_ON  = "#3a7a3a"
BORDER_LK  = "#3a2a2a"
BORDER_SEL = "#8a8a3a"

FONT_TITLE  = ("Courier New", 13, "bold")
FONT_NORMAL = ("Courier New", 11)
FONT_SMALL  = ("Courier New", 10)
FONT_TINY   = ("Courier New", 9)
FONT_BOLD   = ("Courier New", 11, "bold")


# ═════════════════════════════════════════════════════════════════════════════
#  Arabic RTL helper
# ═════════════════════════════════════════════════════════════════════════════

try:
    from bidi.algorithm import get_display
    BIDI_AVAILABLE = True
except ImportError:
    BIDI_AVAILABLE = False


def fix_ar(text):
    if not text:
        return text
    if not any("\u0600" <= c <= "\u06ff" for c in text):
        return text

    if not BIDI_AVAILABLE:
        return text

    # Split into Arabic and non-Arabic tokens, apply bidi only to Arabic runs
    tokens = text.split(" ")
    runs = []
    cur_type = None
    cur_toks = []

    for tok in tokens:
        ttype = "ar" if any("\u0600" <= c <= "\u06ff" for c in tok) else "en"
        if ttype != cur_type:
            if cur_toks:
                runs.append((cur_type, cur_toks))
            cur_type = ttype
            cur_toks = [tok]
        else:
            cur_toks.append(tok)
    if cur_toks:
        runs.append((cur_type, cur_toks))

    # reverse run order for RTL display
    runs.reverse()

    parts = []
    for rtype, rtoks in runs:
        chunk = " ".join(rtoks)
        if rtype == "ar":
            parts.append(get_display(chunk))
        else:
            parts.append(chunk)

    return " ".join(parts)


# ═════════════════════════════════════════════════════════════════════════════
#  Data helpers
# ═════════════════════════════════════════════════════════════════════════════

def load_json(path):
    if not os.path.exists(path):
        messagebox.showerror("Missing File", "Cannot find:\n" + path)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def scan_exe(path, codes_info, codes_data):
    """
    Scan bio4.exe for ALL codes.
    A code is considered applied only if ALL its patches match.
    For find_replace  -> replace bytes must be present.
    For offset_paste / offset_replace -> bytes at offset must match.
    """
    results = {}
    try:
        with open(path, "rb") as f:
            exe_bytes = f.read()
    except Exception:
        return results

    for code in codes_info.get("codes", []):
        cid = code["id"]

        # special case: link_tweaks_exe detected by offset 7212FC != "31 2E 30 2E 36"
        if cid == "link_tweaks_exe":
            try:
                off = 0x7212FC
                chunk = exe_bytes[off:off + 5]
                results[cid] = chunk != bytes.fromhex("312E302E36")
            except Exception:
                results[cid] = False
            continue

        data = codes_data.get(cid, {})

        # get patches (handle variants — check first variant)
        if "variants" in data:
            first_variant = list(data["variants"].values())[0]
            patches = first_variant.get("patches", [])
        else:
            patches = data.get("patches", [])

        if not patches:
            results[cid] = False
            continue

        # check ALL patches — code is applied only if every patch matches
        # scan_bytes: alternative byte values that also count as ON (e.g. rsert_order: E2 or EB)
        scan_alts = data.get("scan_bytes", [])
        all_match = True
        for patch in patches:
            try:
                ptype = patch["type"]
                if ptype == "find_replace":
                    needle = bytes.fromhex(patch["replace"].replace(" ", ""))
                    if needle not in exe_bytes:
                        all_match = False
                        break
                elif ptype in ("offset_paste", "offset_replace"):
                    offset = int(patch["offset"], 16)
                    needle = bytes.fromhex(patch["bytes"].replace(" ", ""))
                    chunk  = exe_bytes[offset:offset + len(needle)]
                    if chunk == needle:
                        continue
                    # check scan_bytes alternatives
                    alt_match = any(
                        exe_bytes[offset:offset + len(bytes.fromhex(a.replace(" ", "")))]
                        == bytes.fromhex(a.replace(" ", ""))
                        for a in scan_alts
                    )
                    if not alt_match:
                        all_match = False
                        break
                else:
                    all_match = False
                    break
            except Exception:
                all_match = False
                break

        results[cid] = all_match

    return results


def is_game_running(exe_path):
    """Check if bio4.exe process is currently running."""
    import subprocess
    exe_name = os.path.basename(exe_path).lower()
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq " + exe_name, "/NH"],
            capture_output=True, text=True
        )
        return exe_name in result.stdout.lower()
    except Exception:
        return False


def _friendly_error(e):
    msg = str(e)
    if "13" in msg or "Permission denied" in msg or "Access is denied" in msg:
        return (
            "Permission Denied -- Cannot write to EXE.\n\n"
            "Solutions:\n"
            "1. Run this tool as Administrator (right-click -> Run as administrator)\n"
            "2. Copy bio4.exe to Desktop or Documents and use that copy"
        )
    return msg


BACKUP_FILE   = os.path.join(FILES_DIR, "patch_backup.json")
SETTINGS_FILE = os.path.join(FILES_DIR, "settings.json")

# ── settings ──────────────────────────────────────────────────────────────────
def load_settings():
    defaults = {
        "lang":              "en",
        "silent_apply":      False,
        "last_exe":          "",
        "remember_exe":      True,
        "auto_scan_startup": False,
        "auto_scan_change":  True,
    }
    if os.path.isfile(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                saved = json.load(f)
            defaults.update(saved)
        except Exception:
            pass
    return defaults

def save_settings(settings):
    try:
        os.makedirs(FILES_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

APP_SETTINGS = load_settings()



def load_patch_backup():
    if os.path.isfile(BACKUP_FILE):
        try:
            with open(BACKUP_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_patch_backup(backup):
    try:
        os.makedirs(FILES_DIR, exist_ok=True)
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(backup, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def apply_patch(exe_path, code_id, codes_data, mod_expansion=None):
    entry = codes_data.get(code_id)
    if not entry:
        return False, "No patch data for '" + code_id + "'"

    try:
        with open(exe_path, "rb") as f:
            exe = bytearray(f.read())
    except Exception as e:
        return False, _friendly_error(e)

    if "variants" in entry:
        patches = list(entry["variants"][
            "with_mod_expansion" if mod_expansion else "without_mod_expansion"
        ]["patches"])
    else:
        patches = list(entry.get("patches", []))

    all_patches = patches + entry.get("shared_patches", [])

    backup = load_patch_backup()
    code_backup = {}

    for patch in all_patches:
        try:
            ptype = patch["type"]
            if ptype == "find_replace":
                find_b    = bytes.fromhex(patch["find"].replace(" ", ""))
                replace_b = bytes.fromhex(patch["replace"].replace(" ", ""))
                idx = exe.find(find_b)
                if idx == -1:
                    return False, "Pattern not found:\n" + patch["find"][:40] + "..."
                exe[idx:idx + len(find_b)] = replace_b
            elif ptype in ("offset_paste", "offset_replace"):
                off    = int(patch["offset"], 16)
                data_b = bytes.fromhex(patch["bytes"].replace(" ", ""))
                key    = patch["offset"].upper().lstrip("0") or "0"
                code_backup[key] = exe[off:off + len(data_b)].hex().upper()
                exe[off:off + len(data_b)] = data_b
        except Exception as e:
            return False, _friendly_error(e)

    backup[code_id] = code_backup
    save_patch_backup(backup)

    try:
        with open(exe_path, "wb") as f:
            f.write(exe)
    except Exception as e:
        return False, _friendly_error(e)

    return True, "OK"


def revert_patch(exe_path, orig_path, code_id, codes_data, mod_expansion=None):
    """
    Revert using (priority):
    1. find_replace  -> swap replace->find
    2. offset_*      -> bio4_original.exe (most reliable — true original)
    3. offset_*      -> patch_backup.json fallback (stored at apply time)
    4. offset_replace -> skip if neither available
    5. offset_paste   -> fail if neither available
    Returns (success, message, skipped)
    """
    # special case: link_tweaks_exe uses direct r+b writes — revert from backup
    if code_id == "link_tweaks_exe":
        backup      = load_patch_backup()
        code_backup = backup.get(code_id, {})
        if not code_backup:
            return False, "No backup found for Link Tweaks. Cannot revert.", 0
        try:
            # restore EXE offset 7212FC
            if "7212FC" in code_backup:
                with open(exe_path, "r+b") as f:
                    f.seek(0x7212FC)
                    f.write(bytes.fromhex(code_backup["7212FC"]))
            # restore DLL offset 894054 if backed up
            # (dll path unknown here — skip silently)
            return True, "OK", 0
        except Exception as e:
            return False, str(e), 0

    entry = codes_data.get(code_id)
    if not entry:
        return False, "No patch data for '" + code_id + "'", 0

    try:
        with open(exe_path, "rb") as f:
            exe = bytearray(f.read())
    except Exception as e:
        return False, _friendly_error(e), 0

    orig = None
    if os.path.isfile(orig_path):
        try:
            with open(orig_path, "rb") as f:
                orig = f.read()
        except Exception:
            pass

    backup     = load_patch_backup()
    code_backup = backup.get(code_id, {})

    if "variants" in entry:
        patches = list(entry["variants"][
            "with_mod_expansion" if mod_expansion else "without_mod_expansion"
        ]["patches"])
    else:
        patches = list(entry.get("patches", []))

    skipped = 0
    for patch in patches:
        ptype = patch.get("type", "")
        try:
            if ptype == "find_replace":
                find_b    = bytes.fromhex(patch["find"].replace(" ", ""))
                replace_b = bytes.fromhex(patch["replace"].replace(" ", ""))
                idx = exe.find(replace_b)
                if idx == -1:
                    skipped += 1
                    continue
                exe[idx:idx + len(replace_b)] = find_b

            elif ptype in ("offset_paste", "offset_replace"):
                off    = int(patch["offset"], 16)
                length = len(bytes.fromhex(patch["bytes"].replace(" ", "")))
                key    = patch["offset"].upper().lstrip("0") or "0"

                # 1. bio4_original.exe — الأولوية القصوى (نسخة أصلية مضمونة)
                if orig is not None:
                    chunk = orig[off:off + length]
                    if len(chunk) == length:
                        exe[off:off + length] = chunk
                        continue

                # 2. patch_backup.json — fallback (بايتات مخزّنة وقت التطبيق)
                if key in code_backup:
                    chunk = bytes.fromhex(code_backup[key])
                    if len(chunk) == length:
                        exe[off:off + length] = chunk
                        continue

                # 3. لا يوجد مصدر
                if ptype == "offset_paste":
                    return False, (
                        "Cannot revert at " + patch["offset"] + ".\n"
                        "Place bio4_original.exe in the_codes/ folder."
                    ), skipped
                else:
                    skipped += 1

        except Exception as e:
            return False, str(e), skipped

    try:
        with open(exe_path, "wb") as f:
            f.write(exe)
    except Exception as e:
        return False, _friendly_error(e), skipped

    if code_id in backup:
        del backup[code_id]
        save_patch_backup(backup)

    return True, "OK", skipped


# ═════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═════════════════════════════════════════════════════════════════════════════

def make_label(parent, text="", fg=TEXT_MAIN, bg=BG_MAIN,
               font=FONT_SMALL, **kw):
    return tk.Label(parent, text=text, fg=fg, bg=bg, font=font, **kw)


def make_button(parent, text, command, fg=ACCENT, bg="#2a2a1a",
                active_bg="#3a3a2a", font=FONT_SMALL, width=10, **kw):
    return tk.Button(
        parent, text=text, command=command,
        fg=fg, bg=bg,
        activeforeground=fg, activebackground=active_bg,
        font=font, width=width,
        relief="flat", bd=0, cursor="hand2",
        highlightthickness=1, highlightbackground=BORDER,
        **kw
    )


# ═════════════════════════════════════════════════════════════════════════════
#  CodeRow
# ═════════════════════════════════════════════════════════════════════════════

class CodeRow(tk.Frame):
    def __init__(self, parent, code, app, **kw):
        super().__init__(parent, bg=BG_ROW,
                         highlightthickness=1,
                         highlightbackground=BORDER, **kw)
        self.code      = code
        self.app       = app
        self._expanded = False
        self.selected  = False
        self._build()

    def _get_name(self):
        if CURRENT_LANG == "en":
            return self.code.get("name_en", self.code["name"])
        return self.code["name"]

    def _get_desc(self):
        if CURRENT_LANG == "en":
            return self.code.get("desc_en", self.code.get("desc", ""))
        return fix_ar(self.code.get("desc", ""))

    def _get_notes(self):
        if CURRENT_LANG == "en":
            return self.code.get("notes_en", [])
        return self.code.get("notes", [])

    def _build(self):
        top = tk.Frame(self, bg=BG_ROW)
        top.pack(fill="x", padx=6, pady=4)

        is_numeric  = self.code.get("dialog") == "numeric_input"
        is_num_tog  = self.code.get("dialog") == "numeric_with_toggle"
        is_dropdown = self.code.get("dialog") in (
            "dropdown", "punisher_pierce", "luis_cabin",
            "link_tweaks", "memory_alloc"
        )
        # punisher_pierce uses Change button but NOT inline numeric
        if self.code.get("dialog") == "punisher_pierce":
            is_numeric = False

        # ── checkbox (queue for Apply Selected) ──
        self.sel_var = tk.IntVar(value=0)
        self.sel_chk = tk.Checkbutton(
            top, variable=self.sel_var,
            bg=BG_ROW, activebackground=BG_ROW,
            fg=ACCENT, selectcolor="#1a1a1a",
            relief="flat", bd=0,
            command=self._on_select
        )
        if not is_numeric and not is_dropdown and not is_num_tog:
            self.sel_chk.pack(side="left", padx=(0, 2))

        # ── ON/OFF toggle OR Change button ──
        if is_dropdown:
            self.toggle_btn = tk.Button(
                top, text="Change", width=7, font=FONT_TINY,
                fg=ACCENT2, bg="#1a1a2a",
                activeforeground=ACCENT2, activebackground="#22223a",
                relief="flat", bd=0,
                highlightthickness=1, highlightbackground="#445",
                cursor="hand2",
                command=self._on_toggle
            )
            self.toggle_btn.pack(side="left", padx=(0, 6))
        elif is_num_tog or is_numeric:
            self.toggle_btn = tk.Button(top, text="", width=0)  # hidden placeholder
        else:
            self.toggle_btn = tk.Button(
                top, text="OFF", width=5, font=FONT_TINY,
                fg="#bbbbbb", bg="#1a1a1a",
                activeforeground="#bbbbbb", activebackground="#222",
                relief="flat", bd=0,
                highlightthickness=1, highlightbackground="#555",
                cursor="hand2",
                command=self._on_toggle
            )
            self.toggle_btn.pack(side="left", padx=(0, 6))

        # ── status badge [L] / blank ──
        self.status_var = tk.StringVar(value="")
        self.status_lbl = tk.Label(
            top, textvariable=self.status_var,
            font=FONT_SMALL, fg="#c85a2a", bg=BG_ROW, width=3,
            anchor="center"
        )
        if not is_numeric and not is_num_tog:
            self.status_lbl.pack(side="left", padx=(0, 4))

        # ── name + desc ──
        info_frame = tk.Frame(top, bg=BG_ROW)
        info_frame.pack(side="left", fill="x", expand=True)

        self.name_lbl = tk.Label(
            info_frame, text=self._get_name(),
            font=FONT_NORMAL, fg="#f0e0c0", bg=BG_ROW,
            anchor="w", justify="left"
        )
        self.name_lbl.pack(anchor="w")

        self.desc_lbl = tk.Label(
            info_frame, text=self._get_desc(),
            font=FONT_TINY, fg="#aaaaaa", bg=BG_ROW,
            anchor="w", justify="left", wraplength=400
        )
        self.desc_lbl.pack(anchor="w")

        notes = self._get_notes()

        # ── inline numeric input (replaces ON/OFF for numeric_input codes) ──
        if is_numeric:
            num_frame = tk.Frame(top, bg=BG_ROW)
            num_frame.pack(side="right", padx=(4, 0))

            entry_data = self.app.codes_data.get(self.code["id"], {})
            default    = entry_data.get("default_dec", 0)
            current = getattr(self.app, "_numeric_current", {}).get(self.code["id"], None)
            init_val = current if current is not None else default

            self._num_var = tk.StringVar(value=str(init_val))

            num_entry = tk.Entry(
                num_frame, textvariable=self._num_var,
                font=FONT_SMALL, fg=ACCENT2, bg="#1a1a1a",
                insertbackground=ACCENT2,
                relief="flat", bd=0,
                highlightthickness=1, highlightbackground=BORDER,
                width=7, justify="center"
            )
            num_entry.pack(side="left", ipady=3, padx=(0, 4))
            self.app._add_paste_menu(num_entry)

            tk.Button(
                num_frame, text="Apply",
                font=FONT_TINY, fg=GREEN, bg="#1a2a0a",
                activeforeground=GREEN, activebackground="#2a4a1a",
                relief="flat", bd=0, cursor="hand2",
                highlightthickness=1, highlightbackground="#2a5a2a",
                command=self._on_numeric_apply
            ).pack(side="left", padx=(0, 2), ipady=2, ipadx=4)

        # ── numeric_with_toggle: ON/OFF + field + Apply ──
        elif is_num_tog:
            entry_data = self.app.codes_data.get(self.code["id"], {})
            default    = entry_data.get("default_dec", 0)
            current    = getattr(self.app, "_numeric_current", {}).get(self.code["id"], None)
            init_val   = current if current is not None else default
            is_applied = self.app.applied.get(self.code["id"], False)

            self._num_var = tk.StringVar(value=str(init_val))

            # ON/OFF toggle
            self.toggle_btn = tk.Button(
                top, text="ON" if is_applied else "OFF", width=5, font=FONT_TINY,
                fg=GREEN if is_applied else "#bbbbbb",
                bg="#2a5a2a" if is_applied else "#1a1a1a",
                activeforeground=GREEN, activebackground="#2a4a1a",
                relief="flat", bd=0,
                highlightthickness=1,
                highlightbackground=GREEN if is_applied else "#555",
                cursor="hand2",
                command=self._on_toggle
            )
            self.toggle_btn.pack(side="left", padx=(0, 6))

            # field + Apply on right
            num_frame = tk.Frame(top, bg=BG_ROW)
            num_frame.pack(side="right", padx=(4, 0))

            num_entry = tk.Entry(
                num_frame, textvariable=self._num_var,
                font=FONT_SMALL, fg=ACCENT2 if is_applied else MUTED,
                bg="#1a1a1a", insertbackground=ACCENT2,
                relief="flat", bd=0,
                highlightthickness=1, highlightbackground=BORDER,
                width=7, justify="center",
                state="normal" if is_applied else "disabled"
            )
            num_entry.pack(side="left", ipady=3, padx=(0, 4))
            self.app._add_paste_menu(num_entry)
            self._num_entry_ref = num_entry  # save ref for refresh

            tk.Button(
                num_frame, text="Apply",
                font=FONT_TINY, fg=GREEN, bg="#1a2a0a",
                activeforeground=GREEN, activebackground="#2a4a1a",
                relief="flat", bd=0, cursor="hand2",
                highlightthickness=1, highlightbackground="#2a5a2a",
                command=self._on_numeric_apply
            ).pack(side="left", padx=(0, 2), ipady=2, ipadx=4)

        # ── expand arrow (only if notes) ──
        if notes:
            self.arrow_btn = tk.Button(
                top, text="▼", width=3, font=FONT_SMALL,
                fg=ACCENT, bg=BG_ROW,
                activeforeground=ACCENT2, activebackground=BG_ROW,
                relief="flat", bd=0, cursor="hand2",
                command=self._toggle_notes
            )
            self.arrow_btn.pack(side="right", padx=4)

        # ── notes frame ──
        self.notes_frame = tk.Frame(self, bg="#0d0d00")
        for note in notes:
            txt = note if CURRENT_LANG == "en" else fix_ar(note)
            tk.Label(
                self.notes_frame, text=txt,
                font=FONT_TINY, fg="#ffcc66", bg="#0d0d00",
                anchor="w", justify="left"
            ).pack(anchor="w", padx=8, pady=1)

    def _on_numeric_apply(self):
        """Called when Apply button is pressed on an inline numeric input code."""
        code_id = self.code["id"]

        # check if any active code has this code in its mutex list
        for other_id, conflicts in self.app.OFFSET_MUTEX.items():
            if code_id in conflicts and self.app.applied.get(other_id, False):
                other_name = self.app.code_by_id.get(other_id, {}).get(
                    "name_en" if CURRENT_LANG == "en" else "name", other_id)
                messagebox.showwarning(
                    "Code Locked" if CURRENT_LANG == "en" else "الكود مقفل",
                    ("This code is disabled while '" + other_name + "' is ON.\n"
                     "Turn it OFF first.")
                    if CURRENT_LANG == "en" else
                    ("هذا الكود مقفل لأن '" + other_name + "' شغال.\n"
                     "أطفيه أول.")
                )
                return

        if not self.app._is_unlocked(code_id):
            missing = self.app._get_missing_requires(code_id)
            if missing:
                msg = ("You need to enable the following codes first:\n\n"
                       if CURRENT_LANG == "en" else
                       "لازم تشغل الأكواد التالية أول:\n\n")
                for dep_id, dep_name, sec_label in missing:
                    msg += "  - " + dep_name + "\n"
                    msg += ("    (Found in: " + sec_label + ")\n"
                            if CURRENT_LANG == "en" else
                            "    (تجده في قسم: " + sec_label + ")\n")
                messagebox.showwarning(
                    "Code Locked" if CURRENT_LANG == "en" else "الكود مقفل", msg)
            return
        # for numeric_with_toggle: only apply value if code is ON
        if self.code.get("dialog") == "numeric_with_toggle":
            if not self.app.applied.get(code_id, False):
                messagebox.showwarning(
                    "Code is OFF" if CURRENT_LANG == "en" else "الكود طافي",
                    "Turn ON the code first before setting a value."
                    if CURRENT_LANG == "en" else
                    "شغّل الكود أولاً قبل ما تحدد القيمة."
                )
                return
        offset     = entry_data.get("offset", "")
        byte_count = entry_data.get("byte_count", 1)
        divide_by  = entry_data.get("divide_by", 1)
        try:
            dec_val = int(self._num_var.get().strip())
            if dec_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive number.")
            return
        actual_val = dec_val // divide_by if divide_by > 1 else dec_val
        hex_bytes  = actual_val.to_bytes(byte_count, byteorder="little").hex().upper()

        # apply any prerequisite patches (e.g. ON patch for random_ptas)
        patches = entry_data.get("patches", [])
        if patches:
            ok, msg = apply_patch(exe, code_id, self.app.codes_data)
            if not ok:
                messagebox.showerror("Error", msg)
                return

        try:
            with open(exe, "r+b") as f:
                off = int(offset, 16)
                f.seek(off)
                orig = f.read(byte_count)
                backup = load_patch_backup()
                backup.setdefault(code_id, {})[offset.upper().lstrip("0") or "0"] = orig.hex().upper()
                save_patch_backup(backup)
                f.seek(off)
                f.write(bytes.fromhex(hex_bytes))
        except Exception as ex:
            messagebox.showerror("Error", str(ex))
            return
        self.app.applied[code_id] = True
        name = self.code.get("name_en" if CURRENT_LANG == "en" else "name", code_id)
        write_log("APPLIED", name + " = " + str(dec_val), exe)
        if not APP_SETTINGS.get("silent_apply", False):
            messagebox.showinfo("[+] Applied", name + "\nValue: " + str(dec_val))
        self.app._after_state_change()

    def _toggle_notes(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.notes_frame.pack(fill="x")
            self.arrow_btn.configure(text="▲")
        else:
            self.notes_frame.pack_forget()
            self.arrow_btn.configure(text="▼")

    def _on_toggle(self):
        self.app.handle_toggle(self.code["id"])

    def _on_select(self):
        if self.sel_var.get() == 1 and not self.app._is_unlocked(self.code["id"]):
            self.sel_var.set(0)
            self.app.handle_toggle(self.code["id"])
            return
        self.selected = bool(self.sel_var.get())
        # sync with global selection
        if self.selected:
            self.app._global_selected.add(self.code["id"])
        else:
            self.app._global_selected.discard(self.code["id"])
        self.app.on_row_select_change()

    def refresh(self, applied, locked, detected):
        if detected and not applied:
            applied = True

        is_numeric  = self.code.get("dialog") == "numeric_input"
        is_dropdown = self.code.get("dialog") in (
            "dropdown", "punisher_pierce", "luis_cabin",
            "link_tweaks", "memory_alloc"
        )
        # punisher_pierce uses Change button but NOT inline numeric
        if self.code.get("dialog") == "punisher_pierce":
            is_numeric = False

        # for numeric codes: check if any active code blocks this one
        mutex_locked = False
        if is_numeric:
            for other_id, conflicts in self.app.OFFSET_MUTEX.items():
                if self.code["id"] in conflicts and self.app.applied.get(other_id, False):
                    mutex_locked = True
                    break

        has_arrow = hasattr(self, "arrow_btn")
        has_num   = hasattr(self, "_num_var")

        # ── dropdown (Change button) ──────────────────────────────────────────
        if is_dropdown:
            if applied:
                bg = BG_ROW_ON
                self.configure(bg=bg, highlightbackground=BORDER_ON)
                self.toggle_btn.configure(
                    text="Change", fg=GREEN, bg="#2a5a2a",
                    highlightbackground=GREEN, state="normal"
                )
                self.name_lbl.configure(fg="#e8e0c0", bg=bg, font=FONT_BOLD)
                self.desc_lbl.configure(bg=bg)
            else:
                bg = BG_ROW
                self.configure(bg=bg, highlightbackground=BORDER)
                self.toggle_btn.configure(
                    text="Change", fg=ACCENT2, bg="#1a1a2a",
                    highlightbackground="#445", state="normal"
                )
                self.name_lbl.configure(fg=TEXT_MAIN, bg=bg, font=FONT_NORMAL)
                self.desc_lbl.configure(bg=bg)
            self.status_lbl.configure(bg=bg)
            if has_arrow:
                self.arrow_btn.configure(bg=bg, activebackground=bg)
            return

        is_num_tog  = self.code.get("dialog") == "numeric_with_toggle"

        # update numeric field state
        if has_num and not is_num_tog:
            if mutex_locked:
                self.configure(bg=BG_ROW_LK, highlightbackground=BORDER_LK)
                self.name_lbl.configure(fg=TEXT_LOCK, bg=BG_ROW_LK)
                self.desc_lbl.configure(bg=BG_ROW_LK)
                if has_arrow:
                    self.arrow_btn.configure(bg=BG_ROW_LK, activebackground=BG_ROW_LK)
            else:
                bg = BG_ROW
                self.configure(bg=bg, highlightbackground=BORDER)
                self.name_lbl.configure(fg="#f0e0c0", bg=bg, font=FONT_NORMAL)
                self.desc_lbl.configure(bg=bg)
                if has_arrow:
                    self.arrow_btn.configure(bg=bg, activebackground=bg)
            return

        # numeric_with_toggle: update ON/OFF button + field enable state
        if has_num and is_num_tog:
            bg = BG_ROW_ON if applied else BG_ROW
            self.configure(bg=bg, highlightbackground=BORDER_ON if applied else BORDER)
            self.toggle_btn.configure(
                text="ON" if applied else "OFF",
                fg=GREEN if applied else "#bbbbbb",
                bg="#2a5a2a" if applied else "#1a1a1a",
                highlightbackground=GREEN if applied else "#555"
            )
            self.name_lbl.configure(fg="#e8e0c0" if applied else TEXT_MAIN,
                                    bg=bg, font=FONT_BOLD if applied else FONT_NORMAL)
            self.desc_lbl.configure(bg=bg)
            if has_arrow:
                self.arrow_btn.configure(bg=bg, activebackground=bg)
            if hasattr(self, "_num_entry_ref"):
                self._num_entry_ref.configure(
                    state="normal" if applied else "disabled",
                    fg=ACCENT2 if applied else MUTED
                )
            return

        # checkbox: disabled if locked or already applied
        if locked or applied:
            self.sel_chk.configure(state="disabled")
            self.sel_var.set(0)
            self.selected = False
        else:
            self.sel_chk.configure(state="normal")

        if locked and applied:
            bg = "#0d1a0a"
            self.configure(bg=bg, highlightbackground="#1a4a1a")
            self.toggle_btn.configure(
                text="ON", fg="#3a9a3a", bg="#1a2a1a",
                highlightbackground="#2a5a2a", state="normal"
            )
            self.status_var.set("[L]")
            self.status_lbl.configure(fg="#c85a2a", bg=bg)
            self.name_lbl.configure(fg="#a0c0a0", bg=bg, font=FONT_BOLD)
            self.desc_lbl.configure(bg=bg)
            self.sel_chk.configure(bg=bg, activebackground=bg)
            if has_arrow:
                self.arrow_btn.configure(bg=bg, activebackground=bg)

        elif locked:
            bg = BG_ROW_LK
            self.configure(bg=bg, highlightbackground=BORDER_LK)
            self.toggle_btn.configure(
                text="OFF", fg=TEXT_LOCK, bg="#1a1a1a",
                highlightbackground="#333", state="normal"  # keep enabled to show message
            )
            self.status_var.set("[L]")
            self.status_lbl.configure(fg="#c85a2a", bg=bg)
            self.name_lbl.configure(fg=TEXT_LOCK, bg=bg, font=FONT_NORMAL)
            self.desc_lbl.configure(bg=bg)
            self.sel_chk.configure(bg=bg, activebackground=bg)
            if has_arrow:
                self.arrow_btn.configure(bg=bg, activebackground=bg)
            self.notes_frame.configure(bg="#0d0d00")

        elif applied:
            bg = BG_ROW_ON
            self.configure(bg=bg, highlightbackground=BORDER_ON)
            self.toggle_btn.configure(
                text="ON", fg=GREEN, bg="#2a5a2a",
                highlightbackground=GREEN, state="normal"
            )
            self.status_var.set("")
            self.status_lbl.configure(fg=MUTED, bg=bg)
            self.name_lbl.configure(fg="#e8e0c0", bg=bg, font=FONT_BOLD)
            self.desc_lbl.configure(bg=bg)
            self.sel_chk.configure(bg=bg, activebackground=bg)
            if has_arrow:
                self.arrow_btn.configure(bg=bg, activebackground=bg)

        else:
            bg = BG_ROW_SEL if self.selected else BG_ROW
            border = BORDER_SEL if self.selected else BORDER
            self.configure(bg=bg, highlightbackground=border)
            self.toggle_btn.configure(
                text="OFF", fg=MUTED, bg="#1a1a1a",
                highlightbackground="#444", state="normal"
            )
            self.status_var.set("")
            self.status_lbl.configure(fg=MUTED, bg=bg)
            self.name_lbl.configure(fg=TEXT_MAIN, bg=bg, font=FONT_NORMAL)
            self.desc_lbl.configure(bg=bg)
            self.sel_chk.configure(bg=bg, activebackground=bg)
            if has_arrow:
                self.arrow_btn.configure(bg=bg, activebackground=bg)


# ═════════════════════════════════════════════════════════════════════════════
#  SidebarItem
# ═════════════════════════════════════════════════════════════════════════════

class SidebarItem(tk.Frame):
    def __init__(self, parent, section, app, **kw):
        super().__init__(parent, bg=BG_SIDEBAR, **kw)
        self.section = section
        self.app     = app

        self.indicator = tk.Frame(self, bg=BG_SIDEBAR, width=3)
        self.indicator.pack(side="left", fill="y")

        label = section.get("label_en", section["label"]) if CURRENT_LANG == "en" else section["label"]
        self.btn = tk.Button(
            self, text=label,
            font=FONT_SMALL, fg="#cccccc", bg=BG_SIDEBAR,
            activeforeground=ACCENT2, activebackground="#1a1200",
            anchor="w", relief="flat", bd=0, cursor="hand2",
            command=lambda: app.select_section(section["id"])
        )
        self.btn.pack(side="left", fill="x", expand=True, ipady=6)

    def set_active(self, active):
        if active:
            self.btn.configure(fg=ACCENT2, bg="#1a1200",
                               activebackground="#1a1200")
            self.indicator.configure(bg=ACCENT)
        else:
            self.btn.configure(fg="#cccccc", bg=BG_SIDEBAR,
                               activebackground="#1a1200")
            self.indicator.configure(bg=BG_SIDEBAR)


# ═════════════════════════════════════════════════════════════════════════════
#  Main App
# ═════════════════════════════════════════════════════════════════════════════

class RE4PatcherApp(tk.Frame):
    """
    RE4 Code Manager.
    Can run embedded inside RE4MasterEditor (master != None)
    or standalone (master == None, creates its own Tk root).
    """

    def __init__(self, master=None, embedded=False, shared_exe_var=None):
        global CURRENT_LANG
        CURRENT_LANG = MASTER_SETTINGS.get("lang", APP_SETTINGS.get("lang", "en"))

        if embedded and master is not None:
            # embedded mode — runs as Frame inside master
            super().__init__(master, bg=BG_MAIN)
            self.exe_path = shared_exe_var if shared_exe_var else tk.StringVar()
            self._embedded = True
        else:
            # standalone mode — create a Tk root
            self._root = tk.Tk()
            self._root.title("RE4 Code Manager")
            self._root.geometry("1000x680")
            self._root.minsize(820, 560)
            self._root.configure(bg=BG_MAIN)
            super().__init__(self._root, bg=BG_MAIN)
            self.pack(fill="both", expand=True)
            self.exe_path = tk.StringVar()
            self._embedded = False

        self.scanned          = False
        self.detected         = {}
        self.applied          = {}
        self.active_section   = None
        self._global_selected = set()

        self.codes_info = load_json(INFO_FILE)
        self.codes_data = load_json(DATA_FILE)

        self.sections_list    = self.codes_info["sections"]
        self.all_codes        = self.codes_info["codes"]
        self.code_by_id       = {c["id"]: c for c in self.all_codes}
        self.codes_by_section = {}
        for c in self.all_codes:
            self.codes_by_section.setdefault(c["section"], []).append(c)

        self._build_ui()
        self.select_section(self.sections_list[0]["id"])
        self.status_total_var.set(
            ("Total codes: " if CURRENT_LANG == "en" else "إجمالي الأكواد: ")
            + str(len(self.all_codes))
        )

        if not embedded:
            if APP_SETTINGS.get("remember_exe", True):
                last = APP_SETTINGS.get("last_exe", "")
                if last and os.path.isfile(last):
                    self.exe_path.set(last)
                    if APP_SETTINGS.get("auto_scan_startup", False):
                        self._root.after(300, self._scan)

        self._first_scan_done = False
        self.exe_path.trace_add("write", self._on_exe_path_change)

    def mainloop(self):
        """Run standalone."""
        if not self._embedded:
            self._root.mainloop()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # top bar
        topbar = tk.Frame(self, bg=BG_TOPBAR)
        topbar.pack(fill="x")
        make_label(topbar, "RE4 Code Manager",
                   fg=ACCENT2, bg=BG_TOPBAR, font=FONT_TITLE
                   ).pack(side="left", padx=14, pady=6)
        make_button(topbar, "Settings", self._open_settings,
                    fg=ACCENT, bg=BG_TOPBAR, active_bg="#1a1200",
                    font=FONT_TINY, width=8
                    ).pack(side="right", padx=4)

        # exe path row (hidden when embedded — master provides exe path)
        path_bar = tk.Frame(self, bg=BG_PATHBAR)
        self.path_bar = path_bar
        if not self._embedded:
            path_bar.pack(fill="x")
        else:
            # embedded: show compact scan-only bar
            scan_bar = tk.Frame(self, bg="#0e0e0e")
            scan_bar.pack(fill="x")
            tk.Button(scan_bar, text="  SCAN EXE  ",
                      font=("Courier New", 10, "bold"),
                      fg="#0a0a0a", bg="#7cfc7c",
                      activeforeground="#0a0a0a", activebackground="#5cdc5c",
                      relief="flat", bd=0, cursor="hand2",
                      highlightthickness=0,
                      command=self._scan, padx=16, pady=5
                      ).pack(side="left", padx=10, pady=6)
            self._scan_status = tk.StringVar(value="")
            tk.Label(scan_bar, textvariable=self._scan_status,
                     fg="#555", bg="#0e0e0e",
                     font=("Courier New", 8)).pack(side="left", padx=8)
        make_label(path_bar, "Game Executable (bio4.exe):",
                   fg=TEXT_DIM, bg=BG_PATHBAR
                   ).pack(side="left", padx=(12, 6), pady=5)
        self.path_entry = tk.Entry(
            path_bar, textvariable=self.exe_path,
            font=FONT_SMALL, fg="#7cfc7c", bg="#0d1a0d",
            insertbackground="#7cfc7c",
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#2a5a2a",
            width=48
        )
        self.path_entry.pack(side="left", pady=5, ipady=3)
        self._add_paste_menu(self.path_entry)

        make_button(path_bar, "Browse...", self._browse,
                    fg=ACCENT, bg="#2a2a1a", active_bg="#3a3a2a", width=9
                    ).pack(side="left", padx=6, pady=5)
        self.scan_btn = make_button(
            path_bar, "Scan EXE", self._scan,
            fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=9
        )
        self.scan_btn.pack(side="left", padx=2, pady=5)
        self.scan_status_var = tk.StringVar(value="")
        make_label(path_bar, fg=GREEN, bg=BG_PATHBAR, font=FONT_TINY,
                   textvariable=self.scan_status_var
                   ).pack(side="left", padx=8)

        # notice bar
        self.notice = tk.Frame(self, bg=BG_NOTICE)
        make_label(
            self.notice,
            fix_ar("[!] حط مسار bio4.exe واضغط Scan عشان تشوف وتفعل الاكواد")
            if CURRENT_LANG == "ar" else
            "[!] Select bio4.exe path and press Scan EXE to view and apply codes",
            fg=ACCENT, bg=BG_NOTICE
        ).pack(side="left", padx=10, pady=4)
        self.notice.pack(fill="x")

        # main body
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(fill="both", expand=True)

        # sidebar
        sidebar_outer = tk.Frame(body, bg=BG_SIDEBAR, width=210)
        sidebar_outer.pack(side="left", fill="y")
        sidebar_outer.pack_propagate(False)

        sb_canvas = tk.Canvas(sidebar_outer, bg=BG_SIDEBAR,
                              highlightthickness=0, width=210)
        sb_scroll = tk.Scrollbar(sidebar_outer, orient="vertical",
                                 command=sb_canvas.yview)
        sb_canvas.configure(yscrollcommand=sb_scroll.set)
        sb_scroll.pack(side="right", fill="y")
        sb_canvas.pack(side="left", fill="both", expand=True)

        self.sidebar_inner = tk.Frame(sb_canvas, bg=BG_SIDEBAR)
        sb_canvas.create_window((0, 0), window=self.sidebar_inner, anchor="nw")
        self.sidebar_inner.bind(
            "<Configure>",
            lambda e: sb_canvas.configure(
                scrollregion=sb_canvas.bbox("all"))
        )

        self.sidebar_items = {}
        for sec in self.sections_list:
            item = SidebarItem(self.sidebar_inner, sec, self)
            item.pack(fill="x")
            self.sidebar_items[sec["id"]] = item

        # right panel
        right = tk.Frame(body, bg=BG_PANEL)
        right.pack(side="left", fill="both", expand=True)

        # section header
        sec_header = tk.Frame(right, bg=BG_HEADER)
        sec_header.pack(fill="x")
        self.section_title_var = tk.StringVar(value="")
        make_label(sec_header, fg=ACCENT2, bg=BG_HEADER,
                   font=("Courier New", 14, "bold"),
                   textvariable=self.section_title_var
                   ).pack(side="left", padx=14, pady=6)
        self.section_count_var = tk.StringVar(value="")
        make_label(sec_header, fg=MUTED, bg=BG_HEADER, font=FONT_TINY,
                   textvariable=self.section_count_var
                   ).pack(side="left", pady=6)

        # search bar
        search_bar = tk.Frame(right, bg=BG_PATHBAR)
        search_bar.pack(fill="x", padx=10, pady=(6, 0))
        make_label(search_bar, text="Search:", fg=TEXT_DIM, bg=BG_PATHBAR,
                   font=FONT_TINY).pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_bar, textvariable=self.search_var,
            font=FONT_SMALL, fg=ACCENT2, bg="#1a1a1a",
            insertbackground=ACCENT2,
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER,
            width=30
        )
        self.search_entry.pack(side="left", ipady=3)
        self.search_var.trace_add("write", lambda *_: self._on_search())
        make_button(search_bar, "X", self._clear_search,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a",
                    font=FONT_TINY, width=2
                    ).pack(side="left", padx=4)

        # search results frame (hidden by default) — with scrollable canvas
        self.search_results_outer = tk.Frame(right, bg="#0d0d1a",
                                             highlightthickness=1,
                                             highlightbackground="#2a2a5a")
        self.search_results_canvas = tk.Canvas(self.search_results_outer,
                                               bg="#0d0d1a", highlightthickness=0,
                                               height=180)
        sr_scroll = tk.Scrollbar(self.search_results_outer, orient="vertical",
                                 command=self.search_results_canvas.yview)
        self.search_results_canvas.configure(yscrollcommand=sr_scroll.set)
        sr_scroll.pack(side="right", fill="y")
        self.search_results_canvas.pack(side="left", fill="both", expand=True)

        self.search_results_frame = tk.Frame(self.search_results_canvas, bg="#0d0d1a")
        self._sr_win = self.search_results_canvas.create_window(
            (0, 0), window=self.search_results_frame, anchor="nw"
        )
        self.search_results_frame.bind(
            "<Configure>",
            lambda e: self.search_results_canvas.configure(
                scrollregion=self.search_results_canvas.bbox("all"))
        )

        codes_outer = tk.Frame(right, bg=BG_PANEL)
        codes_outer.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        self.codes_canvas = tk.Canvas(codes_outer, bg=BG_PANEL,
                                      highlightthickness=0)
        codes_scroll = tk.Scrollbar(codes_outer, orient="vertical",
                                    command=self.codes_canvas.yview)
        self.codes_canvas.configure(yscrollcommand=codes_scroll.set)
        codes_scroll.pack(side="right", fill="y")
        self.codes_canvas.pack(side="left", fill="both", expand=True)

        self.codes_inner = tk.Frame(self.codes_canvas, bg=BG_PANEL)
        self._codes_win = self.codes_canvas.create_window(
            (0, 0), window=self.codes_inner, anchor="nw"
        )
        self.codes_inner.bind(
            "<Configure>",
            lambda e: self.codes_canvas.configure(
                scrollregion=self.codes_canvas.bbox("all"))
        )
        self.codes_canvas.bind(
            "<Configure>",
            lambda e: self.codes_canvas.itemconfig(
                self._codes_win, width=e.width)
        )

        # smart mousewheel: scroll whichever pane the cursor is over
        def _on_mousewheel(e):
            x, y = e.x_root, e.y_root
            try:
                sr = self.search_results_canvas
                if self.search_results_outer.winfo_ismapped():
                    sx, sy = sr.winfo_rootx(), sr.winfo_rooty()
                    if sx <= x <= sx + sr.winfo_width() and sy <= y <= sy + sr.winfo_height():
                        sr.yview_scroll(int(-1 * (e.delta / 120)), "units")
                        return
            except Exception:
                pass
            self.codes_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        self.bind_all("<MouseWheel>", _on_mousewheel)

        # Apply Selected bar
        apply_bar = tk.Frame(right, bg=BG_APPLY,
                             highlightthickness=1,
                             highlightbackground="#2a4a2a")
        apply_bar.pack(fill="x", padx=10, pady=6)

        self.selected_count_var = tk.StringVar(value="0 selected")
        make_label(apply_bar, fg=MUTED, bg=BG_APPLY, font=FONT_TINY,
                   textvariable=self.selected_count_var
                   ).pack(side="left", padx=10, pady=6)

        make_button(apply_bar, "Select All", self._select_all,
                    fg=ACCENT, bg="#2a2a0a", active_bg="#3a3a1a", width=10
                    ).pack(side="left", padx=4, pady=4)
        make_button(apply_bar, "Clear", self._clear_selection,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=8
                    ).pack(side="left", padx=4, pady=4)
        self.apply_btn = make_button(
            apply_bar, "Apply Selected", self._apply_selected,
            fg=GREEN, bg="#1a3a1a", active_bg="#2a5a2a", width=14
        )
        self.apply_btn.pack(side="right", padx=10, pady=4)

        # status bar
        statusbar = tk.Frame(self, bg=BG_STATUS, height=24)
        statusbar.pack(fill="x")
        statusbar.pack_propagate(False)

        self.status_applied_var  = tk.StringVar(value="Applied: 0" if CURRENT_LANG == "en" else "مفعّل: 0")
        self.status_detected_var = tk.StringVar(value="Detected: 0" if CURRENT_LANG == "en" else "مكتشف: 0")
        self.status_exe_var      = tk.StringVar(value="")
        self.status_total_var    = tk.StringVar(value="Total codes: 0" if CURRENT_LANG == "en" else "إجمالي الأكواد: 0")

        make_label(statusbar, fg=MUTED, bg=BG_STATUS, font=FONT_TINY,
                   textvariable=self.status_applied_var
                   ).pack(side="left", padx=12)
        make_label(statusbar, fg=MUTED, bg=BG_STATUS, font=FONT_TINY,
                   textvariable=self.status_detected_var
                   ).pack(side="left", padx=8)
        make_label(statusbar, fg=GREEN, bg=BG_STATUS, font=FONT_TINY,
                   textvariable=self.status_exe_var
                   ).pack(side="left", padx=8)
        make_label(statusbar, fg=MUTED, bg=BG_STATUS, font=FONT_TINY,
                   textvariable=self.status_total_var
                   ).pack(side="right", padx=12)

        self.code_rows = {}

    # ── logic ─────────────────────────────────────────────────────────────────

    # ── Best Settings preset ─────────────────────────────────────────────────
    BEST_SETTINGS = [
        "pointer_edit",
        "sanity_check",
        "aev_type6",
        "aev_fse",
        "aev_ese",
        "aev_auto_door",
        "aev_cam",
        "aev_checkpoint",
        "aev_chain",
        "aev_osd",
        "aev_auto_type5",
        "aev_option",
        "aev_ita",
        "aev_ear",
        "aev_timer",
        "etm_lever",
        "spawn_enemies",
        "em_ita_preload",
        "rsert_order",
        "loot_no_disappear",
        "u3_esl",
        "regen_esl",
        "merchant_init",
        "em_incompat_fix",
        "fix_r100_crash",
        "fix_r101_disappear",
        "grey_screen_fix",
    ]

    def _apply_best_settings(self):
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return
        if not self.scanned:
            messagebox.showerror("Error", "Please Scan the EXE first.")
            return

        # Build queue in exact order, skip already applied
        queue = [cid for cid in self.BEST_SETTINGS
                 if not self.applied.get(cid, False)]

        if not queue:
            messagebox.showinfo("Best Settings", "All recommended codes are already applied.")
            return

        names = "\n".join("  - " + self.code_by_id.get(c, {}).get("name", c)
                          for c in queue)
        if not messagebox.askyesno("Best Settings",
                                   "Apply the following codes in order?\n\n" + names):
            return

        # Apply one by one in exact order to respect dependencies
        success, failed = [], []
        for cid in queue:
            ok, msg = apply_patch(exe, cid, self.codes_data)
            if ok:
                self.applied[cid] = True
                success.append(cid)
            else:
                failed.append((cid, msg))
                # stop on first failure — later codes may depend on this one
                break

        summary = "Applied " + str(len(success)) + " code(s) successfully."
        if failed:
            summary += "\n\nStopped at:\n"
            for cid, err in failed:
                summary += "- " + self.code_by_id.get(cid, {}).get("name", cid)
                summary += "\n  " + err + "\n"
            messagebox.showwarning("Done with errors", summary)
        else:
            messagebox.showinfo("[+] Done", summary)

        self._after_state_change()

    def _open_settings(self):
        global CURRENT_LANG
        dlg = tk.Toplevel(self)
        dlg.title("Settings")
        dlg.geometry("320x480")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        # Language and Remember EXE handled by Master Editor settings

        # Behavior toggles
        make_label(dlg,
                   "Behavior" if CURRENT_LANG == "en" else "الإعدادات",
                   fg=ACCENT2, bg="#111", font=FONT_SMALL
                   ).pack(pady=(14, 6))

        def make_toggle(label_en, label_ar, key):
            var = tk.BooleanVar(value=APP_SETTINGS.get(key, True))
            row = tk.Frame(dlg, bg="#111")
            row.pack(fill="x", padx=20, pady=2)
            tk.Checkbutton(
                row, text=label_en if CURRENT_LANG == "en" else label_ar,
                variable=var, font=FONT_TINY,
                fg=TEXT_MAIN, bg="#111",
                activebackground="#111", selectcolor="#1a1a1a",
                relief="flat",
                command=lambda k=key, v=var: (
                    APP_SETTINGS.update({k: v.get()}),
                    save_settings(APP_SETTINGS)
                )
            ).pack(side="left")

        make_toggle("Silent Apply (no confirmation popup)",
                    "تطبيق صامت (بدون رسالة تأكيد)",
                    "silent_apply")
        def on_startup_toggle():
            val = APP_SETTINGS.get("auto_scan_startup", False)
            if val:
                # startup on → disable change scan
                APP_SETTINGS["auto_scan_change"] = False
                save_settings(APP_SETTINGS)

        make_toggle("Auto Scan on Startup",
                    "مسح تلقائي عند فتح الأداة",
                    "auto_scan_startup")

        make_toggle("Auto Scan when EXE changes",
                    "مسح تلقائي عند تغيير EXE",
                    "auto_scan_change")

        make_label(dlg, "Profiles",
                   fg=ACCENT2, bg="#111", font=FONT_SMALL
                   ).pack(pady=(4, 6))

        prof_row = tk.Frame(dlg, bg="#111")
        prof_row.pack()
        make_button(prof_row, "New Profile", lambda: [dlg.destroy(), self._new_profile()],
                    fg=ACCENT, bg="#2a2a0a", active_bg="#3a3a1a", width=12
                    ).pack(side="left", padx=6)
        make_button(prof_row, "Load Profile", lambda: [dlg.destroy(), self._load_profile()],
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=12
                    ).pack(side="left", padx=6)

        # separator
        tk.Frame(dlg, bg="#333", height=1).pack(fill="x", padx=20, pady=6)

        # Add New Code
        make_label(dlg, "Custom Codes",
                   fg=ACCENT2, bg="#111", font=FONT_SMALL
                   ).pack(pady=(4, 6))
        make_button(dlg, "Add New Code", lambda: [dlg.destroy(), self._add_new_code()],
                    fg=ACCENT2, bg="#1a1a2a", active_bg="#2a2a3a", width=14
                    ).pack(pady=(0, 6))

        # separator
        tk.Frame(dlg, bg="#333", height=1).pack(fill="x", padx=20, pady=6)

        # EXE Analysis
        make_label(dlg,
                   "EXE Analysis" if CURRENT_LANG == "en" else "تحليل EXE",
                   fg=ACCENT2, bg="#111", font=FONT_SMALL
                   ).pack(pady=(4, 6))

        cmp_row = tk.Frame(dlg, bg="#111")
        cmp_row.pack()
        make_button(cmp_row, "Compare Two EXEs",
                    lambda: [dlg.destroy(), self._compare_two_exes()],
                    fg=ACCENT, bg="#2a2a0a", active_bg="#3a3a1a", width=16
                    ).pack(side="left", padx=4)
        make_button(cmp_row, "Compare with Original",
                    lambda: [dlg.destroy(), self._compare_with_original()],
                    fg="#60c8ff", bg="#0a1a2a", active_bg="#1a2a3a", width=18
                    ).pack(side="left", padx=4)

        # separator
        tk.Frame(dlg, bg="#333", height=1).pack(fill="x", padx=20, pady=6)

        # View Log
        make_label(dlg,
                   "Log" if CURRENT_LANG == "en" else "السجل",
                   fg=ACCENT2, bg="#111", font=FONT_SMALL
                   ).pack(pady=(4, 4))
        make_button(dlg,
                    "View Log" if CURRENT_LANG == "en" else "عرض السجل",
                    lambda: [dlg.destroy(), self._view_log()],
                    fg=ACCENT2, bg="#1a2a0a", active_bg="#2a4a1a", width=14
                    ).pack(pady=(0, 6))

        # Restore Original EXE
        make_label(dlg,
                   "Restore Original EXE" if CURRENT_LANG == "en" else "استعادة الملف الأصلي",
                   fg="#e8c060", bg="#111", font=FONT_SMALL
                   ).pack(pady=(4, 4))
        make_button(dlg,
                    "Restore from bio4_original.exe" if CURRENT_LANG == "en" else "استعادة من bio4_original.exe",
                    lambda: [dlg.destroy(), self._restore_original_exe()],
                    fg="#e8c060", bg="#1a1500", active_bg="#2a2000", width=26
                    ).pack(pady=(0, 6))

        # separator
        tk.Frame(dlg, bg="#333", height=1).pack(fill="x", padx=20, pady=6)

        # Reset All
        make_label(dlg,
                   "Reset All Codes" if CURRENT_LANG == "en" else "إعادة تعيين كل الأكواد",
                   fg="#ff6060", bg="#111", font=FONT_SMALL
                   ).pack(pady=(4, 6))
        make_button(dlg,
                    "Reset All" if CURRENT_LANG == "en" else "إعادة تعيين",
                    lambda: [dlg.destroy(), self._reset_all_codes()],
                    fg="#ff6060", bg="#2a0a0a", active_bg="#3a1010", width=14
                    ).pack(pady=(0, 10))

    # ── EXE Comparison ────────────────────────────────────────────────────────

    def _show_report(self, title, report):
        """Show report in a scrollable window and offer to save."""
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.geometry("700x500")
        dlg.configure(bg="#111")

        txt_frame = tk.Frame(dlg, bg="#111")
        txt_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        txt = tk.Text(txt_frame, font=("Courier New", 9),
                      fg="#c8c8c8", bg="#0d0d0d",
                      relief="flat", bd=0,
                      highlightthickness=1, highlightbackground=BORDER,
                      wrap="none")
        sc_y = tk.Scrollbar(txt_frame, orient="vertical", command=txt.yview)
        sc_x = tk.Scrollbar(dlg, orient="horizontal", command=txt.xview)
        txt.configure(yscrollcommand=sc_y.set, xscrollcommand=sc_x.set)
        sc_y.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        sc_x.pack(fill="x", padx=10, pady=(0, 4))

        txt.insert("1.0", report)
        txt.configure(state="disabled")

        btn_row = tk.Frame(dlg, bg="#111")
        btn_row.pack(pady=6)

        def save_report():
            from tkinter import filedialog as fd
            path = fd.asksaveasfilename(
                title="Save Report",
                defaultextension=".txt",
                filetypes=[("Text file", "*.txt"), ("All files", "*.*")]
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(report)
                messagebox.showinfo("Saved", "Report saved:\n" + path)

        make_button(btn_row, "Save Report", save_report,
                    fg=ACCENT, bg="#2a2a1a", active_bg="#3a3a2a", width=12
                    ).pack(side="left", padx=8)
        make_button(btn_row, "Close", dlg.destroy,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=8
                    ).pack(side="left", padx=4)

    def _scan_codes_in_file(self, path):
        """Run scan_exe on a given path and return {code_id: bool}."""
        return scan_exe(path, self.codes_info, self.codes_data)

    def _build_codes_report(self, results_a, results_b, label_a, label_b):
        """Compare two scan results and build a readable report."""
        lines = []
        lines.append("=" * 60)
        lines.append("  " + label_a + "  vs  " + label_b)
        lines.append("=" * 60)

        only_a, only_b, both_on, both_off = [], [], [], []

        all_ids = sorted(set(list(results_a.keys()) + list(results_b.keys())))
        for cid in all_ids:
            a = results_a.get(cid, False)
            b = results_b.get(cid, False)
            code = self.code_by_id.get(cid, {})
            name = code.get("name_en" if CURRENT_LANG == "en" else "name", cid)
            if a and not b:
                only_a.append(name)
            elif b and not a:
                only_b.append(name)
            elif a and b:
                both_on.append(name)
            else:
                both_off.append(name)

        if only_a:
            lines.append("\n[ON in " + label_a + " only]  (" + str(len(only_a)) + " codes)")
            for n in only_a:
                lines.append("  + " + n)

        if only_b:
            lines.append("\n[ON in " + label_b + " only]  (" + str(len(only_b)) + " codes)")
            for n in only_b:
                lines.append("  + " + n)

        if both_on:
            lines.append("\n[ON in both]  (" + str(len(both_on)) + " codes)")
            for n in both_on:
                lines.append("  = " + n)

        lines.append("\n[OFF in both]  (" + str(len(both_off)) + " codes)")
        for n in both_off:
            lines.append("  - " + n)

        lines.append("\n" + "=" * 60)
        lines.append(
            "Total codes: " + str(len(all_ids)) +
            "  |  " + label_a + " applied: " + str(sum(results_a.values())) +
            "  |  " + label_b + " applied: " + str(sum(results_b.values()))
        )
        return "\n".join(lines)

    def _compare_two_exes(self):
        dlg = tk.Toplevel(self)
        dlg.title("Compare Two EXEs")
        dlg.geometry("480x200")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        def pick(var):
            path = filedialog.askopenfilename(
                title="Select EXE",
                filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
            )
            if path:
                var.set(path)

        var_a = tk.StringVar(value=self.exe_path.get())
        var_b = tk.StringVar()

        for label, var in [("EXE  A:", var_a), ("EXE  B:", var_b)]:
            row = tk.Frame(dlg, bg="#111")
            row.pack(fill="x", padx=16, pady=6)
            make_label(row, label, fg=TEXT_DIM, bg="#111",
                       font=FONT_SMALL, width=7).pack(side="left")
            tk.Entry(row, textvariable=var, font=FONT_SMALL,
                     fg=ACCENT2, bg="#1a1a1a", insertbackground=ACCENT2,
                     relief="flat", bd=0,
                     highlightthickness=1, highlightbackground=BORDER,
                     width=36).pack(side="left", ipady=2)
            make_button(row, "...", lambda v=var: pick(v),
                        fg=ACCENT, bg="#2a2a1a", active_bg="#3a3a2a",
                        font=FONT_TINY, width=3
                        ).pack(side="left", padx=4)

        def run():
            a, b = var_a.get().strip(), var_b.get().strip()
            if not a or not os.path.isfile(a):
                messagebox.showerror("Error", "Invalid EXE A path."); return
            if not b or not os.path.isfile(b):
                messagebox.showerror("Error", "Invalid EXE B path."); return
            dlg.destroy()
            res_a = self._scan_codes_in_file(a)
            res_b = self._scan_codes_in_file(b)
            report = self._build_codes_report(
                res_a, res_b,
                os.path.basename(a),
                os.path.basename(b)
            )
            self._show_report(
                "Compare: " + os.path.basename(a) + " vs " + os.path.basename(b),
                report
            )

        make_button(dlg, "Compare", run,
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=12
                    ).pack(pady=12)

    def _compare_with_original(self):
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error",
                "Please select a valid bio4.exe first."
                if CURRENT_LANG == "en" else
                "حط مسار bio4.exe أول.")
            return
        if not os.path.isfile(ORIG_FILE):
            messagebox.showerror("Error",
                "bio4_original.exe not found in the_codes/ folder."
                if CURRENT_LANG == "en" else
                "ما لقيت bio4_original.exe في مجلد the_codes/.")
            return
        res_orig = self._scan_codes_in_file(ORIG_FILE)
        res_exe  = self._scan_codes_in_file(exe)
        report = self._build_codes_report(
            res_orig, res_exe,
            "bio4_original.exe",
            os.path.basename(exe)
        )
        self._show_report(
            "Compare: Original vs " + os.path.basename(exe),
            report
        )

    def _view_log(self):
        """Show the patch log in a scrollable window."""
        if not os.path.isfile(LOG_FILE):
            messagebox.showinfo(
                "Log" if CURRENT_LANG == "en" else "السجل",
                "No log file found yet." if CURRENT_LANG == "en" else "ما في سجل بعد."
            )
            return
        with open(LOG_FILE, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        self._show_report("patch_log.txt", content)

    def _restore_original_exe(self):
        """Replace current bio4.exe with bio4_original.exe."""
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error",
                "Please select bio4.exe first." if CURRENT_LANG == "en"
                else "حط مسار bio4.exe أول.")
            return
        if not os.path.isfile(ORIG_FILE):
            messagebox.showerror("Error",
                "bio4_original.exe not found in the_codes folder."
                if CURRENT_LANG == "en"
                else "bio4_original.exe مو موجود في مجلد the_codes.")
            return
        confirmed = messagebox.askyesno(
            "Are you sure?" if CURRENT_LANG == "en" else "هل أنت متأكد؟",
            ("This will replace your current bio4.exe with bio4_original.exe.\n"
             "All applied codes will be reverted.\nContinue?")
            if CURRENT_LANG == "en" else
            ("هذا سيستبدل bio4.exe الحالي بالملف الأصلي.\n"
             "كل الأكواد المطبقة ستُحذف.\nتكمل؟")
        )
        if not confirmed:
            return
        import shutil
        try:
            shutil.copy2(ORIG_FILE, exe)
            self.applied  = {}
            self.detected = {}
            self.scanned  = False
            self._after_state_change()
            messagebox.showinfo("[+] Done",
                "bio4.exe has been restored to original."
                if CURRENT_LANG == "en"
                else "تم استعادة bio4.exe إلى النسخة الأصلية.")
            write_log("RESTORED", "bio4.exe restored from bio4_original.exe", exe)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _reset_all_codes(self):
        confirm_msg = (
            "Are you sure you want to revert ALL applied codes?\n\n"
            "This will restore all patched bytes in bio4.exe.\n"
            "Make sure bio4_original.exe is in the_codes/ folder."
            if CURRENT_LANG == "en" else
            "هل أنت متأكد أنك تبي تشيل كل الأكواد؟\n\n"
            "هذا يرجع كل البايتات المعدلة في bio4.exe.\n"
            "تأكد أن bio4_original.exe موجود في مجلد the_codes/."
        )
        if not messagebox.askyesno(
            "Reset All" if CURRENT_LANG == "en" else "إعادة تعيين",
            confirm_msg
        ):
            return

        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        applied_ids = [cid for cid, v in self.applied.items() if v]
        if not applied_ids:
            messagebox.showinfo(
                "Reset All" if CURRENT_LANG == "en" else "إعادة تعيين",
                "No codes are currently applied." if CURRENT_LANG == "en"
                else "ما في أكواد مفعّلة حالياً."
            )
            return

        success, failed = [], []
        for cid in applied_ids:
            ok, msg, _ = revert_patch(exe, ORIG_FILE, cid, self.codes_data)
            if ok:
                self.applied[cid] = False
                self.detected[cid] = False
                write_log("REVERTED (reset all)", self.code_by_id.get(cid, {}).get("name", cid), exe)
                success.append(cid)
            else:
                failed.append((cid, msg))

        summary = (
            "Reverted " + str(len(success)) + " code(s)."
            if CURRENT_LANG == "en" else
            "تم إزالة " + str(len(success)) + " كود."
        )
        if failed:
            summary += "\n\nFailed:\n"
            for cid, err in failed:
                summary += "- " + self.code_by_id.get(cid, {}).get("name", cid) + "\n"
            messagebox.showwarning("Done with errors", summary)
        else:
            messagebox.showinfo("[+] Done", summary)

        self._after_state_change()

    def _reload_ui(self):
        """Rebuild entire UI with new language."""
        # Save state
        exe = self.exe_path.get()
        sec = self.active_section

        # Destroy all children
        for w in self.winfo_children():
            w.destroy()

        # Reset widget refs
        self.code_rows = {}
        self.sidebar_items = {}

        # Rebuild
        self._build_ui()

        # Restore state
        self.exe_path.set(exe)
        if self.scanned:
            n_det   = sum(1 for v in self.detected.values() if v)
            n_app   = sum(1 for v in self.applied.values() if v)
            total   = len(self.all_codes)
            orig_status = ("  |  [orig: OK]" if CURRENT_LANG == "en" else "  |  [الأصلي: OK]") if os.path.isfile(ORIG_FILE) \
                else ("  |  [orig: missing]" if CURRENT_LANG == "en" else "  |  [الأصلي: مفقود]")
            scan_msg = (
                f"Scanned — {n_det} detected  |  {n_app} applied  |  {total} total"
                if CURRENT_LANG == "en" else
                f"تم المسح — {n_det} مكتشف  |  {n_app} مطبق  |  {total} إجمالي"
            ) + orig_status
            self.scan_status_var.set(scan_msg)
            # update embedded scan bar label
            if hasattr(self, "_scan_status"):
                self._scan_status.set(
                    f"{n_det} detected  |  {n_app} applied  |  {total} total"
                    if CURRENT_LANG == "en" else
                    f"{n_det} مكتشف  |  {n_app} مطبق  |  {total} إجمالي"
                )
            self.notice.pack_forget()
            self._update_statusbar()

        if sec:
            self.select_section(sec)
        else:
            self.select_section(self.sections_list[0]["id"])

    def _on_exe_path_change(self, *_):
        """Auto-scan when exe path changes after first manual scan."""
        # auto_scan_change disabled if auto_scan_startup is on
        if APP_SETTINGS.get("auto_scan_startup", False):
            return
        if not APP_SETTINGS.get("auto_scan_change", True):
            return
        if not self._first_scan_done:
            return
        path = self.exe_path.get().strip()
        if path and os.path.isfile(path) and path.lower().endswith(".exe"):
            self.after(300, self._scan)

    def _add_paste_menu(self, entry):
        """Add right-click Paste context menu to an Entry widget."""
        menu = tk.Menu(entry, tearoff=0, bg="#1a1a1a", fg=TEXT_MAIN,
                       activebackground="#2a2a2a", activeforeground=ACCENT2,
                       font=FONT_TINY, relief="flat", bd=0)
        menu.add_command(label="Paste", command=lambda: (
            entry.event_generate("<<Paste>>")
        ))
        menu.add_command(label="Copy", command=lambda: (
            entry.event_generate("<<Copy>>")
        ))
        menu.add_command(label="Cut", command=lambda: (
            entry.event_generate("<<Cut>>")
        ))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: (
            entry.select_range(0, "end")
        ))
        entry.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def _on_drop(self, event):
        pass  # placeholder — DND removed

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select bio4.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.exe_path.set(path)
            self._make_backup(path)

    def _make_backup(self, exe_path):
        """Create BIO4_BACKUP.EXE next to bio4.exe if not already exists."""
        import shutil
        backup = os.path.join(os.path.dirname(exe_path), "BIO4_BACKUP.EXE")
        if not os.path.isfile(backup):
            try:
                shutil.copy2(exe_path, backup)
                messagebox.showinfo(
                    "Backup Created",
                    "Backup created successfully:\n" + backup
                )
            except Exception as e:
                messagebox.showwarning(
                    "Backup Failed",
                    "Could not create backup:\n" + str(e)
                )
        # also check path entry manual edits on scan

    def _scan(self):
        path = self.exe_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Please select a valid bio4.exe file.")
            return

        # make backup if not exists
        self._make_backup(path)

        self.scan_btn.configure(text="Scanning..." if CURRENT_LANG == "en" else "جاري المسح...", state="disabled")
        self.update_idletasks()

        # reset state completely — fresh scan
        self.applied  = {}
        self.detected = {}

        self.detected = scan_exe(path, self.codes_info, self.codes_data)
        for cid, found in self.detected.items():
            if found:
                self.applied[cid] = True

        self.scanned = True
        self._first_scan_done = True

        # read current numeric values from EXE for numeric_input codes
        self._numeric_current = {}
        try:
            with open(path, "rb") as f:
                exe_bytes = f.read()
            for code in self.all_codes:
                if code.get("dialog") == "numeric_input":
                    cid        = code["id"]
                    entry      = self.codes_data.get(cid, {})
                    offset     = entry.get("offset", "")
                    byte_count = entry.get("byte_count", 1)
                    divide_by  = entry.get("divide_by", 1)
                    if offset:
                        off = int(offset, 16)
                        chunk = exe_bytes[off:off + byte_count]
                        if len(chunk) == byte_count:
                            val = int.from_bytes(chunk, byteorder="little")
                            # multiply back for display (reverse of divide_by)
                            self._numeric_current[cid] = val * divide_by
        except Exception:
            pass

        # save last exe path
        if APP_SETTINGS.get("remember_exe", True):
            APP_SETTINGS["last_exe"] = path
            save_settings(APP_SETTINGS)
        n_det = sum(1 for v in self.detected.values() if v)
        self.scan_btn.configure(text="Re-Scan" if CURRENT_LANG == "en" else "إعادة المسح", state="normal")
        orig_status = ("  |  [orig: OK]" if CURRENT_LANG == "en" else "  |  [الأصلي: OK]") if os.path.isfile(ORIG_FILE) \
            else ("  |  [orig: missing - revert disabled]" if CURRENT_LANG == "en" else "  |  [الأصلي: مفقود - الإرجاع معطل]")
        n_app   = sum(1 for v in self.applied.values() if v)
        total   = len(self.all_codes)
        scan_msg = (
            f"Scanned — {n_det} detected  |  {n_app} applied  |  {total} total"
            if CURRENT_LANG == "en" else
            f"تم المسح — {n_det} مكتشف  |  {n_app} مطبق  |  {total} إجمالي"
        ) + orig_status
        self.scan_status_var.set(scan_msg)
        if hasattr(self, "_scan_status"):
            self._scan_status.set(
                f"{n_det} detected  |  {n_app} applied  |  {total} total"
                if CURRENT_LANG == "en" else
                f"{n_det} مكتشف  |  {n_app} مطبق  |  {total} إجمالي"
            )
        self.notice.pack_forget()
        self._after_state_change()
        # update master locked panels after scan
        master = getattr(self, '_master_app_ref', None)
        if master:
            master._check_locked_panels()


    def select_section(self, section_id, preserve_scroll=None):
        for sid, item in self.sidebar_items.items():
            item.set_active(sid == section_id)
        self.active_section = section_id

        sec = next((s for s in self.sections_list if s["id"] == section_id), None)
        if sec:
            self.section_title_var.set(sec["label"])

        for w in self.codes_inner.winfo_children():
            w.destroy()
        self.code_rows.clear()

        codes = self.codes_by_section.get(section_id, [])
        self.section_count_var.set("  " + str(len(codes)) + " codes")

        if not codes:
            make_label(self.codes_inner,
                       "-- No codes in this section yet --",
                       fg=MUTED, bg=BG_PANEL, font=FONT_SMALL
                       ).pack(pady=24)
            self._update_apply_bar()
            return

        for code in codes:
            row = CodeRow(self.codes_inner, code, self)
            row.pack(fill="x", pady=2)
            self.code_rows[code["id"]] = row
            self._refresh_row(code["id"])
            # restore global selection
            if code["id"] in self._global_selected:
                row.sel_var.set(1)
                row.selected = True

        # restore scroll or go to top
        if preserve_scroll is not None:
            self.codes_canvas.after(10, lambda: self.codes_canvas.yview_moveto(preserve_scroll))
        else:
            self.codes_canvas.yview_moveto(0)
        self._update_apply_bar()

    def _is_unlocked(self, code_id):
        if not self.scanned:
            return False
        code = self.code_by_id.get(code_id, {})
        for dep in code.get("requires", []):
            if not (self.applied.get(dep) or self.detected.get(dep)):
                return False
        return True

    def _get_missing_requires(self, code_id):
        """Return list of (dep_id, dep_name, section_label) for unmet requires."""
        code = self.code_by_id.get(code_id, {})
        missing = []
        sec_map = {s["id"]: s for s in self.sections_list}
        for dep in code.get("requires", []):
            if not (self.applied.get(dep) or self.detected.get(dep)):
                dep_code = self.code_by_id.get(dep, {})
                dep_name = dep_code.get("name_en" if CURRENT_LANG == "en" else "name", dep)
                dep_sec  = dep_code.get("section", "")
                sec_obj  = sec_map.get(dep_sec, {})
                sec_label = sec_obj.get("label_en" if CURRENT_LANG == "en" else "label", dep_sec)
                missing.append((dep, dep_name, sec_label))
        return missing

    def _get_dependents(self, code_id):
        """Return all applied codes that directly or transitively require code_id."""
        dependents = []
        for code in self.all_codes:
            cid = code["id"]
            if cid == code_id:
                continue
            if not self.applied.get(cid, False):
                continue
            # check if code_id is in transitive requires
            if code_id in self._transitive_requires(cid):
                dependents.append(cid)
        return dependents

    def _transitive_requires(self, cid, visited=None):
        if visited is None:
            visited = set()
        if cid in visited:
            return set()
        visited.add(cid)
        direct = set(self.code_by_id.get(cid, {}).get("requires", []))
        result = set(direct)
        for dep in direct:
            result |= self._transitive_requires(dep, visited)
        return result

    def handle_toggle(self, code_id):
        if not self.scanned:
            messagebox.showinfo(
                "Scan Required" if CURRENT_LANG == "en" else "لازم تسوي Scan",
                "Please select bio4.exe and press Scan EXE first."
                if CURRENT_LANG == "en" else
                "حط مسار bio4.exe واضغط Scan EXE أول."
            )
            return

        if not self._is_unlocked(code_id):
            missing = self._get_missing_requires(code_id)
            if missing:
                msg = ("You need to enable the following codes first:\n\n"
                       if CURRENT_LANG == "en" else
                       "لازم تشغل الأكواد التالية أول:\n\n")
                for dep_id, dep_name, sec_label in missing:
                    msg += "  - " + dep_name + "\n"
                    msg += ("    (Found in: " + sec_label + ")\n"
                            if CURRENT_LANG == "en" else
                            "    (تجده في قسم: " + sec_label + ")\n")
                messagebox.showwarning(
                    "Code Locked" if CURRENT_LANG == "en" else "الكود مقفل",
                    msg
                )
            return
        code = self.code_by_id.get(code_id, {})

        if self.applied.get(code_id, False):
            # revert
            exe = self.exe_path.get().strip()
            if not exe or not os.path.isfile(exe):
                messagebox.showerror("Error", "EXE path is invalid.")
                return

            if is_game_running(exe):
                messagebox.showerror(
                    "Game is Running" if CURRENT_LANG == "en" else "اللعبة شغالة",
                    "Please close the game before reverting codes."
                    if CURRENT_LANG == "en" else
                    "طفي اللعبة أول عشان تقدر تشيل الكود."
                )
                return

            # check if code has offset patches requiring original
            data = self.codes_data.get(code_id, {})
            if "variants" in data:
                all_patches = []
                for v in data["variants"].values():
                    all_patches += v.get("patches", [])
            else:
                all_patches = data.get("patches", [])

            needs_orig = any(p["type"] == "offset_paste"
                             for p in all_patches)

            if needs_orig and not os.path.isfile(ORIG_FILE):
                messagebox.showerror(
                    "Cannot Revert",
                    "This code has offset-based patches.\n"
                    "To revert it, place the original bio4.exe in:\n\n"
                    "the_codes/bio4_original.exe"
                )
                return

            ok, msg, skipped = revert_patch(exe, ORIG_FILE, code_id, self.codes_data)
            if ok:
                self.applied[code_id] = False
                self.detected[code_id] = False
                backup_snap = load_patch_backup()
                write_log("REVERTED", self.code_by_id.get(code_id, {}).get("name", code_id), exe,
                           build_log_details(code_id, self.codes_data, backup_snap))

                # cascade: revert all applied codes that depend on this one
                dependents = self._get_dependents(code_id)
                if dependents:
                    dep_names = "\n".join(
                        "  - " + self.code_by_id.get(d, {}).get(
                            "name_en" if CURRENT_LANG == "en" else "name", d)
                        for d in dependents
                    )
                    title = "Cascade Revert" if CURRENT_LANG == "en" else "إيقاف الأكواد التابعة"
                    msg_cascade = (
                        "The following codes depend on this one.\n"
                        "Turn them OFF too?\n\n" + dep_names
                    ) if CURRENT_LANG == "en" else (
                        "الأكواد التالية تعتمد على هذا الكود.\n"
                        "تطفيها كذلك؟\n\n" + dep_names
                    )
                    if messagebox.askyesno(title, msg_cascade):
                        for dep in dependents:
                            ok2, _, _ = revert_patch(exe, ORIG_FILE, dep, self.codes_data)
                            if ok2:
                                self.applied[dep] = False
                                self.detected[dep] = False
                                write_log("REVERTED (cascade)",
                                          self.code_by_id.get(dep, {}).get("name", dep), exe)
                    # If No: leave dependents as applied=True in EXE
                    # _is_unlocked returns False so they show locked [L]
                    # but their toggle shows ON — user must re-enable base code first

                if skipped > 0:
                    messagebox.showinfo(
                        "Reverted",
                        "Code reverted.\n(" + str(skipped) + " patch(es) were already at original state)"
                    )
                self._after_state_change()
            else:
                messagebox.showerror("Revert Failed", msg)
            return

        if code.get("dialog") == "mod_expansion":
            self._dialog_mod_expansion(code_id)
            return
        if code.get("dialog") == "bgm_files":
            self._dialog_bgm_files(code_id)
            return
        if code.get("dialog") == "link_tweaks":
            self._dialog_link_tweaks(code_id)
            return
        if code.get("dialog") == "numeric_input":
            # numeric codes use inline Apply button, not toggle
            return
        if code.get("dialog") == "memory_alloc":
            self._dialog_memory_alloc(code_id)
            return
        if code.get("dialog") == "random_ptas":
            self._dialog_random_ptas(code_id)
            return
        if code.get("dialog") == "dropdown":
            self._dialog_dropdown(code_id)
            return
        if code.get("dialog") == "r11c_cabin":
            self._dialog_r11c_cabin(code_id)
            return
        if code.get("dialog") == "luis_cabin":
            self._dialog_luis_cabin(code_id)
            return
        if code.get("dialog") == "drawn_enemies_cam":
            self._dialog_drawn_enemies_cam(code_id)
            return
        if code.get("dialog") == "custom_ces":
            self._dialog_custom_ces(code_id)
            return
        self._do_apply(code_id)

    # ── Numeric Input Dialog ─────────────────────────────────────────────────

    def _dialog_numeric_input(self, code_id):
        """Generic dialog for codes with a single numeric (decimal) input."""
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        entry_data = self.codes_data.get(code_id, {})
        code_info  = self.code_by_id.get(code_id, {})
        offset     = entry_data.get("offset", "")
        byte_count = entry_data.get("byte_count", 1)
        default    = entry_data.get("default_dec", 0)
        divide_by  = entry_data.get("divide_by", 1)
        name       = code_info.get("name_en" if CURRENT_LANG == "en" else "name", code_id)

        dlg = tk.Toplevel(self)
        dlg.title(name)
        dlg.geometry("320x180")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, name, fg=ACCENT2, bg="#111", font=FONT_NORMAL).pack(pady=(16, 4))
        make_label(dlg,
                   "Enter value (decimal):" if CURRENT_LANG == "en" else "أدخل القيمة (decimal):",
                   fg=TEXT_DIM, bg="#111", font=FONT_TINY).pack()

        val_var = tk.StringVar(value=str(default))
        e = tk.Entry(dlg, textvariable=val_var, font=FONT_NORMAL,
                     fg=ACCENT2, bg="#1a1a1a", insertbackground=ACCENT2,
                     relief="flat", bd=0, highlightthickness=1,
                     highlightbackground=BORDER, width=12, justify="center")
        e.pack(pady=8, ipady=4)
        self._add_paste_menu(e)

        def do_apply():
            try:
                dec_val = int(val_var.get().strip())
                if dec_val < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid positive number.")
                return

            # check for prefix_template (e.g. random_ptas: BE XX 00 00 00 E9...)
            template = entry_data.get("prefix_template", "")
            divide_by = entry_data.get("divide_by", 1)
            actual_val = dec_val // divide_by if divide_by > 1 else dec_val
            if template:
                xx = format(actual_val, "02X")
                hex_bytes = template.replace("{XX}", xx)
                write_len = len(hex_bytes) // 2
            else:
                hex_bytes = actual_val.to_bytes(byte_count, byteorder="little").hex().upper()
                write_len = byte_count

            try:
                with open(exe, "r+b") as f:
                    off = int(offset, 16)
                    f.seek(off)
                    orig = f.read(write_len)
                    backup = load_patch_backup()
                    backup.setdefault(code_id, {})[offset.upper().lstrip("0") or "0"] = orig.hex().upper()
                    save_patch_backup(backup)
                    f.seek(off)
                    f.write(bytes.fromhex(hex_bytes))
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
                return

            self.applied[code_id] = True
            write_log("APPLIED", name + " = " + str(dec_val), exe)
            dlg.destroy()
            if not APP_SETTINGS.get("silent_apply", False):
                messagebox.showinfo("[+] Applied", name + "\nValue: " + str(dec_val))
            self._after_state_change()

        make_button(dlg, "Apply" if CURRENT_LANG == "en" else "تطبيق",
                    do_apply, fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack(pady=8)

    # ── Dropdown Dialog ──────────────────────────────────────────────────────

    def _dialog_dropdown(self, code_id):
        """Dialog for codes with a fixed list of options (e.g. scope color)."""
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        entry_data = self.codes_data.get(code_id, {})
        code_info  = self.code_by_id.get(code_id, {})
        offset     = entry_data.get("offset", "")
        options    = entry_data.get("options", [])
        name       = code_info.get("name_en" if CURRENT_LANG == "en" else "name", code_id)

        dlg = tk.Toplevel(self)
        dlg.title(name)
        dlg.geometry("320x200")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, name, fg=ACCENT2, bg="#111", font=FONT_NORMAL).pack(pady=(16, 8))

        sel_var = tk.StringVar()
        labels = [o.get("label_ar" if CURRENT_LANG == "ar" else "label", o["label"]) for o in options]
        sel_var.set(labels[0])

        for lbl in labels:
            tk.Radiobutton(dlg, text=lbl, variable=sel_var, value=lbl,
                           font=FONT_SMALL, fg=TEXT_MAIN, bg="#111",
                           activebackground="#111", selectcolor="#1a1a1a",
                           relief="flat").pack(anchor="w", padx=30, pady=2)

        def do_apply():
            idx = labels.index(sel_var.get())
            hex_bytes = options[idx]["bytes"]
            try:
                with open(exe, "r+b") as f:
                    off = int(offset, 16)
                    f.seek(off)
                    orig = f.read(len(bytes.fromhex(hex_bytes)))
                    backup = load_patch_backup()
                    backup.setdefault(code_id, {})[offset.upper().lstrip("0") or "0"] = orig.hex().upper()
                    save_patch_backup(backup)
                    f.seek(off)
                    f.write(bytes.fromhex(hex_bytes))
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
                return

            self.applied[code_id] = True
            write_log("APPLIED", name + " = " + sel_var.get(), exe)
            dlg.destroy()
            if not APP_SETTINGS.get("silent_apply", False):
                messagebox.showinfo("[+] Applied", name + "\n" + sel_var.get())
            self._after_state_change()

        make_button(dlg, "Apply" if CURRENT_LANG == "en" else "تطبيق",
                    do_apply, fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack(pady=10)

    # ── r11c Cabin Dialog ────────────────────────────────────────────────────

    def _dialog_r11c_cabin(self, code_id):
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        dlg = tk.Toplevel(self)
        dlg.title("r11c Cabin Settings")
        dlg.geometry("340x260")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, "r11c Cabin Settings", fg=ACCENT2, bg="#111", font=FONT_NORMAL).pack(pady=(12, 8))

        fields = [
            ("Time Limit (Normal):", "4B44C5", 2, 120),
            ("Time Limit (Easy):",   "4B44D5", 2, 180),
            ("Enemy Count (Normal):", "4B44CC", 1, 15),
            ("Enemy Count (Easy):",   "4B44DC", 1, 10),
        ]
        vars_ = []
        for label, offset, bcount, default in fields:
            row = tk.Frame(dlg, bg="#111")
            row.pack(fill="x", padx=20, pady=3)
            make_label(row, label, fg=TEXT_DIM, bg="#111", font=FONT_TINY, width=22, anchor="w").pack(side="left")
            v = tk.StringVar(value=str(default))
            tk.Entry(row, textvariable=v, font=FONT_SMALL, fg=ACCENT2, bg="#1a1a1a",
                     insertbackground=ACCENT2, relief="flat", bd=0,
                     highlightthickness=1, highlightbackground=BORDER, width=8
                     ).pack(side="left", ipady=2)
            vars_.append((v, offset, bcount))

        def do_apply():
            try:
                with open(exe, "r+b") as f:
                    backup = load_patch_backup()
                    for v, offset, bcount in vars_:
                        dec_val = int(v.get().strip())
                        hex_bytes = dec_val.to_bytes(bcount, byteorder="little")
                        off = int(offset, 16)
                        f.seek(off)
                        orig = f.read(bcount)
                        backup.setdefault(code_id, {})[offset.upper().lstrip("0") or "0"] = orig.hex().upper()
                        f.seek(off)
                        f.write(hex_bytes)
                    save_patch_backup(backup)
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
                return
            self.applied[code_id] = True
            write_log("APPLIED", "r11c Cabin Settings", exe)
            dlg.destroy()
            if not APP_SETTINGS.get("silent_apply", False):
                messagebox.showinfo("[+] Applied", "r11c Cabin settings applied.")
            self._after_state_change()

        make_button(dlg, "Apply" if CURRENT_LANG == "en" else "تطبيق",
                    do_apply, fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack(pady=10)

    # ── Luis Cabin Dialog ────────────────────────────────────────────────────

    def _dialog_luis_cabin(self, code_id):
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        dlg = tk.Toplevel(self)
        dlg.title("Luis Cabin Settings")
        dlg.geometry("340x260")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, "Luis Cabin Settings", fg=ACCENT2, bg="#111", font=FONT_NORMAL).pack(pady=(12, 8))

        fields = [
            ("Time Limit (Normal):",  "4B44C5", 2, 60),
            ("Time Limit (Easy):",    "4B44D5", 2, 90),
            ("Kill Count (Normal):",  "4B44CC", 1, 10),
            ("Kill Count (Easy):",    "4B44DC", 1, 8),
        ]
        vars_ = []
        for label, offset, bcount, default in fields:
            row = tk.Frame(dlg, bg="#111")
            row.pack(fill="x", padx=20, pady=3)
            make_label(row, label, fg=TEXT_DIM, bg="#111", font=FONT_TINY, width=22, anchor="w").pack(side="left")
            v = tk.StringVar(value=str(default))
            tk.Entry(row, textvariable=v, font=FONT_SMALL, fg=ACCENT2, bg="#1a1a1a",
                     insertbackground=ACCENT2, relief="flat", bd=0,
                     highlightthickness=1, highlightbackground=BORDER, width=8
                     ).pack(side="left", ipady=2)
            vars_.append((v, offset, bcount))

        def do_apply():
            try:
                with open(exe, "r+b") as f:
                    backup = load_patch_backup()
                    for v, offset, bcount in vars_:
                        dec_val = int(v.get().strip())
                        hex_bytes = dec_val.to_bytes(bcount, byteorder="little")
                        off = int(offset, 16)
                        f.seek(off)
                        orig = f.read(bcount)
                        backup.setdefault(code_id, {})[offset.upper().lstrip("0") or "0"] = orig.hex().upper()
                        f.seek(off)
                        f.write(hex_bytes)
                    save_patch_backup(backup)
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
                return
            self.applied[code_id] = True
            write_log("APPLIED", "Luis Cabin Settings", exe)
            dlg.destroy()
            if not APP_SETTINGS.get("silent_apply", False):
                messagebox.showinfo("[+] Applied", "Luis Cabin settings applied.")
            self._after_state_change()

        make_button(dlg, "Apply" if CURRENT_LANG == "en" else "تطبيق",
                    do_apply, fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack(pady=10)

    # ── Drawn Enemies During Camera Events Dialog ────────────────────────────

    def _dialog_drawn_enemies_cam(self, code_id):
        """Select up to 4 rooms where enemies are drawn during camera events."""
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        dlg = tk.Toplevel(self)
        dlg.title("Drawn Enemies During Camera Events")
        dlg.geometry("360x280")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, "Drawn Enemies During Camera Events",
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL).pack(pady=(14, 4))
        make_label(dlg,
                   "Enter up to 4 room IDs (e.g. 325, 31c, 21a, 30b)"
                   if CURRENT_LANG == "en" else
                   "أدخل حتى 4 غرف (مثال: 325، 31c، 21a، 30b)",
                   fg=MUTED, bg="#111", font=FONT_TINY).pack()

        vars_ = []
        for i in range(1, 5):
            row = tk.Frame(dlg, bg="#111")
            row.pack(fill="x", padx=30, pady=4)
            make_label(row, "Room " + str(i) + ":",
                       fg=TEXT_DIM, bg="#111", font=FONT_SMALL, width=8).pack(side="left")
            v = tk.StringVar()
            e = tk.Entry(row, textvariable=v, font=FONT_SMALL,
                         fg=ACCENT2, bg="#1a1a1a", insertbackground=ACCENT2,
                         relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=BORDER, width=10)
            e.pack(side="left", ipady=2)
            self._add_paste_menu(e)
            vars_.append(v)

        def room_to_bytes(room_str):
            """Convert room ID like '325' or '30b' to 2-byte little-endian."""
            r = room_str.strip().lower().lstrip("r")
            if len(r) < 3:
                raise ValueError("Invalid room ID: " + room_str)
            last_two = r[-2:]   # e.g. '25'
            first    = r[:-2]   # e.g. '3'
            b0 = int(last_two, 16)
            b1 = int(first, 16)
            return bytes([b0, b1])

        def do_apply():
            rooms = [v.get().strip() for v in vars_ if v.get().strip()]
            if not rooms:
                messagebox.showerror("Error", "Enter at least one room ID.")
                return
            if len(rooms) > 4:
                messagebox.showerror("Error", "Maximum 4 rooms.")
                return

            # build the paste bytes — 4 room slots, unused = FF FF
            room_bytes_list = []
            for r in rooms:
                try:
                    room_bytes_list.append(room_to_bytes(r))
                except Exception:
                    messagebox.showerror("Error", "Invalid room ID: " + r +
                                         "\nFormat: 3-digit hex e.g. 325, 30b, 21a")
                    return
            while len(room_bytes_list) < 4:
                room_bytes_list.append(b'\xff\xff')

            # build the offset_paste bytes with room IDs embedded
            # format: 53 8B 98 AC 4F 00 00 66 81 FB [R1] 74 1F 66 81 FB [R2] 74 18 66 81 FB [R3] 74 11 66 81 FB [R4] 74 0A 81 88 20 50 00 00 00 00 00 10 5B E9 F9 FE FF FF
            r = room_bytes_list
            paste_bytes = (
                bytes.fromhex("53 8B 98 AC 4F 00 00".replace(" ","")) +
                bytes.fromhex("66 81 FB".replace(" ","")) + r[0] +
                bytes.fromhex("74 1F 66 81 FB".replace(" ","")) + r[1] +
                bytes.fromhex("74 18 66 81 FB".replace(" ","")) + r[2] +
                bytes.fromhex("74 11 66 81 FB".replace(" ","")) + r[3] +
                bytes.fromhex("74 0A 81 88 20 50 00 00 00 00 00 10 5B E9 F9 FE FF FF".replace(" ",""))
            )

            # apply find_replace patch first
            try:
                with open(exe, "rb") as f:
                    exe_data = bytearray(f.read())

                find_b    = bytes.fromhex("81882050000000000010 8B153C5F".replace(" ",""))
                replace_b = bytes.fromhex("E9D9000000 9090909090 8B153C5F".replace(" ",""))
                idx = exe_data.find(find_b)
                if idx != -1:
                    exe_data[idx:idx+len(find_b)] = replace_b

                # write paste at 002BDBE8
                off = 0x2BDBE8
                exe_data[off:off+len(paste_bytes)] = paste_bytes

                backup = load_patch_backup()
                backup[code_id] = {"applied": True}
                save_patch_backup(backup)

                with open(exe, "wb") as f:
                    f.write(exe_data)
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
                return

            self.applied[code_id] = True
            write_log("APPLIED", "Drawn Enemies Cam - rooms: " + ", ".join(rooms), exe)
            dlg.destroy()
            if not APP_SETTINGS.get("silent_apply", False):
                messagebox.showinfo("[+] Applied",
                    "Drawn Enemies During Camera Events\nRooms: " + ", ".join("r" + r for r in rooms))
            self._after_state_change()

        make_button(dlg, "Apply" if CURRENT_LANG == "en" else "تطبيق",
                    do_apply, fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack(pady=12)

    # ── Custom Chapter Ending Screens Dialog ─────────────────────────────────

    def _dialog_custom_ces(self, code_id):
        """Set room pairs for Custom Chapter Ending Screens."""
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        dlg = tk.Toplevel(self)
        dlg.title("Custom Chapter Ending Screens")
        dlg.geometry("460x420")
        dlg.resizable(False, True)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, "Custom Chapter Ending Screens",
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL).pack(pady=(14, 4))
        make_label(dlg,
                   "Enter room pairs: Last Entered → Destination (up to 5 pairs)\n"
                   "Format: 3-digit hex e.g. 220, 20a, 10c\n"
                   "Leave blank to skip a subchapter (uses FF FF FF FF)"
                   if CURRENT_LANG == "en" else
                   "أدخل أزواج الغرف: آخر غرفة دخلتها ← الوجهة (حتى 5 أزواج)\n"
                   "الصيغة: 3 أرقام hex مثال: 220، 20a، 10c\n"
                   "اتركها فارغة لتخطي فصل (يستخدم FF FF FF FF)",
                   fg=MUTED, bg="#111", font=FONT_TINY, justify="left").pack(padx=16, anchor="w")

        # headers
        hdr = tk.Frame(dlg, bg="#111")
        hdr.pack(fill="x", padx=20, pady=(8, 2))
        make_label(hdr, "#", fg=ACCENT, bg="#111", font=FONT_TINY, width=3).pack(side="left")
        make_label(hdr, "Last Entered Room" if CURRENT_LANG == "en" else "آخر غرفة",
                   fg=ACCENT, bg="#111", font=FONT_TINY, width=20).pack(side="left")
        make_label(hdr, "Destination Room" if CURRENT_LANG == "en" else "الوجهة",
                   fg=ACCENT, bg="#111", font=FONT_TINY, width=18).pack(side="left")

        pair_vars = []
        for i in range(1, 6):
            row = tk.Frame(dlg, bg="#111")
            row.pack(fill="x", padx=20, pady=3)
            make_label(row, str(i), fg=MUTED, bg="#111", font=FONT_TINY, width=3).pack(side="left")
            v_from = tk.StringVar()
            v_to   = tk.StringVar()
            for v in [v_from, v_to]:
                e = tk.Entry(row, textvariable=v, font=FONT_SMALL,
                             fg=ACCENT2, bg="#1a1a1a", insertbackground=ACCENT2,
                             relief="flat", bd=0,
                             highlightthickness=1, highlightbackground=BORDER, width=14)
                e.pack(side="left", ipady=2, padx=4)
                self._add_paste_menu(e)
            pair_vars.append((v_from, v_to))

        def room_to_bytes(room_str):
            r = room_str.strip().lower().lstrip("r")
            if len(r) < 3:
                raise ValueError("Invalid: " + room_str)
            b0 = int(r[-2:], 16)
            b1 = int(r[:-2], 16)
            return bytes([b0, b1])

        def do_apply():
            # build 10-byte pairs (5 pairs × 4 bytes each + FF padding per subchapter)
            pair_bytes = b""
            valid_pairs = 0
            for v_from, v_to in pair_vars:
                f_str = v_from.get().strip()
                t_str = v_to.get().strip()
                if not f_str and not t_str:
                    pair_bytes += b"\xff\xff\xff\xff"
                    continue
                if not f_str or not t_str:
                    messagebox.showerror("Error",
                        "Each pair needs both rooms, or leave both empty.")
                    return
                try:
                    pair_bytes += room_to_bytes(f_str) + room_to_bytes(t_str)
                    valid_pairs += 1
                except Exception as ex:
                    messagebox.showerror("Error", str(ex))
                    return

            if valid_pairs == 0:
                messagebox.showerror("Error", "Enter at least one room pair.")
                return

            # apply base patches first via apply_patch
            ok, msg = apply_patch(exe, code_id, self.codes_data)
            if not ok:
                messagebox.showerror("Error", "Failed:\n" + msg)
                return

            # write room pairs at 00702578 (formerly 002C2D50)
            try:
                with open(exe, "r+b") as f:
                    f.seek(0x702578)
                    f.write(pair_bytes)
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
                return

            self.applied[code_id] = True
            write_log("APPLIED", "Custom CES - " + str(valid_pairs) + " pairs", exe)
            dlg.destroy()
            if not APP_SETTINGS.get("silent_apply", False):
                messagebox.showinfo("[+] Applied",
                    "Custom Chapter Ending Screens applied.\n" + str(valid_pairs) + " pair(s) set.")
            self._after_state_change()

        make_button(dlg, "Apply" if CURRENT_LANG == "en" else "تطبيق",
                    do_apply, fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack(pady=10)

    # ── Memory Allocation Dialog ─────────────────────────────────────────────

    def _dialog_memory_alloc(self, code_id):
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        entry    = self.codes_data.get(code_id, {})
        options  = entry.get("options", [])
        off_exe  = entry.get("offsets_exe", [])
        off_dll  = entry.get("offsets_dll", [])

        # Step 1 — ask about Tweaks DLL
        use_dll = messagebox.askyesno(
            "Tweaks DLL",
            "Are you using the Tweaks DLL (dinput8.dll)?\n\nYes = write to DLL\nNo = write to EXE"
            if CURRENT_LANG == "en" else
            "هل تستخدم Tweaks DLL (dinput8.dll)?\n\nنعم = يكتب في DLL\nلا = يكتب في EXE"
        )

        dll_path = ""
        if use_dll:
            dll_path = filedialog.askopenfilename(
                title="Select dinput8.dll" if CURRENT_LANG == "en" else "اختر dinput8.dll",
                filetypes=[("DLL file", "*.dll"), ("All files", "*.*")]
            )
            if not dll_path:
                return

        # Step 2 — show options dialog
        dlg = tk.Toplevel(self)
        dlg.title("Memory Allocation (MEM2)")
        dlg.geometry("300x160")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, "Memory Allocation (MEM2)",
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL).pack(pady=(14, 4))
        make_label(dlg,
                   ("Writing to: DLL — " + os.path.basename(dll_path)) if use_dll
                   else "Writing to: EXE",
                   fg=MUTED, bg="#111", font=FONT_TINY).pack(pady=(0, 10))

        labels  = [o.get("label_ar" if CURRENT_LANG == "ar" else "label") for o in options]
        sel_var = tk.StringVar(value=labels[0])

        # combobox — fits all 17 options without scrolling issues
        import tkinter.ttk as ttk
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.TCombobox",
                         fieldbackground="#1a1a1a", background="#1a1a1a",
                         foreground=ACCENT2, selectbackground="#2a2a2a",
                         selectforeground=ACCENT2)
        combo = ttk.Combobox(dlg, textvariable=sel_var,
                             values=labels, state="readonly",
                             font=FONT_SMALL, width=16,
                             style="Dark.TCombobox")
        combo.pack(pady=(0, 14))

        def do_apply():
            idx        = labels.index(sel_var.get())
            hex_bytes  = bytes.fromhex(options[idx]["bytes_le"])
            target     = dll_path if use_dll else exe
            offsets    = off_dll  if use_dll else off_exe
            try:
                with open(target, "r+b") as f:
                    backup = load_patch_backup()
                    for off_str in offsets:
                        off = int(off_str, 16)
                        f.seek(off)
                        orig = f.read(4)
                        backup.setdefault(code_id, {})[off_str.upper().lstrip("0") or "0"] = orig.hex().upper()
                        f.seek(off)
                        f.write(hex_bytes)
                    save_patch_backup(backup)
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
                return
            self.applied[code_id] = True
            write_log("APPLIED", "Memory Allocation = " + sel_var.get() +
                      (" (DLL)" if use_dll else " (EXE)"), exe)
            dlg.destroy()
            if not APP_SETTINGS.get("silent_apply", False):
                messagebox.showinfo("[+] Applied",
                    "Memory Allocation: " + sel_var.get() +
                    ("\nDLL: " + os.path.basename(dll_path) if use_dll else "\nEXE"))
            self._after_state_change()

        make_button(dlg, "Apply" if CURRENT_LANG == "en" else "تطبيق",
                    do_apply, fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack()

    # ── Random Ptas Dialog (ON/OFF + numeric) ───────────────────────────────

    def _dialog_random_ptas(self, code_id):
        """ON/OFF toggle + numeric field for random ptas amount."""
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        entry     = self.codes_data.get(code_id, {})
        code_info = self.code_by_id.get(code_id, {})
        name      = code_info.get("name_en" if CURRENT_LANG == "en" else "name", code_id)
        is_on     = self.applied.get(code_id, False)
        val_off   = entry.get("value_offset", "1B87FD")
        divide_by = entry.get("divide_by", 10)
        on_patch  = entry.get("on_patch", {})

        dlg = tk.Toplevel(self)
        dlg.title(name)
        dlg.geometry("300x175")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, name, fg=ACCENT2, bg="#111", font=FONT_NORMAL).pack(pady=(14, 10))

        # ON/OFF row
        row1 = tk.Frame(dlg, bg="#111")
        row1.pack(fill="x", padx=24, pady=4)
        make_label(row1,
                   "Enable random drops:" if CURRENT_LANG == "en" else "تفعيل الإسقاط العشوائي:",
                   fg=TEXT_DIM, bg="#111", font=FONT_SMALL, anchor="w"
                   ).pack(side="left", expand=True, fill="x")

        state_var = tk.BooleanVar(value=is_on)
        state_btn = tk.Button(row1, text="ON" if is_on else "OFF",
                              width=5, font=FONT_TINY,
                              fg=GREEN if is_on else "#bbbbbb",
                              bg="#2a5a2a" if is_on else "#1a1a1a",
                              relief="flat", bd=0,
                              highlightthickness=1,
                              highlightbackground=GREEN if is_on else "#555",
                              cursor="hand2")
        state_btn.pack(side="right")

        # Amount row
        row2 = tk.Frame(dlg, bg="#111")
        row2.pack(fill="x", padx=24, pady=4)
        make_label(row2,
                   "Amount (ptas):" if CURRENT_LANG == "en" else "الكمية (ptas):",
                   fg=TEXT_DIM, bg="#111", font=FONT_SMALL, anchor="w"
                   ).pack(side="left", expand=True, fill="x")

        # read current value
        try:
            with open(exe, "rb") as f:
                f.seek(int(val_off, 16))
                cur_raw = int.from_bytes(f.read(1), "little") * divide_by
        except Exception:
            cur_raw = entry.get("default_dec", 100)

        amt_var = tk.StringVar(value=str(cur_raw))
        amt_entry = tk.Entry(row2, textvariable=amt_var, font=FONT_NORMAL,
                             fg=ACCENT2 if is_on else MUTED,
                             bg="#1a1a1a", insertbackground=ACCENT2,
                             relief="flat", bd=0,
                             highlightthickness=1, highlightbackground=BORDER,
                             width=6, justify="center",
                             state="normal" if is_on else "disabled")
        amt_entry.pack(side="right", ipady=3)

        def toggle_state():
            nonlocal is_on
            is_on = not is_on
            state_var.set(is_on)
            state_btn.configure(
                text="ON" if is_on else "OFF",
                fg=GREEN if is_on else "#bbbbbb",
                bg="#2a5a2a" if is_on else "#1a1a1a",
                highlightbackground=GREEN if is_on else "#555"
            )
            amt_entry.configure(
                state="normal" if is_on else "disabled",
                fg=ACCENT2 if is_on else MUTED
            )

        state_btn.configure(command=toggle_state)

        def do_apply():
            # ON patch
            if is_on:
                on_bytes = bytes.fromhex(on_patch["bytes"].replace(" ", ""))
                off_on   = int(on_patch["offset"], 16)
                try:
                    with open(exe, "r+b") as f:
                        backup = load_patch_backup()
                        f.seek(off_on)
                        orig = f.read(len(on_bytes))
                        backup.setdefault(code_id, {})["ON"] = orig.hex().upper()
                        f.seek(off_on)
                        f.write(on_bytes)
                        # write amount
                        try:
                            amt = int(amt_var.get().strip()) // divide_by
                        except Exception:
                            amt = 10
                        val_off_int = int(val_off, 16)
                        f.seek(val_off_int)
                        f.write(bytes([amt]))
                        save_patch_backup(backup)
                except Exception as ex:
                    messagebox.showerror("Error", str(ex)); return
                self.applied[code_id] = True
            else:
                # revert
                ok, msg, _ = revert_patch(exe, ORIG_FILE, code_id, self.codes_data)
                if not ok:
                    messagebox.showerror("Error", msg); return
                self.applied[code_id] = False

            write_log("APPLIED" if is_on else "REVERTED", name, exe)
            dlg.destroy()
            if not APP_SETTINGS.get("silent_apply", False):
                messagebox.showinfo("[+] " + ("Applied" if is_on else "Reverted"), name)
            self._after_state_change()

        make_button(dlg, "Apply" if CURRENT_LANG == "en" else "تطبيق",
                    do_apply, fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack(pady=10)

    def _dialog_punisher_pierce(self, code_id):
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        entry_data = self.codes_data.get(code_id, {})
        fields     = entry_data.get("fields", [])
        code_info  = self.code_by_id.get(code_id, {})
        name       = code_info.get("name_en" if CURRENT_LANG == "en" else "name", code_id)

        dlg = tk.Toplevel(self)
        dlg.title(name)
        dlg.geometry("280x195")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, name, fg=ACCENT2, bg="#111", font=FONT_NORMAL).pack(pady=(14, 8))

        field_vars = []
        for field in fields:
            lbl     = field.get("label_en" if CURRENT_LANG == "en" else "label_ar", "")
            default = field.get("default_dec", 0)
            try:
                with open(exe, "rb") as f:
                    f.seek(int(field["offset"], 16) + 1)
                    current = int.from_bytes(f.read(field["byte_count"] - 1), "little")
            except Exception:
                current = default

            row = tk.Frame(dlg, bg="#111")
            row.pack(fill="x", padx=24, pady=4)
            make_label(row, lbl, fg=TEXT_DIM, bg="#111",
                       font=FONT_TINY, anchor="w").pack(side="left", expand=True, fill="x")
            var = tk.StringVar(value=str(current))
            tk.Entry(row, textvariable=var, font=FONT_NORMAL,
                     fg=ACCENT2, bg="#1a1a1a", insertbackground=ACCENT2,
                     relief="flat", bd=0,
                     highlightthickness=1, highlightbackground=BORDER,
                     width=5, justify="center").pack(side="right", ipady=3)
            field_vars.append((var, field))

        def do_apply():
            try:
                backup = load_patch_backup()
                with open(exe, "r+b") as fh:
                    for var, field in field_vars:
                        val = int(var.get().strip())
                        if val < 0: raise ValueError
                        hb  = bytes([0xB8]) + val.to_bytes(field["byte_count"] - 1, "little")
                        off = int(field["offset"], 16)
                        fh.seek(off); orig = fh.read(field["byte_count"])
                        backup.setdefault(code_id, {})[field["offset"].upper().lstrip("0") or "0"] = orig.hex().upper()
                        fh.seek(off); fh.write(hb)
                save_patch_backup(backup)
            except Exception as ex:
                messagebox.showerror("Error", str(ex)); return
            self.applied[code_id] = True
            write_log("APPLIED", name, exe)
            dlg.destroy()
            if not APP_SETTINGS.get("silent_apply", False):
                messagebox.showinfo("[+] Applied", name)
            self._after_state_change()

        make_button(dlg, "Apply" if CURRENT_LANG == "en" else "تطبيق",
                    do_apply, fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack(pady=10)

    def _dialog_link_tweaks(self, code_id):
        """Dialog for link tweaks with EXE code."""
        # check if already applied (scan detects via offset 7212FC)
        # detect: bytes at 7212FC != 31 2E 30 2E 36 means ON
        exe = self.exe_path.get().strip()

        dlg = tk.Toplevel(self)
        dlg.title("Link Tweaks with EXE" if CURRENT_LANG == "en" else "ربط التويكس مع EXE")
        dlg.geometry("420x300")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg,
                   "Link Tweaks with EXE" if CURRENT_LANG == "en" else "ربط التويكس مع EXE",
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL
                   ).pack(pady=(16, 4))
        make_label(dlg,
                   "Enter a 5-character keyword (e.g. 3MKOO)"
                   if CURRENT_LANG == "en" else
                   "أدخل كلمة من 5 أحرف (مثال: 3MKOO)",
                   fg=MUTED, bg="#111", font=FONT_TINY
                   ).pack(pady=(0, 10))

        fields_frame = tk.Frame(dlg, bg="#111")
        fields_frame.pack(fill="x", padx=20)

        def add_row(label_text, default="", browse=False, is_dll=False):
            row = tk.Frame(fields_frame, bg="#111")
            row.pack(fill="x", pady=3)
            make_label(row, label_text, fg=TEXT_DIM, bg="#111",
                       font=FONT_TINY, width=20, anchor="w"
                       ).pack(side="left")
            var = tk.StringVar(value=default)
            e = tk.Entry(row, textvariable=var,
                         font=FONT_SMALL, fg=ACCENT2, bg="#1a1a1a",
                         insertbackground=ACCENT2, relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=BORDER,
                         width=22)
            e.pack(side="left", ipady=2)
            self._add_paste_menu(e)
            if browse:
                def pick(v=var, dll=is_dll):
                    ft = [("DLL file", "*.dll"), ("All files", "*.*")] if dll \
                         else [("Executable", "*.exe"), ("All files", "*.*")]
                    p = filedialog.askopenfilename(filetypes=ft)
                    if p:
                        v.set(p)
                make_button(row, "...", pick,
                            fg=ACCENT, bg="#2a2a1a", active_bg="#3a3a2a",
                            font=FONT_TINY, width=3
                            ).pack(side="left", padx=4)
            return var

        exe_var  = add_row("EXE path:", exe, browse=True, is_dll=False)
        word_var = add_row("Keyword (5 chars):", "")
        dll_var  = add_row("DLL path:", "", browse=True, is_dll=True)

        # word length validation
        def on_word_change(*_):
            w = word_var.get()
            if len(w) > 5:
                word_var.set(w[:5])

        word_var.trace_add("write", on_word_change)

        def do_apply():
            exe_path = exe_var.get().strip()
            word     = word_var.get().strip()
            dll_path = dll_var.get().strip()

            if not exe_path or not os.path.isfile(exe_path):
                messagebox.showerror("Error", "Invalid EXE path.")
                return
            if len(word) != 5:
                messagebox.showerror("Error",
                    "Keyword must be exactly 5 characters."
                    if CURRENT_LANG == "en" else
                    "الكلمة لازم تكون 5 أحرف بالضبط.")
                return

            # convert word to hex bytes
            word_bytes = word.encode("ascii").hex().upper()
            word_spaced = " ".join(word_bytes[i:i+2] for i in range(0, len(word_bytes), 2))

            # build patches
            patches = [
                {"type": "offset_replace", "offset": "7212FC", "bytes": word_spaced},
            ]
            if dll_path and os.path.isfile(dll_path):
                patches.append({"type": "offset_replace", "offset": "894054",
                                 "bytes": word_spaced})

            # apply directly
            try:
                with open(exe_path, "rb") as f:
                    exe_data = bytearray(f.read())
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return

            backup = load_patch_backup()
            code_backup = {}
            for p in patches:
                target = exe_path if p["offset"] == "7212FC" else dll_path
                try:
                    with open(target, "r+b") as f:
                        off = int(p["offset"], 16)
                        data_b = bytes.fromhex(p["bytes"].replace(" ", ""))
                        f.seek(off)
                        orig_b = f.read(len(data_b))
                        code_backup[p["offset"]] = orig_b.hex().upper()
                        f.seek(off)
                        f.write(data_b)
                except Exception as e:
                    messagebox.showerror("Error", "Failed at offset " + p["offset"] + ":\n" + str(e))
                    return

            backup[code_id] = code_backup
            save_patch_backup(backup)
            self.applied[code_id] = True
            write_log("APPLIED", "Link Tweaks with EXE -- keyword: " + word, exe_path)
            dlg.destroy()
            messagebox.showinfo("[+] Applied",
                                "Tweaks linked with keyword: " + word
                                if CURRENT_LANG == "en" else
                                "تم ربط التويكس بالكلمة: " + word)
            self._after_state_change()

        make_button(dlg, "Apply" if CURRENT_LANG == "en" else "تطبيق",
                    do_apply, fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=12
                    ).pack(pady=14)

    def _dialog_bgm_files(self, code_id):
        # ── Step 1: ask how many files ──
        dlg1 = tk.Toplevel(self)
        dlg1.title("Additional BGM Files")
        dlg1.geometry("340x160")
        dlg1.resizable(False, False)
        dlg1.configure(bg="#111")
        dlg1.grab_set()

        make_label(dlg1, "How many BGM files to add? (max 8)",
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL
                   ).pack(pady=(18, 6))
        make_label(dlg1, "Each file = one XWB + one XSB pair",
                   fg=MUTED, bg="#111", font=FONT_TINY
                   ).pack()

        count_var = tk.IntVar(value=1)
        spin_frame = tk.Frame(dlg1, bg="#111")
        spin_frame.pack(pady=10)
        tk.Spinbox(
            spin_frame, from_=1, to=8,
            textvariable=count_var, width=5,
            font=FONT_NORMAL, fg=ACCENT2, bg="#1a1a1a",
            buttonbackground="#2a2a2a",
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER
        ).pack(side="left", ipady=4)

        def next_step():
            n = count_var.get()
            dlg1.destroy()
            self._dialog_bgm_names(code_id, n)

        btn_row = tk.Frame(dlg1, bg="#111")
        btn_row.pack(pady=4)
        make_button(btn_row, "Next >>", next_step,
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack(side="left", padx=8)
        make_button(btn_row, "Cancel", dlg1.destroy,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=8
                    ).pack(side="left", padx=4)

    def _dialog_bgm_names(self, code_id, count):
        MAX_NAME = 20   # BIO4\snd\ = 10 chars, name+ext ≤ 22 chars, total ≤ 32
        ENTRY_SIZE = 32 # bytes per entry (matches game expectation)
        BASE_PATH = "BIO4\\snd\\"

        dlg2 = tk.Toplevel(self)
        dlg2.title("BGM File Names")
        dlg2.geometry("420x" + str(80 + count * 56))
        dlg2.resizable(False, True)
        dlg2.configure(bg="#111")
        dlg2.grab_set()

        make_label(dlg2, "Enter file names (without path or extension):",
                   fg=ACCENT2, bg="#111", font=FONT_SMALL
                   ).pack(pady=(14, 4), padx=16, anchor="w")
        make_label(dlg2, "Example: 1234567   ->  BIO4\\snd\\1234567.xwb / .xsb",
                   fg=MUTED, bg="#111", font=FONT_TINY
                   ).pack(padx=16, anchor="w")

        entries = []
        for i in range(count):
            row = tk.Frame(dlg2, bg="#111")
            row.pack(fill="x", padx=16, pady=4)
            make_label(row, "File " + str(i + 1) + ":",
                       fg=TEXT_DIM, bg="#111", font=FONT_TINY, width=7
                       ).pack(side="left")
            var = tk.StringVar()
            tk.Entry(
                row, textvariable=var,
                font=FONT_SMALL, fg=ACCENT2, bg="#1a1a1a",
                insertbackground=ACCENT2,
                relief="flat", bd=0,
                highlightthickness=1, highlightbackground=BORDER,
                width=24
            ).pack(side="left", ipady=3)
            entries.append(var)

        def do_apply():
            # validate
            names = [v.get().strip() for v in entries]
            for i, name in enumerate(names):
                if not name:
                    messagebox.showerror("Error", "File " + str(i+1) + " name is empty.")
                    return
                full = BASE_PATH + name + ".xwb"
                if len(full) > ENTRY_SIZE - 1:   # -1 for null terminator
                    messagebox.showerror("Error",
                        "File " + str(i+1) + " name too long.\n"
                        "Max " + str(ENTRY_SIZE - 1 - len(BASE_PATH) - 4) + " characters.")
                    return

            # build the 32-byte entries: XWB then XSB for each file, packed together
            # layout: [xwb_entry_32][xsb_entry_32] per file, sequential
            payload = bytearray()
            for name in names:
                xwb = (BASE_PATH + name + ".xwb").encode("ascii")
                xsb = (BASE_PATH + name + ".xsb").encode("ascii")
                # pad each to ENTRY_SIZE bytes with nulls
                xwb_entry = xwb + b'\x00' * (ENTRY_SIZE - len(xwb))
                xsb_entry = xsb + b'\x00' * (ENTRY_SIZE - len(xsb))
                payload += xwb_entry + xsb_entry

            # patch the additional_bgm code normally first (the JMP patches)
            # then write the string table at 0x0078C200
            dlg2.destroy()

            exe = self.exe_path.get().strip()
            if not exe or not os.path.isfile(exe):
                messagebox.showerror("Error", "EXE path is invalid.")
                return

            # apply the code patches (JMP hooks) first
            ok, msg = apply_patch(exe, code_id, self.codes_data)
            if not ok:
                messagebox.showerror("Error", "Failed applying BGM patches:\n" + msg)
                return

            # now write the string table
            STRING_TABLE_OFFSET = 0x0078C200
            try:
                with open(exe, "r+b") as f:
                    f.seek(STRING_TABLE_OFFSET)
                    # clear the area first (8 files max * 2 entries * 32 bytes)
                    f.write(b'\x00' * (8 * 2 * ENTRY_SIZE))
                    f.seek(STRING_TABLE_OFFSET)
                    f.write(bytes(payload))
            except Exception as e:
                messagebox.showerror("Error", "Failed writing string table:\n" + str(e))
                return

            self.applied[code_id] = True
            self._refresh_all()
            self._update_statusbar()
            self._update_apply_bar()

            summary = "BGM files written:\n"
            for name in names:
                summary += "  " + BASE_PATH + name + ".xwb/.xsb\n"
            messagebox.showinfo("[+] Done", summary)

        btn_row = tk.Frame(dlg2, bg="#111")
        btn_row.pack(pady=8)
        make_button(btn_row, "Apply", do_apply,
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack(side="left", padx=8)
        make_button(btn_row, "Cancel", dlg2.destroy,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=8
                    ).pack(side="left", padx=4)

    def _dialog_mod_expansion(self, code_id):
        dlg = tk.Toplevel(self)
        dlg.title("Enemy Spawn Persistence")
        dlg.geometry("380x180")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, (fix_ar("هل انت مفعل EnableModExpansion؟") if CURRENT_LANG == "ar" else "Is EnableModExpansion active?"),
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL
                   ).pack(pady=(20, 6))
        make_label(dlg, (fix_ar("سيؤثر هاذا على الكود اللي راح ينحط في EXE") if CURRENT_LANG == "ar" else "This affects the code written to EXE"),
                   fg=MUTED, bg="#111", font=FONT_TINY
                   ).pack()

        btn_frame = tk.Frame(dlg, bg="#111")
        btn_frame.pack(pady=20)

        make_button(btn_frame, "[Y] Yes",
                    lambda: [dlg.destroy(),
                             self._do_apply(code_id, mod_expansion=True)],
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "[N] No",
                    lambda: [dlg.destroy(),
                             self._do_apply(code_id, mod_expansion=False)],
                    fg=RED_SOFT, bg="#2a0a0a", active_bg="#4a1a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "Cancel", dlg.destroy,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=9
                    ).pack(side="left", padx=8)

    def _do_apply(self, code_id, mod_expansion=None):
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "EXE path is invalid.")
            return
        if is_game_running(exe):
            messagebox.showerror(
                "Game is Running" if CURRENT_LANG == "en" else "اللعبة شغالة",
                "Please close the game before applying codes.\nClose bio4.exe and try again."
                if CURRENT_LANG == "en" else
                "طفي اللعبة أول عشان تقدر تفعل الكود.\nأغلق bio4.exe وحاول مرة ثانية."
            )
            return
        # handle mutual exclusion before applying
        self._handle_dll_mutex(code_id)
        ok, msg = apply_patch(exe, code_id, self.codes_data, mod_expansion)
        if ok:
            self.applied[code_id] = True
            backup  = load_patch_backup()
            details = build_log_details(code_id, self.codes_data, backup)
            write_log("APPLIED", self.code_by_id[code_id]["name"], exe, details)
            if not APP_SETTINGS.get("silent_apply", False):
                messagebox.showinfo(
                    "[+] Applied",
                    "Code applied:\n" + self.code_by_id[code_id]["name"]
                )
            self._after_state_change()
        else:
            messagebox.showerror("Error", "Failed:\n" + msg)

    # ── Apply Selected ────────────────────────────────────────────────────────

    def on_row_select_change(self):
        self._update_apply_bar()

    def _update_apply_bar(self):
        n = len(self._global_selected)
        self.selected_count_var.set(str(n) + " selected")

    def _select_all(self):
        for cid, row in self.code_rows.items():
            if self._is_unlocked(cid) and not self.applied.get(cid, False):
                row.sel_var.set(1)
                row.selected = True
                self._global_selected.add(cid)
        self._refresh_all()
        self._update_apply_bar()

    def _clear_selection(self):
        for row in self.code_rows.values():
            row.sel_var.set(0)
            row.selected = False
        self._global_selected.clear()
        self._refresh_all()
        self._update_apply_bar()

    def _apply_selected(self):
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        queue = [cid for cid in self._global_selected
                 if not self.applied.get(cid, False)]

        if not queue:
            messagebox.showinfo("Info", "No codes selected.")
            return

        needs_dialog = [c for c in queue
                        if self.code_by_id.get(c, {}).get("dialog") == "mod_expansion"]
        if needs_dialog:
            self._dialog_mod_expansion_batch(queue)
        else:
            self._run_apply_queue(queue, mod_expansion=None)

    def _dialog_mod_expansion_batch(self, full_queue):
        dlg = tk.Toplevel(self)
        dlg.title("Enemy Spawn Persistence")
        dlg.geometry("380x180")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, (fix_ar("هل انت مفعل EnableModExpansion؟") if CURRENT_LANG == "ar" else "Is EnableModExpansion active?"),
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL
                   ).pack(pady=(20, 6))
        make_label(dlg, (fix_ar("سيؤثر هاذا على الكود اللي راح ينحط في EXE") if CURRENT_LANG == "ar" else "This affects the code written to EXE"),
                   fg=MUTED, bg="#111", font=FONT_TINY
                   ).pack()

        btn_frame = tk.Frame(dlg, bg="#111")
        btn_frame.pack(pady=20)

        make_button(btn_frame, "[Y] Yes",
                    lambda: [dlg.destroy(),
                             self._run_apply_queue(full_queue, mod_expansion=True)],
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "[N] No",
                    lambda: [dlg.destroy(),
                             self._run_apply_queue(full_queue, mod_expansion=False)],
                    fg=RED_SOFT, bg="#2a0a0a", active_bg="#4a1a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "Cancel", dlg.destroy,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=9
                    ).pack(side="left", padx=8)

    def _run_apply_queue(self, queue, mod_expansion=None):
        exe = self.exe_path.get().strip()
        success, failed = [], []

        for code_id in queue:
            self._handle_dll_mutex(code_id)
            me = mod_expansion if self.code_by_id.get(
                code_id, {}).get("dialog") == "mod_expansion" else None
            ok, msg = apply_patch(exe, code_id, self.codes_data, me)
            if ok:
                self.applied[code_id] = True
                details = build_log_details(code_id, self.codes_data, load_patch_backup())
                write_log("APPLIED", self.code_by_id.get(code_id, {}).get("name", code_id), exe, details)
                success.append(code_id)
            else:
                failed.append((code_id, msg))

        summary = "Applied " + str(len(success)) + " code(s) successfully."
        if failed:
            summary += "\n\nFailed:\n"
            for cid, err in failed:
                summary += "- " + self.code_by_id[cid]["name"] + "\n  " + err + "\n"
            messagebox.showwarning("Done with errors", summary)
        else:
            messagebox.showinfo("[+] Done", summary)

        # clear all selections after apply
        self._global_selected.clear()
        self._after_state_change()

    # ── refresh ───────────────────────────────────────────────────────────────

    def _refresh_row(self, code_id):
        row = self.code_rows.get(code_id)
        if not row:
            return
        row.refresh(
            applied  = self.applied.get(code_id, False),
            locked   = not self._is_unlocked(code_id),
            detected = self.detected.get(code_id, False)
        )

    def _refresh_all(self):
        """Refresh all visible rows in current section."""
        for cid in list(self.code_rows.keys()):
            self._refresh_row(cid)

    def _after_state_change(self):
        scroll_pos = self.codes_canvas.yview()[0]
        self._refresh_all()
        if self.active_section:
            self.select_section(self.active_section, preserve_scroll=scroll_pos)
        self._update_statusbar()
        self._update_apply_bar()

    # ── mutual exclusion: codes sharing same offsets ─────────────────────────
    # Format: code_id -> list of conflicting code_ids
    OFFSET_MUTEX = {
        # DLL apply codes share offset 156
        "apply_dll_qingsheng": ["apply_dll_raz0r"],
        "apply_dll_raz0r":     ["apply_dll_qingsheng"],
        # bodies disappear/no-disappear share same offsets
        "bodies_disappear":    ["bodies_no_disappear"],
        "bodies_no_disappear": ["bodies_disappear"],
        # verdugo versions share same find pattern + offset C2440
        "verdugo_no_teleport":       ["verdugo_no_teleport_raz0r"],
        "verdugo_no_teleport_raz0r": ["verdugo_no_teleport"],
        # saw: killable vs survive chainsaw share offset 3E4E3
        "saw_killable":     ["survive_chainsaw"],
        "survive_chainsaw": ["saw_killable"],
        # u3: esl vs form1 share offset 1034CA
        "u3_esl":        ["u3_form1_kill"],
        "u3_form1_kill": ["u3_esl"],
        # u3: form1 vs die_in_place share offset FE9C2
        "u3_form1_kill":  ["u3_die_in_place"],
        "u3_die_in_place": ["u3_form1_kill"],
        # xwb sideload vs em_xwb_xsb share offset 575487
        "xwb_sideload_r": ["em_xwb_xsb"],
        "em_xwb_xsb":     ["xwb_sideload_r"],
        # cns_x4 disables max_em_count when enabled, but not vice versa
        "cns_x4": ["max_em_count"],
    }

    def _handle_dll_mutex(self, code_id):
        """Revert all conflicting codes before applying code_id."""
        conflicts = self.OFFSET_MUTEX.get(code_id, [])
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            return
        for other in conflicts:
            if self.applied.get(other, False):
                ok, _, _ = revert_patch(exe, ORIG_FILE, other, self.codes_data)
                if ok:
                    self.applied[other] = False
                    self.detected[other] = False

    def _dialog_mod_expansion_batch_profile(self, queue, exe):
        """Called when profile queue contains enemy_persistence."""
        dlg = tk.Toplevel(self)
        dlg.title("Enemy Spawn Persistence")
        dlg.geometry("380x190")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg,
                   "Is EnableModExpansion active?" if CURRENT_LANG == "en"
                   else (fix_ar("هل انت مفعل EnableModExpansion؟") if CURRENT_LANG == "ar" else "Is EnableModExpansion active?"),
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL
                   ).pack(pady=(20, 6))
        make_label(dlg,
                   "This affects the enemy_persistence code in the profile."
                   if CURRENT_LANG == "en"
                   else (fix_ar("سيؤثر هاذا على كود enemy_persistence في البروفايل") if CURRENT_LANG == "ar" else "This affects enemy_persistence in the profile"),
                   fg=MUTED, bg="#111", font=FONT_TINY
                   ).pack()

        btn_frame = tk.Frame(dlg, bg="#111")
        btn_frame.pack(pady=20)

        def run(mod_exp):
            dlg.destroy()
            success, failed = [], []
            for cid in queue:
                self._handle_dll_mutex(cid)
                me = mod_exp if self.code_by_id.get(cid, {}).get("dialog") == "mod_expansion" else None
                ok, msg = apply_patch(exe, cid, self.codes_data, me)
                if ok:
                    self.applied[cid] = True
                    write_log("APPLIED (profile)", self.code_by_id.get(cid, {}).get("name", cid), exe)
                    success.append(cid)
                else:
                    failed.append((cid, msg))
                    break
            summary = "Applied " + str(len(success)) + " code(s)."
            if failed:
                summary += "\n\nStopped at:\n"
                for cid, err in failed:
                    summary += "- " + self.code_by_id.get(cid, {}).get("name", cid) + "\n  " + err + "\n"
                messagebox.showwarning("Done with errors", summary)
            else:
                messagebox.showinfo("[+] Done", summary)
            self._after_state_change()

        make_button(btn_frame, "[Y] Yes", lambda: run(True),
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "[N] No", lambda: run(False),
                    fg=RED_SOFT, bg="#2a0a0a", active_bg="#4a1a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "Cancel", dlg.destroy,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=9
                    ).pack(side="left", padx=8)

    def _update_statusbar(self):
        n_applied  = sum(1 for v in self.applied.values() if v)
        n_detected = sum(1 for v in self.detected.values() if v)
        n_total    = len(self.all_codes)
        self.status_applied_var.set(
            ("Applied: " if CURRENT_LANG == "en" else "مفعّل: ") + str(n_applied))
        self.status_detected_var.set(
            ("Detected: " if CURRENT_LANG == "en" else "مكتشف: ") + str(n_detected))
        self.status_exe_var.set(
            ("[OK] EXE Loaded" if CURRENT_LANG == "en" else "[OK] EXE محمّل")
            if self.scanned else "")
        self.status_total_var.set(
            ("Total codes: " if CURRENT_LANG == "en" else "إجمالي الأكواد: ") + str(n_total))

    # ── Search ────────────────────────────────────────────────────────────────

    def _on_search(self):
        query = self.search_var.get().strip().lower()
        # clear old results
        for w in self.search_results_frame.winfo_children():
            w.destroy()

        if not query:
            self.search_results_outer.pack_forget()
            return

        # find matching codes
        matches = []
        for code in self.all_codes:
            name    = code.get("name_en" if CURRENT_LANG == "en" else "name", "")
            desc    = code.get("desc_en" if CURRENT_LANG == "en" else "desc", "")
            if query in name.lower() or query in desc.lower():
                matches.append(code)

        if not matches:
            make_label(self.search_results_frame,
                       text="No results found" if CURRENT_LANG == "en" else "ما في نتائج",
                       fg=MUTED, bg="#0d0d1a", font=FONT_TINY
                       ).pack(padx=8, pady=4)
        else:
            for code in matches[:12]:  # max 12 results
                sec = next((s for s in self.sections_list if s["id"] == code["section"]), None)
                sec_label = sec.get("label_en" if CURRENT_LANG == "en" else "label", "") if sec else ""
                name = code.get("name_en" if CURRENT_LANG == "en" else "name", code["name"])

                row = tk.Frame(self.search_results_frame, bg="#0d0d1a",
                               cursor="hand2")
                row.pack(fill="x", padx=4, pady=1)

                make_label(row, text=name,
                           fg=ACCENT2, bg="#0d0d1a", font=FONT_TINY
                           ).pack(side="left", padx=6, pady=2)
                make_label(row, text="[" + sec_label + "]",
                           fg=MUTED, bg="#0d0d1a", font=FONT_TINY
                           ).pack(side="left")

                # click -> go to section and highlight
                def _goto(c=code):
                    self._clear_search()
                    self.select_section(c["section"])
                    # scroll to the row
                    self.after(100, lambda: self._scroll_to_code(c["id"]))

                row.bind("<Button-1>", lambda e, c=code: _goto(c))
                for child in row.winfo_children():
                    child.bind("<Button-1>", lambda e, c=code: _goto(c))

        self.search_results_outer.pack(fill="x", padx=10, pady=(0, 4))

    def _scroll_to_code(self, code_id):
        row = self.code_rows.get(code_id)
        if not row:
            return
        self.codes_canvas.update_idletasks()
        row.update_idletasks()
        # get row y position relative to codes_inner
        y = row.winfo_y()
        total = self.codes_inner.winfo_height()
        if total > 0:
            frac = y / total
            self.codes_canvas.yview_moveto(frac)

    def _clear_search(self):
        self.search_var.set("")
        self.search_results_outer.pack_forget()
        for w in self.search_results_frame.winfo_children():
            w.destroy()

    # ── Profiles ─────────────────────────────────────────────────────────────

    def _new_profile(self):
        dlg = tk.Toplevel(self)
        dlg.title("New Profile")
        dlg.geometry("500x520")
        dlg.resizable(False, True)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, "Profile Name:",
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL
                   ).pack(pady=(16, 4), padx=16, anchor="w")
        name_var = tk.StringVar()
        tk.Entry(dlg, textvariable=name_var,
                 font=FONT_SMALL, fg=ACCENT2, bg="#1a1a1a",
                 insertbackground=ACCENT2, relief="flat", bd=0,
                 highlightthickness=1, highlightbackground=BORDER,
                 width=40
                 ).pack(padx=16, ipady=3, anchor="w")

        make_label(dlg, "Select codes to include:",
                   fg=TEXT_DIM, bg="#111", font=FONT_SMALL
                   ).pack(pady=(12, 4), padx=16, anchor="w")

        # scrollable checklist
        list_outer = tk.Frame(dlg, bg="#111")
        list_outer.pack(fill="both", expand=True, padx=16)
        list_canvas = tk.Canvas(list_outer, bg="#1a1a1a",
                                highlightthickness=1,
                                highlightbackground=BORDER, height=300)
        list_scroll = tk.Scrollbar(list_outer, orient="vertical",
                                   command=list_canvas.yview)
        list_canvas.configure(yscrollcommand=list_scroll.set)
        list_scroll.pack(side="right", fill="y")
        list_canvas.pack(side="left", fill="both", expand=True)

        list_inner = tk.Frame(list_canvas, bg="#1a1a1a")
        list_canvas.create_window((0, 0), window=list_inner, anchor="nw")
        list_inner.bind("<Configure>",
                        lambda e: list_canvas.configure(
                            scrollregion=list_canvas.bbox("all")))

        chk_vars = {}
        for code in self.all_codes:
            var = tk.IntVar(value=0)
            name = code.get("name_en" if CURRENT_LANG == "en" else "name", code["name"])
            tk.Checkbutton(
                list_inner, text=name, variable=var,
                font=FONT_TINY, fg=TEXT_MAIN, bg="#1a1a1a",
                activebackground="#1a1a1a", selectcolor="#2a2a2a",
                anchor="w", relief="flat"
            ).pack(fill="x", padx=6, pady=1)
            chk_vars[code["id"]] = var

        def save_profile():
            pname = name_var.get().strip()
            if not pname:
                messagebox.showerror("Error", "Please enter a profile name.")
                return
            selected = [cid for cid, v in chk_vars.items() if v.get()]
            if not selected:
                messagebox.showerror("Error", "Select at least one code.")
                return
            os.makedirs(PROFILES_DIR, exist_ok=True)
            path = os.path.join(PROFILES_DIR, pname + ".json")
            profile = {
                "name": pname,
                "description": "",
                "codes": selected
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
            dlg.destroy()
            messagebox.showinfo("[+] Saved",
                                "Profile saved:\n" + path)

        make_button(dlg, "Save Profile", save_profile,
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=14
                    ).pack(pady=10)

    def _load_profile(self):
        os.makedirs(PROFILES_DIR, exist_ok=True)
        files = [f for f in os.listdir(PROFILES_DIR) if f.endswith(".json")]
        if not files:
            messagebox.showinfo("Profiles",
                                "No profiles found in:\n" + PROFILES_DIR)
            return

        dlg = tk.Toplevel(self)
        dlg.title("Load Profile")
        dlg.geometry("360x300")
        dlg.resizable(False, True)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, "Select a profile:",
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL
                   ).pack(pady=(16, 8))

        listbox = tk.Listbox(
            dlg, font=FONT_SMALL,
            fg=TEXT_MAIN, bg="#1a1a1a",
            selectbackground="#2a3a1a", selectforeground=GREEN,
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER,
            height=10
        )
        for f in files:
            listbox.insert("end", f.replace(".json", ""))
        listbox.pack(fill="both", expand=True, padx=16, pady=4)

        def do_load():
            sel = listbox.curselection()
            if not sel:
                messagebox.showerror("Error", "Select a profile first.")
                return
            fname = files[sel[0]]
            path = os.path.join(PROFILES_DIR, fname)
            try:
                with open(path, encoding="utf-8") as f:
                    profile = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", "Failed to load profile:\n" + str(e))
                return

            dlg.destroy()

            exe = self.exe_path.get().strip()
            if not exe or not os.path.isfile(exe):
                messagebox.showerror("Error", "Please select a valid bio4.exe first.")
                return
            if not self.scanned:
                messagebox.showerror("Error", "Please Scan the EXE first.")
                return

            queue = [cid for cid in profile.get("codes", [])
                     if cid in self.code_by_id and not self.applied.get(cid, False)]
            if not queue:
                messagebox.showinfo("Profile", "All codes in this profile are already applied.")
                return

            names = "\n".join("  - " + self.code_by_id.get(c, {}).get("name", c)
                              for c in queue)
            if not messagebox.askyesno("Load Profile",
                                       "Apply codes from profile '" +
                                       profile.get("name", fname) + "'?\n\n" + names):
                return

            # check if queue has enemy_persistence (needs mod_expansion dialog)
            needs_dialog = [c for c in queue
                            if self.code_by_id.get(c, {}).get("dialog") == "mod_expansion"]
            if needs_dialog:
                self._dialog_mod_expansion_batch_profile(queue, exe)
                return

            # apply in order, stop on failure
            success, failed = [], []
            for cid in queue:
                self._handle_dll_mutex(cid)
                ok, msg = apply_patch(exe, cid, self.codes_data)
                if ok:
                    self.applied[cid] = True
                    write_log("APPLIED (profile)", self.code_by_id.get(cid, {}).get("name", cid), exe)
                    success.append(cid)
                else:
                    failed.append((cid, msg))
                    break

            summary = "Applied " + str(len(success)) + " code(s)."
            if failed:
                summary += "\n\nStopped at:\n"
                for cid, err in failed:
                    summary += "- " + self.code_by_id.get(cid, {}).get("name", cid) + "\n  " + err + "\n"
                messagebox.showwarning("Done with errors", summary)
            else:
                messagebox.showinfo("[+] Done", summary)

            self._after_state_change()

        btn_row = tk.Frame(dlg, bg="#111")
        btn_row.pack(pady=8)
        make_button(btn_row, "Load", do_load,
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=10
                    ).pack(side="left", padx=8)
        make_button(btn_row, "Cancel", dlg.destroy,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=8
                    ).pack(side="left", padx=4)

    # ── Add New Code ──────────────────────────────────────────────────────────

    def _add_new_code(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add New Code")
        dlg.geometry("480x560")
        dlg.resizable(False, True)
        dlg.configure(bg="#111")
        dlg.grab_set()

        fields = {}

        def add_field(label, key, height=1):
            make_label(dlg, label, fg=TEXT_DIM, bg="#111", font=FONT_SMALL
                       ).pack(pady=(10, 2), padx=16, anchor="w")
            if height == 1:
                var = tk.StringVar()
                tk.Entry(dlg, textvariable=var,
                         font=FONT_SMALL, fg=ACCENT2, bg="#1a1a1a",
                         insertbackground=ACCENT2, relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=BORDER,
                         width=52
                         ).pack(padx=16, ipady=3, anchor="w")
                fields[key] = var
            else:
                t = tk.Text(dlg, font=FONT_SMALL, fg=ACCENT2, bg="#1a1a1a",
                            insertbackground=ACCENT2, relief="flat", bd=0,
                            highlightthickness=1, highlightbackground=BORDER,
                            width=52, height=height)
                t.pack(padx=16, anchor="w")
                fields[key] = t

        # Section dropdown
        make_label(dlg, "Section:", fg=TEXT_DIM, bg="#111", font=FONT_SMALL
                   ).pack(pady=(16, 2), padx=16, anchor="w")
        sec_var = tk.StringVar()
        sec_names = [s.get("label_en" if CURRENT_LANG == "en" else "label", s["id"])
                     for s in self.sections_list]
        sec_ids   = [s["id"] for s in self.sections_list]
        sec_menu = tk.OptionMenu(dlg, sec_var, *sec_names)
        sec_menu.configure(font=FONT_SMALL, fg=TEXT_MAIN, bg="#1a1a1a",
                           activebackground="#2a2a2a", relief="flat",
                           highlightthickness=1, highlightbackground=BORDER)
        sec_menu.pack(padx=16, anchor="w")
        sec_var.set(sec_names[0])

        add_field("Code Name:", "name")
        add_field("Description:", "desc")

        # Requires
        make_label(dlg, "Requires another code? (leave blank if none):",
                   fg=TEXT_DIM, bg="#111", font=FONT_SMALL
                   ).pack(pady=(10, 2), padx=16, anchor="w")
        req_var = tk.StringVar()
        req_names = ["(none)"] + [c.get("name_en" if CURRENT_LANG == "en" else "name", c["id"])
                                   for c in self.all_codes]
        req_ids   = [None]    + [c["id"] for c in self.all_codes]
        req_menu = tk.OptionMenu(dlg, req_var, *req_names)
        req_menu.configure(font=FONT_SMALL, fg=TEXT_MAIN, bg="#1a1a1a",
                           activebackground="#2a2a2a", relief="flat",
                           highlightthickness=1, highlightbackground=BORDER)
        req_menu.pack(padx=16, anchor="w")
        req_var.set(req_names[0])

        add_field("Code (offset - bytes, e.g.  4DE390 - C3):", "code", height=4)

        def parse_code_text(text):
            """
            Parse code text in any of these formats:

            Format 1 - offset/paste:
                Find: 002B8417
                Paste:
                E8 68 8D D4 FF

            Format 2 - find/replace (Change To):
                83 C4 08 81 60 54
                Change To:
                A3 00 0E 2E 10 83

            Format 3 - simple offset:
                4DE390 - C3
                4DE391 to C3
            """
            patches = []
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            i = 0
            while i < len(lines):
                line = lines[i]
                line_up = line.upper()

                # Format 1: Find: OFFSET  /  Paste: / BYTES
                if line_up.startswith("FIND:") or line_up.startswith("FIND :"):
                    offset = line.split(":", 1)[1].strip()
                    # next non-empty line should be Paste: or bytes
                    i += 1
                    # skip "Paste:" line
                    if i < len(lines) and lines[i].upper().startswith("PASTE"):
                        i += 1
                    # collect bytes (may span multiple lines until next keyword)
                    byte_parts = []
                    while i < len(lines):
                        nxt = lines[i]
                        nxt_up = nxt.upper()
                        if (nxt_up.startswith("FIND") or
                            nxt_up.startswith("CHANGE") or
                            ("-" in nxt and len(nxt.split("-")[0].strip()) <= 8)):
                            break
                        byte_parts.append(nxt)
                        i += 1
                    byt = " ".join(" ".join(byte_parts).split())
                    if offset and byt:
                        patches.append({
                            "type": "offset_paste",
                            "offset": offset,
                            "bytes": byt
                        })
                    continue

                # Format 2: FIND_BYTES / Change To: / REPLACE_BYTES
                # detect if next non-empty line contains "Change To"
                if i + 1 < len(lines) and "CHANGE TO" in lines[i+1].upper():
                    find_bytes = line
                    i += 2  # skip "Change To:" line
                    # collect replace bytes
                    rep_parts = []
                    while i < len(lines):
                        nxt = lines[i]
                        nxt_up = nxt.upper()
                        if (nxt_up.startswith("FIND") or
                            "CHANGE TO" in nxt_up or
                            ("-" in nxt and len(nxt.split("-")[0].strip()) <= 8)):
                            break
                        rep_parts.append(nxt)
                        i += 1
                    rep_bytes = " ".join(" ".join(rep_parts).split())
                    if find_bytes and rep_bytes:
                        patches.append({
                            "type": "find_replace",
                            "find": find_bytes,
                            "replace": rep_bytes
                        })
                    continue

                # Format 3: OFFSET - BYTES  or  OFFSET to BYTES
                sep = None
                if " - " in line:
                    sep = " - "
                elif " to " in line.lower():
                    sep = line.lower().index(" to ")
                    sep = line[sep:sep+4]  # preserve original case

                if sep:
                    parts = line.split(sep, 1)
                    if len(parts) == 2:
                        offset = parts[0].strip()
                        byt    = parts[1].strip()
                        if offset and byt:
                            patches.append({
                                "type": "offset_replace",
                                "offset": offset,
                                "bytes": byt
                            })
                    i += 1
                    continue

                # skip unrecognized lines
                i += 1

            return patches

        def save_new_code():
            name = fields["name"].get().strip()
            desc = fields["desc"].get().strip()
            code_text = fields["code"].get("1.0", "end").strip()
            sec_label = sec_var.get()
            sec_id = sec_ids[sec_names.index(sec_label)]
            req_label = req_var.get()
            req_id = req_ids[req_names.index(req_label)] if req_label != "(none)" else None

            if not name:
                messagebox.showerror("Error", "Code name is required.")
                return
            if not code_text:
                messagebox.showerror("Error", "Code bytes are required.")
                return

            patches = parse_code_text(code_text)
            if not patches:
                messagebox.showerror("Error",
                    "Could not parse the code.\n\n"
                    "Supported formats:\n"
                    "  Find: OFFSET\n  Paste:\n  BYTES\n\n"
                    "  FIND_BYTES\n  Change To:\n  REPLACE_BYTES\n\n"
                    "  OFFSET - BYTES\n  OFFSET to BYTES")
                return

            # generate id from name
            import re
            cid = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
            if cid in self.code_by_id:
                cid = cid + "_custom"

            # add to codes_info
            new_info = {
                "id": cid,
                "section": sec_id,
                "name": name,
                "name_en": name,
                "desc": desc,
                "desc_en": desc,
                "notes": [],
                "notes_en": [],
                "requires": [req_id] if req_id else [],
                "detectable": True
            }
            self.codes_info["codes"].append(new_info)
            self.code_by_id[cid] = new_info
            self.codes_by_section.setdefault(sec_id, []).append(new_info)
            self.all_codes = self.codes_info["codes"]

            # add to codes_data
            self.codes_data[cid] = {"patches": patches}

            # save both files
            try:
                with open(INFO_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.codes_info, f, ensure_ascii=False, indent=2)
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.codes_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                messagebox.showerror("Error", "Failed to save:\n" + str(e))
                return

            dlg.destroy()
            messagebox.showinfo("[+] Added",
                                "Code added successfully:\n" + name +
                                "\nIn section: " + sec_label)
            self._after_state_change()

        make_button(dlg, "Add Code", save_new_code,
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=12
                    ).pack(pady=12)



# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2: MDT COLOR EDITOR
# ═════════════════════════════════════════════════════════════════════════════

class MDTColorPanel(tk.Frame):
    """MDT Color Editor — two sub-sections: Speech Color Change + Custom Color"""

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.master_app = master_app
        self._built = False

    def activate(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        # tab bar
        self._tab_var = tk.StringVar(value="speech")
        tab_bar = tk.Frame(self, bg="#0e0e0e")
        tab_bar.pack(fill="x")
        tk.Frame(self, bg="#c8a035", height=1).pack(fill="x")

        self._tabs = {}
        for tid, lbl in [("speech", "Speech Color Change"), ("custom", "Custom Color")]:
            btn = tk.Button(tab_bar, text=lbl,
                            font=("Courier New", 9, "bold"),
                            fg="#4a4a4a", bg="#0e0e0e",
                            activeforeground="#c8a035",
                            activebackground="#16110a",
                            relief="flat", bd=0, cursor="hand2",
                            padx=16, pady=7,
                            command=lambda t=tid: self._switch_tab(t))
            btn.pack(side="left")
            self._tabs[tid] = btn

        tk.Frame(self, bg="#111", height=1).pack(fill="x")

        self._content = tk.Frame(self, bg="#0b0b0b")
        self._content.pack(fill="both", expand=True)

        self._panels = {}
        self._panels["speech"] = SpeechColorPanel(self._content, self.master_app)
        self._panels["custom"] = CustomColorPanel(self._content, self.master_app)

        for p in self._panels.values():
            p.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._switch_tab("speech")

    def _switch_tab(self, tab_id):
        for tid, p in self._panels.items():
            p.lower()
            btn = self._tabs.get(tid)
            if btn:
                btn.configure(fg="#4a4a4a", bg="#0e0e0e", highlightthickness=0)
        self._panels[tab_id].lift()
        btn = self._tabs.get(tab_id)
        if btn:
            btn.configure(fg="#c8a035", bg="#16110a",
                           highlightthickness=1, highlightbackground="#c8a035")


# MDT color codes (12 colors at offset 0x8129C0, each 4 bytes ABGR)
MDT_COLOR_OFFSET = 0x8129C0
MDT_COLOR_COUNT  = 12

def read_mdt_colors(exe_path):
    """Read 12 ABGR colors from exe at 0x8129C0."""
    colors = []
    try:
        with open(exe_path, "rb") as f:
            f.seek(MDT_COLOR_OFFSET)
            for _ in range(MDT_COLOR_COUNT):
                data = f.read(4)
                if len(data) < 4:
                    colors.append((0xFF, 0xFF, 0xFF, 0xFF))
                else:
                    a, b, g, r = data
                    colors.append((a, b, g, r))
    except Exception:
        colors = [(0xFF, 0xFF, 0xFF, 0xFF)] * MDT_COLOR_COUNT
    return colors

def write_mdt_color(exe_path, color_index, abgr_tuple):
    """Write one ABGR color at the correct offset."""
    off = MDT_COLOR_OFFSET + color_index * 4
    a, b, g, r = abgr_tuple
    try:
        with open(exe_path, "r+b") as f:
            f.seek(off)
            f.write(bytes([a, b, g, r]))
        return True
    except Exception:
        return False

def abgr_to_hex_color(abgr):
    """Convert ABGR tuple to #RRGGBB for tkinter."""
    a, b, g, r = abgr
    return "#{:02X}{:02X}{:02X}".format(r, g, b)

def hex_to_abgr(hex_color, alpha=0xFF):
    """Convert #RRGGBB to ABGR tuple."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (alpha, b, g, r)


class CustomColorPanel(tk.Frame):
    """Shows 12 color swatches read from EXE offset 8129C0."""

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.master_app = master_app
        self._swatches  = []
        self._colors    = [(0xFF,0xFF,0xFF,0xFF)] * MDT_COLOR_COUNT
        self._build()
        self.bind("<Visibility>", lambda e: self._reload())

    def _build(self):
        top = tk.Frame(self, bg="#0b0b0b")
        top.pack(fill="x", padx=16, pady=10)

        tk.Label(top, text="MDT Colors (offset 0x8129C0)",
                 fg="#c8a035", bg="#0b0b0b",
                 font=("Courier New", 10, "bold")).pack(side="left")

        tk.Button(top, text="Reload from EXE",
                  font=("Courier New", 8),
                  fg="#7cfc7c", bg="#1a2a0a",
                  activeforeground="#7cfc7c", activebackground="#2a4a1a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#7cfc7c",
                  command=self._reload, padx=8, pady=2
                  ).pack(side="right")

        tk.Button(top, text="Reset Colors",
                  font=("Courier New", 8),
                  fg="#ff6060", bg="#2a0a0a",
                  activeforeground="#ff6060", activebackground="#3a1010",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#ff6060",
                  command=self._reset_colors, padx=8, pady=2
                  ).pack(side="right", padx=4)

        grid = tk.Frame(self, bg="#0b0b0b")
        grid.pack(padx=16, pady=8, anchor="w")

        for i in range(MDT_COLOR_COUNT):
            row = i // 4
            col = i % 4
            cell = tk.Frame(grid, bg="#0b0b0b")
            cell.grid(row=row, column=col, padx=12, pady=8)

            swatch = tk.Button(cell, width=6, height=2,
                               bg="#ffffff", relief="ridge", bd=2,
                               cursor="hand2",
                               command=lambda idx=i: self._pick_color(idx))
            swatch.pack()
            tk.Label(cell, text=f"Color {i+1:02d}",
                     fg="#555", bg="#0b0b0b",
                     font=("Courier New", 7)).pack()
            self._swatches.append(swatch)

    def _reload(self):
        exe = self.master_app.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            return
        self._colors = read_mdt_colors(exe)
        for i, swatch in enumerate(self._swatches):
            swatch.configure(bg=abgr_to_hex_color(self._colors[i]))

    def _reset_colors(self):
        exe = self.master_app.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Select bio4.exe first.")
            return
        reset_bytes = bytes.fromhex("F0CFD9E5FF0EDDE8FF03A1FFFFFCA74CFFFF4339FFF5DE0CFF707070FF73DF52FF123F4DFFE80770FFD217FCFF3030D0")
        try:
            with open(exe, "r+b") as f:
                f.seek(MDT_COLOR_OFFSET)
                f.write(reset_bytes)
            self._reload()
            messagebox.showinfo("[+] Reset", "Colors reset to default.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _pick_color(self, idx):
        exe = self.master_app.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Select bio4.exe first.")
            return
        current_hex = abgr_to_hex_color(self._colors[idx])
        result = colorchooser.askcolor(color=current_hex,
                                       title=f"Choose Color {idx+1}")
        if result and result[1]:
            new_hex = result[1]
            abgr    = hex_to_abgr(new_hex)
            if write_mdt_color(exe, idx, abgr):
                self._colors[idx] = abgr
                self._swatches[idx].configure(bg=new_hex)
                messagebox.showinfo("[+] Saved",
                    f"Color {idx+1} updated.")
            else:
                messagebox.showerror("Error", "Failed to write color.")


class SpeechColorPanel(tk.Frame):
    """MDT Speech Color Change — load txt, display with color tags, edit."""

    # MDT codes
    _CODE_MAP = {
        "0x0000": "START",
        "0x0100": "END",
        "0x0300": "\n",
        "0x0400": "[New Page]",
        "0x0800": "PAUSE",
    }

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.master_app  = master_app
        self._txt_path   = tk.StringVar()
        self._entries    = []  # parsed MDT entries
        self._color_only = tk.BooleanVar(value=False)
        self._build()

    def _build(self):
        # path row
        top = tk.Frame(self, bg="#111")
        top.pack(fill="x", padx=12, pady=8)

        tk.Label(top, text="TXT File:",
                 fg="#777", bg="#111",
                 font=("Courier New", 9)).pack(side="left")

        tk.Entry(top, textvariable=self._txt_path,
                 font=("Courier New", 9), fg="#7cfc7c", bg="#0d1a0d",
                 insertbackground="#7cfc7c",
                 relief="flat", bd=0,
                 highlightthickness=1, highlightbackground="#2a5a2a",
                 width=40).pack(side="left", ipady=3, padx=6)

        tk.Button(top, text="Browse",
                  font=("Courier New", 8),
                  fg="#c8a035", bg="#1a1500",
                  activeforeground="#c8a035", activebackground="#2a2000",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#c8a035",
                  command=self._browse_txt, padx=8, pady=2
                  ).pack(side="left")

        tk.Button(top, text="Load",
                  font=("Courier New", 8),
                  fg="#7cfc7c", bg="#1a2a0a",
                  activeforeground="#7cfc7c", activebackground="#2a4a1a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#7cfc7c",
                  command=self._load_txt, padx=8, pady=2
                  ).pack(side="left", padx=4)

        # color only toggle
        opt_row = tk.Frame(self, bg="#0b0b0b")
        opt_row.pack(fill="x", padx=12, pady=(0, 6))
        tk.Checkbutton(opt_row,
                       text="Color this word only (restore after)",
                       variable=self._color_only,
                       fg="#cccccc", bg="#0b0b0b",
                       activebackground="#0b0b0b", selectcolor="#1a1a1a",
                       font=("Courier New", 8), relief="flat"
                       ).pack(side="left")

        # separator
        tk.Frame(self, bg="#222", height=1).pack(fill="x")

        # text display
        body = tk.Frame(self, bg="#0b0b0b")
        body.pack(fill="both", expand=True, padx=8, pady=8)

        self._text = tk.Text(
            body,
            font=("Courier New", 10),
            fg="#d0d0d0", bg="#080808",
            insertbackground="#7cfc7c",
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#222",
            wrap="word", cursor="arrow",
            state="disabled"
        )
        sb = tk.Scrollbar(body, command=self._text.yview)
        self._text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._text.pack(fill="both", expand=True)

        # tags
        self._text.tag_configure("hover",   background="#2a2000")
        self._text.tag_configure("newpage", foreground="#c8a035", font=("Courier New", 8))
        self._text.tag_configure("noclick", foreground="#c8a035")  # non-interactive
        for i in range(MDT_COLOR_COUNT):
            pass  # color tags added on load

        self._text.bind("<Motion>",        self._on_hover)
        self._text.bind("<Button-1>",      self._on_click)
        self._text.bind("<Leave>",         lambda e: self._clear_hover())

        self._hover_range = None

    def _browse_txt(self):
        p = filedialog.askopenfilename(
            title="Select MDT .txt file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if p:
            self._txt_path.set(p)
            self._load_txt()

    def _load_txt(self):
        path = self._txt_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Select a valid .txt file first.")
            return
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                raw = f.read()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        # read colors from exe if available
        exe = self.master_app.exe_path.get().strip()
        colors = read_mdt_colors(exe) if exe and os.path.isfile(exe)                  else [(0xFF,0xFF,0xFF,0xFF)] * MDT_COLOR_COUNT

        self._render(raw, colors)

    def _render(self, raw, colors):
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        # add color tags from EXE colors
        for i, abgr in enumerate(colors):
            hex_col = abgr_to_hex_color(abgr)
            self._text.tag_configure(f"col{i}", foreground=hex_col)

        current_color_tag = None

        # tokenize — handle {0x0600}{0xXX00} color pairs properly
        token_re = re.compile(r"\{0x[0-9A-Fa-f]+\}", re.IGNORECASE)
        tokens   = list(token_re.finditer(raw))
        pos = 0
        i   = 0

        while i <= len(tokens):
            m       = tokens[i] if i < len(tokens) else None
            end_pos = m.start() if m else len(raw)

            # insert text before this token
            if end_pos > pos:
                chunk = raw[pos:end_pos]
                if chunk:
                    tags = ("hover_word",)
                    if current_color_tag:
                        tags = (current_color_tag, "hover_word")
                    self._text.insert("end", chunk, tags)

            if m is None:
                break

            code_val = m.group(0).upper().replace(" ", "")[1:-1]  # e.g. 0X0400

            if code_val in ("0X0000",):
                pass  # start marker — ignore
            elif code_val in ("0X0800",):
                pass  # pause — ignore
            elif code_val == "0X0400":
                self._text.insert("end", " [New Page] ", ("newpage",))
            elif code_val == "0X0300":
                self._text.insert("end", "\n")
            elif code_val == "0X0100":
                self._text.insert("end", "\n" + chr(0x2500)*36 + "\n", ("newpage",))
                current_color_tag = None
            elif code_val == "0X0600":
                # next token is color index {0xXX00}
                if i + 1 < len(tokens):
                    nxt     = tokens[i + 1]
                    nxt_val = nxt.group(0).upper().replace(" ", "")[1:-1]
                    try:
                        raw_int   = int(nxt_val, 16)
                        color_idx = (raw_int >> 8) & 0xFF
                        if color_idx == 0:
                            current_color_tag = None
                        elif color_idx < MDT_COLOR_COUNT:
                            current_color_tag = f"col{color_idx}"
                        else:
                            current_color_tag = None
                    except Exception:
                        pass
                    pos = nxt.end()
                    i  += 2
                    continue
            # else: unknown token — skip silently

            pos = m.end()
            i  += 1

        self._text.configure(state="disabled")
        self._raw = raw

    def _on_hover(self, event):
        self._clear_hover()
        idx = self._text.index(f"@{event.x},{event.y}")
        # skip if over newpage marker
        tags_here = self._text.tag_names(idx)
        if "newpage" in tags_here or "noclick" in tags_here:
            return
        start = self._text.index(f"{idx} wordstart")
        end   = self._text.index(f"{idx} wordend")
        word  = self._text.get(start, end).strip()
        if word and not word.startswith("{") and word not in ("[New Page]", "────────────────────────"):
            self._text.tag_add("hover", start, end)
            self._hover_range = (start, end)

    def _clear_hover(self):
        self._text.tag_remove("hover", "1.0", "end")
        self._hover_range = None

    def _on_click(self, event):
        idx = self._text.index(f"@{event.x},{event.y}")
        tags_here = self._text.tag_names(idx)
        if "newpage" in tags_here or "noclick" in tags_here:
            return
        start = self._text.index(f"{idx} wordstart")
        end   = self._text.index(f"{idx} wordend")
        word  = self._text.get(start, end).strip()
        if not word or word.startswith("{") or word in ("[New", "Page]", "────────────────────────"):
            return

        exe = self.master_app.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Select bio4.exe first.")
            return

        colors  = read_mdt_colors(exe)
        # show color picker popup
        self._show_color_picker(word, colors)

    def _show_color_picker(self, word, colors):
        exe = self.master_app.exe_path.get().strip()
        dlg = tk.Toplevel(self)
        dlg.title(f"Color for: {word}")
        dlg.geometry("320x340")
        dlg.configure(bg="#111")
        dlg.grab_set()

        tk.Label(dlg, text=f'Select color for:  "{word}"',
                 fg="#c8a035", bg="#111",
                 font=("Courier New", 10, "bold")).pack(pady=(14, 8))

        # color grid
        grid = tk.Frame(dlg, bg="#111")
        grid.pack(pady=4)
        self._chosen_idx = None

        btns = []
        for i, abgr in enumerate(colors):
            hex_col = abgr_to_hex_color(abgr)
            r = i // 4
            c = i % 4
            btn = tk.Button(grid, width=5, height=2,
                            bg=hex_col, relief="ridge", bd=2,
                            cursor="hand2",
                            command=lambda idx=i: self._select_color(idx, btns, dlg, word, colors, exe))
            btn.grid(row=r, column=c, padx=4, pady=4)
            btns.append(btn)

        tk.Label(dlg,
                 "Click a color swatch to apply.",
                 fg="#555", bg="#111",
                 font=("Courier New", 8)).pack(pady=4)

    def _select_color(self, color_idx, btns, dlg, word, colors, exe):
        only = self._color_only.get()
        txt_path = self._txt_path.get().strip()
        if not txt_path or not os.path.isfile(txt_path):
            messagebox.showerror("Error", "No TXT file loaded.")
            dlg.destroy()
            return

        with open(txt_path, encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        color_code  = "{{0x0600}}{{0x{:02X}00}}".format(color_idx)
        reset_code  = "{0x0600}{0x0000}"

        if only:
            new_raw = raw.replace(word, f"{color_code}{word}{reset_code}", 1)
        else:
            new_raw = raw.replace(word, f"{color_code}{word}", 1)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(new_raw)

        dlg.destroy()
        self._render(new_raw, colors)
        messagebox.showinfo("[+] Done",
            f'Color applied to "{word}".')


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3: CNS EDITOR
# ═════════════════════════════════════════════════════════════════════════════

CNS_FIELDS = [
    {"label": "ENEMY NUM",      "desc": "enemy_limit",        "offset": "7F9A44", "default": 60},
    {"label": "OBJ NUM",        "desc": "object_limit",       "offset": "7F9A48", "default": 200},
    {"label": "ESP NUM",        "desc": "effect_limit",       "offset": "7F9A4C", "default": 1024},
    {"label": "ESPGEN NUM",     "desc": "effect_spawn_limit", "offset": "7F9A50", "default": 256},
    {"label": "CTRL NUM",       "desc": "control_limit",      "offset": "7F9A54", "default": 10},
    {"label": "LIGHT NUM",      "desc": "light_limit",        "offset": "7F9A58", "default": 100},
    {"label": "PARTS NUM",      "desc": "bones_limit",        "offset": "7F9A5C", "default": 1300},
    {"label": "MODEL INFO NUM", "desc": "model_info_limit",   "offset": "7F9A60", "default": 300},
    {"label": "PRIM NUM",       "desc": "primitive_limit",    "offset": "7F9A64", "default": 655360},
    {"label": "EVT NUM",        "desc": "event_limit",        "offset": "7F9A68", "default": 10},
    {"label": "SAT NUM",        "desc": "SAT_limit",          "offset": "7F9A6C", "default": 30},
    {"label": "EAT NUM",        "desc": "EAT_limit",          "offset": "7F9A70", "default": 30},
]

class CNSEditorPanel(tk.Frame):
    """CNS Editor — edit game limits directly from EXE."""

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.master_app = master_app
        self._vars      = {}
        self._built     = False

    def activate(self):
        if not self._built:
            self._build()
            self._built = True
        self._reload()

    def _build(self):
        # header
        hdr = tk.Frame(self, bg="#0e0e0e")
        hdr.pack(fill="x", padx=0, pady=0)
        tk.Label(hdr, text="CNS EDITOR",
                 fg="#c8a035", bg="#0e0e0e",
                 font=("Courier New", 12, "bold")).pack(side="left", padx=16, pady=10)
        tk.Button(hdr, text="Reload from EXE",
                  font=("Courier New", 8),
                  fg="#7cfc7c", bg="#1a2a0a",
                  activeforeground="#7cfc7c", activebackground="#2a4a1a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#7cfc7c",
                  command=self._reload, padx=8, pady=2
                  ).pack(side="right", padx=12, pady=8)
        tk.Frame(self, bg="#c8a035", height=1).pack(fill="x")

        desc_lbl = tk.Label(self,
                            text="Edit game constant limits. Values are read from and written to bio4.exe.",
                            fg="#555", bg="#0b0b0b",
                            font=("Courier New", 8))
        desc_lbl.pack(anchor="w", padx=16, pady=(8, 4))

        # fields grid
        grid = tk.Frame(self, bg="#0b0b0b")
        grid.pack(padx=16, pady=8, anchor="w")

        for i, field in enumerate(CNS_FIELDS):
            row = i
            # label
            tk.Label(grid,
                     text=f"{field['label']:<16}",
                     fg="#c8a035", bg="#0b0b0b",
                     font=("Courier New", 10, "bold"),
                     width=18, anchor="w"
                     ).grid(row=row, column=0, padx=(0, 8), pady=5, sticky="w")

            tk.Label(grid,
                     text=f"({field['desc']})",
                     fg="#555", bg="#0b0b0b",
                     font=("Courier New", 8),
                     width=22, anchor="w"
                     ).grid(row=row, column=1, padx=(0, 12), pady=5, sticky="w")

            var = tk.StringVar(value=str(field["default"]))
            self._vars[field["offset"]] = (var, field)

            entry = tk.Entry(grid, textvariable=var,
                             font=("Courier New", 10),
                             fg="#7cfc7c", bg="#0d1a0d",
                             insertbackground="#7cfc7c",
                             relief="flat", bd=0,
                             highlightthickness=1, highlightbackground="#2a5a2a",
                             width=10, justify="center")
            entry.grid(row=row, column=2, padx=(0, 8), pady=5)

            # Apply button per field
            off = field["offset"]
            tk.Button(grid, text="Apply",
                      font=("Courier New", 8),
                      fg="#7cfc7c", bg="#1a2a0a",
                      activeforeground="#7cfc7c", activebackground="#2a4a1a",
                      relief="flat", bd=0, cursor="hand2",
                      highlightthickness=1, highlightbackground="#7cfc7c",
                      command=lambda o=off: self._apply_field(o),
                      padx=8, pady=2
                      ).grid(row=row, column=3, pady=5, padx=4)

        # Apply All button
        tk.Frame(self, bg="#222", height=1).pack(fill="x", padx=16, pady=8)
        tk.Button(self, text="Apply All",
                  font=("Courier New", 10, "bold"),
                  fg="#0a0a0a", bg="#c8a035",
                  activeforeground="#0a0a0a", activebackground="#b8902a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=0,
                  command=self._apply_all,
                  padx=20, pady=6
                  ).pack(pady=4)

    def _reload(self):
        exe = self.master_app.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            return
        try:
            with open(exe, "rb") as f:
                for offset, (var, field) in self._vars.items():
                    f.seek(int(offset, 16))
                    raw = f.read(4)
                    if len(raw) == 4:
                        val = struct.unpack("<I", raw)[0]
                        var.set(str(val))
        except Exception:
            pass

    def _apply_field(self, offset):
        exe = self.master_app.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Select bio4.exe first.")
            return
        var, field = self._vars[offset]
        try:
            val = int(var.get().strip())
            if val < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Enter a valid positive number.")
            return
        try:
            with open(exe, "r+b") as f:
                f.seek(int(offset, 16))
                f.write(struct.pack("<I", val))
            messagebox.showinfo("[+] Applied",
                f"{field['label']} = {val}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _apply_all(self):
        exe = self.master_app.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Select bio4.exe first.")
            return
        errors = []
        try:
            with open(exe, "r+b") as f:
                for offset, (var, field) in self._vars.items():
                    try:
                        val = int(var.get().strip())
                        f.seek(int(offset, 16))
                        f.write(struct.pack("<I", val))
                    except Exception as e:
                        errors.append(f"{field['label']}: {e}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        if errors:
            messagebox.showwarning("Done with errors", "\n".join(errors))
        else:
            messagebox.showinfo("[+] Applied", "All CNS values saved.")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4: LOCKED / COMING SOON PANELS
# ═════════════════════════════════════════════════════════════════════════════

class LockedPanel(tk.Frame):
    """Panel shown when a module requires a code to be enabled."""

    def __init__(self, parent, tool_label, required_code_id,
                 required_code_name, master_app, unlocked_panel=None, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.master_app          = master_app
        self.required_code_id    = required_code_id
        self.required_code_name  = required_code_name
        self.tool_label          = tool_label
        self._unlocked_panel     = unlocked_panel  # real panel to show when unlocked
        self._unlocked_by_quick  = False
        self._build()

    def activate(self):
        self._check_lock()
        if self._is_unlocked_now() and self._unlocked_panel:
            self._unlocked_panel.lift()
            self._unlocked_panel.activate()

    def _is_unlocked_now(self):
        cm             = getattr(self.master_app, "_cm_app", None)
        quick_unlocked = getattr(self, "_unlocked_by_quick", False)
        scan_unlocked  = (cm and (
            cm.applied.get(self.required_code_id, False) or
            cm.detected.get(self.required_code_id, False)
        ))
        return quick_unlocked or scan_unlocked

    def _check_lock(self):
        """Re-check if required code is applied — via quick detect or full scan."""
        is_unlocked = self._is_unlocked_now()
        if is_unlocked:
            self._lbl_lock.configure(
                text="Code is enabled — module is ready.",
                fg="#7cfc7c"
            )
            if self._unlocked_panel:
                self._unlocked_panel.lift()
                self._unlocked_panel.activate()
        else:
            self._lbl_lock.configure(
                text=f"This module requires [{self.required_code_name}]\nto be enabled in RE4 CODE MANAGER.",
                fg="#e05050"
            )

    def _build(self):
        f = tk.Frame(self, bg="#0b0b0b")
        f.place(relx=0.5, rely=0.42, anchor="center")

        tk.Label(f, text="[LOCKED]", fg="#c8a035", bg="#0b0b0b",
                 font=("Courier New", 24)).pack(pady=(0, 10))
        tk.Label(f, text=self.tool_label, fg="#c8a035", bg="#0b0b0b",
                 font=("Courier New", 14, "bold")).pack(pady=(0, 12))

        self._lbl_lock = tk.Label(f, text="",
                                   fg="#e05050", bg="#0b0b0b",
                                   font=("Courier New", 10),
                                   justify="center")
        self._lbl_lock.pack(pady=(0, 16))

        tk.Label(f,
                 text="Go to RE4 CODE MANAGER → enable the required code → return here.",
                 fg="#555", bg="#0b0b0b",
                 font=("Courier New", 8),
                 justify="center").pack()

        self._check_lock()


class ComingSoonPanel(tk.Frame):
    def __init__(self, parent, tool_label, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.tool_label = tool_label
        self._build()

    def activate(self): pass

    def _build(self):
        f = tk.Frame(self, bg="#0b0b0b")
        f.place(relx=0.5, rely=0.42, anchor="center")
        tk.Label(f, text=self.tool_label, fg="#c8a035", bg="#0b0b0b",
                 font=("Courier New", 14, "bold")).pack(pady=(0, 14))
        tk.Label(f, text="[ COMING SOON ]", fg="#4a4a4a", bg="#0b0b0b",
                 font=("Courier New", 13, "bold")).pack()
        tk.Label(f, text="This module is under development.",
                 fg="#333", bg="#0b0b0b", font=("Courier New", 9)).pack(pady=(10, 0))


class WelcomePanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg="#080808", **kw)
        self._build()

    def activate(self): pass

    def _build(self):
        f = tk.Frame(self, bg="#080808")
        f.place(relx=0.5, rely=0.42, anchor="center")

        tk.Label(f, text="RE4", fg="#c8a035", bg="#080808",
                 font=("Courier New", 38, "bold")).pack()
        tk.Label(f, text="MASTER EDITOR", fg="#cccccc", bg="#080808",
                 font=("Courier New", 15, "bold")).pack()
        tk.Frame(f, bg="#c8a035", height=1, width=320).pack(pady=18)
        tk.Label(f, text="Select a module from the navigation bar above.",
                 fg="#555", bg="#080808", font=("Courier New", 10)).pack()

        row = tk.Frame(f, bg="#080808")
        row.pack(pady=24)
        icons = ["RE4 CODE\nMANAGER", "OSD\nEDITOR", "CNS\nEDITOR",
                 "SND\nEDITOR", "AEV OPTION\nEDITOR",
                 "MDT COLOR\nEDITOR", "ROOM INIT\nEDITOR", "AVL\nEDITOR"]
        for lbl in icons:
            col = tk.Frame(row, bg="#080808")
            col.pack(side="left", padx=8)
            tk.Label(col, text="◈", fg="#333", bg="#080808",
                     font=("Courier New", 12)).pack()
            tk.Label(col, text=lbl, fg="#333", bg="#080808",
                     font=("Courier New", 6), justify="center").pack()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5: CODE MANAGER PANEL WRAPPER
# ═════════════════════════════════════════════════════════════════════════════

class CodeManagerPanel(tk.Frame):
    """
    Embeds RE4PatcherApp inside the master editor.
    The exe_path is shared from master.
    No browse/path bar shown — master handles it.
    Settings shows code-manager-specific options only.
    """

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.master_app = master_app
        self._app       = None
        self._built     = False

    def activate(self):
        if not self._built:
            self._build()
            self._built = True

    def get_app(self):
        return self._app

    def _build(self):
        # Override paths to point inside MASTER_DIR
        global BASE_DIR, CODES_DIR, INFO_FILE, DATA_FILE, ORIG_FILE
        global PROFILES_DIR, MOD_DIR, FILES_DIR, LOG_FILE
        global BACKUP_FILE, SETTINGS_FILE

        BASE_DIR     = os.path.join(MASTER_DIR, "RE4 CODE MANAGER")
        CODES_DIR    = os.path.join(BASE_DIR, "the_codes")
        INFO_FILE    = os.path.join(CODES_DIR, "codes_info.json")
        DATA_FILE    = os.path.join(CODES_DIR, "codes_data.json")
        ORIG_FILE    = os.path.join(CODES_DIR, "bio4_original.exe")
        PROFILES_DIR = os.path.join(BASE_DIR, "Profiles")
        MOD_DIR      = os.path.join(BASE_DIR, "Modified files")
        FILES_DIR    = os.path.join(BASE_DIR, "the_files")
        LOG_FILE     = os.path.join(FILES_DIR, "patch_log.txt")
        BACKUP_FILE  = os.path.join(FILES_DIR, "patch_backup.json")
        SETTINGS_FILE = os.path.join(FILES_DIR, "settings.json")

        # reload settings
        global APP_SETTINGS
        APP_SETTINGS = load_settings()

        # check data files exist
        if not os.path.isfile(INFO_FILE) or not os.path.isfile(DATA_FILE):
            self._show_missing()
            return

        try:
            app = RE4PatcherApp(
                master=self,
                embedded=True,
                shared_exe_var=self.master_app.exe_path
            )
            app.pack(fill="both", expand=True)
            self._app = app
            self.master_app._cm_app = app
            app._master_app_ref = self.master_app
            self.master_app.after(500, self.master_app._check_locked_panels)
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            tk.Label(self,
                     text="Error loading Code Manager:\n" + str(e),
                     fg="#e05050", bg="#0b0b0b",
                     font=("Courier New", 8),
                     wraplength=600, justify="left").pack(pady=20, padx=20)
            print(err)

    def _show_missing(self):
        f = tk.Frame(self, bg="#0b0b0b")
        f.place(relx=0.5, rely=0.42, anchor="center")
        tk.Label(f, text="RE4 CODE MANAGER data not found.",
                 fg="#e05050", bg="#0b0b0b",
                 font=("Courier New", 10)).pack(pady=8)
        tk.Label(f,
                 text=f"Expected:\n{CODES_DIR}",
                 fg="#555", bg="#0b0b0b",
                 font=("Courier New", 8)).pack()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6: MASTER EDITOR MAIN APP
# ═════════════════════════════════════════════════════════════════════════════

# ═════════════════════════════════════════════════════════════════════════════
# AEV OPTION EDITOR
# ═════════════════════════════════════════════════════════════════════════════

class AEVOptionPanel(tk.Frame):
    """
    AEV Option Editor — load TXT, display text, click word → set AEV option.
    Color: red = AEV will hide after press, green = AEV stays visible.
    Format written: {0x0700}{0xFFXX} or {0x0700}{0xFEXX}
    """

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.master_app = master_app
        self._txt_path  = tk.StringVar()
        self._build()

    def activate(self): pass

    def _build(self):
        # path row
        top = tk.Frame(self, bg="#111")
        top.pack(fill="x", padx=12, pady=8)

        tk.Label(top, text="TXT File:", fg="#777", bg="#111",
                 font=("Courier New", 9)).pack(side="left")

        tk.Entry(top, textvariable=self._txt_path,
                 font=("Courier New", 9), fg="#7cfc7c", bg="#0d1a0d",
                 insertbackground="#7cfc7c",
                 relief="flat", bd=0,
                 highlightthickness=1, highlightbackground="#2a5a2a",
                 width=42).pack(side="left", ipady=3, padx=6)

        tk.Button(top, text="Browse",
                  font=("Courier New", 8),
                  fg="#c8a035", bg="#1a1500",
                  activeforeground="#c8a035", activebackground="#2a2000",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#c8a035",
                  command=self._browse, padx=8, pady=2
                  ).pack(side="left")

        tk.Button(top, text="Load",
                  font=("Courier New", 8),
                  fg="#7cfc7c", bg="#1a2a0a",
                  activeforeground="#7cfc7c", activebackground="#2a4a1a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#7cfc7c",
                  command=self._load, padx=8, pady=2
                  ).pack(side="left", padx=4)

        tk.Frame(self, bg="#222", height=1).pack(fill="x")

        # text display
        body = tk.Frame(self, bg="#0b0b0b")
        body.pack(fill="both", expand=True, padx=8, pady=8)

        self._text = tk.Text(
            body, font=("Courier New", 10),
            fg="#d0d0d0", bg="#080808",
            insertbackground="#7cfc7c",
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#222",
            wrap="word", cursor="arrow", state="disabled"
        )
        sb = tk.Scrollbar(body, command=self._text.yview)
        self._text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._text.pack(fill="both", expand=True)

        self._text.tag_configure("aev_hide",  foreground="#ff4444")
        self._text.tag_configure("aev_show",  foreground="#7cfc7c")
        self._text.tag_configure("newpage",   foreground="#c8a035", font=("Courier New", 8))
        self._text.tag_configure("hover",     background="#2a2000")
        self._text.tag_configure("separator", foreground="#555555")

        self._text.bind("<Motion>",   self._on_hover)
        self._text.bind("<Button-1>", self._on_click)
        self._text.bind("<Leave>",    lambda e: self._clear_hover())
        self._raw = ""

    def _browse(self):
        p = filedialog.askopenfilename(
            title="Select AEV Option .txt file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if p:
            self._txt_path.set(p)
            self._load()

    def _load(self):
        path = self._txt_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Select a valid .txt file first.")
            return
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                self._raw = f.read()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._render(self._raw)

    def _render(self, raw):
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        token_re = re.compile(r"\{0x[0-9A-Fa-f]+\}", re.IGNORECASE)
        tokens   = list(token_re.finditer(raw))
        pos = 0
        i   = 0
        current_aev_tag = None
        last_was_0700   = False

        while i <= len(tokens):
            m       = tokens[i] if i < len(tokens) else None
            end_pos = m.start() if m else len(raw)

            if end_pos > pos:
                chunk = raw[pos:end_pos]
                if chunk:
                    tags = ()
                    if current_aev_tag:
                        tags = (current_aev_tag, "hover_word")
                    else:
                        tags = ("hover_word",)
                    self._text.insert("end", chunk, tags)

            if m is None:
                break

            code_val = m.group(0).upper().replace(" ", "")[1:-1]

            if code_val in ("0X0000",):
                pass
            elif code_val in ("0X0800",):
                pass
            elif code_val == "0X0400":
                self._text.insert("end", " [New Page] ", ("newpage",))
            elif code_val == "0X0300":
                self._text.insert("end", "\n")
            elif code_val == "0X0100":
                self._text.insert("end", "\n" + chr(0x2500)*36 + "\n", ("newpage",))
                current_aev_tag = None
                last_was_0700   = False
            elif code_val == "0X0700":
                # Before starting new AEV block, add "|" separator if needed
                if last_was_0700:
                    self._text.insert("end", " " + chr(0x2502) + " ", ("separator",))
                # next token is {0xFFXX} or {0xFEXX}
                if i + 1 < len(tokens):
                    nxt     = tokens[i + 1]
                    nxt_val = nxt.group(0).upper().replace(" ", "")[1:-1]
                    try:
                        raw_int   = int(nxt_val, 16)
                        hi_byte   = (raw_int >> 8) & 0xFF
                        if hi_byte == 0xFF:
                            current_aev_tag = "aev_hide"
                        elif hi_byte == 0xFE:
                            current_aev_tag = "aev_show"
                        else:
                            current_aev_tag = None
                    except Exception:
                        current_aev_tag = None
                    pos = nxt.end()
                    i  += 2
                    last_was_0700 = True
                    continue
                last_was_0700 = True
            elif code_val in ("0X0100",):
                # End of message — add "|" if inside AEV block, then separator line
                if last_was_0700:
                    self._text.insert("end", " " + chr(0x2502), ("separator",))
                self._text.insert("end", "\n" + chr(0x2500)*36 + "\n", ("newpage",))
                current_aev_tag = None
                last_was_0700   = False
                pos = m.end()
                i  += 1
                continue
            else:
                pass  # unknown token — skip

            pos = m.end()
            i  += 1

        self._text.configure(state="disabled")

    def _on_hover(self, event):
        self._clear_hover()
        idx       = self._text.index(f"@{event.x},{event.y}")
        tags_here = self._text.tag_names(idx)
        if "newpage" in tags_here or "separator" in tags_here:
            return
        start = self._text.index(f"{idx} wordstart")
        end   = self._text.index(f"{idx} wordend")
        word  = self._text.get(start, end).strip()
        if word and not word.startswith("{"):
            self._text.tag_add("hover", start, end)

    def _clear_hover(self):
        self._text.tag_remove("hover", "1.0", "end")

    def _on_click(self, event):
        idx       = self._text.index(f"@{event.x},{event.y}")
        tags_here = self._text.tag_names(idx)
        if "newpage" in tags_here or "separator" in tags_here:
            return
        start = self._text.index(f"{idx} wordstart")
        end   = self._text.index(f"{idx} wordend")
        word  = self._text.get(start, end).strip()
        if not word or word.startswith("{"):
            return

        self._show_aev_dialog(word, start, end)

    def _show_aev_dialog(self, word, start, end):
        txt_path = self._txt_path.get().strip()
        if not txt_path or not os.path.isfile(txt_path):
            messagebox.showerror("Error", "No TXT file loaded.")
            return

        dlg = tk.Toplevel(self)
        dlg.title("AEV Option")
        dlg.geometry("340x240")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        tk.Label(dlg, text=f'AEV for:  "{word}"',
                 fg="#c8a035", bg="#111",
                 font=("Courier New", 10, "bold")).pack(pady=(14, 10))

        # Q1: how many AEVs
        tk.Label(dlg,
                 text="How many AEVs to trigger?" if CURRENT_LANG == "en"
                      else "كم AEV يشتغل؟",
                 fg="#ccc", bg="#111",
                 font=("Courier New", 9)).pack()

        count_var = tk.StringVar(value="1")
        tk.Entry(dlg, textvariable=count_var,
                 font=("Courier New", 10), fg="#7cfc7c", bg="#0d1a0d",
                 insertbackground="#7cfc7c",
                 relief="flat", bd=0,
                 highlightthickness=1, highlightbackground="#2a5a2a",
                 width=6, justify="center").pack(pady=6, ipady=3)

        def on_next():
            try:
                count = int(count_var.get().strip())
                if count < 1: raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Enter a valid number.")
                return
            dlg.destroy()
            self._show_aev_options(word, count)

        tk.Button(dlg, text="Next" if CURRENT_LANG == "en" else "التالي",
                  font=("Courier New", 9, "bold"),
                  fg="#0a0a0a", bg="#c8a035",
                  activeforeground="#0a0a0a", activebackground="#b8902a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=0,
                  command=on_next, padx=14, pady=4
                  ).pack(pady=10)

    def _show_aev_options(self, word, count):
        txt_path = self._txt_path.get().strip()

        dlg = tk.Toplevel(self)
        dlg.title("AEV Options")
        dlg.geometry("380x" + str(120 + count * 100))
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        tk.Label(dlg, text=f'"{word}"',
                 fg="#c8a035", bg="#111",
                 font=("Courier New", 10, "bold")).pack(pady=(12, 8))

        aev_configs = []
        body = tk.Frame(dlg, bg="#111")
        body.pack(fill="both", expand=True, padx=20)

        for n in range(count):
            fr = tk.Frame(body, bg="#1a1a1a",
                          highlightthickness=1, highlightbackground="#333")
            fr.pack(fill="x", pady=4, ipady=4)

            lbl = f"AEV {n+1}" if count > 1 else "AEV"
            tk.Label(fr, text=lbl, fg="#c8a035", bg="#1a1a1a",
                     font=("Courier New", 8, "bold")).pack(anchor="w", padx=8, pady=(4,2))

            # Q1: hide after press?
            hide_var = tk.BooleanVar(value=True)
            row1 = tk.Frame(fr, bg="#1a1a1a")
            row1.pack(fill="x", padx=8)
            tk.Label(row1,
                     text="Hide AEV after press?" if CURRENT_LANG == "en"
                          else "AEV يختفي بعد الضغط؟",
                     fg="#ccc", bg="#1a1a1a",
                     font=("Courier New", 8)).pack(side="left")
            for val, lbl_t in [(True, "Yes"), (False, "No")]:
                tk.Radiobutton(row1, text=lbl_t, variable=hide_var, value=val,
                               fg="#ccc", bg="#1a1a1a",
                               activebackground="#1a1a1a", selectcolor="#0d0d0d",
                               font=("Courier New", 8), relief="flat"
                               ).pack(side="left", padx=6)

            # Q2: AEV index (hex)
            row2 = tk.Frame(fr, bg="#1a1a1a")
            row2.pack(fill="x", padx=8, pady=(2, 4))
            tk.Label(row2,
                     text="AEV INDEX (hex):" if CURRENT_LANG == "en"
                          else "رقم AEV (hex):",
                     fg="#ccc", bg="#1a1a1a",
                     font=("Courier New", 8)).pack(side="left")
            idx_var = tk.StringVar(value="00")
            tk.Entry(row2, textvariable=idx_var,
                     font=("Courier New", 9), fg="#7cfc7c", bg="#0d1a0d",
                     insertbackground="#7cfc7c",
                     relief="flat", bd=0,
                     highlightthickness=1, highlightbackground="#2a5a2a",
                     width=5, justify="center").pack(side="left", padx=6, ipady=2)

            aev_configs.append((hide_var, idx_var))

        def do_apply():
            try:
                with open(txt_path, encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
            except Exception as e:
                messagebox.showerror("Error", str(e))
                dlg.destroy()
                return

            # build prefix codes
            # Only FIRST AEV gets {0x0700}, subsequent ones just get the index
            prefix = ""
            for n_aev, (hide_var, idx_var) in enumerate(aev_configs):
                idx_hex = idx_var.get().strip().upper().zfill(2)
                hi_byte = "FF" if hide_var.get() else "FE"
                if n_aev == 0:
                    code_pair = "{0x0700}{0x" + hi_byte + idx_hex + "}"
                else:
                    code_pair = "{0x" + hi_byte + idx_hex + "}"
                prefix += code_pair

            # check if word already preceded by {0x0700}
            # find word in raw and check what's before it
            word_pos = raw.find(word)
            if word_pos > 0:
                before = raw[max(0, word_pos-12):word_pos].upper()
                if "{0X0700}" in before or "0X0700}" in before:
                    # {0x0700} already there — just add the index token
                    new_raw = raw[:word_pos] + prefix.replace("{0x0700}", "") + raw[word_pos:]
                else:
                    new_raw = raw[:word_pos] + prefix + raw[word_pos:]
            else:
                new_raw = raw.replace(word, prefix + word, 1)

            try:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(new_raw)
                self._raw = new_raw
                self._render(new_raw)
                dlg.destroy()
                messagebox.showinfo("[+] Applied",
                    f'AEV option applied to "{word}".')
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = tk.Frame(dlg, bg="#111")
        btn_frame.pack(fill="x", padx=20, pady=(8,12))
        tk.Button(btn_frame, text="Apply" if CURRENT_LANG == "en" else "تطبيق",
                  font=("Courier New", 10, "bold"),
                  fg="#0a0a0a", bg="#7cfc7c",
                  activeforeground="#0a0a0a", activebackground="#5cdc5c",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=0,
                  command=do_apply, padx=20, pady=6
                  ).pack(fill="x")


# ═════════════════════════════════════════════════════════════════════════════
# AVL EDITOR
# ═════════════════════════════════════════════════════════════════════════════

# AVL binary template per entry (XX = value byte)
# 4E756D626572206F6641657602D = "Number of Aev--" then XX (count)
# 4B657920...  = "Key ID________" then XX
# etc.
AVL_TEMPLATE = bytes.fromhex(
    "4E756D62657220 6F6620416576 2D2D".replace(" ", "")
)

AVL_FIELDS = [
    {"label": "AEV Number",           "label_ar": "رقم AEV",             "offset_in_entry": 15},
    {"label": "Key ID",               "label_ar": "رقم المفتاح",          "offset_in_entry": 25},
    {"label": "Lock Message",         "label_ar": "رسالة الباب المقفل",   "offset_in_entry": 36},
    {"label": "Lock Sound",           "label_ar": "صوت الباب المقفل",     "offset_in_entry": 52},
    {"label": "Lock Camera",          "label_ar": "كاميرا الباب المقفل",  "offset_in_entry": 68},
    {"label": "Unlock Message",       "label_ar": "رسالة الباب المفتوح",  "offset_in_entry": 84},
    {"label": "Unlock Sound",         "label_ar": "صوت الباب المفتوح",    "offset_in_entry": 99},
]

# Full entry template bytes (each XX = 0x00 placeholder)
AVL_ENTRY_BYTES = (
    "4E756D62657220 6F66204165762D2D XX "
    "4B65792049445F5F5F5F5F5F5F5F XX 00 "
    "6C6F636B206D6573736167652D2D2D XX "
    "6C6F636B20736F756E642D2D2D2D2D XX "
    "6C6F636B2063616D6572612D2D2D2D XX "
    "756E6C6F636B206D6573736167652D XX "
    "756E6C6F636B20736F756E642D2D2D XX "
    "3E3E3E3E3E3E3E3E3E3E3E3E3E3E3E3E"
).replace(" ", "")

# Item list for dropdown
ITEM_LIST = [
    ("00","Magnum Ammo"),("01","Hand Grenade"),("02","Incendiary Grenade"),
    ("03","Matilda"),("04","Handgun Ammo"),("05","First Aid Spray"),
    ("06","Green Herb"),("07","Rifle Ammo"),("08","Chicken Egg"),
    ("09","Brown Chicken Egg"),("0A","Gold Chicken Egg"),("0B","aaa"),
    ("0C","Plaga Sample"),("0D","Krauser's Knife"),("0E","Flash Grenade"),
    ("0F","Salazar Family Insignia"),("10","Bowgun"),("11","Bowgun Bolts"),
    ("12","Green Herb x2"),("13","Green Herb x3"),("14","Mixed Herbs (G+R)"),
    ("15","Mixed Herbs (G+R+Y)"),("16","Mixed Herbs (G+Y)"),
    ("17","Rocket Launcher (Special)"),("18","Shotgun Shells"),("19","Red Herb"),
    ("1A","Handcannon Ammo"),("1B","Hourglass w/ Gold Decor"),("1C","Yellow Herb"),
    ("1D","Stone Tablet"),("1E","Lion Ornament"),("1F","Goat Ornament"),
    ("20","TMP Ammo"),("21","Punisher"),("22","Punisher w/ Silencer"),
    ("23","Handgun"),("24","Handgun w/ Silencer"),("25","Red9"),
    ("26","Red9 w/ Stock"),("27","Blacktail"),("28","Blacktail w/ Silencer"),
    ("29","Broken Butterfly"),("2A","Killer7"),("2B","Killer7 w/ Silencer"),
    ("2C","Shotgun"),("2D","Striker"),("2E","Rifle"),("2F","Rifle (Semi-Auto)"),
    ("30","TMP"),("31","Activation Key (Blue)"),("32","TMP w/ Stock"),
    ("33","Activation Key (Red)"),("34","Chicago Typewriter (Infinite)"),
    ("35","Rocket Launcher"),("36","Mine Thrower"),("37","Handcannon"),
    ("38","Combat Knife"),("39","Serpent Ornament"),("3A","Moonstone (Right Half)"),
    ("3B","Insignia Key"),("3C","Round Insignia"),("3D","False Eye"),
    ("3E","Custom TMP"),("3F","Silencer (Handgun)"),("40","Silencer (???)"),
    ("41","P.R.L. 412"),("42","Stock (Red9)"),("43","Stock (TMP)"),
    ("44","Scope (Rifle)"),("45","Scope (Semi-Auto Rifle)"),("46","Mine-Darts"),
    ("47","Shotgun"),("48","Capture Luis Sera"),("49","Target Practice"),
    ("4A","Luis' Memo"),("4B","Castellan Memo"),("4C","Female Intruder"),
    ("4D","Butler's Memo"),("4E","Sample Retrieved"),("4F","Ritual Preparation"),
    ("50","Luis' Memo 2"),("51","Rifle (Semi-Auto) w/ Infrared Scope"),
    ("52","Krauser's Bow"),("53","Chicago Typewriter (Regular)"),
    ("54","Treasure Map (Castle)"),("55","Treasure Map (Island)"),
    ("56","Velvet Blue"),("57","Spinel"),("58","Pearl Pendant"),
    ("59","Brass Pocket Watch"),("5A","Elegant Headdress"),("5B","Antique Pipe"),
    ("5C","Gold Bangle w/ Pearls"),("5D","Amber Ring"),("5E","Beerstein"),
    ("5F","Green Catseye"),("60","Red Catseye"),("61","Yellow Catseye"),
    ("62","Beerstein w/ (G)"),("63","Beerstein w/ (R)"),("64","Beerstein w/ (Y)"),
    ("65","Beerstein w/ (G,R)"),("66","Beerstein w/ (G,Y)"),
    ("67","Beerstein w/ (R,Y)"),("68","Beerstein w/ (G,R,Y)"),
    ("69","Moonstone (Left Half)"),("6A","Chicago Typewriter Ammo"),
    ("6B","Rifle + Scope"),("6C","Rifle (Semi-Auto) w/ Scope"),
    ("6D","Infinite Launcher"),("6E","King's Grail"),("6F","Queen's Grail"),
    ("70","Staff of Royalty"),("71","Gold Bars"),("72","Arrows"),
    ("73","Bonus Time"),("74","Emergency Lock Card Key"),("75","Bonus Points"),
    ("76","Green Catseye"),("77","Ruby"),("78","Treasure Box (S)"),
    ("79","Treasure Box (L)"),("7A","Blue Moonstone"),("7B","Key to the Mine"),
    ("7C","Attache Case S"),("7D","Attache Case M"),("7E","Attache Case L"),
    ("7F","Attache Case XL"),("80","Golden Sword"),("81","Iron Key"),
    ("82","Stone of Sacrifice"),("83","Storage Room Card Key"),
    ("84","Freezer Card Key"),("85","Piece of the Holy Beast, Panther"),
    ("86","Piece of the Holy Beast, Serpent"),("87","Piece of the Holy Beast, Eagle"),
    ("88","Jet-Ski Key"),("89","Dirty Pearl Pendant"),("8A","Dirty Brass Pocket Watch"),
    ("8B","Old Key"),("8C","Camp Key"),("8D","Dynamite"),
    ("8E","Lift Activation Key"),("8F","Gold Bangle"),
    ("90","Elegant Perfume Bottle"),("91","Mirror w/ Pearls & Rubies"),
    ("92","Waste Disposal Card Key"),("93","Elegant Chessboard"),("94","Riot Gun"),
    ("95","Black Bass"),("96","Hourglass w/ Gold Decor"),("97","Black Bass (L)"),
    ("98","Illuminados Pendant"),("99","Rifle w/ Infrared Scope"),("9A","Crown"),
    ("9B","Crown Jewel"),("9C","Royal Insignia"),("9D","Crown with Jewels"),
    ("9E","Crown with an Insignia"),("9F","Salazar Family Crown"),
    ("A0","Rifle Ammo (Infrared)"),("A1","Emerald"),("A2","Bottle Caps"),
    ("A3","Gallery Key"),("A4","Emblem (Right Half)"),("A5","Emblem (Left Half)"),
    ("A6","Hexagonal Emblem"),("A7","Castle Gate Key"),("A8","Mixed Herbs (R+Y)"),
    ("A9","Treasure Map (Village)"),("AA","Scope (Mine-Thrower)"),
    ("AB","Mine-Thrower + Scope"),("AC","Playing Manual 1"),("AD","Info on Ashley"),
    ("AE","Playing Manual 2"),("AF","Alert Order"),
    ("B0","About the Blue Medallions"),("B1","Chief's Note"),
    ("B2","Closure of the Church"),("B3","Anonymous Letter"),
    ("B4","Playing Manual 3"),("B5","Sera and the 3rd Party"),
    ("B6","Two Routes"),("B7","Village's Last Defense"),("B8","Butterfly Lamp"),
    ("B9","Green Eye"),("BA","Red Eye"),("BB","Blue Eye"),
    ("BC","Butterfly Lamp w/ (G)"),("BD","Butterfly Lamp w/ (R)"),
    ("BE","Butterfly Lamp w/ (B)"),("BF","Butterfly Lamp w/ (G,R)"),
    ("C0","Butterfly Lamp w/ (G,B)"),("C1","Butterfly Lamp w/ (R,B)"),
    ("C2","Butterfly Lamp w/ (R,G,B)"),("C3","Prison Key"),
    ("C4","Platinum Sword"),("C5","Infrared Scope"),("C6","Elegant Mask"),
    ("C7","Green Gem"),("C8","Red Gem"),("C9","Purple Gem"),
    ("CA","Elegant Mask w/ (G)"),("CB","Elegant Mask w/ (R)"),
    ("CC","Elegant Mask w/ (P)"),("CD","Elegant Mask w/ (G,R)"),
    ("CE","Elegant Mask w/ (G,P)"),("CF","Elegant Mask w/ (R,P)"),
    ("D0","Elegant Mask w/ (R,G,P)"),("D1","Golden Lynx"),
    ("D2","Green Stone of Judgement"),("D3","Red Stone of Faith"),
    ("D4","Blue Stone of Treason"),("D5","Golden Lynx w/ (G)"),
    ("D6","Golden Lynx w/ (R)"),("D7","Golden Lynx w/ (B)"),
    ("D8","Golden Lynx w/ (G,R)"),("D9","Golden Lynx w/ (G,B)"),
    ("DA","Golden Lynx w/ (R,B)"),("DB","Golden Lynx w/ (G,R,B)"),
    ("DC","Leon w/ Rocket Launcher"),("DD","Leon w/ Shotgun"),
    ("DE","Leon w/ Handgun"),("DF","Ashley Graham"),("E0","Luis Sera"),
    ("E1","Don Jose"),("E2","Don Diego"),("E3","Don Esteban"),("E4","Don Manuel"),
    ("E5","Dr. Salvador"),("E6","Merchant"),("E7","Zealot w/ Scythe"),
    ("E8","Zealot w/ Shield"),("E9","Zealot w/ Bowgun"),("EA","Leader Zealot"),
    ("EB","Soldier w/ Dynamite"),("EC","Soldier w/ Stun-Rod"),
    ("ED","Soldier w/ Hammer"),("EE","Isabel"),("EF","Maria"),("F0","Ada Wong"),
    ("F1","Bella Sisters"),("F2","Don Pedro"),("F3","J.J."),
    ("F4","Letter from Ada"),("F5","Luis' Memo 3"),("F6","Paper Airplane"),
    ("F7","Our Plan"),("F8","Luis' Memo 4"),("F9","Krauser's Note"),
    ("FA","Luis' Memo 5"),("FB","Our Mission"),("FC","aaa"),("FD","aaa"),
    ("FE","Tactical Vest"),("FF","aaa"),
]


class AVLEditorPanel(tk.Frame):
    """AVL Editor — read/write AVL binary files."""

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.master_app = master_app
        self._avl_path  = tk.StringVar()
        self._entries   = []   # list of dicts, one per AVL entry
        self._built     = False

    def activate(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        # header
        hdr = tk.Frame(self, bg="#0e0e0e")
        hdr.pack(fill="x")
        tk.Label(hdr, text="AVL EDITOR",
                 fg="#c8a035", bg="#0e0e0e",
                 font=("Courier New", 12, "bold")).pack(side="left", padx=16, pady=10)
        tk.Frame(self, bg="#c8a035", height=1).pack(fill="x")

        # path row
        top = tk.Frame(self, bg="#111")
        top.pack(fill="x", padx=12, pady=8)

        tk.Label(top, text="AVL File:", fg="#777", bg="#111",
                 font=("Courier New", 9)).pack(side="left")

        tk.Entry(top, textvariable=self._avl_path,
                 font=("Courier New", 9), fg="#7cfc7c", bg="#0d1a0d",
                 insertbackground="#7cfc7c",
                 relief="flat", bd=0,
                 highlightthickness=1, highlightbackground="#2a5a2a",
                 width=40).pack(side="left", ipady=3, padx=6)

        tk.Button(top, text="Browse",
                  font=("Courier New", 8), fg="#c8a035", bg="#1a1500",
                  activeforeground="#c8a035", activebackground="#2a2000",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#c8a035",
                  command=self._browse, padx=8, pady=2
                  ).pack(side="left")

        tk.Button(top, text="Load",
                  font=("Courier New", 8), fg="#7cfc7c", bg="#1a2a0a",
                  activeforeground="#7cfc7c", activebackground="#2a4a1a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#7cfc7c",
                  command=self._load, padx=8, pady=2
                  ).pack(side="left", padx=4)

        # count display
        count_row = tk.Frame(self, bg="#0b0b0b")
        count_row.pack(fill="x", padx=16, pady=(0, 4))
        self._count_var = tk.StringVar(value="AVL count: —")
        tk.Label(count_row, textvariable=self._count_var,
                 fg="#c8a035", bg="#0b0b0b",
                 font=("Courier New", 9)).pack(side="left")

        tk.Button(count_row, text="+ Add AVL",
                  font=("Courier New", 8), fg="#7cfc7c", bg="#1a2a0a",
                  activeforeground="#7cfc7c", activebackground="#2a4a1a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#7cfc7c",
                  command=self._add_entry, padx=8, pady=2
                  ).pack(side="right", padx=4)

        tk.Button(count_row, text="Save File",
                  font=("Courier New", 8), fg="#c8a035", bg="#1a1500",
                  activeforeground="#c8a035", activebackground="#2a2000",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#c8a035",
                  command=self._save, padx=8, pady=2
                  ).pack(side="right")

        tk.Frame(self, bg="#222", height=1).pack(fill="x", padx=0)

        # scrollable entries area
        canvas_frame = tk.Frame(self, bg="#0b0b0b")
        canvas_frame.pack(fill="both", expand=True, padx=0)

        self._canvas = tk.Canvas(canvas_frame, bg="#0b0b0b",
                                  highlightthickness=0)
        sb = tk.Scrollbar(canvas_frame, orient="vertical",
                           command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._entries_frame = tk.Frame(self._canvas, bg="#0b0b0b")
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._entries_frame, anchor="nw"
        )
        self._entries_frame.bind("<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(
                self._canvas_window, width=e.width))

    def _browse(self):
        p = filedialog.askopenfilename(
            title="Select AVL file",
            filetypes=[("AVL files", "*.avl"), ("All files", "*.*")]
        )
        if p:
            self._avl_path.set(p)
            self._load()

    def _load(self):
        path = self._avl_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Select a valid AVL file first.")
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        # parse entries
        # look for header "Number of Aev--"
        header = bytes.fromhex("4E756D62657220 6F6620416576 2D2D".replace(" ", ""))
        entries = []
        pos = 0
        while True:
            idx = data.find(header, pos)
            if idx < 0:
                break
            # read 8 values (XX bytes) at their fixed offsets within the entry
            entry_vals = {}
            offsets = [15, 30, 47, 63, 79, 95, 111]
            for i, off in enumerate(offsets):
                byte_pos = idx + off
                if byte_pos < len(data):
                    entry_vals[i] = data[byte_pos]
                else:
                    entry_vals[i] = 0
            entries.append({"start": idx, "vals": entry_vals})
            pos = idx + 16  # move past header

        self._entries = entries
        self._count_var.set(f"AVL count: {len(entries)}")
        self._render_entries()

    def _render_entries(self):
        for w in self._entries_frame.winfo_children():
            w.destroy()
        self._entry_vars = []

        for n, entry in enumerate(self._entries):
            # separator between entries
            if n > 0:
                tk.Frame(self._entries_frame, bg="#c8a035", height=1
                         ).pack(fill="x", padx=0, pady=4)

            hdr_row = tk.Frame(self._entries_frame, bg="#111")
            hdr_row.pack(fill="x", padx=0)
            tk.Label(hdr_row, text=f"AVL Entry {n+1}",
                     fg="#c8a035", bg="#111",
                     font=("Courier New", 9, "bold")).pack(side="left", padx=12, pady=4)
            # delete button
            def make_delete(idx=n):
                def do():
                    if messagebox.askyesno(
                        "Delete AVL" if CURRENT_LANG=="en" else "حذف AVL",
                        f"Delete AVL Entry {idx+1}?"
                        if CURRENT_LANG=="en" else
                        f"حذف AVL Entry {idx+1}؟"
                    ):
                        del self._entries[idx]
                        self._count_var.set(f"AVL count: {len(self._entries)}")
                        self._render_entries()
                return do
            tk.Button(hdr_row, text="Delete" if CURRENT_LANG=="en" else "حذف",
                      font=("Courier New", 7),
                      fg="#ff6060", bg="#2a0a0a",
                      activeforeground="#ff6060", activebackground="#3a1010",
                      relief="flat", bd=0, cursor="hand2",
                      highlightthickness=1, highlightbackground="#ff6060",
                      command=make_delete(), padx=6, pady=1
                      ).pack(side="right", padx=8)

            grid = tk.Frame(self._entries_frame, bg="#0b0b0b")
            grid.pack(padx=16, pady=4, anchor="w")

            row_vars = {}
            field_labels = [
                ("AEV Number",     "رقم AEV"),
                ("Key ID",         "رقم المفتاح"),
                ("Lock Message",   "رسالة المقفل"),
                ("Lock Sound",     "صوت المقفل"),
                ("Lock Camera",    "كاميرا المقفل"),
                ("Unlock Message", "رسالة المفتوح"),
                ("Unlock Sound",   "صوت المفتوح"),
            ]

            for i, (lbl_en, lbl_ar) in enumerate(field_labels):
                lbl = lbl_en if CURRENT_LANG == "en" else lbl_ar
                row = i

                tk.Label(grid, text=f"{lbl:<20}",
                         fg="#c8a035", bg="#0b0b0b",
                         font=("Courier New", 9),
                         width=22, anchor="w"
                         ).grid(row=row, column=0, padx=(0, 8), pady=3, sticky="w")

                val = entry["vals"].get(i, 0)
                hex_val = f"{val:02X}"

                if lbl_en == "Key ID":
                    # show hex value + button to open item picker
                    var = tk.StringVar(value=hex_val)
                    row_vars[i] = ("item_pick", var, None, None)

                    item_row = tk.Frame(grid, bg="#0b0b0b")
                    item_row.grid(row=row, column=1, padx=(0,8), pady=3, sticky="w")

                    # display label
                    disp_lbl = tk.Label(item_row,
                        text=f"{hex_val} — " + next((nm for hx,nm in ITEM_LIST if hx.upper()==hex_val.upper()), "Unknown"),
                        fg="#c8a035", bg="#0b0b0b",
                        font=("Courier New", 8), width=24, anchor="w")
                    disp_lbl.pack(side="left")

                    def make_pick(v=var, lbl=disp_lbl):
                        def do():
                            self._pick_item(v, lbl)
                        return do

                    tk.Button(item_row, text="...",
                              font=("Courier New", 8),
                              fg="#c8a035", bg="#1a1500",
                              activeforeground="#c8a035", activebackground="#2a2000",
                              relief="flat", bd=0, cursor="hand2",
                              highlightthickness=1, highlightbackground="#c8a035",
                              command=make_pick(), padx=6, pady=1
                              ).pack(side="left", padx=4)
                else:
                    var = tk.StringVar(value=hex_val)
                    tk.Entry(grid, textvariable=var,
                             font=("Courier New", 9),
                             fg="#7cfc7c", bg="#0d1a0d",
                             insertbackground="#7cfc7c",
                             relief="flat", bd=0,
                             highlightthickness=1, highlightbackground="#2a5a2a",
                             width=6, justify="center"
                             ).grid(row=row, column=1, padx=(0, 8), pady=3)
                    row_vars[i] = ("entry", var, None, None)

                tk.Label(grid, text="(hex)",
                         fg="#333", bg="#0b0b0b",
                         font=("Courier New", 7)
                         ).grid(row=row, column=2, pady=3, sticky="w")

            self._entry_vars.append(row_vars)

    def _add_entry(self):
        new_entry = {"start": -1, "vals": {i: 0 for i in range(7)}}
        self._entries.append(new_entry)
        self._count_var.set(f"AVL count: {len(self._entries)}")
        self._render_entries()
        # scroll to bottom
        self._canvas.after(50, lambda: self._canvas.yview_moveto(1.0))

    def _pick_item(self, var, disp_lbl):
        """Open item search/picker dialog."""
        dlg = tk.Toplevel(self)
        dlg.title("Select Item")
        dlg.geometry("340x420")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        tk.Label(dlg, text="Search Item",
                 fg="#c8a035", bg="#111",
                 font=("Courier New", 10, "bold")).pack(pady=(12,6))

        search_var = tk.StringVar()
        search_entry = tk.Entry(dlg, textvariable=search_var,
                                font=("Courier New", 9), fg="#7cfc7c", bg="#0d1a0d",
                                insertbackground="#7cfc7c",
                                relief="flat", bd=0,
                                highlightthickness=1, highlightbackground="#2a5a2a",
                                width=28)
        search_entry.pack(pady=(0,6), ipady=3)
        search_entry.focus()

        # listbox
        list_frame = tk.Frame(dlg, bg="#111")
        list_frame.pack(fill="both", expand=True, padx=10)

        lb = tk.Listbox(list_frame,
                        font=("Courier New", 8),
                        fg="#cccccc", bg="#0a0a0a",
                        selectforeground="#000", selectbackground="#c8a035",
                        relief="flat", bd=0,
                        highlightthickness=1, highlightbackground="#333",
                        activestyle="none")
        sb2 = tk.Scrollbar(list_frame, command=lb.yview)
        lb.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        lb.pack(fill="both", expand=True)

        all_items = [f"{hx} — {nm}" for hx, nm in ITEM_LIST]

        def refresh_list(*_):
            q = search_var.get().strip().upper()
            lb.delete(0, "end")
            for item in all_items:
                if not q or q in item.upper():
                    lb.insert("end", item)

        search_var.trace_add("write", refresh_list)
        refresh_list()

        # pre-select current
        cur = var.get().upper()
        for idx in range(lb.size()):
            if lb.get(idx).startswith(cur):
                lb.selection_set(idx)
                lb.see(idx)
                break

        def do_select(event=None):
            sel = lb.curselection()
            if not sel:
                return
            item_str = lb.get(sel[0])
            hex_id   = item_str.split(" — ")[0].strip()
            name     = item_str.split(" — ")[1].strip()
            var.set(hex_id)
            disp_lbl.configure(text=f"{hex_id} — {name}")
            dlg.destroy()

        lb.bind("<Double-Button-1>", do_select)
        lb.bind("<Return>",          do_select)

        tk.Button(dlg, text="Select" if CURRENT_LANG=="en" else "اختر",
                  font=("Courier New", 9),
                  fg="#0a0a0a", bg="#c8a035",
                  activeforeground="#0a0a0a", activebackground="#b8902a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=0,
                  command=do_select, padx=14, pady=4
                  ).pack(pady=8)

    def _save(self):
        path = self._avl_path.get().strip()
        if not path:
            messagebox.showerror("Error", "No file loaded.")
            return
        try:
            with open(path, "rb") as f:
                raw = bytearray(f.read())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        header   = bytes.fromhex("4E756D62657220 6F66204165762D2D".replace(" ",""))
        offsets  = [15, 30, 47, 63, 79, 95, 111]
        sep_3E   = bytes.fromhex("3E" * 16)

        # gather values from UI
        all_vals = []
        for row_vars in self._entry_vars:
            vals = {}
            for i, (kind, var, *_) in row_vars.items():
                if kind == "item_pick":
                    try: vals[i] = int(var.get().strip(), 16)
                    except: vals[i] = 0
                else:
                    try: vals[i] = int(var.get().strip(), 16)
                    except: vals[i] = 0
            all_vals.append(vals)

        # find existing entry positions
        positions = []
        pos = 0
        while True:
            idx = raw.find(header, pos)
            if idx < 0: break
            positions.append(idx)
            pos = idx + 16

        n_existing = len(positions)
        n_ui       = len(all_vals)

        # update existing entries
        for n in range(min(n_existing, n_ui)):
            start = positions[n]
            for i, off in enumerate(offsets):
                if start + off < len(raw):
                    raw[start + off] = all_vals[n].get(i, 0)

        # add new entries if needed
        for n in range(n_existing, n_ui):
            # find end of last entry — look for sep_3E
            # if last entry has sep_3E, append after it
            # if not, add sep_3E first, then new entry
            last_header_pos = positions[-1] if positions else -1

            has_sep = sep_3E in raw[last_header_pos:last_header_pos + 200] if last_header_pos >= 0 else False

            if not has_sep:
                raw += sep_3E

            # build new entry template
            tmpl_str = (
                "4E756D62657220 6F66204165762D2D 00"
                " 4B65792049445F5F5F5F5F5F5F5F 00 00"
                " 6C6F636B206D6573736167652D2D2D 00"
                " 6C6F636B20736F756E642D2D2D2D2D 00"
                " 6C6F636B2063616D6572612D2D2D2D 00"
                " 756E6C6F636B206D6573736167652D 00"
                " 756E6C6F636B20736F756E642D2D2D 00"
                " 3E3E3E3E3E3E3E3E3E3E3E3E3E3E3E3E"
            ).replace(" ","")
            new_entry = bytearray(bytes.fromhex(tmpl_str))
            for i, off in enumerate(offsets):
                if off < len(new_entry):
                    new_entry[off] = all_vals[n].get(i, 0)
            raw += new_entry
            # update positions list
            positions.append(len(raw) - len(new_entry))

        # count is determined by number of headers in file — no need to write it

        try:
            with open(path, "wb") as f:
                f.write(raw)
            messagebox.showinfo("[+] Saved", f"Saved: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))



# ═════════════════════════════════════════════════════════════════════════════
# TOOLS REGISTRY + MASTER APP
# ═════════════════════════════════════════════════════════════════════════════

# ═════════════════════════════════════════════════════════════════════════════
# OSD EDITOR PANEL
# ═════════════════════════════════════════════════════════════════════════════

import struct as _struct

# OSD binary constants
OSD_MAGIC     = bytes([0x44, 0x69, 0x73, 0x63])  # "Disc"
OSD_FALSE_HDR = bytes([0x00, 0x00, 0x00, 0x00])
OSD_FOOTER    = bytes([0xCD, 0xCD, 0xCD, 0xCD])


def _osd_read_block(data, pos):
    try:
        aev = data[pos];  pos += 1
        n   = data[pos];  pos += 1
        items, qtys = [], []
        for _ in range(n):
            items.append(_struct.unpack_from('<H', data, pos)[0]); pos += 2
            qtys.append(_struct.unpack_from('<H', data, pos)[0]);  pos += 2
        nsf  = data[pos]; pos += 1
        suc  = list(data[pos:pos+nsf]); pos += nsf
        fail = list(data[pos:pos+nsf]); pos += nsf
        return aev, items, qtys, nsf, suc, fail, pos
    except Exception:
        return None


def _osd_block_to_bytes(b):
    buf = bytearray()
    buf += OSD_MAGIC if b["osd_op"] else OSD_FALSE_HDR
    buf.append(b["aev_index"])
    buf.append(len(b["items"]))
    for item, qty in zip(b["items"], b["quantities"]):
        buf += _struct.pack('<H', item)
        buf += _struct.pack('<H', qty)
    buf.append(b["num_sf"])
    buf += bytes(b["success_aevs"])
    buf += bytes(b["fail_aevs"])
    return bytes(buf)


def _osd_parse_file(raw):
    data = raw.rstrip(b'\xCD')
    first = data.find(OSD_MAGIC)
    if first == -1:
        return []
    true_blocks = []
    p = first
    while True:
        idx = data.find(OSD_MAGIC, p)
        if idx == -1: break
        res = _osd_read_block(data, idx + 4)
        if res is None: p = idx + 4; continue
        aev, items, qtys, nsf, suc, fail, end = res
        tb = {"osd_op": True, "aev_index": aev, "items": items,
              "quantities": qtys, "num_sf": nsf,
              "success_aevs": suc, "fail_aevs": fail,
              "file_offset": idx, "file_size": end - idx}
        true_blocks.append((idx, end, tb))
        p = idx + 4
    if not true_blocks:
        return []
    all_blocks = []
    first_block = True
    for i, (t_start, t_end, tb) in enumerate(true_blocks):
        if tb["aev_index"] == 0 and len(tb["items"]) == 0:
            if first_block:
                tb["osd_op"] = False
                all_blocks.append(tb)
        else:
            all_blocks.append(tb)
        first_block = False
        zone_start = t_end
        zone_end   = true_blocks[i+1][0] if i+1 < len(true_blocks) else len(data)
        zone = data[zone_start:zone_end]
        zp = 0
        while zp + 4 <= len(zone):
            res = _osd_read_block(zone, zp + 4)
            if res is None: zp += 1; continue
            aev, items, qtys, nsf, suc, fail, new_zp = res
            if aev == 0 and len(items) == 0: zp = new_zp; continue
            fb = {"osd_op": False, "aev_index": aev, "items": items,
                  "quantities": qtys, "num_sf": nsf,
                  "success_aevs": suc, "fail_aevs": fail,
                  "file_offset": zone_start + zp, "file_size": new_zp - zp}
            all_blocks.append(fb)
            zp = new_zp
    return all_blocks


class OSDEditorPanel(tk.Frame):
    """OSD Editor — GUI for reading/writing RE4 .OSD files."""

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.master_app  = master_app
        self._osd_path   = tk.StringVar()
        self._blocks     = []
        self._block_vars = []
        self._add_footer = tk.BooleanVar(value=False)
        self._built      = False

    def activate(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        # header
        hdr = tk.Frame(self, bg="#0e0e0e")
        hdr.pack(fill="x")
        tk.Label(hdr, text="OSD EDITOR",
                 fg="#c8a035", bg="#0e0e0e",
                 font=("Courier New", 12, "bold")).pack(side="left", padx=16, pady=10)
        tk.Frame(self, bg="#c8a035", height=1).pack(fill="x")

        # path row
        top = tk.Frame(self, bg="#111")
        top.pack(fill="x", padx=12, pady=8)
        tk.Label(top, text="OSD File:", fg="#777", bg="#111",
                 font=("Courier New", 9)).pack(side="left")
        tk.Entry(top, textvariable=self._osd_path,
                 font=("Courier New", 9), fg="#7cfc7c", bg="#0d1a0d",
                 insertbackground="#7cfc7c",
                 relief="flat", bd=0,
                 highlightthickness=1, highlightbackground="#2a5a2a",
                 width=44).pack(side="left", ipady=3, padx=6)
        tk.Button(top, text="Browse",
                  font=("Courier New", 8), fg="#c8a035", bg="#1a1500",
                  activeforeground="#c8a035", activebackground="#2a2000",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#c8a035",
                  command=self._browse, padx=8, pady=2).pack(side="left")
        tk.Button(top, text="Load",
                  font=("Courier New", 8), fg="#7cfc7c", bg="#1a2a0a",
                  activeforeground="#7cfc7c", activebackground="#2a4a1a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#7cfc7c",
                  command=self._load, padx=8, pady=2).pack(side="left", padx=4)

        # options row
        opt_row = tk.Frame(self, bg="#0b0b0b")
        opt_row.pack(fill="x", padx=16, pady=(0, 4))
        self._count_var = tk.StringVar(value="OSD count: —")
        tk.Label(opt_row, textvariable=self._count_var,
                 fg="#c8a035", bg="#0b0b0b",
                 font=("Courier New", 9)).pack(side="left")

        tk.Checkbutton(opt_row,
                       text="Add CD CD CD CD footer",
                       variable=self._add_footer,
                       fg="#ccc", bg="#0b0b0b",
                       activebackground="#0b0b0b", selectcolor="#1a1a1a",
                       font=("Courier New", 8), relief="flat"
                       ).pack(side="left", padx=20)

        tk.Button(opt_row, text="+ Add OSD",
                  font=("Courier New", 8), fg="#7cfc7c", bg="#1a2a0a",
                  activeforeground="#7cfc7c", activebackground="#2a4a1a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#7cfc7c",
                  command=self._add_block, padx=8, pady=2).pack(side="right", padx=4)
        tk.Button(opt_row, text="Save File",
                  font=("Courier New", 8), fg="#c8a035", bg="#1a1500",
                  activeforeground="#c8a035", activebackground="#2a2000",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground="#c8a035",
                  command=self._save, padx=8, pady=2).pack(side="right")

        tk.Frame(self, bg="#222", height=1).pack(fill="x")

        # scrollable area
        cf = tk.Frame(self, bg="#0b0b0b")
        cf.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(cf, bg="#0b0b0b", highlightthickness=0)
        sb = tk.Scrollbar(cf, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._blocks_frame = tk.Frame(self._canvas, bg="#0b0b0b")
        self._cwin = self._canvas.create_window((0,0), window=self._blocks_frame, anchor="nw")
        self._blocks_frame.bind("<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._cwin, width=e.width))

    def _browse(self):
        p = filedialog.askopenfilename(
            title="Select OSD file",
            filetypes=[("OSD files", "*.osd"), ("All files", "*.*")]
        )
        if p:
            self._osd_path.set(p)
            self._load()

    def _load(self):
        path = self._osd_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Select a valid OSD file first.")
            return
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._add_footer.set(raw.endswith(OSD_FOOTER))
        blocks = _osd_parse_file(raw)
        if not blocks:
            blocks = [{"osd_op": False, "aev_index": 0, "items": [],
                       "quantities": [], "num_sf": 0,
                       "success_aevs": [], "fail_aevs": []}]
        self._blocks = blocks
        self._count_var.set(f"OSD count: {len(blocks)}")
        self._render_blocks()

    def _render_blocks(self):
        for w in self._blocks_frame.winfo_children():
            w.destroy()
        self._block_vars = []

        for n, block in enumerate(self._blocks):
            if n > 0:
                tk.Frame(self._blocks_frame, bg="#c8a035", height=1).pack(fill="x", pady=4)

            hdr_row = tk.Frame(self._blocks_frame, bg="#111")
            hdr_row.pack(fill="x")
            tk.Label(hdr_row, text=f"OSD Entry {n+1}",
                     fg="#c8a035", bg="#111",
                     font=("Courier New", 9, "bold")).pack(side="left", padx=12, pady=4)

            def make_del(idx=n):
                def do():
                    if messagebox.askyesno(
                        "Delete OSD", f"Delete OSD Entry {idx+1}?"):
                        del self._blocks[idx]
                        self._count_var.set(f"OSD count: {len(self._blocks)}")
                        self._render_blocks()
                return do
            tk.Button(hdr_row, text="Delete",
                      font=("Courier New", 7), fg="#ff6060", bg="#2a0a0a",
                      activeforeground="#ff6060", activebackground="#3a1010",
                      relief="flat", bd=0, cursor="hand2",
                      highlightthickness=1, highlightbackground="#ff6060",
                      command=make_del(), padx=6, pady=1).pack(side="right", padx=8)

            grid = tk.Frame(self._blocks_frame, bg="#0b0b0b")
            grid.pack(padx=16, pady=4, anchor="w")

            bvars = {}

            # OSD Operation (toggle)
            op_var = tk.BooleanVar(value=block.get("osd_op", False))
            bvars["osd_op"] = op_var
            op_row = tk.Frame(grid, bg="#0b0b0b")
            op_row.grid(row=0, column=0, columnspan=4, padx=0, pady=3, sticky="w")
            tk.Label(op_row, text="OSD Operation (Disc/active):",
                     fg="#c8a035", bg="#0b0b0b",
                     font=("Courier New", 9), width=30, anchor="w").pack(side="left")
            op_btn = tk.Button(op_row,
                               text="TRUE" if op_var.get() else "FALSE",
                               width=7, font=("Courier New", 8),
                               fg="#7cfc7c" if op_var.get() else "#bbbbbb",
                               bg="#1a2a0a" if op_var.get() else "#1a1a1a",
                               relief="flat", bd=0, cursor="hand2",
                               highlightthickness=1,
                               highlightbackground="#7cfc7c" if op_var.get() else "#555")
            op_btn.pack(side="left")
            def make_toggle_op(v=op_var, btn=op_btn):
                def do():
                    v.set(not v.get())
                    btn.configure(
                        text="TRUE" if v.get() else "FALSE",
                        fg="#7cfc7c" if v.get() else "#bbbbbb",
                        bg="#1a2a0a" if v.get() else "#1a1a1a",
                        highlightbackground="#7cfc7c" if v.get() else "#555"
                    )
                return do
            op_btn.configure(command=make_toggle_op())

            # AEV Index (hex)
            self._add_hex_field(grid, bvars, 1, "AEV INDEX (hex)",
                                f"{block.get('aev_index', 0):02X}", "aev_index")

            # Number of Items
            n_items = len(block.get("items", []))
            n_items_var = tk.StringVar(value=str(n_items))
            bvars["n_items_var"] = n_items_var
            self._add_dec_field(grid, bvars, 2, "Number of Items (dec)",
                                str(n_items), "n_items_str",
                                on_change=lambda v=n_items_var, b=bvars, g=grid, blk=block:
                                    self._refresh_dynamic(g, b, blk))

            # Dynamic item fields
            items_frame = tk.Frame(grid, bg="#0b0b0b")
            items_frame.grid(row=3, column=0, columnspan=6, sticky="w")
            bvars["items_frame"] = items_frame
            bvars["items"]       = []
            bvars["quantities"]  = []
            self._build_item_fields(items_frame, bvars, block)

            # Number of Success/Fail
            n_sf = block.get("num_sf", 0)
            bvars["n_sf_var"] = tk.StringVar(value=str(n_sf))
            self._add_dec_field(grid, bvars, 4, "Number of Success/Fail AEVs (dec)",
                                str(n_sf), "n_sf_str",
                                on_change=lambda b=bvars, g=grid, blk=block:
                                    self._refresh_sf(g, b, blk))

            # Dynamic SF fields
            sf_frame = tk.Frame(grid, bg="#0b0b0b")
            sf_frame.grid(row=5, column=0, columnspan=6, sticky="w")
            bvars["sf_frame"]  = sf_frame
            bvars["suc_aevs"]  = []
            bvars["fail_aevs"] = []
            self._build_sf_fields(sf_frame, bvars, block)

            self._block_vars.append(bvars)

    def _add_hex_field(self, grid, bvars, row, label, val, key):
        tk.Label(grid, text=f"{label}:",
                 fg="#c8a035", bg="#0b0b0b",
                 font=("Courier New", 8), width=36, anchor="w"
                 ).grid(row=row, column=0, padx=(0,6), pady=3, sticky="w")
        var = tk.StringVar(value=val)
        bvars[key] = var
        tk.Entry(grid, textvariable=var, font=("Courier New", 9),
                 fg="#7cfc7c", bg="#0d1a0d", insertbackground="#7cfc7c",
                 relief="flat", bd=0,
                 highlightthickness=1, highlightbackground="#2a5a2a",
                 width=6, justify="center").grid(row=row, column=1, pady=3)
        tk.Label(grid, text="(hex)", fg="#333", bg="#0b0b0b",
                 font=("Courier New", 7)).grid(row=row, column=2, pady=3, sticky="w", padx=4)

    def _add_dec_field(self, grid, bvars, row, label, val, key, on_change=None):
        tk.Label(grid, text=f"{label}:",
                 fg="#c8a035", bg="#0b0b0b",
                 font=("Courier New", 8), width=36, anchor="w"
                 ).grid(row=row, column=0, padx=(0,6), pady=3, sticky="w")
        var = tk.StringVar(value=val)
        bvars[key] = var
        e = tk.Entry(grid, textvariable=var, font=("Courier New", 9),
                     fg="#7cfc7c", bg="#0d1a0d", insertbackground="#7cfc7c",
                     relief="flat", bd=0,
                     highlightthickness=1, highlightbackground="#2a5a2a",
                     width=6, justify="center")
        e.grid(row=row, column=1, pady=3)
        tk.Label(grid, text="(dec)", fg="#333", bg="#0b0b0b",
                 font=("Courier New", 7)).grid(row=row, column=2, pady=3, sticky="w", padx=4)
        if on_change:
            var.trace_add("write", lambda *_: on_change())

    def _build_item_fields(self, frame, bvars, block):
        for w in frame.winfo_children():
            w.destroy()
        bvars["items"]      = []
        bvars["quantities"] = []
        items = block.get("items", [])
        qtys  = block.get("quantities", [])
        try:
            n = int(bvars.get("n_items_str", tk.StringVar(value="0")).get())
        except Exception:
            n = len(items)
        for i in range(n):
            row_f = tk.Frame(frame, bg="#0b0b0b")
            row_f.pack(anchor="w", pady=1)
            tk.Label(row_f, text=f"  Item {i+1} ID:",
                     fg="#aaa", bg="#0b0b0b",
                     font=("Courier New", 8), width=14, anchor="w").pack(side="left")
            item_val = f"{items[i]:02X}" if i < len(items) else "00"
            item_var = tk.StringVar(value=item_val)
            bvars["items"].append(item_var)
            item_entry = tk.Entry(row_f, textvariable=item_var,
                                  font=("Courier New", 8), fg="#7cfc7c", bg="#0d1a0d",
                                  insertbackground="#7cfc7c", relief="flat", bd=0,
                                  highlightthickness=1, highlightbackground="#2a5a2a",
                                  width=5, justify="center")
            item_entry.pack(side="left", ipady=2)
            # picker button
            disp_lbl = tk.Label(row_f,
                                text=next((nm for hx,nm in ITEM_LIST if hx.upper()==item_val.upper()), ""),
                                fg="#888", bg="#0b0b0b", font=("Courier New", 7), width=20, anchor="w")
            disp_lbl.pack(side="left", padx=4)
            def make_pick(v=item_var, lbl=disp_lbl):
                def do(): self._pick_item_osd(v, lbl)
                return do
            tk.Button(row_f, text="...",
                      font=("Courier New", 7), fg="#c8a035", bg="#1a1500",
                      activeforeground="#c8a035", activebackground="#2a2000",
                      relief="flat", bd=0, cursor="hand2",
                      highlightthickness=1, highlightbackground="#c8a035",
                      command=make_pick(), padx=4, pady=1).pack(side="left")
            tk.Label(row_f, text=f"  Qty {i+1}:",
                     fg="#aaa", bg="#0b0b0b",
                     font=("Courier New", 8), width=8, anchor="w").pack(side="left", padx=(10,0))
            qty_val = str(qtys[i]) if i < len(qtys) else "65535"
            qty_var = tk.StringVar(value=qty_val)
            bvars["quantities"].append(qty_var)
            tk.Entry(row_f, textvariable=qty_var,
                     font=("Courier New", 8), fg="#7cfc7c", bg="#0d1a0d",
                     insertbackground="#7cfc7c", relief="flat", bd=0,
                     highlightthickness=1, highlightbackground="#2a5a2a",
                     width=6, justify="center").pack(side="left", ipady=2)
            tk.Label(row_f, text="(dec)", fg="#333", bg="#0b0b0b",
                     font=("Courier New", 7)).pack(side="left", padx=2)

    def _build_sf_fields(self, frame, bvars, block):
        for w in frame.winfo_children():
            w.destroy()
        bvars["suc_aevs"]  = []
        bvars["fail_aevs"] = []
        suc  = block.get("success_aevs", [])
        fail = block.get("fail_aevs", [])
        try:
            n = int(bvars["n_sf_str"].get())
        except Exception:
            n = block.get("num_sf", 0)
        for i in range(n):
            row_f = tk.Frame(frame, bg="#0b0b0b")
            row_f.pack(anchor="w", pady=1)
            tk.Label(row_f, text=f"  Success AEV {i+1} (hex):",
                     fg="#aaa", bg="#0b0b0b",
                     font=("Courier New", 8), width=22, anchor="w").pack(side="left")
            sv = tk.StringVar(value=f"{suc[i]:02X}" if i < len(suc) else "FF")
            bvars["suc_aevs"].append(sv)
            tk.Entry(row_f, textvariable=sv, font=("Courier New", 8),
                     fg="#7cfc7c", bg="#0d1a0d", insertbackground="#7cfc7c",
                     relief="flat", bd=0,
                     highlightthickness=1, highlightbackground="#2a5a2a",
                     width=5, justify="center").pack(side="left", ipady=2)
            tk.Label(row_f, text=f"   Fail AEV {i+1} (hex):",
                     fg="#aaa", bg="#0b0b0b",
                     font=("Courier New", 8), width=18, anchor="w").pack(side="left", padx=(16,0))
            fv = tk.StringVar(value=f"{fail[i]:02X}" if i < len(fail) else "FF")
            bvars["fail_aevs"].append(fv)
            tk.Entry(row_f, textvariable=fv, font=("Courier New", 8),
                     fg="#7cfc7c", bg="#0d1a0d", insertbackground="#7cfc7c",
                     relief="flat", bd=0,
                     highlightthickness=1, highlightbackground="#2a5a2a",
                     width=5, justify="center").pack(side="left", ipady=2)

    def _refresh_dynamic(self, grid, bvars, block):
        try:
            n = int(bvars["n_items_str"].get())
        except Exception:
            return
        frame = bvars["items_frame"]
        # update block with current items/qtys before rebuild
        block["items"]      = [i for i in block.get("items", [])]
        block["quantities"] = [q for q in block.get("quantities", [])]
        self._build_item_fields(frame, bvars, block)

    def _refresh_sf(self, grid, bvars, block):
        try:
            n = int(bvars["n_sf_str"].get())
        except Exception:
            return
        frame = bvars["sf_frame"]
        self._build_sf_fields(frame, bvars, block)

    def _pick_item_osd(self, var, disp_lbl):
        dlg = tk.Toplevel(self)
        dlg.title("Select Item")
        dlg.geometry("340x420")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()
        tk.Label(dlg, text="Search Item", fg="#c8a035", bg="#111",
                 font=("Courier New", 10, "bold")).pack(pady=(12,6))
        search_var = tk.StringVar()
        search_entry = tk.Entry(dlg, textvariable=search_var,
                                font=("Courier New", 9), fg="#7cfc7c", bg="#0d1a0d",
                                insertbackground="#7cfc7c", relief="flat", bd=0,
                                highlightthickness=1, highlightbackground="#2a5a2a", width=28)
        search_entry.pack(pady=(0,6), ipady=3)
        search_entry.focus()
        lf = tk.Frame(dlg, bg="#111")
        lf.pack(fill="both", expand=True, padx=10)
        lb = tk.Listbox(lf, font=("Courier New", 8),
                        fg="#cccccc", bg="#0a0a0a",
                        selectforeground="#000", selectbackground="#c8a035",
                        relief="flat", bd=0,
                        highlightthickness=1, highlightbackground="#333", activestyle="none")
        sb2 = tk.Scrollbar(lf, command=lb.yview)
        lb.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        lb.pack(fill="both", expand=True)
        all_items = [f"{hx} — {nm}" for hx, nm in ITEM_LIST]
        def refresh(*_):
            q = search_var.get().strip().upper()
            lb.delete(0, "end")
            for item in all_items:
                if not q or q in item.upper():
                    lb.insert("end", item)
        search_var.trace_add("write", refresh)
        refresh()
        cur = var.get().upper()
        for idx in range(lb.size()):
            if lb.get(idx).startswith(cur):
                lb.selection_set(idx); lb.see(idx); break
        def do_select(event=None):
            sel = lb.curselection()
            if not sel: return
            item_str = lb.get(sel[0])
            hex_id = item_str.split(" — ")[0].strip()
            name   = item_str.split(" — ")[1].strip()
            var.set(hex_id)
            disp_lbl.configure(text=name)
            dlg.destroy()
        lb.bind("<Double-Button-1>", do_select)
        lb.bind("<Return>", do_select)
        tk.Button(dlg, text="Select", font=("Courier New", 9),
                  fg="#0a0a0a", bg="#c8a035",
                  activeforeground="#0a0a0a", activebackground="#b8902a",
                  relief="flat", bd=0, cursor="hand2", highlightthickness=0,
                  command=do_select, padx=14, pady=4).pack(pady=8)

    def _add_block(self):
        self._blocks.append({"osd_op": False, "aev_index": 0, "items": [],
                             "quantities": [], "num_sf": 0,
                             "success_aevs": [], "fail_aevs": []})
        self._count_var.set(f"OSD count: {len(self._blocks)}")
        self._render_blocks()
        self._canvas.after(50, lambda: self._canvas.yview_moveto(1.0))

    def _save(self):
        path = self._osd_path.get().strip()
        if not path:
            messagebox.showerror("Error", "No OSD file loaded.")
            return
        # build blocks from UI
        blocks = []
        for i, bvars in enumerate(self._block_vars):
            try:
                op  = bvars["osd_op"].get()
                aev = int(bvars["aev_index"].get().strip(), 16)
                items, qtys = [], []
                for iv, qv in zip(bvars.get("items", []), bvars.get("quantities", [])):
                    try:
                        items.append(int(iv.get().strip(), 16))
                        qtys.append(int(qv.get().strip()))
                    except Exception:
                        pass
                suc, fail = [], []
                for sv in bvars.get("suc_aevs", []):
                    try: suc.append(int(sv.get().strip(), 16))
                    except: suc.append(0xFF)
                for fv in bvars.get("fail_aevs", []):
                    try: fail.append(int(fv.get().strip(), 16))
                    except: fail.append(0xFF)
                nsf = max(len(suc), len(fail))
                suc  = (suc  + [0xFF]*nsf)[:nsf]
                fail = (fail + [0xFF]*nsf)[:nsf]
                blocks.append({"osd_op": op, "aev_index": aev,
                               "items": items, "quantities": qtys,
                               "num_sf": nsf, "success_aevs": suc, "fail_aevs": fail})
            except Exception as e:
                messagebox.showerror("Error", f"Block {i+1}: {e}")
                return
        buf = bytearray()
        for b in blocks:
            buf += _osd_block_to_bytes(b)
        if self._add_footer.get():
            buf += OSD_FOOTER
        try:
            with open(path, "wb") as f:
                f.write(buf)
            messagebox.showinfo("[+] Saved", f"Saved: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ═════════════════════════════════════════════════════════════════════════════
# ROOM INIT EDITOR PANEL
# ═════════════════════════════════════════════════════════════════════════════

ROOM_INIT_CONFIG = {
    "ST1": {"base_address": 0x4DE450, "rooms": {
        "0":"100","1":"101","2":"102","3":"103","4":"104","5":"105",
        "6":"106","7":"107","8":"108","9":"109","A":"10a","B":"10b",
        "C":"10c","D":"10d","E":"10e","F":"10f","10":"111","11":"112",
        "12":"113","13":"117","14":"118","15":"119","16":"11a","17":"11b",
        "18":"11c","19":"11d","1A":"11e","1B":"11f","1C":"120","1D":"121",
        "1E":"122","1F":"123","20":"124","21":"125","22":"126","23":"127",
        "24":"128","25":"129","26":"12a","27":"12b","28":"12c","29":"12d",
        "2A":"12e","2B":"12f","2C":"130","2D":"131","2E":"132","2F":"133",
        "30":"134","31":"135","32":"136","33":"137"}},
    "ST2": {"base_address": 0x4A9E70, "rooms": {
        "0":"200","1":"201","2":"202","3":"203","4":"204","5":"205",
        "6":"206","7":"207","8":"208","9":"209","A":"20a","B":"20b",
        "C":"20c","D":"20d","E":"20e","F":"20f","10":"210","11":"211",
        "12":"212","13":"213","14":"214","15":"215","16":"216","17":"217",
        "18":"218","19":"219","1A":"21a","1B":"21b","1C":"21d","1D":"220",
        "1E":"221","1F":"222","20":"223","21":"224","22":"225","23":"226",
        "24":"227","25":"228","26":"229","27":"22a","28":"22b","29":"22c",
        "2A":"22e","2B":"22f","2C":"230","2D":"231","2E":"232","2F":"233",
        "30":"234","31":"235","32":"236","33":"237","34":"238","35":"239",
        "36":"240","37":"241","38":"242","39":"243","3A":"244","3B":"245"}},
    "ST3": {"base_address": 0x43E530, "rooms": {
        "0":"300","1":"301","2":"302","3":"303","4":"304","5":"305",
        "6":"306","7":"307","8":"308","9":"309","A":"30a","B":"30b",
        "C":"30c","D":"30d","E":"30e","F":"30f","10":"310","11":"311",
        "12":"312","13":"315","14":"316","15":"317","16":"318","17":"31a",
        "18":"31b","19":"31c","1A":"31d","1B":"320","1C":"321","1D":"325",
        "1E":"326","1F":"327","20":"328","21":"329","22":"330","23":"331",
        "24":"332","25":"333","26":"335","27":"336","28":"337","29":"338",
        "2A":"339","2B":"340","2C":"341","2D":"342","2E":"343","2F":"344",
        "30":"345","31":"346","32":"347","33":"348","34":"349","35":"350",
        "36":"351","37":"352","38":"353","39":"354","3A":"355","3B":"356",
        "3C":"357","3D":"358"}},
}


class RoomInitPanel(tk.Frame):
    """Room Init Editor — clone room INIT IDs in bio4.exe."""

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.master_app    = master_app
        self._re4lfs_path  = None
        self._bio4_path    = None
        self._built        = False

    def activate(self):
        if not self._built:
            self._build()
            self._built = True
        self._refresh_exe()

    def _get_exe(self):
        return self.master_app.exe_path.get().strip()

    def _refresh_exe(self):
        exe = self._get_exe()
        if exe and os.path.isfile(exe):
            exe_dir = os.path.dirname(exe)
            self._bio4_path = os.path.join(os.path.dirname(exe_dir), "BIO4")
            # re4lfs.exe next to the master EXE in Room Init folder
            self._re4lfs_path = os.path.join(MASTER_DIR, "ROOM INIT EDITOR", "re4lfs.exe")
            enabled = True
        else:
            enabled = False
        self._set_controls(enabled)
        if enabled:
            self._update_source_id()
            self._update_target_id()

    def _build(self):
        # header
        hdr = tk.Frame(self, bg="#0e0e0e")
        hdr.pack(fill="x")
        tk.Label(hdr, text="ROOM INIT EDITOR",
                 fg="#c8a035", bg="#0e0e0e",
                 font=("Courier New", 12, "bold")).pack(side="left", padx=16, pady=10)
        tk.Frame(self, bg="#c8a035", height=1).pack(fill="x")

        desc = tk.Label(self,
                        text="bio4.exe path is set from the top bar. Place re4lfs.exe in: RE4 MASTER EDITOR/ROOM INIT EDITOR/",
                        fg="#555", bg="#0b0b0b", font=("Courier New", 8))
        desc.pack(anchor="w", padx=16, pady=(8,4))

        # room selection
        sel_frame = tk.Frame(self, bg="#0b0b0b")
        sel_frame.pack(fill="x", padx=16, pady=4)

        # Source
        src_box = tk.LabelFrame(sel_frame, text="Source Room (Copy From)",
                                fg="#c8a035", bg="#0b0b0b",
                                font=("Courier New", 8, "bold"))
        src_box.grid(row=0, column=0, padx=(0,12), sticky="ew")

        tk.Label(src_box, text="Stage:", fg="#ccc", bg="#0b0b0b",
                 font=("Courier New", 8)).grid(row=0, column=0, padx=8, pady=4, sticky="w")
        self._src_stage = ttk.Combobox(src_box, values=sorted(ROOM_INIT_CONFIG.keys()),
                                        state="readonly", width=8,
                                        font=("Courier New", 8))
        self._src_stage.grid(row=0, column=1, padx=4, pady=4)
        self._src_stage.current(0)

        tk.Label(src_box, text="Room:", fg="#ccc", bg="#0b0b0b",
                 font=("Courier New", 8)).grid(row=1, column=0, padx=8, pady=4, sticky="w")
        self._src_room = ttk.Combobox(src_box, state="readonly", width=14,
                                       font=("Courier New", 8))
        self._src_room.grid(row=1, column=1, padx=4, pady=4)

        tk.Label(src_box, text="INIT ID:", fg="#ccc", bg="#0b0b0b",
                 font=("Courier New", 8)).grid(row=2, column=0, padx=8, pady=4, sticky="w")
        self._src_id = tk.Entry(src_box, font=("Courier New", 9),
                                fg="#7cfc7c", bg="#0d1a0d",
                                relief="flat", bd=0,
                                highlightthickness=1, highlightbackground="#2a5a2a",
                                width=12, state="readonly")
        self._src_id.grid(row=2, column=1, padx=4, pady=4, ipady=2)

        # Target
        tgt_box = tk.LabelFrame(sel_frame, text="Target Room (Paste To)",
                                fg="#c8a035", bg="#0b0b0b",
                                font=("Courier New", 8, "bold"))
        tgt_box.grid(row=0, column=1, sticky="ew")

        tk.Label(tgt_box, text="Stage:", fg="#ccc", bg="#0b0b0b",
                 font=("Courier New", 8)).grid(row=0, column=0, padx=8, pady=4, sticky="w")
        self._tgt_stage = ttk.Combobox(tgt_box, values=sorted(ROOM_INIT_CONFIG.keys()),
                                        state="readonly", width=8,
                                        font=("Courier New", 8))
        self._tgt_stage.grid(row=0, column=1, padx=4, pady=4)
        self._tgt_stage.current(0)

        tk.Label(tgt_box, text="Room:", fg="#ccc", bg="#0b0b0b",
                 font=("Courier New", 8)).grid(row=1, column=0, padx=8, pady=4, sticky="w")
        self._tgt_room = ttk.Combobox(tgt_box, state="readonly", width=14,
                                       font=("Courier New", 8))
        self._tgt_room.grid(row=1, column=1, padx=4, pady=4)

        tk.Label(tgt_box, text="INIT ID:", fg="#ccc", bg="#0b0b0b",
                 font=("Courier New", 8)).grid(row=2, column=0, padx=8, pady=4, sticky="w")
        self._tgt_id = tk.Entry(tgt_box, font=("Courier New", 9),
                                fg="#7cfc7c", bg="#0d1a0d",
                                relief="flat", bd=0,
                                highlightthickness=1, highlightbackground="#2a5a2a",
                                width=12, state="readonly")
        self._tgt_id.grid(row=2, column=1, padx=4, pady=4, ipady=2)

        sel_frame.columnconfigure(0, weight=1)
        sel_frame.columnconfigure(1, weight=1)

        # populate rooms
        self._populate_rooms(self._src_stage, self._src_room)
        self._populate_rooms(self._tgt_stage, self._tgt_room)

        # bind changes
        self._src_stage.bind("<<ComboboxSelected>>",
            lambda e: (self._populate_rooms(self._src_stage, self._src_room),
                       self._update_source_id()))
        self._src_room.bind("<<ComboboxSelected>>", lambda e: self._update_source_id())
        self._tgt_stage.bind("<<ComboboxSelected>>",
            lambda e: (self._populate_rooms(self._tgt_stage, self._tgt_room),
                       self._update_target_id()))
        self._tgt_room.bind("<<ComboboxSelected>>", lambda e: self._update_target_id())

        # Advanced options
        adv_frame = tk.Frame(self, bg="#0b0b0b")
        adv_frame.pack(fill="x", padx=16, pady=8)

        opts = [
            ("Clone Advanced (assets, sounds, etc.)", "_clone_adv"),
            ("Auto-Extract LFS Files",                "_auto_lfs"),
            ("Force LFS (overwrite existing)",         "_force_lfs"),
            ("Disable original LFS (rename to .org)", "_disable_lfs"),
        ]
        self._opt_vars = {}
        defaults = [True, True, False, True]
        for i, ((lbl, key), default) in enumerate(zip(opts, defaults)):
            var = tk.BooleanVar(value=default)
            self._opt_vars[key] = var
            row_f = tk.Frame(adv_frame, bg="#0b0b0b")
            row_f.pack(anchor="w", pady=2)
            tk.Checkbutton(row_f, text=lbl, variable=var,
                           fg="#ccc", bg="#0b0b0b",
                           activebackground="#0b0b0b", selectcolor="#1a1a1a",
                           font=("Courier New", 8), relief="flat").pack(side="left")

        # Clone button
        tk.Frame(self, bg="#222", height=1).pack(fill="x", padx=16)
        btn_row = tk.Frame(self, bg="#0b0b0b")
        btn_row.pack(pady=10)
        self._clone_btn = tk.Button(btn_row,
                                    text="Clone Room Data",
                                    font=("Courier New", 11, "bold"),
                                    fg="#0a0a0a", bg="#c8a035",
                                    activeforeground="#0a0a0a", activebackground="#b8902a",
                                    relief="flat", bd=0, cursor="hand2",
                                    highlightthickness=0,
                                    command=self._clone, padx=24, pady=8)
        self._clone_btn.pack()

        # Status
        self._status_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self._status_var,
                 fg="#7cfc7c", bg="#0b0b0b",
                 font=("Courier New", 8), wraplength=600).pack(pady=4)

        self._controls = [self._src_stage, self._src_room,
                          self._tgt_stage, self._tgt_room, self._clone_btn]
        self._set_controls(False)

    def _set_controls(self, enabled):
        state = "normal" if enabled else "disabled"
        if hasattr(self, "_controls"):
            for w in self._controls:
                try: w.configure(state=state)
                except Exception: pass

    def _populate_rooms(self, stage_combo, room_combo):
        stage_key = stage_combo.get()
        if not stage_key or stage_key not in ROOM_INIT_CONFIG:
            return
        rooms = ROOM_INIT_CONFIG[stage_key]["rooms"]
        sorted_rooms = sorted(
            [(f"r{room_id} (val {val})", val) for val, room_id in rooms.items()],
            key=lambda x: x[0]
        )
        room_combo["values"] = [t for t, _ in sorted_rooms]
        room_combo._vals      = [v for _, v in sorted_rooms]
        if sorted_rooms:
            room_combo.current(0)

    def _get_room_val(self, combo):
        idx = combo.current()
        vals = getattr(combo, "_vals", [])
        if 0 <= idx < len(vals):
            return vals[idx]
        return None

    def _calc_offset(self, stage_key, room_val):
        return ROOM_INIT_CONFIG[stage_key]["base_address"] + (int(room_val, 16) * 0x14) + 0x06

    def _read_init_id(self, stage_key, room_val):
        exe = self._get_exe()
        if not exe or not os.path.isfile(exe):
            return ""
        try:
            off = self._calc_offset(stage_key, room_val)
            with open(exe, "rb") as f:
                f.seek(off)
                return f.read(4).hex().upper()
        except Exception:
            return ""

    def _update_source_id(self):
        stage = self._src_stage.get()
        val   = self._get_room_val(self._src_room)
        if stage and val:
            id_hex = self._read_init_id(stage, val)
            self._src_id.configure(state="normal")
            self._src_id.delete(0, "end")
            self._src_id.insert(0, id_hex)
            self._src_id.configure(state="readonly")

    def _update_target_id(self):
        stage = self._tgt_stage.get()
        val   = self._get_room_val(self._tgt_room)
        if stage and val:
            id_hex = self._read_init_id(stage, val)
            self._tgt_id.configure(state="normal")
            self._tgt_id.delete(0, "end")
            self._tgt_id.insert(0, id_hex)
            self._tgt_id.configure(state="readonly")

    def _clone(self):
        exe = self._get_exe()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Select bio4.exe first.")
            return
        src_id = self._src_id.get().strip()
        if len(src_id) != 8:
            messagebox.showerror("Error", "Source INIT ID is not valid.")
            return
        src_stage = self._src_stage.get()
        tgt_stage = self._tgt_stage.get()
        src_val   = self._get_room_val(self._src_room)
        tgt_val   = self._get_room_val(self._tgt_room)
        if not src_val or not tgt_val:
            messagebox.showerror("Error", "Invalid room selection.")
            return

        src_room_id = ROOM_INIT_CONFIG[src_stage]["rooms"].get(src_val)
        tgt_room_id = ROOM_INIT_CONFIG[tgt_stage]["rooms"].get(tgt_val)

        clone_adv    = self._opt_vars["_clone_adv"].get()
        auto_lfs     = self._opt_vars["_auto_lfs"].get()
        force_lfs    = self._opt_vars["_force_lfs"].get()
        disable_lfs  = self._opt_vars["_disable_lfs"].get()

        if not clone_adv:
            if not messagebox.askyesno("Confirm Simple Clone",
                "Patch target room INIT ID in EXE only. Proceed?"):
                return
            try:
                off = self._calc_offset(tgt_stage, tgt_val)
                with open(exe, "rb+") as f:
                    f.seek(off); f.write(bytes.fromhex(src_id))
                self._update_target_id()
                self._status_var.set(f"Simple Clone done. Target INIT ID patched.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            return

        # Advanced clone
        if not self._bio4_path or not os.path.isdir(self._bio4_path):
            messagebox.showerror("Error",
                "BIO4 folder not found. Ensure bio4.exe is in Bin32 folder.")
            return

        import subprocess

        def get_files(stage_key, room_id):
            stage_dir  = os.path.join(self._bio4_path, stage_key)
            img_dir    = os.path.join(self._bio4_path, "ImagePackHD")
            snd_room   = os.path.join(self._bio4_path, "Snd", "room", stage_key)
            snd_foot   = os.path.join(self._bio4_path, "Snd", "foot", stage_key)
            files = [
                os.path.join(stage_dir, f"r{room_id}.udas"),
                os.path.join(img_dir,   f"44000{room_id}.pack"),
                os.path.join(snd_room,  f"r{room_id}.xwb"),
                os.path.join(snd_room,  f"r{room_id}.xsb"),
                os.path.join(snd_foot,  f"r{room_id}f.xwb"),
                os.path.join(snd_foot,  f"r{room_id}f.xsb"),
            ]
            return files

        src_files = get_files(src_stage, src_room_id)
        tgt_files = get_files(tgt_stage, tgt_room_id)
        lfs_ok    = self._re4lfs_path and os.path.isfile(self._re4lfs_path)

        if not messagebox.askyesno("Confirm Advanced Clone",
            f"Clone r{src_room_id} → r{tgt_room_id}\n\n"
            f"Advanced: {clone_adv}  Auto-LFS: {auto_lfs}  Force: {force_lfs}  Disable-LFS: {disable_lfs}\n\n"
            "Proceed?"):
            return

        try:
            for src_f, tgt_f in zip(src_files, tgt_files):
                ext = os.path.splitext(src_f)[1].lower()
                if ext in (".xwb", ".xsb"):
                    if not os.path.isfile(src_f):
                        messagebox.showerror("Error", f"Sound file not found:\n{os.path.basename(src_f)}")
                        return
                    import shutil
                    os.makedirs(os.path.dirname(tgt_f), exist_ok=True)
                    shutil.copy2(src_f, tgt_f)
                    continue

                if auto_lfs and lfs_ok:
                    lfs = src_f + ".lfs"
                    lfs_org = src_f + ".lfs.org"
                    lfs_src = lfs if os.path.isfile(lfs) else (lfs_org if os.path.isfile(lfs_org) else None)
                    if not os.path.isfile(src_f) and lfs_src:
                        subprocess.run([self._re4lfs_path, lfs_src], check=True,
                                       capture_output=True, creationflags=0x08000000)
                    elif force_lfs and lfs_src:
                        if os.path.isfile(src_f):
                            os.rename(src_f, src_f + ".preclone")
                        subprocess.run([self._re4lfs_path, lfs_src], check=True,
                                       capture_output=True, creationflags=0x08000000)

                if not os.path.isfile(src_f):
                    messagebox.showerror("Error", f"Source file not found:\n{os.path.basename(src_f)}")
                    return

                os.makedirs(os.path.dirname(tgt_f), exist_ok=True)
                import shutil
                shutil.copy2(src_f, tgt_f)

                # patch room IDs in file
                src_pat = self._make_pattern(src_room_id)
                tgt_pat = self._make_pattern(tgt_room_id)
                with open(tgt_f, "rb") as f:
                    data = f.read()
                with open(tgt_f, "wb") as f:
                    f.write(data.replace(src_pat, tgt_pat))

                if disable_lfs:
                    lfs_tgt = tgt_f + ".lfs"
                    if os.path.isfile(lfs_tgt):
                        os.rename(lfs_tgt, lfs_tgt + ".org")

            # patch EXE
            off = self._calc_offset(tgt_stage, tgt_val)
            with open(exe, "rb+") as f:
                f.seek(off); f.write(bytes.fromhex(src_id))
            self._update_target_id()
            self._status_var.set(f"Advanced Clone done: r{src_room_id} → r{tgt_room_id}")
        except Exception as e:
            messagebox.showerror("Error During Clone", str(e))

    def _make_pattern(self, room_id_str):
        stage_char   = room_id_str[0]
        room_hex_str = room_id_str[1:]
        stage_byte = int(stage_char).to_bytes(1, "little")
        room_byte  = int(room_hex_str, 16).to_bytes(1, "little")
        return room_byte + stage_byte + b"\x00\x44"

TOOLS_DEF = [
    {"id": "code_manager",    "label": "RE4 CODE MANAGER",  "lock": None},
    {"id": "osd_editor",      "label": "OSD EDITOR",        "lock": ("aev_osd",    "AEV-OSD"), "panel": "osd"},
    {"id": "cns_editor",      "label": "CNS EDITOR",        "lock": None},
    {"id": "snd_editor",      "label": "SND EDITOR",        "lock": None},
    {"id": "aev_editor",      "label": "AEV OPTION EDITOR", "lock": ("aev_option", "AEV OPTION")},
    {"id": "mdt_color_editor","label": "MDT COLOR EDITOR",  "lock": None},
    {"id": "room_init_editor","label": "ROOM INIT EDITOR",  "lock": None, "panel": "room_init"},
    {"id": "avl_editor",      "label": "AVL EDITOR",        "lock": None},
]

_BG    = "#080808"
_NAV   = "#0e0e0e"
_GOLD  = "#c8a035"
_GREEN = "#7cfc7c"
_MUTED = "#4a4a4a"


class RE4MasterEditor(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("RE4 Master Editor")
        self.geometry("1120x730")
        self.minsize(920, 620)
        self.configure(bg=_BG)

        self.exe_path        = tk.StringVar()
        self._panels         = {}
        self._nav_btns       = {}
        self._cm_app         = None
        self._unlocked_codes = set()

        if MASTER_SETTINGS.get("remember_exe", True):
            last = MASTER_SETTINGS.get("last_exe", "")
            if last and os.path.isfile(last):
                self.exe_path.set(last)

        self.exe_path.trace_add("write", self._on_exe_change)
        self._build_ui()
        self._show_welcome()

    def _build_ui(self):
        # top bar
        topbar = tk.Frame(self, bg="#0c0c0c")
        topbar.pack(fill="x")
        tk.Frame(self, bg=_GOLD, height=1).pack(fill="x")

        tk.Label(topbar, text="RE4 ", fg=_GOLD, bg="#0c0c0c",
                 font=("Courier New", 12, "bold")).pack(side="left", padx=(14,0), pady=7)
        tk.Label(topbar, text="MASTER EDITOR", fg="#cccccc", bg="#0c0c0c",
                 font=("Courier New", 12, "bold")).pack(side="left", pady=7)
        tk.Label(topbar, text="  v1.0.0", fg=_MUTED, bg="#0c0c0c",
                 font=("Courier New", 7)).pack(side="left", pady=7)

        tk.Button(topbar, text="Settings",
                  font=("Courier New", 8),
                  fg=_MUTED, bg="#0c0c0c",
                  activeforeground=_GOLD, activebackground="#16110a",
                  relief="flat", bd=0, cursor="hand2",
                  command=self._open_settings
                  ).pack(side="right", padx=(0,10), pady=6)

        pf = tk.Frame(topbar, bg="#0c0c0c")
        pf.pack(side="right", padx=6, pady=5)

        tk.Label(pf, text="bio4.exe:", fg="#555", bg="#0c0c0c",
                 font=("Courier New", 8)).pack(side="left", padx=(0,5))

        self._path_entry = tk.Entry(
            pf, textvariable=self.exe_path,
            font=("Courier New", 8), fg=_GREEN, bg="#0d1a0d",
            insertbackground=_GREEN,
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#2a5a2a",
            width=38
        )
        self._path_entry.pack(side="left", ipady=3)
        self._add_paste_menu(self._path_entry)

        tk.Button(pf, text="Browse",
                  font=("Courier New", 7),
                  fg=_GOLD, bg="#1a1500",
                  activeforeground=_GOLD, activebackground="#2a2000",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground=_GOLD,
                  command=self._browse_exe, padx=6, pady=1
                  ).pack(side="left", padx=4)

        # nav
        navbar = tk.Frame(self, bg=_NAV)
        navbar.pack(fill="x")
        tk.Frame(self, bg="#1a1a1a", height=1).pack(fill="x")

        for tool in TOOLS_DEF:
            tid      = tool["id"]
            lock     = tool.get("lock")
            init_fg  = "#cc2222" if lock else _MUTED
            btn = tk.Button(navbar, text=tool["label"],
                            font=("Courier New", 8, "bold"),
                            fg=init_fg, bg=_NAV,
                            activeforeground=_GOLD,
                            activebackground="#16110a",
                            relief="flat", bd=0,
                            cursor="hand2", padx=12, pady=7,
                            command=lambda t=tid: self._switch_tool(t))
            btn.pack(side="left")
            self._nav_btns[tid] = btn

        tk.Frame(self, bg="#111", height=1).pack(fill="x")

        # content
        self._content = tk.Frame(self, bg="#0b0b0b")
        self._content.pack(fill="both", expand=True)

        self._welcome = WelcomePanel(self._content)
        self._welcome.place(relx=0, rely=0, relwidth=1, relheight=1)

        for tool in TOOLS_DEF:
            tid   = tool["id"]
            label = tool["label"]
            lock  = tool.get("lock")
            if tid == "code_manager":
                panel = CodeManagerPanel(self._content, self)
            elif tid == "cns_editor":
                panel = CNSEditorPanel(self._content, self)
            elif tid == "mdt_color_editor":
                panel = MDTColorPanel(self._content, self)
            elif tid == "aev_editor":
                panel = AEVOptionPanel(self._content, self)
            elif tid == "avl_editor":
                panel = AVLEditorPanel(self._content, self)
            elif tid == "osd_editor":
                panel = OSDEditorPanel(self._content, self)
            elif tid == "room_init_editor":
                panel = RoomInitPanel(self._content, self)
            else:
                panel = ComingSoonPanel(self._content, label)
            panel.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._panels[tid] = panel

        # status bar
        tk.Frame(self, bg="#111", height=1).pack(fill="x")
        sbar = tk.Frame(self, bg="#0d0d0d")
        sbar.pack(fill="x")
        self._status_var = tk.StringVar(value="")
        tk.Label(sbar, textvariable=self._status_var,
                 fg="#444", bg="#0d0d0d",
                 font=("Courier New", 7)).pack(side="left", padx=12, pady=3)
        tk.Label(sbar, text="by YEMENI",
                 fg="#333", bg="#0d0d0d",
                 font=("Courier New", 7)).pack(side="right", padx=12, pady=3)

    def _show_welcome(self):
        for p in self._panels.values():
            p.lower()
        self._welcome.lift()
        for tool in TOOLS_DEF:
            btn  = self._nav_btns.get(tool["id"])
            lock = tool.get("lock")
            if btn:
                is_unlocked = not lock or lock[0] in self._unlocked_codes
                btn.configure(
                    fg=_MUTED if is_unlocked else "#cc2222",
                    bg=_NAV, highlightthickness=0
                )
        self._status_var.set("")

    def _switch_tool(self, tool_id):
        tool_def  = next((t for t in TOOLS_DEF if t["id"] == tool_id), None)
        lock      = tool_def.get("lock") if tool_def else None
        if lock and lock[0] not in self._unlocked_codes:
            messagebox.showwarning(
                "Module Locked" if CURRENT_LANG == "en" else "القسم مقفل",
                f"This module requires [{lock[1]}] to be enabled in RE4 CODE MANAGER."
                if CURRENT_LANG == "en" else
                f"هذا القسم يتطلب تفعيل [{lock[1]}] في RE4 CODE MANAGER."
            )
            return

        self._welcome.lower()
        for tid, panel in self._panels.items():
            panel.lower()
            btn = self._nav_btns.get(tid)
            if btn:
                btn.configure(fg=_MUTED, bg=_NAV, highlightthickness=0)

        panel = self._panels.get(tool_id)
        if panel:
            panel.lift()
            panel.activate()

        btn = self._nav_btns.get(tool_id)
        if btn:
            btn.configure(fg=_GOLD, bg="#16110a",
                           highlightthickness=1, highlightbackground=_GOLD)

        label = next((t["label"] for t in TOOLS_DEF if t["id"] == tool_id), tool_id)
        self._status_var.set(label)

    def _add_paste_menu(self, entry):
        menu = tk.Menu(entry, tearoff=0, bg="#1a1a1a", fg="#ccc",
                       activebackground="#2a2a2a",
                       font=("Courier New", 8))
        menu.add_command(label="Paste", command=lambda: entry.event_generate("<<Paste>>"))
        menu.add_command(label="Copy",  command=lambda: entry.event_generate("<<Copy>>"))
        menu.add_command(label="Select All", command=lambda: entry.select_range(0,"end"))
        entry.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def _browse_exe(self):
        p = filedialog.askopenfilename(
            title="Select bio4.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if p:
            self.exe_path.set(p)

    def _on_exe_change(self, *_):
        path = self.exe_path.get().strip()
        if path and os.path.isfile(path):
            if MASTER_SETTINGS.get("remember_exe", True):
                MASTER_SETTINGS["last_exe"] = path
                save_master_settings(MASTER_SETTINGS)

    def _check_locked_panels(self):
        cm = self._cm_app
        if not cm:
            return
        for tool in TOOLS_DEF:
            lock = tool.get("lock")
            if not lock:
                continue
            code_id = lock[0]
            tid     = tool["id"]
            if cm.applied.get(code_id, False) or cm.detected.get(code_id, False):
                self._unlocked_codes.add(code_id)
            else:
                self._unlocked_codes.discard(code_id)
            btn = self._nav_btns.get(tid)
            if btn:
                btn.configure(fg=_GOLD if code_id in self._unlocked_codes else "#cc2222")

    def _open_settings(self):
        dlg = tk.Toplevel(self)
        dlg.title("Settings")
        dlg.geometry("300x200")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        tk.Label(dlg, text="Settings", fg=_GOLD, bg="#111",
                 font=("Courier New", 11, "bold")).pack(pady=(16,10))
        tk.Frame(dlg, bg="#333", height=1).pack(fill="x", padx=20, pady=4)
        tk.Label(dlg, text="Language", fg="#555", bg="#111",
                 font=("Courier New", 8)).pack()

        lang_var = tk.StringVar(value=MASTER_SETTINGS.get("lang", "en"))
        lf = tk.Frame(dlg, bg="#111")
        lf.pack(pady=4)
        for val, lbl in [("en", "English"), ("ar", "العربية")]:
            tk.Radiobutton(lf, text=lbl, variable=lang_var, value=val,
                           fg="#ccc", bg="#111",
                           activebackground="#111", selectcolor="#1a1a1a",
                           font=("Courier New", 9), relief="flat"
                           ).pack(side="left", padx=12)

        tk.Frame(dlg, bg="#333", height=1).pack(fill="x", padx=20, pady=4)
        rem_var = tk.BooleanVar(value=MASTER_SETTINGS.get("remember_exe", True))
        tk.Checkbutton(dlg, text="Remember last EXE path",
                       variable=rem_var, fg="#ccc", bg="#111",
                       activebackground="#111", selectcolor="#1a1a1a",
                       font=("Courier New", 9), relief="flat",
                       command=lambda: (
                           MASTER_SETTINGS.update({"remember_exe": rem_var.get()}),
                           save_master_settings(MASTER_SETTINGS)
                       )).pack(padx=24, anchor="w", pady=4)

        def apply_lang():
            global CURRENT_LANG
            new_lang = lang_var.get()
            MASTER_SETTINGS["lang"] = new_lang
            APP_SETTINGS["lang"]    = new_lang
            save_master_settings(MASTER_SETTINGS)
            save_settings(APP_SETTINGS)
            CURRENT_LANG = new_lang
            dlg.destroy()
            cm = self._cm_app
            if cm:
                try: cm._reload_ui()
                except Exception: pass
            messagebox.showinfo(
                "Language" if CURRENT_LANG == "en" else "اللغة",
                "Language updated." if CURRENT_LANG == "en" else "تم تحديث اللغة."
            )

        tk.Button(dlg, text="Apply", font=("Courier New", 9),
                  fg=_GREEN, bg="#1a2a0a",
                  activeforeground=_GREEN, activebackground="#2a4a1a",
                  relief="flat", bd=0, cursor="hand2",
                  highlightthickness=1, highlightbackground=_GREEN,
                  command=apply_lang, padx=12, pady=3
                  ).pack(pady=12)


# ═════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = RE4MasterEditor()
    app.mainloop()
