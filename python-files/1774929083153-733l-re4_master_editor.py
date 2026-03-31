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
        panel = self._panels[tab_id]
        panel.lift()
        if hasattr(panel, "activate"):
            panel.activate()
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
        self._built      = False
        self._build()
        self._built      = True

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

        self._char_mode = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_row,
                       text="Select each character",
                       variable=self._char_mode,
                       command=self._on_char_mode_change,
                       fg="#cccccc", bg="#0b0b0b",
                       activebackground="#0b0b0b", selectcolor="#1a1a1a",
                       font=("Courier New", 8), relief="flat"
                       ).pack(side="left", padx=14)

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
        tags_here = self._text.tag_names(idx)
        if "newpage" in tags_here or "noclick" in tags_here:
            return
        if getattr(self, "_char_mode", None) and self._char_mode.get():
            ch = self._text.get(idx)
            if ch and not ch.isspace():
                self._text.tag_add("hover", idx, f"{idx}+1c")
                self._hover_range = (idx, f"{idx}+1c")
        else:
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
        if getattr(self, "_char_mode", None) and self._char_mode.get():
            ch = self._text.get(idx)
            if not ch or ch.isspace() or ch.startswith("{"):
                return
            word  = ch
            start = idx
            end   = f"{idx}+1c"
        else:
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

        # char mode toggle
        char_row = tk.Frame(self, bg="#0b0b0b")
        char_row.pack(fill="x", padx=12, pady=(0,4))
        self._char_mode = tk.BooleanVar(value=False)
        tk.Checkbutton(char_row,
                       text="Select each character",
                       variable=self._char_mode,
                       command=self._on_char_mode_change,
                       fg="#cccccc", bg="#0b0b0b",
                       activebackground="#0b0b0b", selectcolor="#1a1a1a",
                       font=("Courier New", 8), relief="flat"
                       ).pack(side="left")

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
        self._text.tag_configure("aev_boxes",    foreground="#ffffff", font=("Courier New", 7))
        self._text.tag_configure("box_aev_hide", foreground="#ff4444", font=("Courier New", 10))
        self._text.tag_configure("box_aev_show", foreground="#7cfc7c", font=("Courier New", 10))
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
        aev_tag_buffer  = []  # stores tags for current AEV option block
        aev_boxes_drawn = False  # draw boxes only once per block

        while i <= len(tokens):
            m       = tokens[i] if i < len(tokens) else None
            end_pos = m.start() if m else len(raw)

            if end_pos > pos:
                chunk = raw[pos:end_pos]
                if chunk:
                    if len(aev_tag_buffer) > 1:
                        # draw colored squares ONCE above this block
                        if not aev_boxes_drawn:
                            for t in aev_tag_buffer:
                                self._text.insert("end", "■", (f"box_{t}",))
                            self._text.insert("end", "\n")
                            aev_boxes_drawn = True
                        self._text.insert("end", chunk, ("hover_word",))
                    elif len(aev_tag_buffer) == 1:
                        self._text.insert("end", chunk, (aev_tag_buffer[0], "hover_word"))
                    else:
                        tags = (current_aev_tag, "hover_word") if current_aev_tag else ("hover_word",)
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
                # consume ALL consecutive {0xFFXX}/{0xFEXX} tokens
                aev_tag_buffer  = []
                aev_boxes_drawn = False  # reset for new block
                j = i + 1
                while j < len(tokens):
                    nxt_val = tokens[j].group(0).upper().replace(" ", "")[1:-1]
                    try:
                        raw_int = int(nxt_val, 16)
                        hi_byte = (raw_int >> 8) & 0xFF
                        if hi_byte in (0xFF, 0xFE):
                            tag = "aev_hide" if hi_byte == 0xFF else "aev_show"
                            aev_tag_buffer.append(tag)
                            j += 1
                        else:
                            break
                    except Exception:
                        break
                current_aev_tag = aev_tag_buffer[-1] if len(aev_tag_buffer) == 1 else None
                pos = tokens[j-1].end() if j > i+1 else tokens[i].end()
                i   = j
                last_was_0700 = True
                continue
            elif code_val in ("0X0100",):
                if last_was_0700:
                    self._text.insert("end", " " + chr(0x2502), ("separator",))
                self._text.insert("end", "\n" + chr(0x2500)*36 + "\n", ("newpage",))
                current_aev_tag = None
                last_was_0700   = False
                aev_tag_buffer  = []
                aev_boxes_drawn = False
                pos = m.end()
                i  += 1
                continue
            else:
                pass  # unknown token — skip

            pos = m.end()
            i  += 1

        self._text.configure(state="disabled")

    def _on_char_mode_change(self):
        pass

    def _on_hover(self, event):
        self._clear_hover()
        idx       = self._text.index(f"@{event.x},{event.y}")
        tags_here = self._text.tag_names(idx)
        if "newpage" in tags_here or "separator" in tags_here:
            return
        if getattr(self, "_char_mode", None) and self._char_mode.get():
            ch = self._text.get(idx)
            if ch and not ch.isspace():
                self._text.tag_add("hover", idx, f"{idx}+1c")
        else:
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
                    _make_validated_entry(grid, var, mode="hex2",
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


def _make_validated_entry(parent, var, mode="hex2", **kw):
    """
    Validated Entry. Uses vcmd (validatecommand) for instant block.
    mode: hex2 (max FF/2chars), hex4 (max FFFF/4chars),
          dec3 (max 255/3chars), dec5 (max 65535/5chars)
    """
    max_len = {"hex2": 2, "hex4": 4, "dec3": 3, "dec5": 5}.get(mode, 2)
    max_val = {"hex2": 255, "hex4": 65535, "dec3": 255, "dec5": 65535}.get(mode, 255)
    is_hex  = mode.startswith("hex")

    def vcmd_func(P):
        if P == "": return True
        if len(P) > max_len: return False
        try:
            v = int(P, 16 if is_hex else 10)
            return 0 <= v <= max_val
        except ValueError:
            # allow partial hex like "F" mid-typing
            if is_hex and all(c in "0123456789ABCDEFabcdef" for c in P):
                return len(P) <= max_len
            return False

    vcmd = (parent.register(vcmd_func), "%P")
    e = tk.Entry(parent, textvariable=var,
                 validate="key", validatecommand=vcmd, **kw)
    return e
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

    def _add_hex_field(self, grid, bvars, row, label, val, key, mode="hex2"):
        tk.Label(grid, text=f"{label}:",
                 fg="#c8a035", bg="#0b0b0b",
                 font=("Courier New", 8), width=36, anchor="w"
                 ).grid(row=row, column=0, padx=(0,6), pady=3, sticky="w")
        var = tk.StringVar(value=val)
        bvars[key] = var
        e = _make_validated_entry(grid, var, mode=mode,
                 font=("Courier New", 9),
                 fg="#7cfc7c", bg="#0d1a0d", insertbackground="#7cfc7c",
                 relief="flat", bd=0,
                 highlightthickness=1, highlightbackground="#2a5a2a",
                 width=6, justify="center")
        e.grid(row=row, column=1, pady=3)
        tk.Label(grid, text="(hex)", fg="#333", bg="#0b0b0b",
                 font=("Courier New", 7)).grid(row=row, column=2, pady=3, sticky="w", padx=4)

    def _add_dec_field(self, grid, bvars, row, label, val, key, on_change=None, mode="dec3"):
        tk.Label(grid, text=f"{label}:",
                 fg="#c8a035", bg="#0b0b0b",
                 font=("Courier New", 8), width=36, anchor="w"
                 ).grid(row=row, column=0, padx=(0,6), pady=3, sticky="w")
        var = tk.StringVar(value=val)
        bvars[key] = var
        e = _make_validated_entry(grid, var, mode=mode,
                     font=("Courier New", 9),
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
                                  font=("Courier New", 8), fg="#c8a035", bg="#0d0d0d",
                                  relief="flat", bd=0,
                                  highlightthickness=1, highlightbackground="#444",
                                  width=5, justify="center", state="readonly")
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
            _make_validated_entry(row_f, qty_var, mode="dec5",
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
            _make_validated_entry(row_f, sv, mode="hex2",
                     font=("Courier New", 8),
                     fg="#7cfc7c", bg="#0d1a0d", insertbackground="#7cfc7c",
                     relief="flat", bd=0,
                     highlightthickness=1, highlightbackground="#2a5a2a",
                     width=5, justify="center").pack(side="left", ipady=2)
            tk.Label(row_f, text=f"   Fail AEV {i+1} (hex):",
                     fg="#aaa", bg="#0b0b0b",
                     font=("Courier New", 8), width=18, anchor="w").pack(side="left", padx=(16,0))
            fv = tk.StringVar(value=f"{fail[i]:02X}" if i < len(fail) else "FF")
            bvars["fail_aevs"].append(fv)
            _make_validated_entry(row_f, fv, mode="hex2",
                     font=("Courier New", 8),
                     fg="#7cfc7c", bg="#0d1a0d", insertbackground="#7cfc7c",
                     relief="flat", bd=0,
                     highlightthickness=1, highlightbackground="#2a5a2a",
                     width=5, justify="center").pack(side="left", ipady=2)

    def _refresh_dynamic(self, grid, bvars, block):
        # debounce — only rebuild after 400ms of no typing
        if hasattr(self, "_refresh_after"):
            self.after_cancel(self._refresh_after)
        def do_refresh():
            try:
                n = max(0, min(16, int(bvars["n_items_str"].get())))
            except Exception:
                return
            frame = bvars["items_frame"]
            block["items"]      = list(block.get("items", []))
            block["quantities"] = list(block.get("quantities", []))
            self._build_item_fields(frame, bvars, block)
        self._refresh_after = self.after(400, do_refresh)

    def _refresh_sf(self, grid, bvars, block):
        if hasattr(self, "_refresh_sf_after"):
            self.after_cancel(self._refresh_sf_after)
        def do_refresh():
            try:
                n = max(0, min(16, int(bvars["n_sf_str"].get())))
            except Exception:
                return
            frame = bvars["sf_frame"]
            self._build_sf_fields(frame, bvars, block)
        self._refresh_sf_after = self.after(400, do_refresh)

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
        # sync current UI state back to _blocks before adding
        try:
            current = self._collect_blocks()
            self._blocks = current
        except Exception:
            pass
        self._blocks.append({"osd_op": False, "aev_index": 0, "items": [],
                             "quantities": [], "num_sf": 0,
                             "success_aevs": [], "fail_aevs": []})
        self._count_var.set(f"OSD count: {len(self._blocks)}")
        self._render_blocks()
        self._canvas.after(50, lambda: self._canvas.yview_moveto(1.0))

    def _collect_blocks(self):
        """Build block list from current UI vars."""
        blocks = []
        for i, bvars in enumerate(self._block_vars):
            op  = bvars["osd_op"].get()
            aev = int(bvars["aev_index"].get().strip() or "0", 16)
            items, qtys = [], []
            for iv, qv in zip(bvars.get("items",[]), bvars.get("quantities",[])):
                try: items.append(int(iv.get().strip() or "0", 16))
                except: items.append(0)
                try: qtys.append(int(qv.get().strip() or "65535"))
                except: qtys.append(65535)
            suc, fail = [], []
            for sv in bvars.get("suc_aevs", []):
                try: suc.append(int(sv.get().strip() or "FF", 16))
                except: suc.append(0xFF)
            for fv in bvars.get("fail_aevs", []):
                try: fail.append(int(fv.get().strip() or "FF", 16))
                except: fail.append(0xFF)
            nsf = max(len(suc), len(fail))
            suc  = (suc  + [0xFF]*nsf)[:nsf]
            fail = (fail + [0xFF]*nsf)[:nsf]
            blocks.append({"osd_op": op, "aev_index": aev, "items": items,
                           "quantities": qtys, "num_sf": nsf,
                           "success_aevs": suc, "fail_aevs": fail})
        return blocks

    def _save(self):
        path = self._osd_path.get().strip()
        if not path:
            messagebox.showerror("Error", "No OSD file loaded.")
            return
        try:
            blocks = self._collect_blocks()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        try:
            with open(path, "rb") as f:
                raw = bytearray(f.read())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        has_footer = raw[-4:] == bytearray(OSD_FOOTER)
        if has_footer:
            raw = raw[:-4]

        orig_blocks = _osd_parse_file(bytes(raw))

        # build new bytes
        new_bufs = [_osd_block_to_bytes(b) for b in blocks]

        if not orig_blocks:
            # file is all zeros — write from start
            pos = 0
            for nb in new_bufs:
                nsz = len(nb)
                if pos + nsz <= len(raw):
                    raw[pos:pos+nsz] = nb
                else:
                    raw[pos:] = bytearray(nb[:len(raw)-pos])
                    raw += bytearray(nb[len(raw)-pos:])
                pos += nsz
        else:
            size_added = 0
            for i, (nb, orig) in enumerate(zip(new_bufs, orig_blocks)):
                file_off = orig["file_offset"] + size_added
                orig_sz  = orig["file_size"]
                new_sz   = len(nb)
                extra    = new_sz - orig_sz
                if extra <= 0:
                    raw[file_off:file_off+new_sz] = nb
                    if extra < 0:
                        raw[file_off+new_sz:file_off+orig_sz] = bytes(-extra)
                else:
                    after    = bytes(raw[file_off+orig_sz:])
                    tail     = after.rstrip(b'\x00')
                    trailing = len(after) - len(tail)
                    new_after = tail + bytes(trailing - extra) if trailing >= extra else tail
                    raw = bytearray(raw[:file_off]) + bytearray(nb) + bytearray(new_after)
                    size_added += extra
            # append extra new blocks
            if len(new_bufs) > len(orig_blocks):
                last = orig_blocks[-1]
                pos  = last["file_offset"] + last["file_size"] + size_added
                for nb in new_bufs[len(orig_blocks):]:
                    nsz = len(nb)
                    if pos + nsz <= len(raw):
                        raw[pos:pos+nsz] = nb
                    else:
                        fill = max(0, len(raw) - pos)
                        raw[pos:] = bytearray(nb[:fill])
                        raw += bytearray(nb[fill:])
                    pos += nsz

        if self._add_footer.get() or has_footer:
            raw += bytearray(OSD_FOOTER)

        try:
            with open(path, "wb") as f:
                f.write(raw)
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


# ═════════════════════════════════════════════════════════════════════════════
# WEAPONS AND ITEMS EDITOR PANEL
# ═════════════════════════════════════════════════════════════════════════════

class WeaponsItemsPanel(tk.Frame):
    """
    Weapons And Items Editor — embeds Player7z's tool.
    Launches via customtkinter in the same process.
    """

    CREDIT_TEXT = (
        "هذا القسم مستوحى من أداة Player7z\n"
        "أخذت السورس كود ودمجته بالأداة\n\n"
        "لو حاولت تحمل السورس الكود الخاص بالأداة من GitHub\n"
        "لن تجد هذا القسم لأن Player7z ما يبي ينشر السورس للعلن\n\n"
        "شكراً له لأنه أعطاني السورس كود 🙏"
    )

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg="#0b0b0b", **kw)
        self.master_app  = master_app
        self._launched   = False
        self._app_win    = None
        self._built      = False

    def activate(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        # header
        hdr = tk.Frame(self, bg="#0e0e0e")
        hdr.pack(fill="x")
        tk.Label(hdr, text="WEAPONS AND ITEMS EDITOR",
                 fg="#c8a035", bg="#0e0e0e",
                 font=("Courier New", 12, "bold")).pack(side="left", padx=16, pady=10)
        tk.Label(hdr, text="by Player7z",
                 fg="#555", bg="#0e0e0e",
                 font=("Courier New", 8)).pack(side="left", pady=10)
        tk.Frame(self, bg="#c8a035", height=1).pack(fill="x")

        # center frame
        center = tk.Frame(self, bg="#0b0b0b")
        center.place(relx=0.5, rely=0.45, anchor="center")

        self._credit_lbl = tk.Label(center,
                text=self.CREDIT_TEXT if CURRENT_LANG == "ar" else (
                    "This module is based on Player7z\'s tool.\n"
                    "The source code was shared privately —\n"
                    "you won\'t find this section on GitHub\n"
                    "because Player7z chose not to publish it publicly.\n\n"
                    "Special thanks to Player7z 🙏"
                ),
                fg="#888", bg="#0b0b0b",
                font=("Courier New", 9),
                justify="center")
        self._credit_lbl.pack(pady=(0, 24))

        self._start_btn = tk.Button(center,
                text="  Start  ",
                font=("Courier New", 12, "bold"),
                fg="#0a0a0a", bg="#c8a035",
                activeforeground="#0a0a0a", activebackground="#b8902a",
                relief="flat", bd=0, cursor="hand2",
                highlightthickness=0,
                command=self._launch,
                padx=30, pady=10)
        self._start_btn.pack()

    def _launch(self):
        # Hide credit + button
        self._credit_lbl.destroy()
        self._start_btn.destroy()

        exe = self.master_app.exe_path.get().strip()
        orig_exe = os.path.join(MASTER_DIR, "RE4 CODE MANAGER", "the_codes", "bio4_Original.exe")

        # Launch the app embedded in a tk.Toplevel
        try:
            import customtkinter as ctk
            _launch_weapons_editor(exe, orig_exe, parent_master=self.master_app)
        except ImportError:
            messagebox.showerror(
                "customtkinter missing",
                "This module requires customtkinter.\n"
                "Install it with: pip install customtkinter"
            )
            return

        # Show status label
        tk.Label(self, text="Weapons & Items Editor launched in separate window.",
                 fg="#7cfc7c", bg="#0b0b0b",
                 font=("Courier New", 9)).place(relx=0.5, rely=0.5, anchor="center")


def _launch_weapons_editor(exe_path, orig_exe_path, parent_master=None):
    """Launch the embedded Weapons & Items editor in a CTkToplevel window."""
    import customtkinter as ctk
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")
    win = ctk.CTkToplevel()
    win.title("Weapons & Items Editor  —  by Player7z")
    win.geometry("980x920")
    win.resizable(True, True)
    try:
        app_frame = _WeaponsEditorEmbedded(
            win,
            exe_path=exe_path,
            orig_exe_path=orig_exe_path,
            parent_lang=CURRENT_LANG
        )
        app_frame.pack(fill="both", expand=True)
        win.lift()
    except Exception as e:
        import traceback as _tb
        ctk.CTkLabel(win,
                     text=f"Error loading Weapons Editor:\n{e}\n\n{_tb.format_exc()[:300]}",
                     text_color="#ff6060", wraplength=900
                     ).pack(pady=40, padx=20)




# ── Weapons & Items Editor imports (lazy) ──────────────────────────────────
import random as _random
import time   as _time
import webbrowser as _webbrowser
import configparser as _configparser

import customtkinter as ctk

# --- Helper Classes and Functions ---
def hide_console():
    """Hides the console window on Windows."""
    try:
        if sys.platform.startswith('win'): ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception as e: print(f"Error hiding console: {e}")
    
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class ItemSelector(ctk.CTkToplevel):
    def __init__(self, parent, data_to_display, callback, title="Select an Item"):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.callback = callback
        self.data_to_display = data_to_display
        self.parent = parent
        self._center_and_position(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # --- MODIFIED LOGIC ---
        # Removed self.search_var and its trace.
        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search by Name or ID...")
        self.search_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._filter_items) # Bind to key release instead
        
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.item_widgets = []
        self._populate_list()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.search_entry.bind("<MouseWheel>", lambda e, s=self.scroll_frame: self._on_mousewheel(e, s))

    def _on_mousewheel(self, event, scroll_frame):
        scroll_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _center_and_position(self, parent):
        width=400;height=500
        if parent.item_selector_last_pos:x,y=parent.item_selector_last_pos;self.geometry(f"{width}x{height}+{x}+{y}")
        else:parent_x=parent.winfo_x();parent_y=parent.winfo_y();parent_width=parent.winfo_width();parent_height=parent.winfo_height();x=int(parent_x+(parent_width/2)-(width/2));y=int(parent_y+(parent_height/2)-(height/2));self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _on_closing(self):
        self.grab_release()
        self.after(10, self.destroy)
        self.parent.item_selector_last_pos = (self.winfo_x(), self.winfo_y())

    def _populate_list(self):
        row_index = 0
        mousewheel_func = lambda e, s=self.scroll_frame: self._on_mousewheel(e, s)
        for category, items in self.data_to_display["categories"].items():
            header = ctk.CTkLabel(self.scroll_frame, text=category, font=ctk.CTkFont(weight="bold"), anchor="w")
            header.grid(row=row_index, column=0, sticky="ew", padx=5, pady=(10, 2))
            header.bind("<MouseWheel>", mousewheel_func)
            row_index += 1
            category_items = []
            for item_name in items:
                item_label = ctk.CTkLabel(self.scroll_frame, text=item_name, anchor="w", cursor="hand2")
                item_label.grid(row=row_index, column=0, sticky="ew", padx=20, pady=1)
                item_label.bind("<Enter>", lambda e, w=item_label: w.configure(text_color="#847666"))
                item_label.bind("<Leave>", lambda e, w=item_label: w.configure(text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"]))
                item_label.bind("<Button-1>", lambda e, name=item_name: self._select_item(name))
                item_label.bind("<MouseWheel>", mousewheel_func)
                category_items.append(item_label)
                row_index += 1
            self.item_widgets.append({"header": header, "items": category_items})

    def _filter_items(self, event=None):
        query = self.search_entry.get().lower()
        for category_widget in self.item_widgets:
            visible_items_in_category = 0
            for item_label in category_widget["items"]:
                item_name = item_label.cget("text")
                item_id = self.parent.item_name_to_id.get(item_name)
                
                show_item = False
                # Check 1: Name match
                if query in item_name.lower():
                    show_item = True
                # Check 2 & 3: ID match
                elif item_id is not None:
                    if query == str(item_id) or query == hex(item_id)[2:].lower():
                        show_item = True

                if show_item:
                    item_label.grid()
                    visible_items_in_category += 1
                else:
                    item_label.grid_remove()
            
            # Show or hide the category header based on visible items
            if visible_items_in_category > 0:
                category_widget["header"].grid()
            else:
                category_widget["header"].grid_remove()
        self.scroll_frame._parent_canvas.yview_moveto(0)
        
    def _select_item(self,item_name):self.callback(item_name);self._on_closing()

class SacrificeSelector(ctk.CTkToplevel):
    def __init__(self, parent, key_item_name, callback):
        super().__init__(parent)
        self.title("Select an Item to Sacrifice")
        self.transient(parent)
        self.grab_set()
        self.callback = callback
        self.key_item_name = key_item_name
        self.parent = parent
        
        # --- MODIFIED LOGIC: Build a categorized list ---
        sacrificable_set = {
            name for name in parent.all_data["master_item_prices"]
            if name not in parent.treasure_items and name not in parent.key_items
        }
        
        categorized_data = {}
        for category, items in parent.all_data["items"]["categories"].items():
            # Find which items in this category are actually sacrificable
            items_in_category = sorted([item for item in items if item in sacrificable_set])
            if items_in_category:
                # If we found any, add them to our new structure
                categorized_data[category] = items_in_category
        
        self.data_to_display = {"categories": categorized_data}
        # --- END OF MODIFIED LOGIC ---

        self._center_and_position(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        warning_frame = ctk.CTkFrame(self, fg_color="#58181F")
        warning_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        warning_label_header = ctk.CTkLabel(warning_frame, text="⚠️ WARNING: ACTION REQUIRED ⚠️", font=ctk.CTkFont(size=16, weight="bold"), text_color="#F9D423")
        warning_label_header.pack(pady=(10, 5))
        warning_label_text = ctk.CTkLabel(warning_frame, text=f"To sell the Key Item '{self.key_item_name}', you must sacrifice another item's price slot.\n\nThe sacrificed item will become UN-BUYABLE and UN-SELLABLE.\n\nChoose an item from the list below to sacrifice.", justify="center", wraplength=380)
        warning_label_text.pack(pady=(0, 10), padx=10)

        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search by Name or ID...")
        self.search_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._filter_items)
        
        cancel_button = ctk.CTkButton(self, text="Cancel Sacrifice", command=self._on_closing, fg_color=parent.SECONDARY_COLOR, hover_color=parent.SECONDARY_COLOR_HOVER)
        cancel_button.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Select an item to sacrifice its price slot")
        self.scroll_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        self.item_widgets = []
        self._populate_list()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.search_entry.bind("<MouseWheel>", lambda e, s=self.scroll_frame: self._on_mousewheel(e, s))
        
    def _on_mousewheel(self, event, scroll_frame):
        scroll_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _center_and_position(self, parent):
        width=420;height=600
        parent_x=parent.winfo_x();parent_y=parent.winfo_y();parent_width=parent.winfo_width();parent_height=parent.winfo_height();x=int(parent_x+(parent_width/2)-(width/2));y=int(parent_y+(parent_height/2)-(height/2));self.geometry(f"{width}x{height}+{x}+{y}")

    def _on_closing(self):
        self.grab_release()
        self.after(10, self.destroy)
        self.parent.item_selector_last_pos = (self.winfo_x(), self.winfo_y())

    def _select_item(self, sacrificed_item_name):
        self.callback(self.key_item_name, sacrificed_item_name)
        self._on_closing()
    
    def _populate_list(self):
        row_index = 0
        mousewheel_func = lambda e, s=self.scroll_frame: self._on_mousewheel(e, s)
        for category, items in self.data_to_display["categories"].items():
            header = ctk.CTkLabel(self.scroll_frame, text=category, font=ctk.CTkFont(weight="bold"), anchor="w")
            header.grid(row=row_index, column=0, sticky="ew", padx=5, pady=(10, 2))
            header.bind("<MouseWheel>", mousewheel_func)
            row_index += 1
            category_items = []
            for item_name in items:
                item_label = ctk.CTkLabel(self.scroll_frame, text=item_name, anchor="w", cursor="hand2")
                item_label.grid(row=row_index, column=0, sticky="ew", padx=20, pady=1)
                item_label.bind("<Enter>", lambda e, w=item_label: w.configure(text_color="#847666"))
                item_label.bind("<Leave>", lambda e, w=item_label: w.configure(text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"]))
                item_label.bind("<Button-1>", lambda e, name=item_name: self._select_item(name))
                item_label.bind("<MouseWheel>", mousewheel_func)
                category_items.append(item_label)
                row_index += 1
            self.item_widgets.append({"header": header, "items": category_items})
            
    def _filter_items(self, event=None):
        query = self.search_entry.get().lower()
        for category_widget in self.item_widgets:
            visible_items_in_category = 0
            for item_label in category_widget["items"]:
                item_name = item_label.cget("text")
                item_id = self.parent.item_name_to_id.get(item_name)
                
                show_item = False
                if query in item_name.lower():
                    show_item = True
                elif item_id is not None:
                    if query == str(item_id) or query == hex(item_id)[2:].lower():
                        show_item = True

                if show_item:
                    item_label.grid()
                    visible_items_in_category += 1
                else:
                    item_label.grid_remove()
            
            if visible_items_in_category > 0:
                category_widget["header"].grid()
            else:
                category_widget["header"].grid_remove()
        self.scroll_frame._parent_canvas.yview_moveto(0)

class _WeaponsEditorEmbedded(ctk.CTkFrame):
    APP_VERSION = "v0.7.8.5E (Final)"
    CHANNEL_URL = "https://www.youtube.com/@Player-7z"
    FIRING_SPEED_MULTIPLIER = 0.03333 
    RELOAD_SPEED_MULTIPLIER = 0.03333 
    FIRING_SPEED_PRESETS = sorted(["2.43", "1.83", "1.53", "1.33", "1.17", "1.10", "0.70", "0.67", "0.53", "0.47", "0.40", "0.34", "0.31", "0.28", "0.24", "0.21", "0.17", "0.14", "0.10", "0.07", "0.03"], key=float)
    RELOAD_SPEED_PRESETS = ["0.83", "0.87", "0.93", "1.17", "1.33", "1.47", "1.53", "1.63", "1.67", "1.70", "1.73", "1.90", "1.93", "2.00", "2.20", "2.30", "2.33", "2.37", "2.40", "2.43", "2.57", "2.83", "2.87", "3.00", "3.03", "3.23", "3.43", "3.67", "4.00"]

    def __init__(self, parent, exe_path='', orig_exe_path='', parent_lang='en'):
        super().__init__(parent, fg_color='#1a1a1a')
        self._master_exe = exe_path; self._orig_exe = orig_exe_path; self._parent_lang = parent_lang
        # title was: (f"Ultimate Items & Weapons & Merchant Tool {self.APP_VERSION} By Player7z 'to revive the community' "); 
        
        
        self.THEME_COLOR="#847666"; self.SECONDARY_COLOR="#4A4A4A"; self.THEME_COLOR_HOVER="#63584c"; self.SECONDARY_COLOR_HOVER="#555555"; self.EXCLUSIVE_COLOR = "#FFD700"
        self.SACRIFICE_COLOR = "#E06C75"

        # --- NEW: Define colors for entry widgets ---
        self.DEFAULT_ENTRY_COLOR = ctk.CTkEntry(self).cget("fg_color")
        self.DISABLED_COLOR = "#3D3D3D"
        self.DISABLED_TEXT_COLOR = "#A9A9A9" # Add this line
        
        ctk.set_default_color_theme("dark-blue")
        
        # Core variables
        self.exe_path = self._master_exe
        self.backup_path = self._orig_exe
        self.active_backup_path = self._orig_exe
        self.all_data={}; self.item_id_to_name={}; self.item_name_to_id={}; self.weapon_name_to_id={"None":0}; self.weapon_id_to_name={0:"None"};
        
        # Tab System variables
        self.tabs = {}; self.tab_buttons = {}; self.current_tab_name = None
        self.tab_build_functions = {}

        # Feature specific variables
        self.stock_widgets_data=[]; self.treasure_items = set(); self.key_items = set(); self.pending_sacrifices = {}
        self.price_editor_widgets = {}; self.header_widgets = {}; self.sorted_price_item_list = []; self.sorted_list_ammo_grouped = []; self.sorted_list_ammo_categorized = []
        self.base_prices = {}; self.weapon_ammo_map = {}; self.ammo_weapon_map = {}
        self.stacking_offsets = {}; self.stacking_groups = {}; self.stacking_group_map = {}; self.stackable_items_set = set()
        self.upgrade_price_widgets = {}; self.item_type_widgets = {}; self.original_item_types = {}; self.item_type_map = {}; self.item_type_reverse_map = {}
        self.item_size_offsets = {}; self.item_size_widgets = {}; self.original_item_sizes = {}; self.sorted_sizable_items = []
        self.combination_data = {}; self.combination_widgets = []; self.all_items_categorized = {}
        self.starter_items_widgets = {}
        self.shooting_range_widgets = []
        self.money_health_widgets = {}
        
        # State variables
        self.price_editor_loaded = False; self.is_updating_prices = False; self.is_updating_stacking = False;
        self.is_updating_exclusive_fp = False; self.exclusive_fp_base_entry = None; self.exclusive_fp_ingame_entry = None; self.cap_lvl7_entry = None;
        self.upgrade_editor_loaded = False; self.item_type_editor_loaded = False; self.item_size_editor_loaded = False;
        self.combinations_editor_loaded = False; self.new_game_editor_loaded = False; self.shooting_range_editor_loaded = False; self.money_health_editor_loaded = False; self.is_loading_new_game_data = False
        self.sell_price_mode = "full"; self.ammo_sort_is_grouped = True
        self.item_selector_last_pos=None; self.last_selected_weapon = "-"; self.last_selected_upgrade_weapon = "-"
        self.is_updating_fs = False; self.is_updating_rs = False
        self.merchant_display_to_key = {}; self.default_status_color = None
        self.current_scroll_frame = None

        self.tab_build_functions = {
            "Items Prices-Stacking": {'build_func': self._build_price_editor_once, 'loaded_flag': lambda: self.price_editor_loaded},
            "Upgrades Prices Editor": {'build_func': self._build_upgrade_editor_once, 'loaded_flag': lambda: self.upgrade_editor_loaded},
            "Item Type Editor": {'build_func': self._build_item_type_editor_once, 'loaded_flag': lambda: self.item_type_editor_loaded},
            "Item Size Editor": {'build_func': self._build_item_size_editor_once, 'loaded_flag': lambda: self.item_size_editor_loaded},
            "Item Combinations Editor": {'build_func': self._build_item_combinations_editor_once, 'loaded_flag': lambda: self.combinations_editor_loaded},
            "Starter Inventories": {'build_func': self._build_new_game_editor_once, 'loaded_flag': lambda: self.new_game_editor_loaded},
            "Shooting Range Items": {'build_func': self._build_shooting_range_editor_once, 'loaded_flag': lambda: self.shooting_range_editor_loaded},
            "Starter Money-Health": {'build_func': self._build_money_health_editor_once, 'loaded_flag': lambda: self.money_health_editor_loaded}
        }

        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(2, weight=1)
        self.create_widgets()
        self.load_all_data(initial_load=True)
        if not hasattr(self, 'create_menu'): pass
        else: self.create_menu()
        if self._master_exe and os.path.isfile(self._master_exe):
            self.after(200, lambda: self._auto_load_exe())
      
    def _check_for_first_launch(self):
        """Checks for first launch of this version and shows the 'About' dialog."""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)) if hasattr(__file__, '__file__') else '.', 'config.ini')
        config = _configparser.ConfigParser()
        
        last_run_version = None
        if os.path.exists(config_path):
            try:
                config.read(config_path)
                if 'User' in config and 'last_run_version' in config['User']:
                    last_run_version = config['User']['last_run_version']
            except _configparser.Error:
                # Config file is corrupt, treat as first launch
                pass

        if last_run_version != self.APP_VERSION:
            # Show the 'About' dialog as a welcome/update message
            self.show_about_dialog(is_first_launch=True)
            
            # Update the config file with the current version
            try:
                if 'User' not in config:
                    config['User'] = {}
                config['User']['last_run_version'] = self.APP_VERSION
                with open(config_path, 'w') as configfile:
                    config.write(configfile)
            except IOError:
                # If we can't write the file (e.g., permissions issue), it's not critical.
                # The user will just see the pop-up again next _time.
                pass
    
    def _open_channel_link(self):
        """Opens the predefined channel URL in a new browser tab."""
        try:
            _webbrowser.open_new_tab(self.CHANNEL_URL)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open link: {e}")
        
    def _show_success_message(self, message, callback=None):
        """Shows a temporary green success message. After a delay, it executes an optional callback."""
        self.status_bar.configure(text=message, text_color="#76B947")
        self.after(3000, self._handle_success_fade, callback)

    def _handle_success_fade(self, callback):
        """Resets the status bar color and then runs the callback if it exists."""
        self.status_bar.configure(text_color=self.default_status_color)
        if callback:
            callback()
        else:
            self._update_stable_status()
        
    def _update_stable_status(self):
        """Sets the status bar to the correct 'stable' message for the current tab."""
        if not self.exe_path and self.current_tab_name not in ["Randomizer", "Mod Analyzer"]:
            self.status_bar.configure(text="Ready. Select an executable to begin.")
            return

        tab_messages = {
            "Weapon Stat Editor": f"Ready. Current Weapon: {self.last_selected_weapon}",
            "Upgrades Prices Editor": f"Ready. Current Weapon: {self.last_selected_upgrade_weapon}",
            "Merchant Stock Editor": f"Ready. Current Merchant: {self.merchant_menu.get()}",
            "Items Prices-Stacking": "Item prices and stacking data is loaded.",
            "Item Type Editor": "Item type data is loaded.",
            "Item Size Editor": "Item size data is loaded.",
            "Item Combinations Editor": "Item combination data is loaded.",
            "Starter Inventories": "Starter inventory data is loaded.",
            "Shooting Range Items": "Shooting range item data is loaded.",
            "Starter Money-Health": "Starter money and health data is loaded.",
            "Randomizer": "Ready to randomize.",
            "Mod Analyzer": "Ready to analyze."
        }
        
        message = tab_messages.get(self.current_tab_name, "Ready.")
        self.status_bar.configure(text=message)
    
    def _update_exclusive_fp_prices(self, source_widget):
        if self.is_updating_exclusive_fp: return
        # Check if all required widgets have been created
        if not all([self.exclusive_fp_base_entry, self.exclusive_fp_ingame_entry, self.upgrade_price_widgets.get('fs'), self.cap_lvl7_entry]):
            return
        
        self.is_updating_exclusive_fp = True
        try:
            # Get prices from both padding slots, defaulting to 0 if empty
            fs7_price = int(self.upgrade_price_widgets['fs'][-1].get() or 0)
            cap7_price = int(self.cap_lvl7_entry.get() or 0)

            # --- THIS IS THE FIX: Revert to simple addition of BOTH values ---
            total_padding_price = fs7_price + cap7_price
            # --- END OF FIX ---

            if source_widget == self.exclusive_fp_ingame_entry:
                in_game_price = int(self.exclusive_fp_ingame_entry.get() or 0)
                # Reverse calculation is now correct again
                new_base_price = in_game_price - total_padding_price
                self.exclusive_fp_base_entry.delete(0, "end")
                self.exclusive_fp_base_entry.insert(0, str(new_base_price))
            else: # Source is the base entry or one of the padding entries
                base_price = int(self.exclusive_fp_base_entry.get() or 0)
                # Forward calculation is now correct again
                new_in_game_price = base_price + total_padding_price
                self.exclusive_fp_ingame_entry.delete(0, "end")
                self.exclusive_fp_ingame_entry.insert(0, str(new_in_game_price))
        except (ValueError, IndexError):
            pass 
        finally:
            self.is_updating_exclusive_fp = False
            
    def _on_fs7_price_change(self, event=None):
        # When the FS Lvl 7 price changes, we need to recalculate the In-Game Exclusive price
        if self.exclusive_fp_base_entry:
            self._update_exclusive_fp_prices(source_widget=self.exclusive_fp_base_entry)

    # --- THIS IS THE MISSING FUNCTION ---
    def _on_cap7_price_change(self, event=None):
        # This function is identical to the fs7 version, just for a different widget
        if self.exclusive_fp_base_entry:
            self._update_exclusive_fp_prices(source_widget=self.exclusive_fp_base_entry)
    # --- END OF MISSING FUNCTION ---
    
    def _on_fs7_price_change(self, event=None):
        # When the FS Lvl 7 price changes, we need to recalculate the In-Game Exclusive price
        if self.exclusive_fp_base_entry:
            self._update_exclusive_fp_prices(source_widget=self.exclusive_fp_base_entry)
    
    # --- START OF MOD ANALYZER SECTION ---
    def _create_analyzer_tab(self, parent_frame):
        analyzer_tab = parent_frame
        analyzer_tab.grid_columnconfigure(0, weight=1)
        analyzer_tab.grid_rowconfigure(2, weight=1)

        file_frame = ctk.CTkFrame(analyzer_tab)
        file_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(file_frame, text="Modified EXE:").grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
        self.analyzer_mod_exe_entry = ctk.CTkEntry(file_frame, placeholder_text="Select the modded .exe to analyze...")
        self.analyzer_mod_exe_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        mod_browse_button = ctk.CTkButton(file_frame, text="Browse...", width=100, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda: self._analyzer_browse_file(self.analyzer_mod_exe_entry))
        mod_browse_button.grid(row=0, column=2, padx=(5,10), pady=5)

        ctk.CTkLabel(file_frame, text="Base EXE:").grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
        self.analyzer_base_exe_entry = ctk.CTkEntry(file_frame, placeholder_text="Select the original .exe to compare against...")
        self.analyzer_base_exe_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        base_browse_button = ctk.CTkButton(file_frame, text="Browse...", width=100, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda: self._analyzer_browse_file(self.analyzer_base_exe_entry))
        base_browse_button.grid(row=1, column=2, padx=(5,10), pady=5)

        action_frame = ctk.CTkFrame(analyzer_tab)
        action_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)
        self.analyzer_generate_button = ctk.CTkButton(action_frame, text="Generate Report", font=ctk.CTkFont(size=14, weight="bold"), fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=self._analyzer_generate_report)
        self.analyzer_generate_button.grid(row=0, column=0, padx=10, pady=10, ipady=5, sticky="ew")
        
        results_frame = ctk.CTkFrame(analyzer_tab)
        results_frame.grid(row=2, column=0, padx=10, pady=(5,10), sticky="nsew")
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)
        
        self.analyzer_results_textbox = ctk.CTkTextbox(results_frame, wrap="word", font=ctk.CTkFont(family="Consolas", size=12))
        self.analyzer_results_textbox.grid(row=0, column=0, columnspan=2, padx=10, pady=(10,5), sticky="nsew")
        self.analyzer_results_textbox.insert("0.0", "Select the files to compare and click 'Generate Report'.\n\nThe base EXE should be an original, unmodified executable or a .bakp file.")

        copy_button = ctk.CTkButton(results_frame, text="Copy Report to Clipboard", fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER, command=self._analyzer_copy_to_clipboard)
        copy_button.grid(row=1, column=0, padx=10, pady=(5,10), sticky="ew")
        
    def _analyzer_browse_file(self, entry_widget):
        filepath = filedialog.askopenfilename(title="Select Resident Evil 4 EXE", filetypes=(("Executable files", "*.exe"),("Backup files", "*.bakp"),("All files", "*.*")))
        if filepath:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filepath)
    
    def _analyzer_copy_to_clipboard(self):
        report_text = self.analyzer_results_textbox.get("1.0", "end-1c")
        if report_text and "Select the files to compare" not in report_text:
            self.clipboard_clear()
            self.clipboard_append(report_text)
            self._show_success_message("Report copied to clipboard!")
            
    def _analyzer_generate_report(self):
        mod_path = self.analyzer_mod_exe_entry.get()
        base_path = self.analyzer_base_exe_entry.get()

        if not mod_path or not base_path: messagebox.showerror("Error", "Please select both a modified and a base EXE file."); return
        if not os.path.exists(mod_path) or not os.path.exists(base_path): messagebox.showerror("Error", "One or both selected files do not exist."); return
        if mod_path == base_path: messagebox.showerror("Error", "The modified and base files cannot be the same."); return
            
        self.analyzer_results_textbox.delete("1.0", "end"); self.analyzer_results_textbox.insert("1.0", "Generating report, please wait..."); self.update_idletasks()

        try:
            report_lines = []
            with open(mod_path, 'rb') as f_mod, open(base_path, 'rb') as f_base:
                changes = self._analyzer_compare_weapon_stats(f_mod, f_base); report_lines.extend(["[Weapon Stats]"] + changes) if changes else None
                changes = self._analyzer_compare_upgrade_prices(f_mod, f_base); report_lines.extend(["\n[Upgrade Prices]"] + changes) if changes else None
                changes = self._analyzer_compare_master_prices(f_mod, f_base); report_lines.extend(["\n[Items Prices-Stacking]"] + changes) if changes else None
                changes = self._analyzer_compare_item_types(f_mod, f_base); report_lines.extend(["\n[Item Types]"] + changes) if changes else None
                changes = self._analyzer_compare_item_sizes(f_mod, f_base); report_lines.extend(["\n[Item Sizes]"] + changes) if changes else None
                changes = self._analyzer_compare_item_combinations(f_mod, f_base); report_lines.extend(["\n[Item Combinations]"] + changes) if changes else None
                changes = self._analyzer_compare_merchant_stock(f_mod, f_base); report_lines.extend(["\n[Merchant Stock]"] + changes) if changes else None
                changes = self._analyzer_compare_money_health(f_mod, f_base)
                if changes:
                    report_lines.extend(["\n[Starter Money & Health]"] + changes)
                
                changes = self._analyzer_compare_shooting_range(f_mod, f_base)
                if changes:
                    report_lines.extend(["\n[Shooting Range Items]"] + changes)

                changes = self._analyzer_compare_new_game_data(f_mod, f_base)
                if changes:
                    report_lines.extend(["\n[Starter Inventories]"] + changes)

            self.analyzer_results_textbox.delete("1.0", "end")
            if report_lines:
                header = f"--- Mod Analysis Report ---\nModified: {os.path.basename(mod_path)}\nBase:     {os.path.basename(base_path)}\n\n"
                self.analyzer_results_textbox.insert("1.0", header + "\n".join(report_lines).strip() + "\n\n--- End of Report ---")
            else:
                self.analyzer_results_textbox.insert("1.0", "No differences found between the selected files for the data this tool can analyze.")
        except Exception as e:
            self.analyzer_results_textbox.delete("1.0", "end"); self.analyzer_results_textbox.insert("1.0", f"An error occurred while generating the report:\n\n{e}")
            
    def _analyzer_compare_weapon_stats(self, f_mod, f_base):
        report_data = []
        for weapon_name, weapon_data in self.all_data["weapons"].items():
            if "---" in weapon_name: continue
            for stat_key, label, levels, dtype, size in [("firepower_base_offset", "Firepower", 7, 'f', 4), ("reload_speed_base_offset", "Reload Speed", 3, 'f', 4)]:
                if stat_key in weapon_data:
                    base_offset = int(weapon_data[stat_key], 16)
                    for i in range(levels):
                        offset = base_offset + (i * size)
                        f_mod.seek(offset); f_base.seek(offset)
                        mod_val, base_val = struct.unpack(f'<{dtype}', f_mod.read(size))[0], struct.unpack(f'<{dtype}', f_base.read(size))[0]
                        if abs(mod_val - base_val) > 1e-6:
                            report_data.append((f"{weapon_name} - {label} Lvl {i+1}", f"{base_val:.1f}", f"{mod_val:.1f}"))
            if "capacity_base_offset" in weapon_data:
                base_offset = int(weapon_data["capacity_base_offset"], 16)
                
                # --- START OF NEW CODE ---
                # This block checks the weapon's accessory (e.g., Silencer)
                accessory_offset = base_offset + 4
                f_mod.seek(accessory_offset)
                mod_accessory_val, = struct.unpack('<H', f_mod.read(2))
                f_base.seek(accessory_offset)
                base_accessory_val, = struct.unpack('<H', f_base.read(2))
                if mod_accessory_val != base_accessory_val:
                    mod_accessory_name = "Silencer/Scoope" if mod_accessory_val == 0x0101 else "Normal"
                    base_accessory_name = "Silencer/Scoope" if base_accessory_val == 0x0101 else "Normal"
                    report_data.append((f"{weapon_name} - Accessory", f'"{base_accessory_name}"', f'"{mod_accessory_name}"'))
                # --- END OF NEW CODE ---
                
                # --- EXISTING BLOCK TO CHECK AMMO TYPE ---
                ammo_offset = base_offset + 6
                f_mod.seek(ammo_offset); f_base.seek(ammo_offset)
                mod_ammo_id, base_ammo_id = struct.unpack('<H', f_mod.read(2))[0], struct.unpack('<H', f_base.read(2))[0]
                if mod_ammo_id != base_ammo_id:
                    mod_ammo_name = self.item_id_to_name.get(mod_ammo_id, f"ID:{hex(mod_ammo_id)}")
                    base_ammo_name = self.item_id_to_name.get(base_ammo_id, f"ID:{hex(base_ammo_id)}")
                    report_data.append((f"{weapon_name} - Ammo Type", f'"{base_ammo_name}"', f'"{mod_ammo_name}"'))
                # --- END OF EXISTING BLOCK ---

                capacity_start_offset = base_offset + 8
                for i in range(7):
                    offset = capacity_start_offset + (i * 2)
                    f_mod.seek(offset); f_base.seek(offset)
                    mod_val, base_val = struct.unpack('<h', f_mod.read(2))[0], struct.unpack('<h', f_base.read(2))[0]
                    if mod_val != base_val:
                        report_data.append((f"{weapon_name} - Capacity Lvl {i+1}", f"{base_val}", f"{mod_val}"))

            if "firing_speed_offsets" in weapon_data:
                base_offset = int(weapon_data["firing_speed_offsets"][0], 16)
                for i in range(5):
                    offset = base_offset + (i * 4)
                    f_mod.seek(offset); f_base.seek(offset)
                    mod_val, base_val = struct.unpack('<f', f_mod.read(4))[0], struct.unpack('<f', f_base.read(4))[0]
                    if abs(mod_val - base_val) > 1e-6:
                        mod_sec, base_sec = mod_val * self.FIRING_SPEED_MULTIPLIER, base_val * self.FIRING_SPEED_MULTIPLIER
                        report_data.append((f"{weapon_name} - Firing Speed Lvl {i+1}", f"{base_sec:.2f}s", f"{mod_sec:.2f}s"))
            if "max_levels_offsets" in weapon_data:
                offset = int(weapon_data["max_levels_offsets"][0], 16)
                if weapon_name == "Matilda": offset += 2
                f_mod.seek(offset); f_base.seek(offset)
                mod_lvls, base_lvls = struct.unpack('<BBBB', f_mod.read(4)), struct.unpack('<BBBB', f_base.read(4))
                if mod_lvls != base_lvls:
                    report_data.append((f"{weapon_name} - Max Levels (FP,FS,RS,Cap)", f"{base_lvls}", f"{mod_lvls}"))
        
        if not report_data: return []
        max_len = max(len(item[0]) for item in report_data)
        return [f"- {label:<{max_len}}: {old_val} -> {new_val}" for label, old_val, new_val in report_data]
        
    def _analyzer_compare_upgrade_prices(self, f_mod, f_base):
        report_data = []
        for weapon_name, offset_str in self.all_data["upgrade_prices"].items():
            offset = int(offset_str, 16) + 2
            f_mod.seek(offset); f_base.seek(offset)
            mod_bytes, base_bytes = f_mod.read(40), f_base.read(40)
            if mod_bytes != base_bytes:
                mod_prices, base_prices = struct.unpack('<20H', mod_bytes), struct.unpack('<20H', base_bytes)
                labels = (["Firepower"]*6) + (["Firing Speed"]*2) + (["Reload Speed"]*2) + (["Capacity"]*6) + (["UNUSED"]*4)
                for i in range(16):
                    if mod_prices[i] != base_prices[i]:
                        report_data.append((f"{weapon_name} - {labels[i]} Upgrade", f"{base_prices[i]*10}", f"{mod_prices[i]*10}"))
        
        if not report_data: return []
        max_len = max(len(item[0]) for item in report_data)
        return [f"- {label:<{max_len}}: {old_val} -> {new_val}" for label, old_val, new_val in report_data]
        
    def _analyzer_compare_master_prices(self, f_mod, f_base):
        report_data = []
        for item_name, offsets in self.all_data["master_item_prices"].items():
            if offsets:
                offset = int(offsets[0], 16)
                # Check Price
                f_mod.seek(offset + 2); f_base.seek(offset + 2)
                mod_price, base_price = struct.unpack('<H', f_mod.read(2))[0]*10, struct.unpack('<H', f_base.read(2))[0]*10
                if mod_price != base_price:
                    report_data.append((f"{item_name} (Price)", f"{base_price}", f"{mod_price}"))
                
                # --- NEW: Check Purchase Quantity ---
                f_mod.seek(offset + 4); f_base.seek(offset + 4)
                mod_pq, base_pq = struct.unpack('<H', f_mod.read(2))[0], struct.unpack('<H', f_base.read(2))[0]
                if mod_pq != base_pq:
                    report_data.append((f"{item_name} (Purchase Qty)", f"{base_pq}", f"{mod_pq}"))

        for item_name, offset in self.stacking_offsets.items():
            f_mod.seek(offset); f_base.seek(offset)
            mod_stack, base_stack = struct.unpack('<h', f_mod.read(2))[0], struct.unpack('<h', f_base.read(2))[0]
            if mod_stack != base_stack:
                report_data.append((f"{item_name} (Stack)", f"{base_stack}", f"{mod_stack}"))
                
        if not report_data: return []
        max_len = max(len(item[0]) for item in report_data)
        return [f"- {label:<{max_len}}: {old_val} -> {new_val}" for label, old_val, new_val in report_data]
        
    def _analyzer_compare_item_types(self, f_mod, f_base):
        report_data = []
        base_offset = self.item_type_base_offset
        max_id = max(self.item_name_to_id.values())
        f_mod.seek(base_offset); f_base.seek(base_offset)
        mod_types, base_types = f_mod.read(max_id + 1), f_base.read(max_id + 1)
        for item_name, item_id in self.item_name_to_id.items():
            if item_id <= max_id and mod_types[item_id] != base_types[item_id]:
                mod_type_name = self.item_type_map.get(mod_types[item_id], f"Unknown ({hex(mod_types[item_id])})")
                base_type_name = self.item_type_map.get(base_types[item_id], f"Unknown ({hex(base_types[item_id])})")
                report_data.append((item_name, f'"{base_type_name}"', f'"{mod_type_name}"'))
                
        if not report_data: return []
        max_len = max(len(item[0]) for item in report_data)
        return [f'- {label:<{max_len}}: {old_val} -> {new_val}' for label, old_val, new_val in report_data]
       
    def _analyzer_compare_item_sizes(self, f_mod, f_base):
        report_data = []
        for item_name, offset_str in self.item_size_offsets.items():
            offset = int(offset_str, 16)
            f_mod.seek(offset); f_base.seek(offset)
            mod_bytes, base_bytes = f_mod.read(16), f_base.read(16)
            if mod_bytes != base_bytes:
                try:
                    _, mod_w, mod_h, _, _ = struct.unpack('<I B B 2x f f', mod_bytes)
                    _, base_w, base_h, _, _ = struct.unpack('<I B B 2x f f', base_bytes)
                    report_data.append((item_name, f"{base_w}x{base_h}", f"{mod_w}x{mod_h}"))
                except struct.error:
                    report_data.append((item_name, "Data mismatch", "(could not unpack)"))
                    
        if not report_data: return []
        max_len = max(len(item[0]) for item in report_data)
        return [f"- {label:<{max_len}}: {old_val} -> {new_val}" for label, old_val, new_val in report_data]
        
    def _analyzer_compare_item_combinations(self, f_mod, f_base):
        report_data = []
        count_offset = int(self.combination_data["counter_offsets"][0], 16)
        list_offset = int(self.combination_data["list_base_offset"], 16)
        
        f_mod.seek(count_offset); mod_count = struct.unpack('<B', f_mod.read(1))[0]
        f_base.seek(count_offset); base_count = struct.unpack('<B', f_base.read(1))[0]

        if mod_count != base_count:
            report_data.append(("Total Combinations", f"{base_count}", f"{mod_count}"))

        max_count = max(mod_count, base_count)
        for i in range(max_count):
            f_mod.seek(list_offset + i * 6); mod_bytes = f_mod.read(6)
            f_base.seek(list_offset + i * 6); base_bytes = f_base.read(6)
            if mod_bytes != base_bytes:
                a1, b1, r1 = struct.unpack('<HHH', base_bytes)
                a2, b2, r2 = struct.unpack('<HHH', mod_bytes)
                
                name_a1, name_b1, name_r1 = self.item_id_to_name.get(a1, f"ID:{hex(a1)}"), self.item_id_to_name.get(b1, f"ID:{hex(b1)}"), self.item_id_to_name.get(r1, f"ID:{hex(r1)}")
                name_a2, name_b2, name_r2 = self.item_id_to_name.get(a2, f"ID:{hex(a2)}"), self.item_id_to_name.get(b2, f"ID:{hex(b2)}"), self.item_id_to_name.get(r2, f"ID:{hex(r2)}")
                
                base_str = f'"{name_a1}" + "{name_b1}" -> "{name_r1}"'
                mod_str = f'"{name_a2}" + "{name_b2}" -> "{name_r2}"'
                
                if i < base_count and i < mod_count: # A change
                    report_data.append((f"Slot {i+1}", base_str, mod_str))
                elif i >= base_count: # An addition
                    report_data.append((f"Added Slot {i+1}", mod_str))
                elif i >= mod_count: # A deletion
                    report_data.append((f"Removed Slot {i+1}", base_str))

        if not report_data: return []
        max_len = max(len(item[0]) for item in report_data)
        changes = []
        for item in report_data:
            if len(item) == 3:
                label, old_val, new_val = item
                changes.append(f"- {label:<{max_len}}: {old_val} -> {new_val}")
            else:
                label, val = item
                changes.append(f"- {label:<{max_len}}: {val}")
        return changes
        
    def _analyzer_compare_new_game_data(self, f_mod, f_base):
        changes = []
        try:
            starter_data = self.all_data["game_mode_starters"]
        except KeyError:
            return ["- Starter Inventories data structure not found in re4_data.json"]

        for mode_name, slots in starter_data.items():
            if not isinstance(slots, list): continue
            
            mode_report_lines = []
            all_labels_for_mode = []

            if mode_name == "Story Mode" and starter_data.get("difficulty_flag_offset"):
                all_labels_for_mode.append("Force Easy Inventory")
            for slot_info in slots:
                all_labels_for_mode.append(f'{slot_info["name"]} (Item)')
                if slot_info.get("qty_offset"):
                    all_labels_for_mode.append(f'{slot_info["name"]} (Qty)')
            
            max_label_length = max(len(label) for label in all_labels_for_mode) if all_labels_for_mode else 0

            if mode_name == "Story Mode":
                flag_offset_str = starter_data.get("difficulty_flag_offset")
                if flag_offset_str:
                    offset = int(flag_offset_str, 16)
                    f_mod.seek(offset); mod_flag = struct.unpack('<B', f_mod.read(1))[0]
                    f_base.seek(offset); base_flag = struct.unpack('<B', f_base.read(1))[0]
                    if mod_flag != base_flag:
                        mod_status = "Enabled" if mod_flag == 0x06 else "Disabled"
                        base_status = "Enabled" if base_flag == 0x06 else "Disabled"
                        label = "Force Easy Inventory"
                        mode_report_lines.append(f"- {label:<{max_label_length}}: {base_status} -> {mod_status}")

            for slot_info in slots:
                id_offset = int(slot_info["id_offset"], 16)
                f_mod.seek(id_offset); mod_id = struct.unpack('<B', f_mod.read(1))[0]
                f_base.seek(id_offset); base_id = struct.unpack('<B', f_base.read(1))[0]
                if mod_id != base_id:
                    mod_item_name = self.item_id_to_name.get(mod_id, f"ID:{hex(mod_id)}")
                    base_item_name = self.item_id_to_name.get(base_id, f"ID:{hex(base_id)}")
                    label = f'{slot_info["name"]} (Item)'
                    mode_report_lines.append(f'- {label:<{max_label_length}}: "{base_item_name}" -> "{mod_item_name}"')

                if slot_info.get("qty_offset"):
                    qty_offset = int(slot_info["qty_offset"], 16)
                    f_mod.seek(qty_offset); mod_qty = struct.unpack('<B', f_mod.read(1))[0]
                    f_base.seek(qty_offset); base_qty = struct.unpack('<B', f_base.read(1))[0]
                    if mod_qty != base_qty:
                        label = f'{slot_info["name"]} (Qty)'
                        mode_report_lines.append(f'- {label:<{max_label_length}}: {base_qty} -> {mod_qty}')
            
            if mode_report_lines:
                changes.append(f"  [{mode_name}]")
                changes.extend(mode_report_lines)
        
        return changes
        
    def _analyzer_compare_merchant_stock(self, f_mod, f_base):
        report_data = []
        for chapter_key, chapter_info in self.all_data["merchant"].items():
            display_name = chapter_info.get("display_name", chapter_key)
            if chapter_info["stock_slots"] > 0:
                offset = int(chapter_info["stock_offset"], 16)
                for i in range(chapter_info["stock_slots"]):
                    f_mod.seek(offset + i*8); f_base.seek(offset + i*8)
                    mod_id, mod_qty, _ = struct.unpack('<HHI', f_mod.read(8))
                    base_id, base_qty, _ = struct.unpack('<HHI', f_base.read(8))
                    if mod_id != base_id:
                        mod_name = self.item_id_to_name.get(mod_id, f"ID:{hex(mod_id)}")
                        base_name = self.item_id_to_name.get(base_id, f"ID:{hex(base_id)}")
                        report_data.append((f"{display_name} - Stock Slot {i+1}", base_name, mod_name))
                    elif mod_qty != base_qty and base_id != 0xFFFF:
                        item_name = self.item_id_to_name.get(base_id)
                        report_data.append((f"{display_name} - {item_name} Qty", f"{base_qty}", f"{mod_qty}"))
            if chapter_info["upgrade_slots"] > 0:
                offset = int(chapter_info["upgrades_offset"], 16)
                for i in range(chapter_info["upgrade_slots"]):
                    f_mod.seek(offset + i*8); f_base.seek(offset + i*8)
                    mod_data = struct.unpack('<HBBBBH', f_mod.read(8))
                    base_data = struct.unpack('<HBBBBH', f_base.read(8))
                    if mod_data[0] != base_data[0]:
                        mod_name = self.weapon_id_to_name.get(mod_data[0], f"ID:{hex(mod_data[0])}")
                        base_name = self.weapon_id_to_name.get(base_data[0], f"ID:{hex(base_data[0])}")
                        report_data.append((f"{display_name} - Upgrade Slot {i+1}", base_name, mod_name))
                    elif mod_data != base_data and base_data[0] != 0xFFFF:
                        weapon_name = self.weapon_id_to_name.get(base_data[0])
                        stat_labels = ['FP', 'FS', 'RS', 'Cap']
                        for j in range(4):
                            if mod_data[j+1] != base_data[j+1]:
                                report_data.append((f"{display_name} - {weapon_name} {stat_labels[j]} Lvl", f"{base_data[j+1]}", f"{mod_data[j+1]}"))
                                
        if not report_data: return []
        max_len = max(len(item[0]) for item in report_data)
        return [f"- {label:<{max_len}}: {old_val} -> {new_val}" for label, old_val, new_val in report_data]

    # --- END OF MOD ANALYZER SECTION ---
    
    # --- START OF WEAPON STAT EDITOR SECTION ---
    def _create_weapon_stat_editor_tab(self, parent_frame):
        weapon_editor_tab = parent_frame
        weapon_editor_tab.grid_columnconfigure(0, weight=1); weapon_editor_tab.grid_rowconfigure(0, weight=1)
        
        weapon_scroll_frame = ctk.CTkScrollableFrame(weapon_editor_tab, label_text="Edit Base Weapon Statistics"); weapon_scroll_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew"); weapon_scroll_frame.grid_columnconfigure(0, weight=1)
        
        mousewheel_func = lambda event: self._on_mousewheel(event, weapon_scroll_frame)
        
        weapon_selector_frame = ctk.CTkFrame(weapon_scroll_frame); weapon_selector_frame.pack(fill="x", padx=10, pady=10); weapon_selector_frame.bind("<MouseWheel>", mousewheel_func)
        weapon_selector_frame.grid_columnconfigure((1, 4), weight=1)
        ctk.CTkLabel(weapon_selector_frame, text="Select Weapon:").grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        weapon_editor_selector_display_frame = ctk.CTkFrame(weapon_selector_frame, fg_color="transparent"); weapon_editor_selector_display_frame.grid(row=0, column=1, padx=5, pady=10, sticky="ew"); weapon_editor_selector_display_frame.grid_columnconfigure(0, weight=1)
        self.weapon_editor_entry = ctk.CTkEntry(weapon_editor_selector_display_frame, state="disabled", placeholder_text="-"); self.weapon_editor_entry.grid(row=0, column=0, sticky="ew")
        self.weapon_editor_button = ctk.CTkButton(weapon_editor_selector_display_frame, text="...", width=30, state="disabled", command=self.open_weapon_editor_selector, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER); self.weapon_editor_button.grid(row=0, column=1, padx=(5,0))
        ctk.CTkLabel(weapon_selector_frame, text="Accessory:").grid(row=0, column=2, padx=(10, 5), pady=10, sticky="w")
        self.accessory_combo = ctk.CTkComboBox(weapon_selector_frame, values=["Normal", "Silencer/Scoope"], state="disabled", width=110, fg_color=self.SECONDARY_COLOR, button_color=self.SECONDARY_COLOR, button_hover_color=self.SECONDARY_COLOR_HOVER); self.accessory_combo.grid(row=0, column=3, padx=5, pady=10, sticky="w")
        ctk.CTkLabel(weapon_selector_frame, text="Ammo Type:").grid(row=0, column=4, padx=(10, 5), pady=10, sticky="w")
        ammo_type_display_frame = ctk.CTkFrame(weapon_selector_frame, fg_color="transparent"); ammo_type_display_frame.grid(row=0, column=5, padx=5, pady=10, sticky="ew"); ammo_type_display_frame.grid_columnconfigure(0, weight=1)
        self.ammo_type_entry = ctk.CTkEntry(ammo_type_display_frame, state="disabled"); self.ammo_type_entry.grid(row=0, column=0, sticky="ew")
        self.ammo_type_button = ctk.CTkButton(ammo_type_display_frame, text="...", width=30, state="disabled", command=self.open_ammo_selector, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER); self.ammo_type_button.grid(row=0, column=1, padx=(5,0))
        self.apply_header_button = ctk.CTkButton(weapon_selector_frame, text="Apply", width=60, state="disabled", command=self.apply_header_stats, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER); self.apply_header_button.grid(row=0, column=6, padx=(10,10), pady=10)
        
        stats_frame = ctk.CTkFrame(weapon_scroll_frame, border_width=1, border_color="gray25"); stats_frame.pack(fill="x", padx=10, pady=10); stats_frame.grid_columnconfigure(1, weight=1)
        stats_header_frame = ctk.CTkFrame(stats_frame, fg_color="transparent"); stats_header_frame.grid(row=0, column=0, columnspan=5, pady=(5,0), sticky="ew")
        stats_header_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(stats_header_frame, text="Weapon Stats Per Level", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR).grid(row=0, column=0)
        
        self.shared_stats_frame = ctk.CTkFrame(stats_frame, fg_color="transparent", height=20); self.shared_stats_frame.grid(row=1, column=0, columnspan=5, padx=20, pady=(0,10), sticky="ew")
        self.shared_stats_label = ctk.CTkLabel(self.shared_stats_frame, text="", text_color="#E5C07B", font=ctk.CTkFont(size=12, slant="italic"))
        
        ctk.CTkLabel(stats_frame, text="Attribute", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, padx=20, pady=5)
        ctk.CTkLabel(stats_frame, text="Value", font=ctk.CTkFont(weight="bold")).grid(row=2, column=1, padx=10, pady=5)
        ctk.CTkLabel(stats_frame, text="Level", font=ctk.CTkFont(weight="bold")).grid(row=2, column=2, padx=10, pady=5)
        
        stat_dropdown_kwargs = {"state": "disabled", "fg_color": self.SECONDARY_COLOR, "button_color": self.SECONDARY_COLOR, "button_hover_color": self.SECONDARY_COLOR_HOVER}
        arrow_kwargs = {"width": 25, "fg_color": self.THEME_COLOR, "hover_color": self.THEME_COLOR_HOVER, "state": "disabled"}
        
        # (All stat rows are the same, but the row numbers are incremented by 1)
        # Damage/Firepower
        ctk.CTkLabel(stats_frame, text="Damage/Firepower:").grid(row=3, column=0, padx=20, pady=5, sticky="w"); self.firepower_entry = ctk.CTkEntry(stats_frame, state="disabled"); self.firepower_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew"); fp_level_frame = ctk.CTkFrame(stats_frame, fg_color="transparent"); fp_level_frame.grid(row=3, column=2, padx=10, pady=5, sticky="ew"); self.firepower_level_menu = ctk.CTkOptionMenu(fp_level_frame, values=["-"], command=self.on_firepower_level_changed, **stat_dropdown_kwargs); self.firepower_level_menu.pack(side="left", expand=True, fill="x"); self.fp_level_down_arrow = ctk.CTkButton(fp_level_frame, text="▼", command=lambda: self._cycle_level(self.firepower_level_menu, -1), **arrow_kwargs); self.fp_level_down_arrow.pack(side="left", padx=(2,0)); self.fp_level_up_arrow = ctk.CTkButton(fp_level_frame, text="▲", command=lambda: self._cycle_level(self.firepower_level_menu, 1), **arrow_kwargs); self.fp_level_up_arrow.pack(side="left", padx=(2,0)); self.read_fp_button = ctk.CTkButton(stats_frame, text="Read", width=60, state="disabled", command=self.read_firepower, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER); self.read_fp_button.grid(row=3, column=3, padx=5, pady=5); self.apply_fp_button = ctk.CTkButton(stats_frame, text="Apply", width=60, state="disabled", command=self.apply_firepower, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER); self.apply_fp_button.grid(row=3, column=4, padx=5, pady=5)
        # Capacity
        ctk.CTkLabel(stats_frame, text="Capacity:").grid(row=4, column=0, padx=20, pady=5, sticky="w"); self.capacity_entry = ctk.CTkEntry(stats_frame, state="disabled"); self.capacity_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew"); cap_level_frame = ctk.CTkFrame(stats_frame, fg_color="transparent"); cap_level_frame.grid(row=4, column=2, padx=10, pady=5, sticky="ew"); self.capacity_level_menu = ctk.CTkOptionMenu(cap_level_frame, values=["-"], command=self.on_capacity_level_changed, **stat_dropdown_kwargs); self.capacity_level_menu.pack(side="left", expand=True, fill="x"); self.cap_level_down_arrow = ctk.CTkButton(cap_level_frame, text="▼", command=lambda: self._cycle_level(self.capacity_level_menu, -1), **arrow_kwargs); self.cap_level_down_arrow.pack(side="left", padx=(2,0)); self.cap_level_up_arrow = ctk.CTkButton(cap_level_frame, text="▲", command=lambda: self._cycle_level(self.capacity_level_menu, 1), **arrow_kwargs); self.cap_level_up_arrow.pack(side="left", padx=(2,0)); self.read_cap_button = ctk.CTkButton(stats_frame, text="Read", width=60, state="disabled", command=self.read_capacity, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER); self.read_cap_button.grid(row=4, column=3, padx=5, pady=5); self.apply_cap_button = ctk.CTkButton(stats_frame, text="Apply", width=60, state="disabled", command=self.apply_capacity, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER); self.apply_cap_button.grid(row=4, column=4, padx=5, pady=5)
        # Firing Speed
        ctk.CTkLabel(stats_frame, text="Firing Speed:").grid(row=5, column=0, padx=20, pady=5, sticky="w"); fs_frame = ctk.CTkFrame(stats_frame, fg_color="transparent"); fs_frame.grid(row=5, column=1, padx=10, pady=5, sticky="ew"); fs_frame.grid_columnconfigure((0, 2), weight=1); self.fs_seconds_entry = ctk.CTkComboBox(fs_frame, values=self.FIRING_SPEED_PRESETS, state="disabled", command=self.update_fs_from_seconds); self.fs_seconds_entry.grid(row=0, column=0, sticky="ew"); self.fs_seconds_entry._entry.bind("<MouseWheel>", mousewheel_func); self.fs_raw_label = ctk.CTkLabel(fs_frame, text="Raw:"); self.fs_raw_label.grid(row=0, column=1, padx=(10, 5)); self.fs_raw_entry = ctk.CTkEntry(fs_frame, placeholder_text="Raw Float", state="disabled"); self.fs_raw_entry.grid(row=0, column=2, sticky="ew"); self.fs_seconds_entry.bind("<KeyRelease>", self.update_fs_from_seconds); self.fs_raw_entry.bind("<KeyRelease>", self.update_fs_from_raw); fs_level_frame = ctk.CTkFrame(stats_frame, fg_color="transparent"); fs_level_frame.grid(row=5, column=2, padx=10, pady=5, sticky="ew"); self.firing_speed_level_menu = ctk.CTkOptionMenu(fs_level_frame, values=["-"], command=self.on_firing_speed_level_changed, **stat_dropdown_kwargs); self.firing_speed_level_menu.pack(side="left", expand=True, fill="x"); self.fs_level_down_arrow = ctk.CTkButton(fs_level_frame, text="▼", command=lambda: self._cycle_level(self.firing_speed_level_menu, -1), **arrow_kwargs); self.fs_level_down_arrow.pack(side="left", padx=(2,0)); self.fs_level_up_arrow = ctk.CTkButton(fs_level_frame, text="▲", command=lambda: self._cycle_level(self.firing_speed_level_menu, 1), **arrow_kwargs); self.fs_level_up_arrow.pack(side="left", padx=(2,0)); self.read_fs_button = ctk.CTkButton(stats_frame, text="Read", width=60, state="disabled", command=self.read_firing_speed, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER); self.read_fs_button.grid(row=5, column=3, padx=5, pady=5); self.apply_fs_button = ctk.CTkButton(stats_frame, text="Apply", width=60, state="disabled", command=self.apply_firing_speed, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER); self.apply_fs_button.grid(row=5, column=4, padx=5, pady=5)
        self.fs_warning_label = ctk.CTkLabel(stats_frame, text="", text_color="#E5C07B"); self.fs_warning_label.grid(row=6, column=0, columnspan=5, padx=20, pady=(0,5), sticky="w")
        # Reload Speed
        ctk.CTkLabel(stats_frame, text="Reload Speed:").grid(row=7, column=0, padx=20, pady=5, sticky="w"); rs_frame = ctk.CTkFrame(stats_frame, fg_color="transparent"); rs_frame.grid(row=7, column=1, padx=10, pady=5, sticky="ew"); rs_frame.grid_columnconfigure((0, 2), weight=1); self.rs_seconds_entry = ctk.CTkComboBox(rs_frame, values=self.RELOAD_SPEED_PRESETS, state="disabled", command=self.update_rs_from_seconds); self.rs_seconds_entry.grid(row=0, column=0, sticky="ew"); self.rs_seconds_entry._entry.bind("<MouseWheel>", mousewheel_func); self.rs_raw_label = ctk.CTkLabel(rs_frame, text="Raw:"); self.rs_raw_label.grid(row=0, column=1, padx=(10, 5)); self.rs_raw_entry = ctk.CTkEntry(rs_frame, placeholder_text="Raw Float", state="disabled"); self.rs_raw_entry.grid(row=0, column=2, sticky="ew"); self.rs_seconds_entry.bind("<KeyRelease>", self.update_rs_from_seconds); self.rs_raw_entry.bind("<KeyRelease>", self.update_rs_from_raw); rs_level_frame = ctk.CTkFrame(stats_frame, fg_color="transparent"); rs_level_frame.grid(row=7, column=2, padx=10, pady=5, sticky="ew"); self.reload_speed_level_menu = ctk.CTkOptionMenu(rs_level_frame, values=["-"], command=self.on_reload_speed_level_changed, **stat_dropdown_kwargs); self.reload_speed_level_menu.pack(side="left", expand=True, fill="x"); self.rs_level_down_arrow = ctk.CTkButton(rs_level_frame, text="▼", command=lambda: self._cycle_level(self.reload_speed_level_menu, -1), **arrow_kwargs); self.rs_level_down_arrow.pack(side="left", padx=(2,0)); self.rs_level_up_arrow = ctk.CTkButton(rs_level_frame, text="▲", command=lambda: self._cycle_level(self.reload_speed_level_menu, 1), **arrow_kwargs); self.rs_level_up_arrow.pack(side="left", padx=(2,0)); self.read_rs_button = ctk.CTkButton(stats_frame, text="Read", width=60, state="disabled", command=self.read_reload_speed, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER); self.read_rs_button.grid(row=7, column=3, padx=5, pady=5); self.apply_rs_button = ctk.CTkButton(stats_frame, text="Apply", width=60, state="disabled", command=self.apply_reload_speed, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER); self.apply_rs_button.grid(row=7, column=4, padx=5, pady=5)
        
        # (Max levels frame is unchanged)
        max_levels_frame = ctk.CTkFrame(weapon_scroll_frame, border_width=1, border_color="gray25"); max_levels_frame.pack(fill="x", padx=10, pady=10); max_levels_frame.bind("<MouseWheel>", mousewheel_func); max_levels_frame.grid_columnconfigure(0, weight=2); max_levels_frame.grid_columnconfigure(1, weight=1); max_levels_header_frame = ctk.CTkFrame(max_levels_frame, fg_color="transparent"); max_levels_header_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(5,10), sticky="ew"); max_levels_header_frame.grid_columnconfigure(0, weight=1); ctk.CTkLabel(max_levels_header_frame, text="Maximum Upgrade Levels", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR).grid(row=0, column=0)
        entries_frame = ctk.CTkFrame(max_levels_frame, fg_color="transparent"); entries_frame.grid(row=1, column=0, sticky="nsew", padx=(10,0)); entries_frame.grid_columnconfigure((1, 4), weight=1)
        ctk.CTkLabel(entries_frame, text="Max Firepower:").grid(row=0, column=0, padx=(10,5), pady=5, sticky="w"); self.max_fp_entry = ctk.CTkEntry(entries_frame, state="disabled"); self.max_fp_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew"); ctk.CTkLabel(entries_frame, text="(Max: 6)", text_color="gray50").grid(row=0, column=2, padx=(0,10), pady=5, sticky="w")
        ctk.CTkLabel(entries_frame, text="Max Firing Speed:").grid(row=0, column=3, padx=(10,5), pady=5, sticky="w"); self.max_fs_entry = ctk.CTkEntry(entries_frame, state="disabled"); self.max_fs_entry.grid(row=0, column=4, padx=5, pady=5, sticky="ew"); ctk.CTkLabel(entries_frame, text="(Max: 6)", text_color="gray50").grid(row=0, column=5, padx=(0,10), pady=5, sticky="w")
        ctk.CTkLabel(entries_frame, text="Max Reload Speed:").grid(row=1, column=0, padx=(10,5), pady=5, sticky="w"); self.max_rs_entry = ctk.CTkEntry(entries_frame, state="disabled"); self.max_rs_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew"); ctk.CTkLabel(entries_frame, text="(Max: 3)", text_color="gray50").grid(row=1, column=2, padx=(0,10), pady=5, sticky="w")
        ctk.CTkLabel(entries_frame, text="Max Capacity:").grid(row=1, column=3, padx=(10,5), pady=5, sticky="w"); self.max_cap_entry = ctk.CTkEntry(entries_frame, state="disabled"); self.max_cap_entry.grid(row=1, column=4, padx=5, pady=5, sticky="ew"); ctk.CTkLabel(entries_frame, text="(Max: 6)", text_color="gray50").grid(row=1, column=5, padx=(0,10), pady=5, sticky="w")
        buttons_frame = ctk.CTkFrame(max_levels_frame, fg_color="transparent"); buttons_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5); buttons_frame.grid_rowconfigure((0,1), weight=1); self.read_max_levels_button = ctk.CTkButton(buttons_frame, text="Read Max Levels", state="disabled", command=self.read_max_levels, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER); self.read_max_levels_button.pack(fill="both", expand=True, padx=10, pady=4); self.apply_max_levels_button = ctk.CTkButton(buttons_frame, text="Apply Max Levels", state="disabled", command=self.apply_max_levels, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER); self.apply_max_levels_button.pack(fill="both", expand=True, padx=10, pady=4)

        self.max_fs_warning_frame = ctk.CTkFrame(weapon_scroll_frame, fg_color="#58181F")
        self.max_fs_warning_label = ctk.CTkLabel(self.max_fs_warning_frame, text="⚠️ WARNING: Setting Max Firing Speed > 3 will cause its upgrade prices to be shared with Reload Speed prices.", text_color="#F9D423", wraplength=800, justify="center")
        self.max_fs_warning_label.pack(padx=10, pady=10)
        # --- END OF NEW CODE ---

        stat_editor_bottom_frame = ctk.CTkFrame(weapon_editor_tab); stat_editor_bottom_frame.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="ew"); stat_editor_bottom_frame.grid_columnconfigure((0, 1), weight=1)
        self.reset_all_stats_button = ctk.CTkButton(stat_editor_bottom_frame, text="Reset Selected Weapon Stats", state="disabled", command=self.reset_all_stats, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER); self.reset_all_stats_button.grid(row=0, column=0, padx=(10,5), pady=10, sticky="ew")
        self.reset_all_weapons_all_stats_button = ctk.CTkButton(stat_editor_bottom_frame, text="Reset ALL Weapon Stats", state="disabled", command=self.reset_all_weapons_all_stats, fg_color="#C75450", hover_color="#A34440"); self.reset_all_weapons_all_stats_button.grid(row=0, column=1, padx=(5,10), pady=10, sticky="ew")
        
    def _cycle_level(self, menu_widget, direction):
        if menu_widget.cget("state") == "disabled": return
        values = menu_widget.cget("values")
        if not values or values == ["-"]: return
        
        current_value = menu_widget.get()
        try:
            current_index = values.index(current_value)
            new_index = (current_index + direction) % len(values)
            new_value = values[new_index]
            menu_widget.set(new_value)
        except ValueError:
            new_value = values[0]
            menu_widget.set(new_value)
        
        if hasattr(menu_widget, '_command') and menu_widget._command:
            menu_widget._command(new_value)

    def on_weapon_selected(self, selected_weapon):
        if "---" in selected_weapon:
            self.weapon_editor_entry.configure(state="normal"); self.weapon_editor_entry.delete(0, "end"); self.weapon_editor_entry.insert(0, self.last_selected_weapon); self.weapon_editor_entry.configure(state="disabled")
            return
        
        self.last_selected_weapon = selected_weapon
        weapon_info = self.all_data.get("weapons", {}).get(selected_weapon, {})
        base_weapon_name = weapon_info.get("base_weapon")
        
        effective_weapon_info = weapon_info
        if base_weapon_name:
            base_weapon_info = self.all_data.get("weapons", {}).get(base_weapon_name, {})
            effective_weapon_info = {**base_weapon_info, **weapon_info}

        if base_weapon_name:
            self.shared_stats_label.configure(text=f"Note: This is a variation of '{base_weapon_name}'. Shared stats are read-only.")
            self.shared_stats_label.pack(anchor="w")
        else:
            self.shared_stats_label.pack_forget()

        # Check for which stats are UNIQUE to the selected form (editable)
        has_firepower = "firepower_base_offset" in weapon_info; has_capacity = "capacity_base_offset" in weapon_info; has_firing_speed = "firing_speed_offsets" in weapon_info; has_reload_speed = "reload_speed_base_offset" in weapon_info; has_max_levels = "max_levels_offsets" in weapon_info
        
        # Check for which stats EXIST AT ALL (unique or inherited) (viewable)
        effective_has_firepower = "firepower_base_offset" in effective_weapon_info; effective_has_capacity = "capacity_base_offset" in effective_weapon_info; effective_has_firing_speed = "firing_speed_offsets" in effective_weapon_info; effective_has_reload_speed = "reload_speed_base_offset" in effective_weapon_info; effective_has_max_levels = "max_levels_offsets" in effective_weapon_info

        # Determine state and colors for each stat
        fp_state = "normal" if has_firepower else "disabled"; fp_fg_color = self.DEFAULT_ENTRY_COLOR if has_firepower else self.DISABLED_COLOR; fp_text_color = self.default_status_color if has_firepower else self.DISABLED_TEXT_COLOR
        cap_state = "normal" if has_capacity else "disabled"; cap_fg_color = self.DEFAULT_ENTRY_COLOR if has_capacity else self.DISABLED_COLOR; cap_text_color = self.default_status_color if has_capacity else self.DISABLED_TEXT_COLOR
        fs_state = "normal" if has_firing_speed else "disabled"; fs_fg_color = self.DEFAULT_ENTRY_COLOR if has_firing_speed else self.DISABLED_COLOR; fs_text_color = self.default_status_color if has_firing_speed else self.DISABLED_TEXT_COLOR
        rs_state = "normal" if has_reload_speed else "disabled"; rs_fg_color = self.DEFAULT_ENTRY_COLOR if has_reload_speed else self.DISABLED_COLOR; rs_text_color = self.default_status_color if has_reload_speed else self.DISABLED_TEXT_COLOR
        max_state = "normal" if has_max_levels else "disabled"; max_fg_color = self.DEFAULT_ENTRY_COLOR if has_max_levels else self.DISABLED_COLOR; max_text_color = self.default_status_color if has_max_levels else self.DISABLED_TEXT_COLOR

        # Level browsing is enabled if the stat exists at all (unique or inherited)
        fp_level_state = "normal" if effective_has_firepower else "disabled"; cap_level_state = "normal" if effective_has_capacity else "disabled"; fs_level_state = "normal" if effective_has_firing_speed else "disabled"; rs_level_state = "normal" if effective_has_reload_speed else "disabled"
        
        # Configure entry/apply widgets
        self.firepower_entry.configure(state=fp_state, fg_color=fp_fg_color, text_color=fp_text_color); self.read_fp_button.configure(state=fp_state); self.apply_fp_button.configure(state=fp_state)
        self.capacity_entry.configure(state=cap_state, fg_color=cap_fg_color, text_color=cap_text_color); self.read_cap_button.configure(state=cap_state); self.apply_cap_button.configure(state=cap_state)
        self.fs_seconds_entry.configure(state=fs_state, fg_color=fs_fg_color, text_color=fs_text_color); self.fs_raw_entry.configure(state=fs_state, fg_color=fs_fg_color, text_color=fs_text_color); self.read_fs_button.configure(state=fs_state); self.apply_fs_button.configure(state=fs_state)
        self.rs_seconds_entry.configure(state=rs_state, fg_color=rs_fg_color, text_color=rs_text_color); self.rs_raw_entry.configure(state=rs_state, fg_color=rs_fg_color, text_color=rs_text_color); self.read_rs_button.configure(state=rs_state); self.apply_rs_button.configure(state=rs_state)
        self.max_fp_entry.configure(state=max_state, fg_color=max_fg_color, text_color=max_text_color); self.max_fs_entry.configure(state=max_state, fg_color=max_fg_color, text_color=max_text_color); self.max_rs_entry.configure(state=max_state, fg_color=max_fg_color, text_color=max_text_color); self.max_cap_entry.configure(state=max_state, fg_color=max_fg_color, text_color=max_text_color); self.read_max_levels_button.configure(state=max_state); self.apply_max_levels_button.configure(state=max_state)

        # Configure level browsing widgets
        self.fp_level_down_arrow.configure(state=fp_level_state); self.firepower_level_menu.configure(state=fp_level_state); self.fp_level_up_arrow.configure(state=fp_level_state)
        self.cap_level_down_arrow.configure(state=cap_level_state); self.capacity_level_menu.configure(state=cap_level_state); self.cap_level_up_arrow.configure(state=cap_level_state)
        self.fs_level_down_arrow.configure(state=fs_level_state); self.firing_speed_level_menu.configure(state=fs_level_state); self.fs_level_up_arrow.configure(state=fs_level_state)
        self.rs_level_down_arrow.configure(state=rs_level_state); self.reload_speed_level_menu.configure(state=rs_level_state); self.rs_level_up_arrow.configure(state=rs_level_state)
        
        # Configure Raw labels text color
        self.fs_raw_label.configure(text_color=self.default_status_color if fs_state == "normal" else "gray50")
        self.rs_raw_label.configure(text_color=self.default_status_color if rs_state == "normal" else "gray50")

        # Configure Header and Reset buttons
        header_state = "normal" if effective_has_capacity else "disabled"; self.accessory_combo.configure(state=header_state); self.ammo_type_button.configure(state=header_state); self.apply_header_button.configure(state=header_state)
        reset_state = "normal" if self.active_backup_path and os.path.exists(self.active_backup_path) else "disabled"; self.reset_all_stats_button.configure(state=reset_state)
        if hasattr(self, 'reset_all_weapons_all_stats_button'): self.reset_all_weapons_all_stats_button.configure(state=reset_state)

        # Set dropdown values and warnings
        self.fs_warning_label.configure(text=effective_weapon_info.get("firing_speed_notes", ""))
        fp_levels = [f"Level {i}" for i in range(1, 8)] if effective_has_firepower else ["-"]; self.firepower_level_menu.configure(values=fp_levels); self.firepower_level_menu.set(fp_levels[0])
        cap_levels = [f"Level {i}" for i in range(1, 8)] if effective_has_capacity else ["-"]; self.capacity_level_menu.configure(values=cap_levels); self.capacity_level_menu.set(cap_levels[0])
        fs_levels = [f"Level {i}" for i in range(1, 8)] if effective_has_firing_speed else ["-"]; self.firing_speed_level_menu.configure(values=fs_levels); self.firing_speed_level_menu.set(fs_levels[0])
        rs_levels = [f"Level {i}" for i in range(1, 4)] if effective_has_reload_speed else ["-"]; self.reload_speed_level_menu.configure(values=rs_levels); self.reload_speed_level_menu.set(rs_levels[0])
        
        # Read and display data
        if self.exe_path:
            self.read_header_stats()
            # Read all stats that are available for the effective weapon
            if effective_has_firepower: self.read_firepower()
            else: self.firepower_entry.delete(0, "end"); self.firepower_entry.insert(0, "N/A")
            if effective_has_capacity: self.read_capacity()
            else: self.capacity_entry.delete(0, "end"); self.capacity_entry.insert(0, "N/A")
            if effective_has_firing_speed: self.read_firing_speed()
            else: self.fs_seconds_entry.set("N/A"); self.fs_raw_entry.delete(0, "end"); self.fs_raw_entry.insert(0, "N/A")
            if effective_has_reload_speed: self.read_reload_speed()
            else: self.rs_seconds_entry.set("N/A"); self.rs_raw_entry.delete(0, "end"); self.rs_raw_entry.insert(0, "N/A")
            if effective_has_max_levels: self.read_max_levels()
            else:
                for entry in [self.max_fp_entry, self.max_fs_entry, self.max_rs_entry, self.max_cap_entry]: entry.delete(0, "end"); entry.insert(0, "N/A")
                
    def _get_stat_offset(self, weapon, level_str, stat_type):
        if weapon not in self.all_data["weapons"] or level_str == "-": return None
        level_num = int(level_str.split(' ')[1]); level_index = level_num - 1
        
        weapon_info = self.all_data["weapons"].get(weapon, {})
        stat_key_map = {
            'firepower': 'firepower_base_offset', 'capacity': 'capacity_base_offset',
            'firing_speed': 'firing_speed_offsets', 'reload_speed': 'reload_speed_base_offset'
        }
        offset_key = stat_key_map.get(stat_type)
        if not offset_key: return None

        # --- NEW INHERITANCE LOGIC ---
        data_to_use = weapon_info
        if offset_key not in weapon_info:
            base_weapon_name = weapon_info.get("base_weapon")
            if base_weapon_name:
                data_to_use = self.all_data["weapons"].get(base_weapon_name, {})
            else:
                return None # No offset found and no base weapon to inherit from

        if stat_type == 'firepower': base = int(data_to_use.get("firepower_base_offset", "0"), 16); return base + (level_index * 4) if base != 0 else None
        elif stat_type == 'capacity': base = int(data_to_use.get("capacity_base_offset", "0"), 16); return base + 8 + (level_index * 2) if base != 0 else None
        elif stat_type == 'firing_speed': offsets = data_to_use.get("firing_speed_offsets", []); return int(offsets[0], 16) + (level_index * 4) if offsets else None
        elif stat_type == 'reload_speed': base = int(data_to_use.get("reload_speed_base_offset", "0"), 16); return base + (level_index * 4) if base != 0 else None
        return None
        
    def update_fs_from_seconds(self, event_or_value=None):
        if self.is_updating_fs: return; self.is_updating_fs = True
        try: seconds = float(self.fs_seconds_entry.get()); raw_val = seconds / self.FIRING_SPEED_MULTIPLIER; self.fs_raw_entry.delete(0, "end"); self.fs_raw_entry.insert(0, f"{raw_val:.1f}")
        except ValueError: self.fs_raw_entry.delete(0, "end")
        finally: self.is_updating_fs = False
    def update_fs_from_raw(self, event=None):
        if self.is_updating_fs: return; self.is_updating_fs = True
        try: raw_val = float(self.fs_raw_entry.get()); seconds = raw_val * self.FIRING_SPEED_MULTIPLIER; self.fs_seconds_entry.set(f"{seconds:.2f}")
        except ValueError: self.fs_seconds_entry.set("")
        finally: self.is_updating_fs = False
    def update_rs_from_seconds(self, event_or_value=None):
        if self.is_updating_rs: return; self.is_updating_rs = True
        try: seconds = float(self.rs_seconds_entry.get()); raw_val = seconds / self.RELOAD_SPEED_MULTIPLIER; self.rs_raw_entry.delete(0, "end"); self.rs_raw_entry.insert(0, f"{raw_val:.1f}")
        except ValueError: self.rs_raw_entry.delete(0, "end")
        finally: self.is_updating_rs = False
    def update_rs_from_raw(self, event=None):
        if self.is_updating_rs: return; self.is_updating_rs = True
        try: raw_val = float(self.rs_raw_entry.get()); seconds = raw_val * self.RELOAD_SPEED_MULTIPLIER; self.rs_seconds_entry.set(f"{seconds:.2f}")
        except ValueError: self.rs_seconds_entry.set("")
        finally: self.is_updating_rs = False
    def on_firepower_level_changed(self, _): self.read_firepower()
    def on_capacity_level_changed(self, _): self.read_capacity()
    def on_firing_speed_level_changed(self, _): self.read_firing_speed()
    def on_reload_speed_level_changed(self, _): self.read_reload_speed()
    def read_header_stats(self):
        weapon_name = self.weapon_editor_entry.get()
        weapon_info = self.all_data["weapons"].get(weapon_name, {})
        base_offset_str = weapon_info.get("capacity_base_offset")
        if not base_offset_str or not self.exe_path:
            self.accessory_combo.set("N/A"); self.ammo_type_entry.configure(state="normal"); self.ammo_type_entry.delete(0,"end"); self.ammo_type_entry.insert(0,"N/A"); self.ammo_type_entry.configure(state="disabled")
            return
        try:
            base_offset = int(base_offset_str, 16); accessory_offset = base_offset + 4; ammo_offset = base_offset + 6
            with open(self.exe_path, 'rb') as f:
                f.seek(accessory_offset); accessory_val = struct.unpack('<H', f.read(2))[0]
                self.accessory_combo.set("Silencer/Scoope" if accessory_val == 0x0101 else "Normal")
                f.seek(ammo_offset); ammo_id = struct.unpack('<H', f.read(2))[0]
                ammo_name = self.item_id_to_name.get(ammo_id, f"Unknown ID: {hex(ammo_id)}")
                self.ammo_type_entry.configure(state="normal"); self.ammo_type_entry.delete(0, "end"); self.ammo_type_entry.insert(0, ammo_name); self.ammo_type_entry.configure(state="disabled")
            self.status_bar.configure(text=f"Read header stats for {weapon_name}.")
        except Exception as e: messagebox.showerror("Read Error", f"Could not read header stats: {e}")
    
    def apply_header_stats(self, event=None):
        weapon_name = self.weapon_editor_entry.get()
        weapon_info = self.all_data["weapons"].get(weapon_name, {})
        base_offset_str = weapon_info.get("capacity_base_offset")
        if not base_offset_str or not self.exe_path: return
        try:
            base_offset = int(base_offset_str, 16); accessory_offset = base_offset + 4; ammo_offset = base_offset + 6
            accessory_val = 0x0101 if self.accessory_combo.get() == "Silencer/Scoope" else 0x0100
            ammo_name = self.ammo_type_entry.get()
            ammo_id = self.item_name_to_id.get(ammo_name, 0)
            with open(self.exe_path, 'rb+') as f:
                f.seek(accessory_offset); f.write(struct.pack('<H', accessory_val))
                f.seek(ammo_offset); f.write(struct.pack('<H', ammo_id))
            
            self.read_header_stats()
            if self.price_editor_loaded: self._refresh_price_data_and_labels(read_exe=True)
            self._show_success_message(f"Applied header stats to {weapon_name}!")
        except Exception as e: messagebox.showerror("Write Error", f"Could not apply header stats: {e}")
        
    def read_firepower(self):
        weapon = self.weapon_editor_entry.get(); level = self.firepower_level_menu.get(); offset = self._get_stat_offset(weapon, level, 'firepower')
        if not offset or not self.exe_path: return
        try:
            with open(self.exe_path, 'rb') as f: f.seek(offset); val = struct.unpack('<f', f.read(4))[0]
            
            is_disabled = self.firepower_entry.cget("state") == "disabled"
            if is_disabled: self.firepower_entry.configure(state="normal")
            
            self.firepower_entry.delete(0, "end"); self.firepower_entry.insert(0, f"{val:.1f}")
            
            if is_disabled: self.firepower_entry.configure(state="disabled")

            self.status_bar.configure(text=f"Read FP for {weapon} {level}.")
        except Exception as e: messagebox.showerror("Read Error", f"Could not read firepower: {e}")
        
    def apply_firepower(self, event=None):
        weapon = self.weapon_editor_entry.get(); level = self.firepower_level_menu.get(); offset = self._get_stat_offset(weapon, level, 'firepower')
        if not offset: return
        try:
            new_val = float(self.firepower_entry.get());
            with open(self.exe_path, 'rb+') as f: f.seek(offset); f.write(struct.pack('<f', new_val))
            self.read_firepower()
            self._show_success_message(f"Applied FP to {weapon} {level}!")
        except ValueError: messagebox.showerror("Invalid Input", "Please enter a valid number for Firepower.")
        except Exception as e: messagebox.showerror("Write Error", f"Could not apply change: {e}")
        
    def read_capacity(self):
        weapon = self.weapon_editor_entry.get(); level = self.capacity_level_menu.get(); offset = self._get_stat_offset(weapon, level, 'capacity')
        if not offset or not self.exe_path: return
        try:
            with open(self.exe_path, 'rb') as f: f.seek(offset); val = struct.unpack('<h', f.read(2))[0]
            
            is_disabled = self.capacity_entry.cget("state") == "disabled"
            if is_disabled: self.capacity_entry.configure(state="normal")

            self.capacity_entry.delete(0, "end"); self.capacity_entry.insert(0, str(val))
            
            if is_disabled: self.capacity_entry.configure(state="disabled")

            self.status_bar.configure(text=f"Read Capacity for {weapon} {level}.")
        except Exception as e: messagebox.showerror("Read Error", f"Could not read capacity: {e}")
    
    def apply_capacity(self, event=None):
        weapon = self.weapon_editor_entry.get(); level = self.capacity_level_menu.get(); offset = self._get_stat_offset(weapon, level, 'capacity')
        if not offset: return
        try:
            new_val = int(self.capacity_entry.get());
            with open(self.exe_path, 'rb+') as f: f.seek(offset); f.write(struct.pack('<h', new_val))
            self.read_capacity()
            if self.price_editor_loaded: self._refresh_price_data_and_labels(read_exe=True)
            self._show_success_message(f"Applied Capacity to {weapon} {level}!")
        except ValueError: messagebox.showerror("Invalid Input", "Please enter a valid integer for Capacity.")
        except Exception as e: messagebox.showerror("Write Error", f"Could not apply capacity: {e}")
        
    def read_firing_speed(self):
        weapon = self.weapon_editor_entry.get(); level = self.firing_speed_level_menu.get(); offset = self._get_stat_offset(weapon, level, 'firing_speed')
        if not offset or not self.exe_path: return
        try:
            with open(self.exe_path, 'rb') as f: f.seek(offset); raw_val = struct.unpack('<f', f.read(4))[0]
            seconds_val = raw_val * self.FIRING_SPEED_MULTIPLIER

            # Check if widgets are disabled (checking one is enough as they are synced)
            is_disabled = self.fs_seconds_entry.cget("state") == "disabled"

            # Temporarily enable BOTH widgets if they were disabled
            if is_disabled:
                self.fs_raw_entry.configure(state="normal")
                self.fs_seconds_entry.configure(state="normal")

            # Update values directly
            self.fs_raw_entry.delete(0, "end"); self.fs_raw_entry.insert(0, f"{raw_val:.1f}")
            self.fs_seconds_entry.set(f"{seconds_val:.2f}")

            # Restore disabled state to BOTH if necessary
            if is_disabled:
                self.fs_raw_entry.configure(state="disabled")
                self.fs_seconds_entry.configure(state="disabled")

            self.status_bar.configure(text=f"Read Firing Speed for {weapon} {level}.")
        except Exception as e: messagebox.showerror("Read Error", f"Could not read Firing Speed: {e}")

    def apply_firing_speed(self, event=None):
        weapon = self.weapon_editor_entry.get(); level = self.firing_speed_level_menu.get(); weapon_info = self.all_data["weapons"].get(weapon, {})
        offsets_str = weapon_info.get("firing_speed_offsets")
        if not offsets_str: return
        try:
            raw_float_to_write = float(self.fs_raw_entry.get()); patch_byte = struct.pack('<f', raw_float_to_write); level_index = int(level.split(' ')[1]) - 1
            with open(self.exe_path, 'rb+') as f:
                for base_offset_str in offsets_str: f.seek(int(base_offset_str, 16) + (level_index * 4)); f.write(patch_byte)
            self.read_firing_speed()
            self._show_success_message(f"Applied Firing Speed to {weapon} {level} at {len(offsets_str)} locations!")
        except ValueError: messagebox.showerror("Invalid Input", "Please enter a valid number in the Firing Speed fields.")
        except Exception as e: messagebox.showerror("Write Error", f"Could not apply Firing Speed change: {e}")
        
    def read_reload_speed(self):
        weapon = self.weapon_editor_entry.get(); level = self.reload_speed_level_menu.get(); offset = self._get_stat_offset(weapon, level, 'reload_speed')
        if not offset or not self.exe_path: return
        try:
            with open(self.exe_path, 'rb') as f: f.seek(offset); raw_val = struct.unpack('<f', f.read(4))[0]
            seconds_val = raw_val * self.RELOAD_SPEED_MULTIPLIER
            
            # Check if widgets are disabled
            is_disabled = self.rs_seconds_entry.cget("state") == "disabled"

            # Temporarily enable BOTH
            if is_disabled:
                self.rs_raw_entry.configure(state="normal")
                self.rs_seconds_entry.configure(state="normal")
            
            # Update values directly
            self.rs_raw_entry.delete(0, "end"); self.rs_raw_entry.insert(0, f"{raw_val:.1f}")
            self.rs_seconds_entry.set(f"{seconds_val:.2f}")

            # Restore disabled state to BOTH
            if is_disabled:
                self.rs_raw_entry.configure(state="disabled")
                self.rs_seconds_entry.configure(state="disabled")

            self.status_bar.configure(text=f"Read Reload Speed for {weapon} {level}.")
        except Exception as e: messagebox.showerror("Read Error", f"Could not read Reload Speed: {e}")
        
    def apply_reload_speed(self, event=None):
        weapon = self.weapon_editor_entry.get(); level = self.reload_speed_level_menu.get(); offset = self._get_stat_offset(weapon, level, 'reload_speed')
        if not offset: return
        try:
            raw_float_to_write = float(self.rs_raw_entry.get()); patch_byte = struct.pack('<f', raw_float_to_write)
            with open(self.exe_path, 'rb+') as f: f.seek(offset); f.write(patch_byte)
            self.read_reload_speed()
            self._show_success_message(f"Applied Reload Speed to {weapon} {level}!")
        except ValueError: messagebox.showerror("Invalid Input", "Please enter a valid number for Reload Speed.")
        except Exception as e: messagebox.showerror("Write Error", f"Could not apply Reload Speed change: {e}")
        
    def read_max_levels(self):
        weapon = self.weapon_editor_entry.get()
        # This function call now returns the max_fs value which we need
        max_fp, max_fs_val_check, _, _ = self._get_max_levels_from_exe(weapon)
        if max_fp is None: return

        weapon_info = self.all_data["weapons"].get(weapon, {})
        offsets = weapon_info.get("max_levels_offsets")
        if not offsets: return

        try:
            with open(self.exe_path, 'rb') as f:
                first_offset = int(offsets[0], 16)
                f.seek(first_offset)
                if weapon == "Matilda": f.read(2)
                data_bytes = f.read(4)
                max_fp_val, max_fs, max_rs, max_cap = struct.unpack('<BBBB', data_bytes)
            
            # --- MODIFIED LOGIC TO SHOW/HIDE WARNING ---
            if max_fs > 3:
                self.max_fs_warning_frame.pack(fill="x", padx=10, pady=(0, 10))
            else:
                self.max_fs_warning_frame.pack_forget()
            # --- END OF MODIFICATION ---

            entries = [self.max_fp_entry, self.max_fs_entry, self.max_rs_entry, self.max_cap_entry]
            values = [max_fp_val, max_fs, max_rs, max_cap]
            
            original_state = self.max_fp_entry.cget("state")
            if original_state == "disabled":
                for entry in entries: entry.configure(state="normal")
            
            for entry, value in zip(entries, values):
                entry.delete(0, "end"); entry.insert(0, str(value))
            
            if original_state == "disabled":
                for entry in entries: entry.configure(state=original_state)

            self.status_bar.configure(text=f"Read max levels for {weapon} (will patch {len(offsets)} locations).")

        except Exception as e: messagebox.showerror("Read Error", f"Could not read max levels: {e}")

    def apply_max_levels(self, event=None):
        weapon = self.weapon_editor_entry.get(); weapon_info = self.all_data["weapons"].get(weapon, {})
        if not self.exe_path or not weapon_info.get("max_levels_offsets"): return
        try:
            offsets = weapon_info["max_levels_offsets"]; new_max_fp = int(self.max_fp_entry.get()); new_max_fs = int(self.max_fs_entry.get()); new_max_rs = int(self.max_rs_entry.get()); new_max_cap = int(self.max_cap_entry.get())
            patch_bytes = struct.pack('<BBBB', new_max_fp, new_max_fs, new_max_rs, new_max_cap)
            with open(self.exe_path, 'rb+') as f:
                for offset_str in offsets: 
                    offset = int(offset_str, 16)
                    if weapon == "Matilda": offset += 2
                    f.seek(offset); f.write(patch_bytes)
            
            # Re-read to update UI, including the new warning label visibility
            self.read_max_levels()
            
            # If the upgrade editor is open for this weapon, refresh it to show the new price layout
            if self.upgrade_editor_loaded and self.upgrade_weapon_entry.get() == weapon:
                self.read_upgrade_prices()
            
            self._show_success_message(f"Patched max levels for {weapon} at {len(offsets)} locations!")
        except ValueError: messagebox.showerror("Invalid Input", "Please ensure all max level values are valid integers.")
        except Exception as e: messagebox.showerror("Write Error", f"Could not apply max level changes: {e}")
    # --- START OF MERCHANT STOCK EDITOR SECTION ---
    def _create_merchant_stock_editor_tab(self, parent_frame):
        merchant_tab = parent_frame
        merchant_tab.grid_columnconfigure(0, weight=1); merchant_tab.grid_rowconfigure(1, weight=1)
        
        top_controls_frame = ctk.CTkFrame(merchant_tab); top_controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(top_controls_frame, text="Select Merchant:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(10,5))
        self.merchant_menu = ctk.CTkOptionMenu(top_controls_frame, values=["-"], state="disabled", command=self.on_merchant_chapter_selected, fg_color=self.THEME_COLOR, button_color=self.THEME_COLOR, button_hover_color=self.THEME_COLOR_HOVER)
        self.merchant_menu.pack(side="left", padx=5, pady=10, expand=True, fill="x")
        self.merchant_refresh_button = ctk.CTkButton(top_controls_frame, text="Read/Refresh", state="disabled", command=lambda: self.on_merchant_chapter_selected(self.merchant_menu.get()), fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER, width=120)
        self.merchant_refresh_button.pack(side="left", padx=(5,10), pady=10)
        self.reset_selected_merchant_button = ctk.CTkButton(top_controls_frame, text="Reset Merchant", state="disabled", command=self.reset_selected_merchant, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER, width=120)
        self.reset_selected_merchant_button.pack(side="left", padx=(0,10), pady=10)

        self.stock_scroll_frame = ctk.CTkScrollableFrame(merchant_tab, label_text="Merchant Stock & Upgrades", label_fg_color=self.THEME_COLOR); self.stock_scroll_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        bottom_frame = ctk.CTkFrame(merchant_tab); bottom_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew"); bottom_frame.grid_columnconfigure((0,1), weight=1)
        self.reset_all_merchants_button = ctk.CTkButton(bottom_frame, text="Reset ALL Merchants", state="disabled", command=self.reset_all_merchants, fg_color="#C75450", hover_color="#A34440")
        self.reset_all_merchants_button.grid(row=0, column=0, padx=(10,5), pady=10, sticky="ew")
        self.apply_stock_button = ctk.CTkButton(bottom_frame, text="Apply Inventory Changes", state="disabled", command=self.apply_merchant_changes, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
        self.apply_stock_button.grid(row=0, column=1, padx=(5,10), pady=10, sticky="ew")
    
    def _get_current_sacrifices_from_exe(self):
        if not self.exe_path: return {}
        sacrificed_items = {}
        try:
            with open(self.exe_path, 'rb') as f:
                for item_name, offsets in self.all_data["master_item_prices"].items():
                    if not offsets or item_name in self.key_items or item_name in self.treasure_items: continue
                    f.seek(int(offsets[0], 16))
                    item_id_in_file = struct.unpack('<H', f.read(2))[0]
                    original_id = self.item_name_to_id.get(item_name)
                    if original_id is not None and item_id_in_file != original_id:
                        key_item_name = self.item_id_to_name.get(item_id_in_file)
                        if key_item_name and key_item_name in self.key_items:
                            sacrificed_items[item_name] = key_item_name
        except Exception as e:
            print(f"Error reading current sacrifices: {e}")
        return sacrificed_items

    def on_merchant_chapter_selected(self, selected_display_name):
        if not self.exe_path: return
        self.status_bar.configure(text=f"Reading inventory for {selected_display_name}...")
        
        for widget_info in self.stock_widgets_data: widget_info["frame"].destroy()
        self.stock_widgets_data = []

        if selected_display_name == "-": 
            self.status_bar.configure(text="Select a merchant to view their inventory.")
            return
            
        chapter_key = self.merchant_display_to_key[selected_display_name]
        
        all_data = self.read_raw_merchant_data(chapter_key)
        if not all_data:
            self.status_bar.configure(text=f"Failed to read data for {selected_display_name}.")
            return
        self.build_ui_from_virtual_inventory(all_data)

    def build_ui_from_virtual_inventory(self, all_data):
        stock_list, upgrade_list = all_data
        virtual_inventory = []; used_upgrade_indices = set()
        
        if stock_list:
            for i, stock_item in enumerate(stock_list):
                item_name = self.item_id_to_name.get(stock_item["id"], f"Unknown ID: {hex(stock_item['id'])}");
                slot = {"stock": stock_item, "upgrade": None, "original_stock_index": i, "original_upgrade_index": -1}
                
                if item_name in self.key_items:
                    for sacrificed, key in self.pending_sacrifices.items():
                        if key == item_name:
                            slot["sacrifice_info"] = {"key_item": key, "sacrificed_item": sacrificed}
                            break
                
                if item_name in self.weapon_name_to_id and upgrade_list:
                    for j, upgrade_item in enumerate(upgrade_list):
                        if j in used_upgrade_indices: continue
                        upgrade_weapon_name = self.weapon_id_to_name.get(upgrade_item["id"], "Unknown")
                        if item_name == upgrade_weapon_name:
                            slot["upgrade"] = upgrade_item; slot["original_upgrade_index"] = j; used_upgrade_indices.add(j)
                            break
                virtual_inventory.append(slot)

        if upgrade_list:
            for j, upgrade_item in enumerate(upgrade_list):
                if j not in used_upgrade_indices:
                    virtual_inventory.append({"stock": None, "upgrade": upgrade_item, "original_stock_index": -1, "original_upgrade_index": j})
        
        self.stock_scroll_frame.grid_columnconfigure(0, weight=1)
        
        mousewheel_func = lambda event, frame=self.stock_scroll_frame: self._on_mousewheel(event, frame)

        for i, slot_data in enumerate(virtual_inventory):
            slot_frame = ctk.CTkFrame(self.stock_scroll_frame, border_width=1, border_color="gray25")
            slot_frame.grid(row=i, column=0, pady=10, padx=5, sticky="ew")
            
            slot_frame.grid_columnconfigure(0, minsize=90); slot_frame.grid_columnconfigure(1, weight=1, minsize=200)
            slot_frame.grid_columnconfigure(2, minsize=90); slot_frame.grid_columnconfigure(3, weight=1, minsize=200)

            slot_frame.bind("<MouseWheel>", mousewheel_func)
            
            slot_header = ctk.CTkLabel(slot_frame, text=f"Display Slot {i+1}", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR)
            slot_header.grid(row=0, column=0, columnspan=4, pady=(5,10))
            slot_header.bind("<MouseWheel>", mousewheel_func)

            ui_widgets = {"frame": slot_frame, "data": slot_data} 
            
            if slot_data.get("stock"):
                item_label = ctk.CTkLabel(slot_frame, text="Item for Sale:")
                item_label.grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
                item_label.bind("<MouseWheel>", mousewheel_func)
                
                item_display_frame = ctk.CTkFrame(slot_frame, fg_color="transparent"); item_display_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew"); item_display_frame.grid_columnconfigure(0, weight=1); item_display_frame.bind("<MouseWheel>", mousewheel_func)
                item_entry = ctk.CTkEntry(item_display_frame, state="disabled"); item_entry.grid(row=0, column=0, sticky="ew"); item_entry.bind("<MouseWheel>", mousewheel_func)
                item_button = ctk.CTkButton(item_display_frame, text="...", width=30, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda widget=item_entry, data=ui_widgets: self.open_item_selector(widget, data)); item_button.grid(row=0, column=1, padx=(5,0)); item_button.bind("<MouseWheel>", mousewheel_func)
                
                qty_label = ctk.CTkLabel(slot_frame, text="Stock Qty:")
                qty_label.grid(row=2, column=0, padx=(10,5), pady=5, sticky="w")
                qty_label.bind("<MouseWheel>", mousewheel_func)
                qty_entry = ctk.CTkEntry(slot_frame, width=120); qty_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w"); qty_entry.bind("<MouseWheel>", mousewheel_func)

                purchase_qty_label = ctk.CTkLabel(slot_frame, text="Purchase Qty:")
                purchase_qty_label.grid(row=3, column=0, padx=(10,5), pady=5, sticky="w")
                purchase_qty_label.bind("<MouseWheel>", mousewheel_func)
                
                purchase_qty_entry = ctk.CTkEntry(slot_frame, width=120)
                purchase_qty_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
                purchase_qty_entry.bind("<MouseWheel>", mousewheel_func)

                note_label = ctk.CTkLabel(slot_frame, text="(Global setting for how many you buy at once)", text_color="gray50", font=ctk.CTkFont(slant="italic"))
                note_label.grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="w")
                
                # --- NEW WARNING LABEL (initially hidden) ---
                warning_label = ctk.CTkLabel(slot_frame, text="", text_color="#E5C07B", wraplength=350, justify="left")
                warning_label.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")
                warning_label.grid_remove() # Hide it by default

                item_name = self.item_id_to_name.get(slot_data["stock"]["id"], "Unknown")
                display_text = item_name
                if slot_data.get("sacrifice_info"):
                    si = slot_data["sacrifice_info"]
                    display_text = f"{si['key_item']} (via {si['sacrificed_item']})"

                item_entry.configure(state="normal"); item_entry.delete(0, "end"); item_entry.insert(0, display_text); item_entry.configure(state="disabled")
                qty_entry.insert(0, str(slot_data["stock"]["qty"]))

                purchase_qty_val = 1 
                item_offsets = self.all_data["master_item_prices"].get(item_name)
                if item_offsets:
                    try:
                        with open(self.exe_path, 'rb') as f:
                            f.seek(int(item_offsets[0], 16) + 4)
                            purchase_qty_val = struct.unpack('<H', f.read(2))[0]
                    except Exception:
                        purchase_qty_val = 1 
                purchase_qty_entry.insert(0, str(purchase_qty_val))
                
                ui_widgets.update({"item_entry": item_entry, "qty_entry": qty_entry, "purchase_qty_entry": purchase_qty_entry, "warning_label": warning_label})
                
                # --- NEW: Bind event and run initial check ---
                purchase_qty_entry.bind("<KeyRelease>", lambda event, w=ui_widgets: self._check_and_update_purchase_warning(w))
                self._check_and_update_purchase_warning(ui_widgets)

            if slot_data.get("upgrade"):
                upgrade_label = ctk.CTkLabel(slot_frame, text="Upgrades For:")
                upgrade_label.grid(row=1, column=2, padx=(20, 5), pady=5, sticky="w")
                upgrade_label.bind("<MouseWheel>", mousewheel_func)
                
                upgrade_display_frame = ctk.CTkFrame(slot_frame, fg_color="transparent"); upgrade_display_frame.grid(row=1, column=3, padx=5, pady=5, sticky="ew"); upgrade_display_frame.grid_columnconfigure(0, weight=1); upgrade_display_frame.bind("<MouseWheel>", mousewheel_func)
                upgrade_entry = ctk.CTkEntry(upgrade_display_frame, state="disabled"); upgrade_entry.grid(row=0, column=0, sticky="ew"); upgrade_entry.bind("<MouseWheel>", mousewheel_func)
                upgrade_button = ctk.CTkButton(upgrade_display_frame, text="...", width=30, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda widget=upgrade_entry: self.open_weapon_selector(widget)); upgrade_button.grid(row=0, column=1, padx=(5,0)); upgrade_button.bind("<MouseWheel>", mousewheel_func)

                weapon_name = self.weapon_id_to_name.get(slot_data["upgrade"]["id"], "None")
                upgrade_entry.configure(state="normal"); upgrade_entry.insert(0, weapon_name); upgrade_entry.configure(state="disabled")
                ui_widgets.update({"upgrade_entry": upgrade_entry})

                upgrades_frame = ctk.CTkFrame(slot_frame, fg_color="transparent"); upgrades_frame.grid(row=2, column=2, columnspan=2, rowspan=4, sticky="nsew", padx=(10, 0), pady=0) # rowspan increased to 4
                upgrades_frame.grid_columnconfigure((0,1,2,3), weight=1)
                upgrades_frame.bind("<MouseWheel>", mousewheel_func)

                stat_map = {'fp': 'FP', 'fs': 'FS', 'rs': 'RS', 'cap': 'Cap'}
                for col_idx, (stat_key, stat_label_text) in enumerate(stat_map.items()):
                    stat_header = ctk.CTkLabel(upgrades_frame, text=stat_label_text, font=ctk.CTkFont(weight="bold"))
                    stat_header.grid(row=0, column=col_idx, pady=(5,0))
                    stat_header.bind("<MouseWheel>", mousewheel_func)
                    
                    level_control_frame = ctk.CTkFrame(upgrades_frame, fg_color="transparent"); level_control_frame.grid(row=1, column=col_idx, padx=2, pady=0); level_control_frame.bind("<MouseWheel>", mousewheel_func)
                    level_label = ctk.CTkLabel(level_control_frame, text="-", width=40, anchor="center")
                    level_label.bind("<MouseWheel>", mousewheel_func)
                    
                    down_arrow = ctk.CTkButton(level_control_frame, text="▼", width=25, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda d=ui_widgets, s=stat_key: self._on_level_arrow_press(d, s, -1)); down_arrow.pack(side="left"); down_arrow.bind("<MouseWheel>", mousewheel_func)
                    level_label.pack(side="left"); up_arrow = ctk.CTkButton(level_control_frame, text="▲", width=25, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda d=ui_widgets, s=stat_key: self._on_level_arrow_press(d, s, 1)); up_arrow.pack(side="left"); up_arrow.bind("<MouseWheel>", mousewheel_func)
                    ui_widgets[f"{stat_key}_level_label"] = level_label
                    self._update_level_display(ui_widgets, stat_key)
            self.stock_widgets_data.append(ui_widgets)
        self.status_bar.configure(text=f"Successfully loaded inventory for {self.merchant_menu.get()}.")
        
    def _on_level_arrow_press(self, ui_widgets_dict, stat_key, direction):
        upgrade_data = ui_widgets_dict.get("data", {}).get("upgrade")
        if not upgrade_data: return
        current_level = upgrade_data.get(stat_key, 1)
        new_level = current_level + direction
        if 1 <= new_level <= 7:
            upgrade_data[stat_key] = new_level
            self._update_level_display(ui_widgets_dict, stat_key)
    
    def _update_level_display(self, ui_widgets_dict, stat_key):
        level_label = ui_widgets_dict.get(f"{stat_key}_level_label")
        upgrade_data = ui_widgets_dict.get("data", {}).get("upgrade")
        if not level_label or not upgrade_data: return
        current_level = upgrade_data.get(stat_key, 1)
        level_label.configure(text=f"Lvl: {current_level}")
    
    def read_raw_merchant_data(self, chapter_key):
        if not self.exe_path: return None
        chapter_info = self.all_data["merchant"][chapter_key]
        stock_offset = int(chapter_info["stock_offset"], 16)
        upgrades_offset = int(chapter_info["upgrades_offset"], 16)
        stock_slots = chapter_info.get("stock_slots", 0)
        upgrade_slots = chapter_info.get("upgrade_slots", 0)
        stock_list, upgrade_list = [], []
        try:
            with open(self.exe_path, 'rb') as f:
                if stock_offset > 0 and stock_slots > 0:
                    for i in range(stock_slots): 
                        f.seek(stock_offset + (i * 8))
                        item_id, qty, _ = struct.unpack('<HHI', f.read(8))
                        if item_id == 0xFFFF: break
                        stock_list.append({"id": item_id, "qty": qty})

                if upgrades_offset > 0 and upgrade_slots > 0:
                    for i in range(upgrade_slots): 
                        f.seek(upgrades_offset + (i * 8))
                        weapon_id, fp, fs, rs, cap, _ = struct.unpack('<HBBBBH', f.read(8))
                        if weapon_id == 0xFFFF: break
                        upgrade_list.append({"id": weapon_id, "fp": fp, "fs": fs, "rs": rs, "cap": cap})
            return stock_list, upgrade_list
        except Exception as e: 
            messagebox.showerror("Read Error", f"Could not read merchant data: {e}")
            return None

    def apply_merchant_changes(self, event=None):
        if not self.exe_path: return
        selected_display_name = self.merchant_menu.get()
        if selected_display_name == "-": return
        chapter_key = self.merchant_display_to_key[selected_display_name]
        chapter_info = self.all_data["merchant"][chapter_key]
        stock_offset = int(chapter_info["stock_offset"], 16)
        upgrades_offset = int(chapter_info["upgrades_offset"], 16)
        num_stock_slots = chapter_info.get("stock_slots", 0)
        num_upgrade_slots = chapter_info.get("upgrade_slots", 0)
        
        try:
            final_stock_map = {}
            final_upgrade_map = {}
            sacrifices_to_revert = {}
            purchase_qty_writes = {} # --- NEW: Dictionary to store purchase quantity changes
            
            current_sacrifices_in_exe = self._get_current_sacrifices_from_exe()

            desired_sacrifices = self.pending_sacrifices
            
            for ui_widgets in self.stock_widgets_data:
                slot_data = ui_widgets["data"]
                
                if "item_entry" in ui_widgets and slot_data["original_stock_index"] != -1:
                    item_name_from_ui = ui_widgets["item_entry"].get().split(" (via")[0]
                    item_id = self.item_name_to_id.get(item_name_from_ui, 0)
                    qty = int(ui_widgets["qty_entry"].get())
                    final_stock_map[slot_data["original_stock_index"]] = {"id": item_id, "qty": qty}
                    
                    # --- NEW: Get purchase quantity change ---
                    if "purchase_qty_entry" in ui_widgets:
                        real_item_name = self.item_id_to_name.get(item_id, None)
                        if real_item_name and real_item_name in self.all_data["master_item_prices"]:
                            new_pq = int(ui_widgets["purchase_qty_entry"].get())
                            purchase_qty_writes[real_item_name] = new_pq
                
                if "upgrade_entry" in ui_widgets and slot_data["original_upgrade_index"] != -1:
                    weapon_id = self.weapon_name_to_id.get(ui_widgets["upgrade_entry"].get(), 0)
                    final_upgrade_map[slot_data["original_upgrade_index"]] = {
                        "id": weapon_id,
                        "fp": slot_data["upgrade"]["fp"], "fs": slot_data["upgrade"]["fs"],
                        "rs": slot_data["upgrade"]["rs"], "cap": slot_data["upgrade"]["cap"]
                    }
            
            for item_name in current_sacrifices_in_exe:
                if item_name not in desired_sacrifices:
                    sacrifices_to_revert[item_name] = item_name
            
            sacrifices_to_make = desired_sacrifices

            with open(self.exe_path, 'rb+') as f:
                # --- NEW: Write purchase quantity changes first ---
                for item_name, new_pq_val in purchase_qty_writes.items():
                    pq_bytes = struct.pack('<H', new_pq_val)
                    offsets = self.all_data["master_item_prices"][item_name]
                    for offset_str in offsets:
                        f.seek(int(offset_str, 16) + 4)
                        f.write(pq_bytes)

                # --- Existing logic continues below ---
                for sacrificed_item, _ in sacrifices_to_revert.items():
                    original_id_bytes = struct.pack('<H', self.item_name_to_id[sacrificed_item])
                    offsets = self.all_data["master_item_prices"][sacrificed_item]
                    for offset_str in offsets:
                        f.seek(int(offset_str, 16))
                        f.write(original_id_bytes)
                
                for sacrificed_item, key_item in sacrifices_to_make.items():
                    key_item_id_bytes = struct.pack('<H', self.item_name_to_id[key_item])
                    offsets = self.all_data["master_item_prices"][sacrificed_item]
                    for offset_str in offsets:
                        f.seek(int(offset_str, 16))
                        f.write(key_item_id_bytes)

                if stock_offset > 0 and num_stock_slots > 0:
                    for i in range(num_stock_slots):
                        offset = stock_offset + (i * 8)
                        item = final_stock_map.get(i)
                        data = struct.pack('<HHI', item["id"], item["qty"], 0) if item else struct.pack('<HHI', 0xFFFF, 0, 0)
                        f.seek(offset); f.write(data)
                
                if upgrades_offset > 0 and num_upgrade_slots > 0:
                    for i in range(num_upgrade_slots):
                        offset = upgrades_offset + (i * 8)
                        item = final_upgrade_map.get(i)
                        data = struct.pack('<HBBBBH', item["id"], item["fp"], item["fs"], item["rs"], item["cap"], 0) if item else struct.pack('<HBBBBH', 0xFFFF, 0,0,0,0,0)
                        f.seek(offset); f.write(data)

            self.pending_sacrifices = self._get_current_sacrifices_from_exe()
            self.on_merchant_chapter_selected(selected_display_name)
            if self.price_editor_loaded: self._refresh_price_data_and_labels(read_exe=True)
            self._show_success_message(f"Applied inventory changes for {selected_display_name}!")

        except ValueError: messagebox.showerror("Invalid Input", "Please ensure all quantity values are valid integers.")
        except Exception as e: messagebox.showerror("Write Error", f"Could not apply changes to EXE: {e}")
        
    def _get_current_stack_size(self, item_name):
        """Gets the current max stack size for an item from the exe, returns 1 if not stackable."""
        if not self.exe_path: return 1
        offset = self.stacking_offsets.get(item_name)
        if offset:
            try:
                with open(self.exe_path, 'rb') as f:
                    f.seek(offset)
                    return struct.unpack('<h', f.read(2))[0]
            except Exception:
                return 1
        return 1 # Default for non-stackable items
        
    def _check_and_update_purchase_warning(self, ui_widgets):
        """Checks if purchase qty exceeds stack size and updates the warning label visibility."""
        if 'purchase_qty_entry' not in ui_widgets or 'warning_label' not in ui_widgets:
            return

        warning_label = ui_widgets['warning_label']
        try:
            item_name = ui_widgets['item_entry'].get().split(" (via")[0]
            purchase_qty = int(ui_widgets['purchase_qty_entry'].get())
            max_stack = self._get_current_stack_size(item_name)

            if purchase_qty > max_stack and max_stack > 0: # a max_stack of -1 is infinite
                warning_label.configure(text=f"⚠️ Warning: Purchase Qty ({purchase_qty}) exceeds max stack ({max_stack}). Adjust in 'Items Prices-Stacking' tab.")
                warning_label.grid()
            else:
                warning_label.grid_remove()
        except (ValueError, KeyError):
            warning_label.grid_remove() # Hide if entry is not a valid number or item not found    
    
    # --- END OF MERCHANT STOCK EDITOR SECTION ---
    
    # --- START OF STARTER INVENTORIES SECTION ---
    def _create_new_game_editor_tab(self, parent_frame):
        self.new_game_editor_placeholder_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.new_game_editor_placeholder_frame.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(self.new_game_editor_placeholder_frame, text="Starter Inventories", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.THEME_COLOR).pack(pady=(10, 20))
        ctk.CTkLabel(self.new_game_editor_placeholder_frame, text="This section allows you to edit starting inventories for different game modes.\n\nSelect an executable to load the editor.",
                     justify="center", wraplength=500).pack(pady=10)

    def _reset_all_inventories_from_backup(self):
        if not self.exe_path or not self.active_backup_path:
            messagebox.showwarning("Warning", "An executable and a backup file must be loaded.")
            return

        if not messagebox.askyesno("Confirm Full Reset", "Are you sure you want to restore ALL starter inventories from your backup file?\n\nThis will overwrite any unsaved changes in this tab."):
            return

        try:
            with open(self.active_backup_path, 'rb') as f_bak, open(self.exe_path, 'rb+') as f_exe:
                starter_data = self.all_data["game_mode_starters"]
                
                flag_offset_str = starter_data.get("difficulty_flag_offset")
                if flag_offset_str:
                    offset = int(flag_offset_str, 16)
                    f_bak.seek(offset)
                    original_byte = f_bak.read(1)
                    f_exe.seek(offset)
                    f_exe.write(original_byte)

                for mode_name, slots in starter_data.items():
                    if not isinstance(slots, list): continue
                    
                    for slot_info in slots:
                        offset = int(slot_info["id_offset"], 16)
                        f_bak.seek(offset)
                        original_byte = f_bak.read(1)
                        f_exe.seek(offset)
                        f_exe.write(original_byte)
                        
                        if slot_info.get("qty_offset"):
                            offset = int(slot_info["qty_offset"], 16)
                            f_bak.seek(offset)
                            original_byte = f_bak.read(1)
                            f_exe.seek(offset)
                            f_exe.write(original_byte)
            
            self.read_new_game_data()
            self._show_success_message("All starter inventories restored from backup!")
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not restore inventories from backup: {e}")
            
    def _build_new_game_editor_once(self):
        self.new_game_editor_placeholder_frame.destroy()
        new_game_tab = self.tabs["Starter Inventories"]
        new_game_tab.grid_rowconfigure(0, weight=1); new_game_tab.grid_columnconfigure(0, weight=1)
        main_frame = ctk.CTkFrame(new_game_tab)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1); main_frame.grid_columnconfigure(0, weight=1)
        self.starter_items_frame = ctk.CTkScrollableFrame(main_frame, label_text="Starter Inventories")
        self.starter_items_frame.grid(row=0, column=0, padx=10, pady=(0,10), sticky="nsew")
        self.starter_items_widgets = {}
        game_modes = [m for m in self.all_data.get("game_mode_starters", {}).keys() if m not in ["comment", "difficulty_flag_offset"]]
        mousewheel_func = lambda event: self._on_mousewheel(event, self.starter_items_frame)
        for mode_name in game_modes:
            self.starter_items_widgets[mode_name] = []
            div_frame = ctk.CTkFrame(self.starter_items_frame, fg_color=self.SECONDARY_COLOR); div_frame.bind("<MouseWheel>", mousewheel_func)
            div_frame.grid_columnconfigure(0, weight=1)
            div_label = ctk.CTkLabel(div_frame, text=mode_name, font=ctk.CTkFont(weight="bold")); div_label.bind("<MouseWheel>", mousewheel_func)
            div_label.grid(row=0, column=0, padx=10, pady=3, sticky="w")
            reset_button = ctk.CTkButton(div_frame, text="Reset Group from Backup ↺", width=180, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda m=mode_name: self.reset_new_game_data(m))
            reset_button.grid(row=0, column=1, padx=10, pady=3, sticky="e"); reset_button.bind("<MouseWheel>", mousewheel_func)
            self.starter_items_widgets[mode_name].append({"frame": div_frame, "is_divider": True, "reset_button": reset_button})
            if mode_name == "Story Mode":
                self.story_mode_options_frame = ctk.CTkFrame(self.starter_items_frame); self.story_mode_options_frame.bind("<MouseWheel>", mousewheel_func)
                ctk.CTkLabel(self.story_mode_options_frame, text="View Items For:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10,5), pady=10)
                self.difficulty_selector = ctk.CTkSegmentedButton(self.story_mode_options_frame, values=["Normal/Pro", "Easy"], command=self._update_new_game_display, selected_color=self.THEME_COLOR, selected_hover_color=self.THEME_COLOR_HOVER)
                self.difficulty_selector.pack(side="left", padx=5, pady=10); self.difficulty_selector.set("Normal/Pro")
                self.set_gag_inv_button = ctk.CTkButton(self.story_mode_options_frame, text="Set 'Gag' Inventory", command=self._set_gag_inventory, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
                self.set_gag_inv_button.pack(side="left", padx=15, pady=10)
                self.force_easy_inv_checkbox = ctk.CTkCheckBox(self.story_mode_options_frame, text="Force Easy Inventory on Prof/Normal", command=self._on_force_easy_inv_toggle)
                self.force_easy_inv_checkbox.pack(side="right", padx=10, pady=10)
            slots_for_mode = self.all_data["game_mode_starters"].get(mode_name, [])
            for slot_info in slots_for_mode: self._create_starter_item_row(self.starter_items_frame, slot_info, mode_name)
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        bottom_frame.grid_columnconfigure((0, 1), weight=1)
        self.reset_all_new_game_button = ctk.CTkButton(bottom_frame, text="Reset All From Backup ↺", state="disabled", command=self._reset_all_inventories_from_backup, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        self.reset_all_new_game_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.apply_new_game_button = ctk.CTkButton(bottom_frame, text="Apply All Changes", state="disabled", command=self.apply_new_game_data, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
        self.apply_new_game_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")
        self.new_game_editor_loaded = True
        if self.exe_path:
            self.apply_new_game_button.configure(state="normal")
            self.reset_all_new_game_button.configure(state="normal")
            self._update_reset_button_states()
            self.read_new_game_data()
        else:
            self._update_new_game_display()
            
    def _on_force_easy_inv_toggle(self):
        if self.is_loading_new_game_data: return
        if self.force_easy_inv_checkbox.get() == 1:
            if not messagebox.askokcancel("Confirm Feature", "Enable 'Force Easy Inventory'?\n\nThis will make Normal/Pro difficulties use the 'Easy' inventory slots."):
                self.force_easy_inv_checkbox.deselect()

    def _set_gag_inventory(self):
        gag_preset = { 
            "Attache Case": "Attache Case S", 
            "Slot 2: Healing Item (Normal/Pro)": "Treasure Box (L)", 
            "Slot 2: Healing Item (Easy)": "Treasure Box (L)", 
            "Slot 1: Weapon": "Chicken Egg", 
            "Slot 3: Ammo": "Treasure Box (S)" 
        }
        gag_qty_preset = { "Slot 3: Ammo": "20" }
        
        for widgets in self.starter_items_widgets.get("Story Mode", []):
            if widgets.get("is_divider"):
                continue
                
            slot_name = widgets["slot_info"]["name"]
            if slot_name in gag_preset:
                widgets["item_entry"].configure(state="normal"); widgets["item_entry"].delete(0, "end"); widgets["item_entry"].insert(0, gag_preset[slot_name]); widgets["item_entry"].configure(state="disabled")
            if slot_name in gag_qty_preset and widgets["qty_entry"] is not None:
                widgets["qty_entry"].delete(0, "end"); widgets["qty_entry"].insert(0, gag_qty_preset[slot_name])
                
        self.is_loading_new_game_data = True; self.force_easy_inv_checkbox.deselect(); self.is_loading_new_game_data = False
        self.status_bar.configure(text="Gag inventory preset applied. Click 'Apply Changes' to save.")
        
    def _create_starter_item_row(self, parent, slot_info, mode_name):
        frame = ctk.CTkFrame(parent)
        frame.grid_columnconfigure(1, weight=1)
        main_label = ctk.CTkLabel(frame, text=slot_info["name"] + ":", width=150, anchor="w")
        main_label.grid(row=0, column=0, padx=(10,5), pady=10)
        entry_item = ctk.CTkEntry(frame, state="disabled", placeholder_text="<Empty>"); entry_item.grid(row=0, column=1, sticky="ew", padx=5, pady=10)
        
        # THIS IS THE FIX: The lambda was incorrect. It now correctly passes the entry widget.
        button_item = ctk.CTkButton(frame, text="...", width=30, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda widget=entry_item: self._open_starter_item_selector(widget))
        
        button_item.grid(row=0, column=2, padx=(0,10), pady=10)
        entry_qty = None
        if slot_info.get("qty_offset"):
            ctk.CTkLabel(frame, text="Quantity:").grid(row=0, column=3, padx=(20,5), pady=10)
            entry_qty = ctk.CTkEntry(frame, width=80); entry_qty.grid(row=0, column=4, padx=(0,10), pady=10)
            entry_qty.bind("<KeyRelease>", lambda event: self._set_new_game_unsaved_status())
        widget_dict = {"frame": frame, "label": main_label, "item_entry": entry_item, "button": button_item, "qty_entry": entry_qty, "slot_info": slot_info}
        self.starter_items_widgets[mode_name].append(widget_dict)
        
    def _update_new_game_display(self, selected_difficulty=None):
        if not self.new_game_editor_loaded: return
        
        story_mode_difficulty = self.difficulty_selector.get() if hasattr(self, 'difficulty_selector') else "Normal/Pro"

        for widget_list in self.starter_items_widgets.values():
            for widgets in widget_list:
                widgets["frame"].pack_forget()
        if hasattr(self, 'story_mode_options_frame'):
            self.story_mode_options_frame.pack_forget()
        
        game_modes = [m for m in self.all_data.get("game_mode_starters", {}).keys() if m not in ["comment", "difficulty_flag_offset"]]
        
        for mode_name in game_modes:
            widget_list = self.starter_items_widgets.get(mode_name, [])
            
            for widgets in widget_list:
                if widgets.get("is_divider"):
                    widgets["frame"].pack(fill="x", padx=5, pady=(20, 5))
                    break
            
            if mode_name == "Story Mode" and hasattr(self, 'story_mode_options_frame'):
                self.story_mode_options_frame.pack(fill="x", padx=5, pady=5)

            for widgets in widget_list:
                if widgets.get("is_divider"):
                    continue

                frame = widgets["frame"]
                if mode_name == "Story Mode":
                    slot_difficulty = widgets["slot_info"]["difficulty"]
                    if slot_difficulty == "All" or slot_difficulty == story_mode_difficulty:
                        frame.pack(fill="x", padx=5, pady=5)
                else:
                    frame.pack(fill="x", padx=5, pady=5)

    def read_new_game_data(self):
        if not self.new_game_editor_loaded or not self.exe_path: return
        try:
            self.is_loading_new_game_data = True
            with open(self.exe_path, 'rb') as f:
                flag_offset = int(self.all_data["game_mode_starters"]["difficulty_flag_offset"], 16)
                f.seek(flag_offset)
                flag_val = struct.unpack('<B', f.read(1))[0]
                if flag_val == 0x06: self.force_easy_inv_checkbox.select()
                else: self.force_easy_inv_checkbox.deselect()

                for mode_name, widget_list in self.starter_items_widgets.items():
                    for widgets in widget_list:
                        if widgets.get("is_divider"): continue
                        slot_info = widgets["slot_info"]
                        f.seek(int(slot_info["id_offset"], 16))
                        item_id = struct.unpack('<B', f.read(1))[0]
                        item_name = self.item_id_to_name.get(item_id, "None")
                        widgets["item_entry"].configure(state="normal"); widgets["item_entry"].delete(0, "end"); widgets["item_entry"].insert(0, item_name); widgets["item_entry"].configure(state="disabled")
                        
                        if widgets["qty_entry"] is not None:
                            f.seek(int(slot_info["qty_offset"], 16))
                            qty = struct.unpack('<B', f.read(1))[0]
                            widgets["qty_entry"].delete(0, "end"); widgets["qty_entry"].insert(0, str(qty))

            self._update_new_game_display()
            self._update_stable_status()
        except Exception as e:
            messagebox.showerror("Read Error", f"Could not read New Game data: {e}")
        finally:
            self.is_loading_new_game_data = False
            
    def apply_new_game_data(self):
        if not self.exe_path: return
        try:
            with open(self.exe_path, 'rb+') as f:
                flag_offset = int(self.all_data["game_mode_starters"]["difficulty_flag_offset"], 16)
                flag_val = 0x06 if self.force_easy_inv_checkbox.get() == 1 else 0x03
                f.seek(flag_offset); f.write(struct.pack('<B', flag_val))
                for mode_name, widget_list in self.starter_items_widgets.items():
                    for widgets in widget_list:
                        if widgets.get("is_divider"): continue
                        is_active = widgets["button"].cget("state") == "normal"
                        if not is_active: continue
                        slot_info = widgets["slot_info"]
                        item_name = widgets["item_entry"].get() or "None"
                        item_id = self.item_name_to_id.get(item_name, 0xFF)
                        f.seek(int(slot_info["id_offset"], 16)); f.write(struct.pack('<B', item_id))
                        if widgets["qty_entry"] is not None:
                            qty = int(widgets["qty_entry"].get() or 0)
                            f.seek(int(slot_info["qty_offset"], 16)); f.write(struct.pack('<B', qty))
            
            self._show_success_message("Applied all starter inventory changes successfully!", callback=self.read_new_game_data)
        except ValueError: messagebox.showerror("Invalid Input", "Quantity must be a valid number.")
        except Exception as e: messagebox.showerror("Write Error", f"Could not apply New Game data changes: {e}")

    def reset_new_game_data(self, mode_name):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path):
            messagebox.showerror("Error", "Valid backup source not found.")
            return
        if not messagebox.askyesno("Confirm Reset", f"Are you sure you want to restore all {mode_name} starting items from your backup file?"):
            return
        try:
            with open(self.active_backup_path, 'rb') as f_bak, open(self.exe_path, 'rb+') as f_exe:
                if mode_name == "Story Mode":
                    flag_offset = int(self.all_data["game_mode_starters"]["difficulty_flag_offset"], 16)
                    f_bak.seek(flag_offset)
                    original_byte = f_bak.read(1)
                    f_exe.seek(flag_offset)
                    f_exe.write(original_byte)
                
                slots_to_reset = self.all_data["game_mode_starters"].get(mode_name, [])
                for slot_info in slots_to_reset:
                    offset = int(slot_info["id_offset"], 16)
                    f_bak.seek(offset)
                    original_byte = f_bak.read(1)
                    f_exe.seek(offset)
                    f_exe.write(original_byte)

                    if slot_info.get("qty_offset"):
                        offset = int(slot_info["qty_offset"], 16)
                        f_bak.seek(offset)
                        original_byte = f_bak.read(1)
                        f_exe.seek(offset)
                        f_exe.write(original_byte)

            self._show_success_message(f"Successfully reset {mode_name} data from backup.", callback=self.read_new_game_data)
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset New Game data from backup: {e}")
            
    # --- END OF STARTER INVENTORIES SECTION ---
    
    # --- START OF ITEMS PRICES-STACKING SECTION ---
    def _create_items_prices_stacking_tab(self, parent_frame):
        self.price_editor_placeholder_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.price_editor_placeholder_frame.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(self.price_editor_placeholder_frame, text="Items Prices-Stacking", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.THEME_COLOR).pack(pady=(10, 20))
        ctk.CTkLabel(self.price_editor_placeholder_frame, text="This section allows you to change the default price for items.\nSelect an executable to load the editor.",
                     justify="center", wraplength=400).pack(pady=10)

    def _on_sell_mode_toggle(self):
        self.sell_price_mode = "full" if self.sell_mode_switch.get() == 1 else "empty"
        for item_name, widget_info in self.price_editor_widgets.items():
            if not widget_info.get("is_divider"):
                self._on_any_price_entry_changed(item_name, widget_info["base_entry"])
    
    def _on_stacking_entry_changed(self, item_name, source_widget):
        if self.is_updating_stacking: return
        self.is_updating_stacking = True
        try:
            new_value = source_widget.get()
            group_name = self.stacking_group_map.get(item_name)
            if group_name:
                group_info = self.stacking_groups.get(group_name)
                if group_info:
                    for member_item_name in group_info["items"]:
                        if member_item_name == item_name: continue
                        widget_info = self.price_editor_widgets.get(member_item_name)
                        if widget_info and "stack_entry" in widget_info:
                            stack_entry = widget_info["stack_entry"]
                            if stack_entry.get() != new_value:
                                stack_entry.delete(0, "end")
                                stack_entry.insert(0, new_value)
        finally:
            self.is_updating_stacking = False
    
    def _on_any_price_entry_changed(self, item_name, source_widget):
        if self.is_updating_prices: return
        self.is_updating_prices = True

        widget_info = self.price_editor_widgets.get(item_name)
        if not widget_info: 
            self.is_updating_prices = False
            return
        
        buy_entry, base_entry, sell_entry = widget_info["buy_entry"], widget_info["base_entry"], widget_info["sell_entry"]
        is_weapon = item_name in self.weapon_ammo_map
        is_treasure = item_name in self.treasure_items

        try:
            new_base = 0
            if is_weapon:
                ammo_value = widget_info["capacity"] * widget_info["ammo_cost_per_bullet"]
                if source_widget == buy_entry:
                    new_base = int(buy_entry.get()) - ammo_value
                elif source_widget == sell_entry:
                    sell_ammo_value = ammo_value if self.sell_price_mode == "full" else 0
                    # Corrected logic: Recalculate total value before dividing
                    total_value = int(sell_entry.get()) * 2
                    new_base = total_value - sell_ammo_value
                else: # source_widget is base_entry
                    new_base = int(base_entry.get())
            else: # Not a weapon
                if source_widget == buy_entry:
                    new_base = int(buy_entry.get())
                elif source_widget == sell_entry:
                    new_base = int(sell_entry.get()) * 2 if not is_treasure else int(sell_entry.get())
                else: # source_widget is base_entry
                    new_base = int(base_entry.get())

            # --- START OF THE CORRECTED CALCULATION BLOCK ---
            
            # 1. Calculate the final buy price
            buy_price = new_base
            if is_weapon:
                buy_price += widget_info["capacity"] * widget_info["ammo_cost_per_bullet"]

            # 2. Calculate the final sell price based on total value
            total_value_for_sell = new_base
            if is_weapon and self.sell_price_mode == "full":
                total_value_for_sell += widget_info["capacity"] * widget_info["ammo_cost_per_bullet"]
            
            sell_price = total_value_for_sell // 2 if not is_treasure else total_value_for_sell

            # --- END OF THE CORRECTED CALCULATION BLOCK ---

            if source_widget != base_entry:
                base_entry.delete(0, "end"); base_entry.insert(0, str(new_base))
            if source_widget != buy_entry:
                buy_entry.delete(0, "end"); buy_entry.insert(0, str(buy_price))
            if source_widget != sell_entry:
                sell_entry.delete(0, "end"); sell_entry.insert(0, str(sell_price))
            
            if item_name in self.ammo_weapon_map:
                new_ammo_price = int(base_entry.get())
                for weapon_user in self.ammo_weapon_map[item_name]:
                    if weapon_user in self.price_editor_widgets:
                        weapon_widget_info = self.price_editor_widgets[weapon_user]
                        weapon_widget_info["ammo_cost_per_bullet"] = new_ammo_price
                        self._on_any_price_entry_changed(weapon_user, weapon_widget_info["base_entry"])
        except (ValueError, TypeError):
            pass
        finally:
            self.is_updating_prices = False
            
    def get_weapon_lvl1_capacity(self, weapon_name):
        if not self.exe_path: return 0
        weapon_data = self.all_data["weapons"].get(weapon_name, {}); cap_offset_str = weapon_data.get("capacity_base_offset")
        if not cap_offset_str: return 0
        try:
            lvl1_cap_offset = int(cap_offset_str, 16) + 8
            with open(self.exe_path, 'rb') as f: f.seek(lvl1_cap_offset); return struct.unpack('<H', f.read(2))[0]
        except Exception: return 0
    
    def get_weapon_ammo_type(self, weapon_name):
        if not self.exe_path: return None
        weapon_info = self.all_data.get("weapons", {}).get(weapon_name, {})
        base_offset_str = weapon_info.get("capacity_base_offset")
        if not base_offset_str: return None
        try:
            ammo_offset = int(base_offset_str, 16) + 6
            with open(self.exe_path, 'rb') as f:
                f.seek(ammo_offset)
                ammo_id = struct.unpack('<H', f.read(2))[0]
                return self.item_id_to_name.get(ammo_id)
        except Exception:
            return None

    def _build_price_editor_once(self):
        self.price_editor_placeholder_frame.destroy()
        price_tab_container = self.tabs["Items Prices-Stacking"]
        price_tab_container.grid_rowconfigure(1, weight=1)
        price_tab_container.grid_columnconfigure(0, weight=1)

        top_controls = ctk.CTkFrame(price_tab_container, fg_color="transparent")
        top_controls.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        top_controls.grid_columnconfigure(0, weight=1) 
        
        # --- MODIFIED LOGIC ---
        self.price_search_entry = ctk.CTkEntry(top_controls, placeholder_text="Search by Name or ID...")
        self.price_search_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.price_search_entry.bind("<KeyRelease>", lambda e: self._update_price_display())
        
        self.ammo_stack_view_switch = ctk.CTkSwitch(top_controls, text="Stacking View", onvalue=1, offvalue=0, command=lambda: self._update_price_display(), progress_color=self.THEME_COLOR)
        self.ammo_stack_view_switch.grid(row=0, column=1, padx=(0,10))
        
        ctk.CTkLabel(top_controls, text="Ammo Sort:").grid(row=0, column=2, padx=(10,5))
        self.ammo_sort_switch = ctk.CTkSwitch(top_controls, text="Grouped", onvalue=0, offvalue=1, command=self._on_ammo_sort_toggle, progress_color=self.THEME_COLOR)
        self.ammo_sort_switch.grid(row=0, column=3, padx=(0,20))
        self.ammo_sort_switch.select(0)
        ctk.CTkLabel(top_controls, text="Sell with Empty Clip:").grid(row=0, column=4, padx=(10, 5))
        self.sell_mode_switch = ctk.CTkSwitch(top_controls, text="Full Clip", onvalue=1, offvalue=0, command=self._on_sell_mode_toggle, progress_color=self.THEME_COLOR)
        self.sell_mode_switch.grid(row=0, column=5)
        self.sell_mode_switch.select()
        
        self.price_editor_frame = ctk.CTkScrollableFrame(price_tab_container)
        self.price_editor_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
        self.price_editor_frame.grid_columnconfigure(0, weight=2, minsize=250)
        self.price_editor_frame.grid_columnconfigure((1,2,3,4), weight=1, minsize=120)

        bottom_frame = ctk.CTkFrame(price_tab_container)
        bottom_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        self.reset_all_prices_button = ctk.CTkButton(bottom_frame, text="Reset from Backup", state="disabled", command=self.reset_all_stock_prices, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        self.reset_all_prices_button.pack(side="left", padx=(10,5), pady=10, expand=True, fill="x")
        apply_changes_button = ctk.CTkButton(bottom_frame, text="Apply All Changes", command=self.apply_all_changes, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
        apply_changes_button.pack(side="left", padx=(5,10), pady=10, expand=True, fill="x")
        self.price_editor_loaded = True

        try:
            self.header_widgets = {
                "name": ctk.CTkLabel(self.price_editor_frame, text="Item Name", font=ctk.CTkFont(weight="bold"), anchor="w"),
                "stack": ctk.CTkLabel(self.price_editor_frame, text="Item Stacking", font=ctk.CTkFont(weight="bold"), anchor="center"),
                "buy": ctk.CTkLabel(self.price_editor_frame, text="Buy Price (In-Game)", font=ctk.CTkFont(weight="bold"), anchor="center"),
                "base": ctk.CTkLabel(self.price_editor_frame, text="Base Price (EXE)", font=ctk.CTkFont(weight="bold"), anchor="center"),
                "sell": ctk.CTkLabel(self.price_editor_frame, text="Sell Price", font=ctk.CTkFont(weight="bold"), anchor="center"),
            }

            with open(self.exe_path, 'rb') as f:
                for item_name, offsets in self.all_data["master_item_prices"].items():
                    if offsets: f.seek(int(offsets[0], 16) + 2); self.base_prices[item_name] = struct.unpack('<H', f.read(2))[0] * 10
            
            all_items_in_order = set(self.sorted_list_ammo_grouped + self.sorted_list_ammo_categorized)
            for item_name in all_items_in_order:
                mousewheel_func = lambda event, frame=self.price_editor_frame: self._on_mousewheel(event, frame)

                if item_name.startswith("---"):
                    div_frame = ctk.CTkFrame(self.price_editor_frame, fg_color=self.SECONDARY_COLOR)
                    div_frame.bind("<MouseWheel>", mousewheel_func)
                    div_frame.grid_columnconfigure(0, weight=1)
                    
                    div_label = ctk.CTkLabel(div_frame, text=item_name.strip("- "), font=ctk.CTkFont(weight="bold"))
                    div_label.grid(row=0, column=0, padx=10, pady=3, sticky="w")
                    div_label.bind("<MouseWheel>", mousewheel_func)
                    
                    reset_button = ctk.CTkButton(div_frame, text="Reset Group ↺", width=120, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda cat=item_name: self.reset_price_group(cat), state="disabled")
                    reset_button.grid(row=0, column=1, padx=10, pady=3, sticky="e")
                    reset_button.bind("<MouseWheel>", mousewheel_func)
                    self.price_editor_widgets[item_name] = {"frame": div_frame, "is_divider": True, "reset_button": reset_button}
                    continue
                
                original_base_price = self.base_prices.get(item_name, 0)
                is_weapon = item_name in self.weapon_ammo_map
                
                label = ctk.CTkLabel(self.price_editor_frame, text=item_name, anchor="w")
                stack_entry = ctk.CTkEntry(self.price_editor_frame)
                
                if item_name in self.stacking_offsets:
                    with open(self.exe_path, 'rb') as f:
                        offset = self.stacking_offsets[item_name]
                        f.seek(offset)
                        val = struct.unpack('<h', f.read(2))[0]
                        stack_entry.insert(0, str(val))
                    stack_entry.bind("<KeyRelease>", lambda e, n=item_name, w=stack_entry: self._on_stacking_entry_changed(n, w))
                else:
                    stack_entry.insert(0, "N/A")
                    stack_entry.configure(state="disabled")
                
                buy_entry = ctk.CTkEntry(self.price_editor_frame)
                base_entry = ctk.CTkEntry(self.price_editor_frame)
                sell_entry = ctk.CTkEntry(self.price_editor_frame)
                
                for widget in [label, stack_entry, buy_entry, base_entry, sell_entry]:
                    widget.bind("<MouseWheel>", mousewheel_func)

                widget_data = {
                    "label": label, "stack_entry": stack_entry, "buy_entry": buy_entry,
                    "base_entry": base_entry, "sell_entry": sell_entry,
                    "original_price": original_base_price
                }
                
                if is_weapon:
                    capacity = self.get_weapon_lvl1_capacity(item_name)
                    ammo_name = self.get_weapon_ammo_type(item_name)
                    ammo_cost = self.base_prices.get(ammo_name, 0)
                    widget_data.update({"capacity": capacity, "ammo_cost_per_bullet": ammo_cost})

                buy_entry.bind("<KeyRelease>", lambda e, n=item_name, w=buy_entry: self._on_any_price_entry_changed(n, w))
                base_entry.bind("<KeyRelease>", lambda e, n=item_name, w=base_entry: self._on_any_price_entry_changed(n, w))
                sell_entry.bind("<KeyRelease>", lambda e, n=item_name, w=sell_entry: self._on_any_price_entry_changed(n, w))

                base_entry.insert(0, str(original_base_price))
                self.price_editor_widgets[item_name] = widget_data
                self._on_any_price_entry_changed(item_name, base_entry) # Trigger initial calculation
                
            self._on_ammo_sort_toggle()
            self._update_reset_button_states()
            self.status_bar.configure(text="Master price list loaded successfully.")
            self._refresh_price_data_and_labels()

        except Exception as e: messagebox.showerror("Read Error", f"Could not build master price list: {e}")
        
    def _on_ammo_sort_toggle(self, *args):
        self.ammo_sort_is_grouped = self.ammo_sort_switch.get() == 0
        if self.ammo_sort_is_grouped:
            self.sorted_price_item_list = self.sorted_list_ammo_grouped
            self.ammo_sort_switch.configure(text="Grouped")
        else:
            self.sorted_price_item_list = self.sorted_list_ammo_categorized
            self.ammo_sort_switch.configure(text="Categorized")
        self._update_price_display()

    def _update_price_display(self):
        for widget_info in self.price_editor_widgets.values():
            if widget_info.get("is_divider"):
                widget_info["frame"].grid_remove()
            else:
                for widget in widget_info.values():
                    if isinstance(widget, ctk.CTkBaseClass):
                        widget.grid_remove()
        
        for widget in self.header_widgets.values():
            widget.grid_remove()

        self.header_widgets["name"].grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.header_widgets["stack"].grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.header_widgets["buy"].grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        self.header_widgets["base"].grid(row=0, column=3, padx=10, pady=5, sticky="ew")
        self.header_widgets["sell"].grid(row=0, column=4, padx=10, pady=5, sticky="ew")

        # --- THIS IS THE FIX ---
        # Get the query directly from the entry widget, not the deleted variable.
        query = self.price_search_entry.get().lower()
        
        is_stack_view = self.ammo_stack_view_switch.get() == 1
        
        items_to_process = self.sorted_price_item_list
        if is_stack_view:
            items_to_process = [item for item in items_to_process if item in self.stackable_items_set or item.startswith("---")]
            
        # --- MODIFIED SEARCH LOGIC ---
        visible_items = []
        for item_name in items_to_process:
            if item_name.startswith("---"):
                visible_items.append(item_name)
                continue

            item_id = self.item_name_to_id.get(item_name)
            is_match = False
            if query in item_name.lower():
                is_match = True
            elif item_id is not None:
                if query == str(item_id) or query == hex(item_id)[2:].lower():
                    is_match = True
            
            if is_match:
                visible_items.append(item_name)
        
        visible_dividers = {}
        current_divider = None
        for item in visible_items:
            if item.startswith("---"):
                current_divider = item
                visible_dividers[current_divider] = False
            elif current_divider and not item.startswith("---"):
                visible_dividers[current_divider] = True

        row_index = 1
        for item_name in self.sorted_price_item_list:
            if is_stack_view and not (item_name in self.stackable_items_set or item_name.startswith("---")):
                continue
        
            widget_info = self.price_editor_widgets.get(item_name)
            if not widget_info: continue

            if widget_info.get("is_divider"):
                if visible_dividers.get(item_name, False):
                    widget_info["frame"].grid(row=row_index, column=0, columnspan=5, sticky="ew", pady=(10, 2), padx=5)
                    row_index += 1
            elif item_name in visible_items: # Check if the item passed the filter
                widget_info["label"].grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
                widget_info["stack_entry"].grid(row=row_index, column=1, padx=10, pady=5, sticky="ew")
                widget_info["buy_entry"].grid(row=row_index, column=2, padx=10, pady=5, sticky="ew")
                widget_info["base_entry"].grid(row=row_index, column=3, padx=10, pady=5, sticky="ew")
                widget_info["sell_entry"].grid(row=row_index, column=4, padx=10, pady=5, sticky="ew")
                row_index += 1
        self.price_editor_frame._parent_canvas.yview_moveto(0)
        
    def _update_item_type_display(self, event=None):
        # FIX: Get text directly from the item_type_search_entry widget
        query = self.item_type_search_entry.get().lower()
        
        # --- MODIFIED SEARCH LOGIC ---
        visible_items = set()
        for item_name in self.item_type_widgets:
            if self.item_type_widgets[item_name].get("is_divider"):
                continue
            
            item_id = self.item_name_to_id.get(item_name)
            is_match = False
            # Check 1: Name match
            if query in item_name.lower():
                is_match = True
            # Check 2 & 3: ID match (if ID exists)
            elif item_id is not None:
                if query == str(item_id) or query == hex(item_id)[2:].lower():
                    is_match = True
            
            if is_match:
                visible_items.add(item_name)

        # Now, iterate through the UI structure to show/hide elements
        row_index = 0
        for cat_name, cat_items in self.all_data["items"]["categories"].items():
            divider_key = f"---{cat_name}---"
            
            # Check if any item in this category is visible
            is_category_visible = any(item in visible_items for item in cat_items)
            
            if is_category_visible:
                # Show the divider
                self.item_type_widgets[divider_key]["frame"].grid(row=row_index, column=0, columnspan=2, sticky="ew", pady=(10, 2), padx=5)
                row_index += 1
                
                # Show the visible items within this category
                for item_name in sorted(cat_items):
                    if item_name in visible_items:
                        widgets = self.item_type_widgets[item_name]
                        widgets["label"].grid(row=row_index, column=0, sticky="ew", padx=10, pady=2)
                        widgets["dropdown"].grid(row=row_index, column=1, sticky="ew", padx=10, pady=2)
                        row_index += 1
            else:
                 # Hide the divider and all its items
                 self.item_type_widgets[divider_key]["frame"].grid_remove()
                 for item_name in cat_items:
                     if item_name in self.item_type_widgets:
                         self.item_type_widgets[item_name]["label"].grid_remove()
                         self.item_type_widgets[item_name]["dropdown"].grid_remove()
        
        # Reset scroll position
        self.item_type_frame._parent_canvas.yview_moveto(0)
        
    def _update_item_size_display(self, event=None):
        # FIX: Get text directly from the item_size_search_entry widget
        query = self.item_size_search_entry.get().lower()
        row_index = 0
        for item_name in self.sorted_sizable_items:
            widgets = self.item_size_widgets[item_name]
            
            item_id = self.item_name_to_id.get(item_name)
            is_match = False
            # Check 1: Name match
            if query in item_name.lower():
                is_match = True
            # Check 2 & 3: ID match
            elif item_id is not None:
                if query == str(item_id) or query == hex(item_id)[2:].lower():
                    is_match = True

            if is_match:
                widgets["label"].grid(row=row_index, column=0, sticky="ew", padx=10, pady=2)
                widgets["size_frame"].grid(row=row_index, column=1, sticky="w", padx=10, pady=2)
                row_index += 1
            else:
                widgets["label"].grid_remove()
                widgets["size_frame"].grid_remove()
        
        # Reset scroll position
        self.item_size_frame._parent_canvas.yview_moveto(0)
        
    def apply_all_changes(self):
        if not self.exe_path: return

        price_changes_made = False
        stacking_changes_made = False
        items_to_update = []
        try:
            for item_name, widget_info in self.price_editor_widgets.items():
                if widget_info.get("is_divider"): continue
                entry = widget_info["base_entry"]
                if entry.cget("state") == "disabled": continue
                
                price_val = int(entry.get())
                if not (0 <= price_val <= 655350):
                    messagebox.showerror("Invalid Price", f"A price must be between 0 and 655,350.\n\nPlease correct: {item_name}")
                    return
                
                original_price = widget_info["original_price"]
                current_price = int(entry.get())
                if current_price != original_price:
                    raw_price = current_price // 10
                    price_bytes = struct.pack('<H', raw_price)
                    items_to_update.append({"name": item_name, "bytes": price_bytes, "offsets": self.all_data["master_item_prices"][item_name]})
            
            if items_to_update:
                price_changes_made = True
                with open(self.exe_path, 'rb+') as f:
                    for item in items_to_update:
                        widget_info = self.price_editor_widgets[item["name"]]
                        for offset_str in item["offsets"]: f.seek(int(offset_str, 16) + 2); f.write(item["bytes"])
                        self.base_prices[item["name"]] = int(widget_info["base_entry"].get())

        except ValueError: messagebox.showerror("Invalid Input", "One or more prices are not valid integers."); return
        except KeyError as e: messagebox.showerror("Write Error", f"Could not apply price changes: Item key not found '{e}'"); return
        except Exception as e: messagebox.showerror("Write Error", f"Could not apply price changes: {e}"); return
        
        offsets_to_write = {}
        try:
            with open(self.exe_path, 'rb') as f:
                original_stack_values = {}
                for item_name, offset in self.stacking_offsets.items():
                    f.seek(offset)
                    original_stack_values[item_name] = struct.unpack('<h', f.read(2))[0]

            for item_name, widget_info in self.price_editor_widgets.items():
                if widget_info.get("is_divider") or "stack_entry" not in widget_info: continue
                stack_entry = widget_info["stack_entry"]
                if stack_entry.cget("state") == "disabled": continue
                
                stack_val = int(stack_entry.get())
                if not (-32768 <= stack_val <= 32767):
                    messagebox.showerror("Invalid Stack Size", f"Stack size must be between -32,768 and 32,767.\n\nPlease correct: {item_name}")
                    return

                if stack_val != original_stack_values.get(item_name):
                    offset = self.stacking_offsets.get(item_name)
                    if offset: offsets_to_write[offset] = stack_val

            if offsets_to_write:
                stacking_changes_made = True
                with open(self.exe_path, 'rb+') as f:
                    for offset, value in offsets_to_write.items():
                        f.seek(offset)
                        f.write(struct.pack('<h', value))

        except ValueError: messagebox.showerror("Invalid Input", "One or more stack sizes are not valid integers."); return
        except Exception as e: messagebox.showerror("Write Error", f"Could not apply stacking changes: {e}"); return

        if price_changes_made or stacking_changes_made:
            num_changes = len(items_to_update) + len(offsets_to_write)
            self._refresh_price_data_and_labels(read_exe=True)
            self._show_success_message(f"Applied {num_changes} change(s) successfully!")
        else:
            self.status_bar.configure(text="No changes to apply.")
            
    def _refresh_price_data_and_labels(self, read_exe=False):
        if not self.price_editor_loaded or not self.exe_path: return
        try:
            all_price_widget_keys = list(self.price_editor_widgets.keys())
            for item_name in all_price_widget_keys:
                widget_info = self.price_editor_widgets.get(item_name)
                if widget_info and not widget_info.get("is_divider"):
                    widget_info["label"].configure(text=item_name, text_color=self.default_status_color)

            current_sacrifices = self.pending_sacrifices
            
            for sacrificed_item, key_item in current_sacrifices.items():
                if sacrificed_item in self.price_editor_widgets:
                    widget_info = self.price_editor_widgets[sacrificed_item]
                    widget_info["label"].configure(text=f"{key_item} (via {sacrificed_item})", text_color=self.SACRIFICE_COLOR)

            if read_exe:
                with open(self.exe_path, 'rb') as f:
                    for item_name, offsets in self.all_data["master_item_prices"].items():
                        if offsets:
                            f.seek(int(offsets[0], 16) + 2)
                            self.base_prices[item_name] = struct.unpack('<H', f.read(2))[0] * 10
                
                for item_name, widget_info in self.price_editor_widgets.items():
                    if widget_info.get("is_divider"): continue
                    
                    if "stack_entry" in widget_info and widget_info["stack_entry"].cget("state") != "disabled":
                        with open(self.exe_path, 'rb') as f:
                            offset = self.stacking_offsets.get(item_name)
                            if offset:
                                f.seek(offset)
                                val = struct.unpack('<h', f.read(2))[0]
                                widget_info["stack_entry"].delete(0, "end"); widget_info["stack_entry"].insert(0, str(val))
                    
                    new_base_price = self.base_prices.get(item_name, 0)
                    widget_info["original_price"] = new_base_price
                    
                    base_entry = widget_info["base_entry"]
                    base_entry.delete(0, "end"); base_entry.insert(0, str(new_base_price))

                    if item_name in self.weapon_ammo_map:
                         widget_info["capacity"] = self.get_weapon_lvl1_capacity(item_name)
                         ammo_name = self.get_weapon_ammo_type(item_name)
                         widget_info["ammo_cost_per_bullet"] = self.base_prices.get(ammo_name, 0)

                    self._on_any_price_entry_changed(item_name, base_entry)

                self.status_bar.configure(text="Prices and stacking refreshed from EXE.")
            else:
                self.status_bar.configure(text="Price editor synchronized with pending changes.")

        except Exception as e:
            messagebox.showerror("Refresh Error", f"Could not refresh data: {e}")
    # --- END OF ITEMS PRICES-STACKING SECTION ---

    # --- START OF UPGRADE PRICES EDITOR SECTION ---
    def _create_upgrade_prices_editor_tab(self, parent_frame):
        self.upgrade_editor_placeholder_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.upgrade_editor_placeholder_frame.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(self.upgrade_editor_placeholder_frame, text="Upgrades Prices Editor", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.THEME_COLOR).pack(pady=(10, 20))
        ctk.CTkLabel(self.upgrade_editor_placeholder_frame, text="This section allows you to change the price for weapon upgrades.\nSelect an executable to load the editor.",
                     justify="center", wraplength=400).pack(pady=10)

    def _get_max_levels_from_exe(self, weapon_name):
        if not self.exe_path: return None, None, None, None
        weapon_info = self.all_data["weapons"].get(weapon_name, {})
        offsets = weapon_info.get("max_levels_offsets")
        if not offsets: return 1, 1, 1, 1
        try:
            with open(self.exe_path, 'rb') as f:
                first_offset = int(offsets[0], 16)
                f.seek(first_offset)
                if weapon_name == "Matilda": f.read(2)
                data_bytes = f.read(4)
                return struct.unpack('<BBBB', data_bytes)
        except Exception:
            return 1, 1, 1, 1

    def _build_upgrade_editor_once(self):
        self.upgrade_editor_placeholder_frame.destroy()
        upgrade_tab = self.tabs["Upgrades Prices Editor"]
        upgrade_tab.grid_rowconfigure(1, weight=1)
        upgrade_tab.grid_columnconfigure(0, weight=1)

        top_controls = ctk.CTkFrame(upgrade_tab)
        top_controls.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        top_controls.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(top_controls, text="Select Weapon:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(10,5), pady=10)
        
        upgrade_weapon_selector_display_frame = ctk.CTkFrame(top_controls, fg_color="transparent")
        upgrade_weapon_selector_display_frame.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        upgrade_weapon_selector_display_frame.grid_columnconfigure(0, weight=1)
        
        self.upgrade_weapon_entry = ctk.CTkEntry(upgrade_weapon_selector_display_frame, state="disabled", placeholder_text="-")
        self.upgrade_weapon_entry.grid(row=0, column=0, sticky="ew")
        
        button_state = "normal" if self.exe_path else "disabled"
        self.upgrade_weapon_button = ctk.CTkButton(upgrade_weapon_selector_display_frame, text="...", width=30, state=button_state, command=self.open_upgrade_weapon_selector, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
        self.upgrade_weapon_button.grid(row=0, column=1, padx=(5,0))

        self.reset_upgrades_button = ctk.CTkButton(top_controls, text="Reset Selected", state="disabled", command=self.reset_upgrade_prices, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        self.reset_upgrades_button.grid(row=0, column=2, padx=(20, 10), pady=10, sticky="e")

        self.upgrade_prices_frame = ctk.CTkScrollableFrame(upgrade_tab, label_text="Upgrade Prices")
        self.upgrade_prices_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        bottom_frame = ctk.CTkFrame(upgrade_tab)
        bottom_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure((0, 1), weight=1)
        self.reset_all_upgrades_button = ctk.CTkButton(bottom_frame, text="Reset ALL Upgrade Prices", state="disabled", command=self.reset_all_upgrade_prices, fg_color="#C75450", hover_color="#A34440")
        self.reset_all_upgrades_button.grid(row=0, column=0, padx=(10,5), pady=10, sticky="ew")
        self.apply_upgrades_button = ctk.CTkButton(bottom_frame, text="Apply Price Changes", state="disabled", command=self.apply_upgrade_prices, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
        self.apply_upgrades_button.grid(row=0, column=1, padx=(5,10), pady=10, sticky="ew")
        
        self.upgrade_editor_loaded = True

    def _on_upgrade_weapon_selected(self, weapon_name):
        for widget in self.upgrade_prices_frame.winfo_children():
            widget.destroy()
        self.upgrade_price_widgets = {}

        if self.upgrade_editor_loaded:
            self._update_reset_button_states()

        if weapon_name == "-" or weapon_name not in self.all_data["upgrade_prices"]:
            self.last_selected_upgrade_weapon = "-"
            self.upgrade_weapon_entry.configure(state="normal"); self.upgrade_weapon_entry.delete(0, "end"); self.upgrade_weapon_entry.insert(0, "-"); self.upgrade_weapon_entry.configure(state="disabled")
            self.apply_upgrades_button.configure(state="disabled")
            if hasattr(self, 'reset_upgrades_button'): self.reset_upgrades_button.configure(state="disabled")
            self.status_bar.configure(text="Select a weapon to view its upgrade prices.")
            return
        
        self.last_selected_upgrade_weapon = weapon_name
        self.upgrade_weapon_entry.configure(state="normal"); self.upgrade_weapon_entry.delete(0, "end"); self.upgrade_weapon_entry.insert(0, weapon_name); self.upgrade_weapon_entry.configure(state="disabled")
            
        self.apply_upgrades_button.configure(state="normal")
        self.read_upgrade_prices()

    def _build_upgrade_price_frame(self, parent, structure_tuple, file_handle, exclusive_fp_index, scroll_frame, is_shared_mode=False):
        key, num_levels, label = structure_tuple
        mousewheel_func = lambda event: self._on_mousewheel(event, scroll_frame)
        
        frame = ctk.CTkFrame(parent, border_width=1, border_color="gray25"); frame.bind("<MouseWheel>", mousewheel_func)
        header_label = ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR); header_label.pack(pady=(5,10)); header_label.bind("<MouseWheel>", mousewheel_func)
        
        grid_frame = ctk.CTkFrame(frame, fg_color="transparent"); grid_frame.pack(fill="x", padx=10, pady=5); grid_frame.bind("<MouseWheel>", mousewheel_func)
        
        if key not in self.upgrade_price_widgets:
            self.upgrade_price_widgets[key] = []
            
        for i in range(num_levels):
            price = struct.unpack('<H', file_handle.read(2))[0] * 10
            
            row, col = divmod(i, 2)
            
            sub_frame = ctk.CTkFrame(grid_frame, fg_color="transparent"); sub_frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew"); sub_frame.bind("<MouseWheel>", mousewheel_func)
            grid_frame.grid_columnconfigure(col, weight=1)

            is_exclusive_slot = (key == 'fp' and i == exclusive_fp_index)
            is_cap_lvl7_slot = (key == 'cap' and i == 5) # Lvl 7 is the 6th item (index 5)
            is_obsolete = (key == 'fp' and i > exclusive_fp_index)
            
            if is_exclusive_slot and is_shared_mode:
                sub_frame.grid_columnconfigure((1, 3), weight=1)
                
                base_label = ctk.CTkLabel(sub_frame, text="Exclusive (EXE):", text_color=self.EXCLUSIVE_COLOR); base_label.grid(row=0, column=0, padx=(0,5))
                base_entry = ctk.CTkEntry(sub_frame); base_entry.grid(row=0, column=1, sticky="ew")
                base_entry.insert(0, str(price))
                
                ingame_label = ctk.CTkLabel(sub_frame, text="In-Game:", text_color=self.EXCLUSIVE_COLOR); ingame_label.grid(row=0, column=2, padx=(10,5))
                ingame_entry = ctk.CTkEntry(sub_frame); ingame_entry.grid(row=0, column=3, sticky="ew")
                
                self.exclusive_fp_base_entry = base_entry
                self.exclusive_fp_ingame_entry = ingame_entry
                
                base_entry.bind("<KeyRelease>", lambda e, w=base_entry: self._update_exclusive_fp_prices(w))
                ingame_entry.bind("<KeyRelease>", lambda e, w=ingame_entry: self._update_exclusive_fp_prices(w))
                
                self.upgrade_price_widgets[key].append(base_entry)
            else:
                label_text = f"Lvl {i+2} Price:"
                text_color = "default"
                if is_exclusive_slot:
                    label_text = f"Exclusive (Lvl {i+2}):"
                    text_color = self.EXCLUSIVE_COLOR

                price_label = ctk.CTkLabel(sub_frame, text=label_text); price_label.bind("<MouseWheel>", mousewheel_func)
                if text_color != "default":
                    price_label.configure(text_color=text_color)
                price_label.pack(side="left", padx=(0,5))
                
                entry = ctk.CTkEntry(sub_frame); entry.bind("<MouseWheel>", mousewheel_func)
                entry.insert(0, str(price))
                if is_obsolete:
                    entry.configure(state="disabled")
                entry.pack(side="left", fill="x", expand=True)
                self.upgrade_price_widgets[key].append(entry)

                if is_cap_lvl7_slot:
                    self.cap_lvl7_entry = entry

        # THIS IS THE KEY TO STABILITY: handle padding seek within the builder
        if key in ['fp', 'fs', 'rs']: 
            file_handle.seek(2, 1)
            
        return frame
        
    def read_upgrade_prices(self):
        weapon_name = self.upgrade_weapon_entry.get()
        if weapon_name == "-": return

        offset_str = self.all_data["upgrade_prices"].get(weapon_name)
        if not offset_str: return
        
        for widget in self.upgrade_prices_frame.winfo_children():
            widget.destroy()
        self.upgrade_price_widgets = {}
        self.exclusive_fp_base_entry = None
        self.exclusive_fp_ingame_entry = None
        self.cap_lvl7_entry = None

        max_fp, max_fs, _, _ = self._get_max_levels_from_exe(weapon_name)
        exclusive_fp_index = max_fp - 1 if max_fp else -1
        is_shared_mode = max_fs > 3

        try:
            main_layout_frame = ctk.CTkFrame(self.upgrade_prices_frame, fg_color="transparent")
            main_layout_frame.pack(fill="both", expand=True)
            main_layout_frame.grid_columnconfigure((0, 1), weight=1)
            main_layout_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, self.upgrade_prices_frame))
            
            with open(self.exe_path, 'rb') as f:
                f.seek(int(offset_str, 16) + 2)
                
                fp_frame = self._build_upgrade_price_frame(main_layout_frame, ('fp', 6, 'Firepower'), f, exclusive_fp_index, self.upgrade_prices_frame, is_shared_mode)
                fp_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

                if not is_shared_mode:
                    fs_frame = self._build_upgrade_price_frame(main_layout_frame, ('fs', 2, 'Firing Speed'), f, exclusive_fp_index, self.upgrade_prices_frame)
                    fs_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
                    rs_frame = self._build_upgrade_price_frame(main_layout_frame, ('rs', 2, 'Reload Speed'), f, exclusive_fp_index, self.upgrade_prices_frame)
                    rs_frame.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
                else:
                    fs_rs_frame = ctk.CTkFrame(main_layout_frame, border_width=1, border_color="gray25")
                    fs_rs_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
                    header = ctk.CTkLabel(fs_rs_frame, text="Firing & Reload Speed (Shared Prices)", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.EXCLUSIVE_COLOR)
                    header.pack(pady=(5,0))
                    warning = ctk.CTkLabel(fs_rs_frame, text="Max Firing Speed is > 3. Prices are shared with Reload Speed.", font=ctk.CTkFont(slant="italic"), text_color="gray60")
                    warning.pack(pady=(0,10))
                    grid_frame = ctk.CTkFrame(fs_rs_frame, fg_color="transparent"); grid_frame.pack(fill="x", padx=10, pady=5)
                    grid_frame.grid_columnconfigure((0,1), weight=1)
                    shared_labels = ["FS Lvl 2 Price:", "FS Lvl 3 Price:", "FS Lvl 4 (Padding):", "FS Lvl 5 / RS Lvl 2:", "FS Lvl 6 / RS Lvl 3:", "FS Lvl 7 (Padding):"]
                    
                    # Read all 6 price points for the shared block
                    prices_in_order = [struct.unpack('<H', f.read(2))[0] * 10 for _ in range(6)]
                    
                    self.upgrade_price_widgets['fs'] = []; self.upgrade_price_widgets['rs'] = []
                    for i, label_text in enumerate(shared_labels):
                        row, col = divmod(i, 2)
                        sub_frame = ctk.CTkFrame(grid_frame, fg_color="transparent"); sub_frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")
                        price_label = ctk.CTkLabel(sub_frame, text=label_text); price_label.pack(side="left", padx=(0,5))
                        entry = ctk.CTkEntry(sub_frame); entry.insert(0, str(prices_in_order[i])); entry.pack(side="left", fill="x", expand=True)
                        self.upgrade_price_widgets['fs'].append(entry)
                
                # The file pointer is now at the correct position for Capacity in both cases
                cap_frame = self._build_upgrade_price_frame(main_layout_frame, ('cap', 6, 'Capacity'), f, exclusive_fp_index, self.upgrade_prices_frame)
                cap_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
            
            if is_shared_mode and self.exclusive_fp_base_entry:
                self.upgrade_price_widgets['fs'][-1].bind("<KeyRelease>", self._on_fs7_price_change)
                if self.cap_lvl7_entry:
                    self.cap_lvl7_entry.bind("<KeyRelease>", self._on_cap7_price_change)
                self._update_exclusive_fp_prices(source_widget=self.exclusive_fp_base_entry)

            self._update_stable_status()
        except Exception as e:
            messagebox.showerror("Read Error", f"Could not read upgrade prices for {weapon_name}: {e}")
            
    def apply_upgrade_prices(self):
        weapon_name = self.upgrade_weapon_entry.get()
        if weapon_name == "-": return

        offset_str = self.all_data["upgrade_prices"].get(weapon_name)
        if not offset_str: return

        max_fp, max_fs, _, _ = self._get_max_levels_from_exe(weapon_name)

        try:
            patch_bytes = bytearray()
            
            all_widgets = []
            for key in ['fp', 'fs', 'rs', 'cap']:
                all_widgets.extend(self.upgrade_price_widgets.get(key, []))
            for widget in all_widgets:
                if widget == self.exclusive_fp_base_entry: price_val = int(self.exclusive_fp_base_entry.get())
                else: price_val = int(widget.get())
                if not (0 <= price_val <= 655350):
                    messagebox.showerror("Invalid Price", "An upgrade price must be between 0 and 655,350."); return

            # Firepower
            for entry in self.upgrade_price_widgets['fp']: patch_bytes.extend(struct.pack('<H', int(entry.get()) // 10))
            patch_bytes.extend(b'\x00\x00') # FP padding
            
            if max_fs <= 3:
                # Normal Case
                for entry in self.upgrade_price_widgets['fs']: patch_bytes.extend(struct.pack('<H', int(entry.get()) // 10))
                patch_bytes.extend(b'\x00\x00') # FS padding
                for entry in self.upgrade_price_widgets['rs']: patch_bytes.extend(struct.pack('<H', int(entry.get()) // 10))
                patch_bytes.extend(b'\x00\x00') # RS padding
            else:
                # Shared Case: just pack the 6 FS widgets in order
                for entry in self.upgrade_price_widgets['fs']:
                    patch_bytes.extend(struct.pack('<H', int(entry.get()) // 10))
            
            # Capacity
            for entry in self.upgrade_price_widgets['cap']:
                patch_bytes.extend(struct.pack('<H', int(entry.get()) // 10))
            patch_bytes.extend(b'\x00\x00') # Final padding

            with open(self.exe_path, 'rb+') as f:
                f.seek(int(offset_str, 16) + 2)
                f.write(patch_bytes)

            self.read_upgrade_prices()
            self._show_success_message(f"Applied upgrade prices for {weapon_name}!")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please ensure all prices are valid integers.")
        except Exception as e:
            messagebox.showerror("Write Error", f"Could not apply upgrade prices: {e}")
            
    # --- END OF UPGRADE PRICES EDITOR SECTION ---
    
    # --- START OF RANDOMIZER SECTION ---
    def _create_randomizer_tab(self, parent_frame):
        randomizer_tab = parent_frame
        randomizer_tab.grid_columnconfigure(0, weight=1)

        seed_frame = ctk.CTkFrame(randomizer_tab)
        seed_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        seed_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(seed_frame, text="Seed:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(10,5), pady=10)
        self.seed_entry = ctk.CTkEntry(seed_frame, placeholder_text="Enter a number or click Generate")
        self.seed_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.generate_seed_button = ctk.CTkButton(seed_frame, text="Generate", command=self._generate_seed, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        self.generate_seed_button.grid(row=0, column=2, padx=(5,10), pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(randomizer_tab)
        scroll_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
        randomizer_tab.grid_rowconfigure(1, weight=1)
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        mousewheel_func = lambda event: self._on_mousewheel(event, scroll_frame)

        # --- Item Prices ---
        price_frame = ctk.CTkFrame(scroll_frame, border_width=1, border_color="gray25"); price_frame.bind("<MouseWheel>", mousewheel_func)
        price_frame.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        price_frame.grid_columnconfigure(0, weight=1)
        price_header_frame = ctk.CTkFrame(price_frame, fg_color="transparent"); price_header_frame.bind("<MouseWheel>", mousewheel_func)
        price_header_frame.grid(row=0, column=0, padx=10, pady=(5,10), sticky="ew")
        price_header_frame.grid_columnconfigure(1, weight=1)
        self.randomize_prices_switch = ctk.CTkSwitch(price_header_frame, text="", onvalue=1, offvalue=0, command=self._toggle_price_randomizer_widgets, progress_color=self.THEME_COLOR); self.randomize_prices_switch.bind("<MouseWheel>", mousewheel_func)
        self.randomize_prices_switch.grid(row=0, column=0, padx=(0,5))
        phf_label = ctk.CTkLabel(price_header_frame, text="Randomize Item Prices", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR); phf_label.bind("<MouseWheel>", mousewheel_func)
        phf_label.grid(row=0, column=1, sticky="w")
        self.price_options_frame = ctk.CTkFrame(price_frame, fg_color="transparent"); self.price_options_frame.bind("<MouseWheel>", mousewheel_func)
        self.price_options_frame.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
        self.price_options_frame.grid_columnconfigure(1, weight=1)
        pof_label = ctk.CTkLabel(self.price_options_frame, text="Base Price Variance:"); pof_label.bind("<MouseWheel>", mousewheel_func); pof_label.grid(row=0, column=0, sticky="w")
        variance_frame = ctk.CTkFrame(self.price_options_frame, fg_color="transparent"); variance_frame.bind("<MouseWheel>", mousewheel_func); variance_frame.grid(row=0, column=1, columnspan=2, sticky="ew")
        self.price_variance_min_entry = ctk.CTkEntry(variance_frame, width=80); self.price_variance_min_entry.pack(side="left", padx=(5,0)); self.price_variance_min_entry.bind("<MouseWheel>", mousewheel_func)
        vf_label1 = ctk.CTkLabel(variance_frame, text="% to"); vf_label1.pack(side="left", padx=5); vf_label1.bind("<MouseWheel>", mousewheel_func)
        self.price_variance_max_entry = ctk.CTkEntry(variance_frame, width=80); self.price_variance_max_entry.pack(side="left", padx=(0,5)); self.price_variance_max_entry.bind("<MouseWheel>", mousewheel_func)
        vf_label2 = ctk.CTkLabel(variance_frame, text="% of original"); vf_label2.pack(side="left"); vf_label2.bind("<MouseWheel>", mousewheel_func)
        self.price_variance_min_entry.insert(0, "50"); self.price_variance_max_entry.insert(0, "200")
        self.treasure_protect_checkbox = ctk.CTkCheckBox(self.price_options_frame, text="Keep Treasure sell prices at 100%"); self.treasure_protect_checkbox.bind("<MouseWheel>", mousewheel_func)
        self.treasure_protect_checkbox.grid(row=1, column=0, columnspan=3, pady=(10,0), sticky="w")
        self.treasure_protect_checkbox.select()

        # --- Upgrade Prices ---
        upgrade_price_frame = ctk.CTkFrame(scroll_frame, border_width=1, border_color="gray25"); upgrade_price_frame.bind("<MouseWheel>", mousewheel_func)
        upgrade_price_frame.grid(row=1, column=0, padx=5, pady=10, sticky="ew")
        upgrade_price_frame.grid_columnconfigure(0, weight=1)
        upgrade_header_frame = ctk.CTkFrame(upgrade_price_frame, fg_color="transparent"); upgrade_header_frame.bind("<MouseWheel>", mousewheel_func)
        upgrade_header_frame.grid(row=0, column=0, padx=10, pady=(5,10), sticky="ew")
        upgrade_header_frame.grid_columnconfigure(1, weight=1)
        self.randomize_upgrade_prices_switch = ctk.CTkSwitch(upgrade_header_frame, text="", onvalue=1, offvalue=0, command=self._toggle_upgrade_price_randomizer_widgets, progress_color=self.THEME_COLOR); self.randomize_upgrade_prices_switch.bind("<MouseWheel>", mousewheel_func)
        self.randomize_upgrade_prices_switch.grid(row=0, column=0, padx=(0,5))
        uhf_label = ctk.CTkLabel(upgrade_header_frame, text="Randomize Weapon Upgrade Prices", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR); uhf_label.bind("<MouseWheel>", mousewheel_func)
        uhf_label.grid(row=0, column=1, sticky="w")
        self.upgrade_price_options_frame = ctk.CTkFrame(upgrade_price_frame, fg_color="transparent"); self.upgrade_price_options_frame.bind("<MouseWheel>", mousewheel_func)
        self.upgrade_price_options_frame.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
        self.upgrade_price_options_frame.grid_columnconfigure(1, weight=1)
        upof_label = ctk.CTkLabel(self.upgrade_price_options_frame, text="Upgrade Price Variance:"); upof_label.bind("<MouseWheel>", mousewheel_func); upof_label.grid(row=0, column=0, sticky="w")
        up_variance_frame = ctk.CTkFrame(self.upgrade_price_options_frame, fg_color="transparent"); up_variance_frame.bind("<MouseWheel>", mousewheel_func)
        up_variance_frame.grid(row=0, column=1, columnspan=2, sticky="ew")
        self.upgrade_price_variance_min_entry = ctk.CTkEntry(up_variance_frame, width=80); self.upgrade_price_variance_min_entry.pack(side="left", padx=(5,0)); self.upgrade_price_variance_min_entry.bind("<MouseWheel>", mousewheel_func)
        upvf_label1 = ctk.CTkLabel(up_variance_frame, text="% to"); upvf_label1.pack(side="left", padx=5); upvf_label1.bind("<MouseWheel>", mousewheel_func)
        self.upgrade_price_variance_max_entry = ctk.CTkEntry(up_variance_frame, width=80); self.upgrade_price_variance_max_entry.pack(side="left", padx=(0,5)); self.upgrade_price_variance_max_entry.bind("<MouseWheel>", mousewheel_func)
        upvf_label2 = ctk.CTkLabel(up_variance_frame, text="% of original"); upvf_label2.pack(side="left"); upvf_label2.bind("<MouseWheel>", mousewheel_func)
        self.upgrade_price_variance_min_entry.insert(0, "75"); self.upgrade_price_variance_max_entry.insert(0, "150")
        
        # --- Weapon Stats ---
        weapon_stat_frame = ctk.CTkFrame(scroll_frame, border_width=1, border_color="gray25"); weapon_stat_frame.bind("<MouseWheel>", mousewheel_func)
        weapon_stat_frame.grid(row=2, column=0, padx=5, pady=10, sticky="ew")
        weapon_stat_frame.grid_columnconfigure(0, weight=1)
        stat_header_frame = ctk.CTkFrame(weapon_stat_frame, fg_color="transparent"); stat_header_frame.bind("<MouseWheel>", mousewheel_func)
        stat_header_frame.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="ew")
        stat_header_frame.grid_columnconfigure(1, weight=1)
        self.randomize_weapon_stats_switch = ctk.CTkSwitch(stat_header_frame, text="", onvalue=1, offvalue=0, command=self._toggle_weapon_stat_randomizer_widgets, progress_color=self.THEME_COLOR); self.randomize_weapon_stats_switch.bind("<MouseWheel>", mousewheel_func)
        self.randomize_weapon_stats_switch.grid(row=0, column=0, padx=(0, 5))
        shf_label = ctk.CTkLabel(stat_header_frame, text="Randomize Weapon Stats", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR); shf_label.bind("<MouseWheel>", mousewheel_func)
        shf_label.grid(row=0, column=1, sticky="w")
        self.weapon_stat_options_frame = ctk.CTkFrame(weapon_stat_frame, fg_color="transparent"); self.weapon_stat_options_frame.bind("<MouseWheel>", mousewheel_func)
        self.weapon_stat_options_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.weapon_stat_options_frame.grid_columnconfigure(1, weight=1)
        self.randomizer_stat_widgets = {}
        stat_rows = [("fp", "Firepower:", "80", "120"), ("cap", "Capacity:", "70", "130"), ("fs", "Firing Speed:", "80", "120"), ("rs", "Reload Speed:", "80", "120")]
        for i, (key, text, default_min, default_max) in enumerate(stat_rows): self.randomizer_stat_widgets[key] = self._create_stat_randomizer_row(self.weapon_stat_options_frame, i, text, default_min, default_max, mousewheel_func)

        # --- Merchant Stock ---
        merchant_frame = ctk.CTkFrame(scroll_frame, border_width=1, border_color="gray25"); merchant_frame.bind("<MouseWheel>", mousewheel_func)
        merchant_frame.grid(row=3, column=0, padx=5, pady=10, sticky="ew")
        merchant_frame.grid_columnconfigure(0, weight=1)
        merchant_header_frame = ctk.CTkFrame(merchant_frame, fg_color="transparent"); merchant_header_frame.bind("<MouseWheel>", mousewheel_func)
        merchant_header_frame.grid(row=0, column=0, padx=10, pady=(5,10), sticky="ew")
        merchant_header_frame.grid_columnconfigure(1, weight=1)
        self.randomize_merchant_switch = ctk.CTkSwitch(merchant_header_frame, text="", onvalue=1, offvalue=0, command=self._toggle_merchant_randomizer_widgets, progress_color=self.THEME_COLOR); self.randomize_merchant_switch.bind("<MouseWheel>", mousewheel_func)
        self.randomize_merchant_switch.grid(row=0, column=0, padx=(0,5))
        mhf_label = ctk.CTkLabel(merchant_header_frame, text="Randomize Merchant Stock", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR); mhf_label.bind("<MouseWheel>", mousewheel_func)
        mhf_label.grid(row=0, column=1, sticky="w")
        self.merchant_options_frame = ctk.CTkFrame(merchant_frame, fg_color="transparent"); self.merchant_options_frame.bind("<MouseWheel>", mousewheel_func)
        self.merchant_options_frame.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
        self.merchant_stock_checkbox = ctk.CTkCheckBox(self.merchant_options_frame, text="Randomize Items for Sale (Weapons, Ammo, etc.)"); self.merchant_stock_checkbox.grid(row=0, column=0, pady=5, sticky="w"); self.merchant_stock_checkbox.select(); self.merchant_stock_checkbox.bind("<MouseWheel>", mousewheel_func)
        self.merchant_upgrades_checkbox = ctk.CTkCheckBox(self.merchant_options_frame, text="Randomize Upgrades Offered"); self.merchant_upgrades_checkbox.grid(row=1, column=0, pady=5, sticky="w"); self.merchant_upgrades_checkbox.select(); self.merchant_upgrades_checkbox.bind("<MouseWheel>", mousewheel_func)
        self.merchant_include_key_items_checkbox = ctk.CTkCheckBox(self.merchant_options_frame, text="Allow Key Items in Item Pool (Potentially game-breaking)"); self.merchant_include_key_items_checkbox.grid(row=2, column=0, pady=(10,0), sticky="w"); self.merchant_include_key_items_checkbox.bind("<MouseWheel>", mousewheel_func)

        # --- Item Types ---
        item_type_frame = ctk.CTkFrame(scroll_frame, border_width=1, border_color="gray25"); item_type_frame.bind("<MouseWheel>", mousewheel_func)
        item_type_frame.grid(row=4, column=0, padx=5, pady=10, sticky="ew")
        item_type_frame.grid_columnconfigure(0, weight=1)
        item_type_header_frame = ctk.CTkFrame(item_type_frame, fg_color="transparent"); item_type_header_frame.bind("<MouseWheel>", mousewheel_func)
        item_type_header_frame.grid(row=0, column=0, padx=10, pady=(5,10), sticky="ew")
        item_type_header_frame.grid_columnconfigure(1, weight=1)
        self.randomize_item_types_switch = ctk.CTkSwitch(item_type_header_frame, text="", onvalue=1, offvalue=0, command=self._toggle_item_type_randomizer_widgets, progress_color=self.THEME_COLOR); self.randomize_item_types_switch.bind("<MouseWheel>", mousewheel_func)
        self.randomize_item_types_switch.grid(row=0, column=0, padx=(0,5))
        ithf_label = ctk.CTkLabel(item_type_header_frame, text="Randomize Item Types", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR); ithf_label.bind("<MouseWheel>", mousewheel_func)
        ithf_label.grid(row=0, column=1, sticky="w")
        self.item_type_options_frame = ctk.CTkFrame(item_type_frame, fg_color="transparent"); self.item_type_options_frame.bind("<MouseWheel>", mousewheel_func)
        self.item_type_options_frame.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
        self.item_type_safe_swap_checkbox = ctk.CTkCheckBox(self.item_type_options_frame, text="Randomize Treasure <-> Key Items (Safe)")
        self.item_type_safe_swap_checkbox.grid(row=0, column=0, pady=5, sticky="w"); self.item_type_safe_swap_checkbox.select(); self.item_type_safe_swap_checkbox.bind("<MouseWheel>", mousewheel_func)
        self.item_type_full_random_checkbox = ctk.CTkCheckBox(self.item_type_options_frame, text="Allow ALL item types in pool (EXPERIMENTAL - HIGHLY UNSTABLE)")
        self.item_type_full_random_checkbox.grid(row=1, column=0, pady=(10,0), sticky="w"); self.item_type_full_random_checkbox.bind("<MouseWheel>", mousewheel_func)
        
        # --- Item Sizes ---
        item_size_frame = ctk.CTkFrame(scroll_frame, border_width=1, border_color="gray25"); item_size_frame.bind("<MouseWheel>", mousewheel_func)
        item_size_frame.grid(row=5, column=0, padx=5, pady=10, sticky="ew")
        item_size_frame.grid_columnconfigure(0, weight=1)
        item_size_header_frame = ctk.CTkFrame(item_size_frame, fg_color="transparent"); item_size_header_frame.bind("<MouseWheel>", mousewheel_func)
        item_size_header_frame.grid(row=0, column=0, padx=10, pady=(5,10), sticky="ew")
        item_size_header_frame.grid_columnconfigure(1, weight=1)
        self.randomize_item_sizes_switch = ctk.CTkSwitch(item_size_header_frame, text="", onvalue=1, offvalue=0, command=self._toggle_item_size_randomizer_widgets, progress_color=self.THEME_COLOR); self.randomize_item_sizes_switch.bind("<MouseWheel>", mousewheel_func)
        self.randomize_item_sizes_switch.grid(row=0, column=0, padx=(0,5))
        ishf_label = ctk.CTkLabel(item_size_header_frame, text="Randomize Item Sizes", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR); ishf_label.bind("<MouseWheel>", mousewheel_func)
        ishf_label.grid(row=0, column=1, sticky="w")
        self.item_size_options_frame = ctk.CTkFrame(item_size_frame, fg_color="transparent"); self.item_size_options_frame.bind("<MouseWheel>", mousewheel_func)
        self.item_size_options_frame.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
        self.item_size_options_frame.grid_columnconfigure(1, weight=1)
        isof_label1 = ctk.CTkLabel(self.item_size_options_frame, text="Width Variance:"); isof_label1.grid(row=0, column=0, sticky="w", pady=2); isof_label1.bind("<MouseWheel>", mousewheel_func)
        size_var_w_frame = ctk.CTkFrame(self.item_size_options_frame, fg_color="transparent"); size_var_w_frame.grid(row=0, column=1, columnspan=2, sticky="ew"); size_var_w_frame.bind("<MouseWheel>", mousewheel_func)
        self.item_size_w_min_entry = ctk.CTkEntry(size_var_w_frame, width=80); self.item_size_w_min_entry.pack(side="left", padx=(5,0)); self.item_size_w_min_entry.bind("<MouseWheel>", mousewheel_func)
        svwf_label1 = ctk.CTkLabel(size_var_w_frame, text="% to"); svwf_label1.pack(side="left", padx=5); svwf_label1.bind("<MouseWheel>", mousewheel_func)
        self.item_size_w_max_entry = ctk.CTkEntry(size_var_w_frame, width=80); self.item_size_w_max_entry.pack(side="left", padx=(0,5)); self.item_size_w_max_entry.bind("<MouseWheel>", mousewheel_func)
        svwf_label2 = ctk.CTkLabel(size_var_w_frame, text="% of original"); svwf_label2.pack(side="left"); svwf_label2.bind("<MouseWheel>", mousewheel_func)
        self.item_size_w_min_entry.insert(0, "75"); self.item_size_w_max_entry.insert(0, "125")
        isof_label2 = ctk.CTkLabel(self.item_size_options_frame, text="Height Variance:"); isof_label2.grid(row=1, column=0, sticky="w", pady=2); isof_label2.bind("<MouseWheel>", mousewheel_func)
        size_var_h_frame = ctk.CTkFrame(self.item_size_options_frame, fg_color="transparent"); size_var_h_frame.grid(row=1, column=1, columnspan=2, sticky="ew"); size_var_h_frame.bind("<MouseWheel>", mousewheel_func)
        self.item_size_h_min_entry = ctk.CTkEntry(size_var_h_frame, width=80); self.item_size_h_min_entry.pack(side="left", padx=(5,0)); self.item_size_h_min_entry.bind("<MouseWheel>", mousewheel_func)
        svhf_label1 = ctk.CTkLabel(size_var_h_frame, text="% to"); svhf_label1.pack(side="left", padx=5); svhf_label1.bind("<MouseWheel>", mousewheel_func)
        self.item_size_h_max_entry = ctk.CTkEntry(size_var_h_frame, width=80); self.item_size_h_max_entry.pack(side="left", padx=(0,5)); self.item_size_h_max_entry.bind("<MouseWheel>", mousewheel_func)
        svhf_label2 = ctk.CTkLabel(size_var_h_frame, text="% of original"); svhf_label2.pack(side="left"); svhf_label2.bind("<MouseWheel>", mousewheel_func)
        self.item_size_h_min_entry.insert(0, "75"); self.item_size_h_max_entry.insert(0, "125")

        # --- Item Combinations ---
        item_combo_frame = ctk.CTkFrame(scroll_frame, border_width=1, border_color="gray25"); item_combo_frame.bind("<MouseWheel>", mousewheel_func)
        item_combo_frame.grid(row=6, column=0, padx=5, pady=10, sticky="ew")
        item_combo_frame.grid_columnconfigure(0, weight=1)
        item_combo_header_frame = ctk.CTkFrame(item_combo_frame, fg_color="transparent"); item_combo_header_frame.bind("<MouseWheel>", mousewheel_func)
        item_combo_header_frame.grid(row=0, column=0, padx=10, pady=(5,10), sticky="ew")
        item_combo_header_frame.grid_columnconfigure(1, weight=1)
        self.randomize_combinations_switch = ctk.CTkSwitch(item_combo_header_frame, text="", onvalue=1, offvalue=0, command=self._toggle_item_combination_randomizer_widgets, progress_color=self.THEME_COLOR); self.randomize_combinations_switch.bind("<MouseWheel>", mousewheel_func)
        self.randomize_combinations_switch.grid(row=0, column=0, padx=(0,5))
        ichf_label = ctk.CTkLabel(item_combo_header_frame, text="Randomize Item Combinations", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR); ichf_label.bind("<MouseWheel>", mousewheel_func)
        ichf_label.grid(row=0, column=1, sticky="w")
        self.combination_options_frame = ctk.CTkFrame(item_combo_frame, fg_color="transparent"); self.combination_options_frame.bind("<MouseWheel>", mousewheel_func)
        self.combination_options_frame.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
        self.randomize_combo_ingredients_checkbox = ctk.CTkCheckBox(self.combination_options_frame, text="Randomize Ingredients (Item A + Item B)")
        self.randomize_combo_ingredients_checkbox.grid(row=0, column=0, pady=5, sticky="w"); self.randomize_combo_ingredients_checkbox.select(); self.randomize_combo_ingredients_checkbox.bind("<MouseWheel>", mousewheel_func)
        self.randomize_combo_results_checkbox = ctk.CTkCheckBox(self.combination_options_frame, text="Randomize Results")
        self.randomize_combo_results_checkbox.grid(row=1, column=0, pady=5, sticky="w"); self.randomize_combo_results_checkbox.select(); self.randomize_combo_results_checkbox.bind("<MouseWheel>", mousewheel_func)
        # --- NEW CHECKBOX ADDED HERE ---
        self.randomize_combo_logic_checkbox = ctk.CTkCheckBox(self.combination_options_frame, text="Enforce Logical Fusing (e.g., Gems only fuse with Gems)")
        self.randomize_combo_logic_checkbox.grid(row=2, column=0, pady=(10,0), sticky="w"); self.randomize_combo_logic_checkbox.select(); self.randomize_combo_logic_checkbox.bind("<MouseWheel>", mousewheel_func)

        # --- Starter Inventories ---
        starter_inv_frame = ctk.CTkFrame(scroll_frame, border_width=1, border_color="gray25"); starter_inv_frame.bind("<MouseWheel>", mousewheel_func)
        starter_inv_frame.grid(row=7, column=0, padx=5, pady=10, sticky="ew")
        starter_inv_frame.grid_columnconfigure(0, weight=1)
        starter_inv_header_frame = ctk.CTkFrame(starter_inv_frame, fg_color="transparent"); starter_inv_header_frame.bind("<MouseWheel>", mousewheel_func)
        starter_inv_header_frame.grid(row=0, column=0, padx=10, pady=(5,10), sticky="ew")
        starter_inv_header_frame.grid_columnconfigure(1, weight=1)
        self.randomize_starter_inv_switch = ctk.CTkSwitch(starter_inv_header_frame, text="", onvalue=1, offvalue=0, command=self._toggle_starter_inv_randomizer_widgets, progress_color=self.THEME_COLOR); self.randomize_starter_inv_switch.bind("<MouseWheel>", mousewheel_func)
        self.randomize_starter_inv_switch.grid(row=0, column=0, padx=(0,5))
        sihf_label = ctk.CTkLabel(starter_inv_header_frame, text="Randomize Starter Inventories", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR); sihf_label.bind("<MouseWheel>", mousewheel_func)
        sihf_label.grid(row=0, column=1, sticky="w")
        self.starter_inv_options_frame = ctk.CTkFrame(starter_inv_frame, fg_color="transparent"); self.starter_inv_options_frame.bind("<MouseWheel>", mousewheel_func)
        self.starter_inv_options_frame.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
        self.randomize_starter_inv_checkbox = ctk.CTkCheckBox(self.starter_inv_options_frame, text="Shuffle starter items of the same type (e.g., weapons for weapons)")
        self.randomize_starter_inv_checkbox.grid(row=0, column=0, pady=5, sticky="w"); self.randomize_starter_inv_checkbox.select(); self.randomize_starter_inv_checkbox.bind("<MouseWheel>", mousewheel_func)

        # --- Shooting Range---
        shooting_range_frame = ctk.CTkFrame(scroll_frame, border_width=1, border_color="gray25"); shooting_range_frame.bind("<MouseWheel>", mousewheel_func)
        shooting_range_frame.grid(row=8, column=0, padx=5, pady=10, sticky="ew")
        shooting_range_frame.grid_columnconfigure(0, weight=1)
        shooting_range_header_frame = ctk.CTkFrame(shooting_range_frame, fg_color="transparent"); shooting_range_header_frame.bind("<MouseWheel>", mousewheel_func)
        shooting_range_header_frame.grid(row=0, column=0, padx=10, pady=(5,10), sticky="ew")
        shooting_range_header_frame.grid_columnconfigure(1, weight=1)
        self.randomize_shooting_range_switch = ctk.CTkSwitch(shooting_range_header_frame, text="", onvalue=1, offvalue=0, command=self._toggle_shooting_range_randomizer_widgets, progress_color=self.THEME_COLOR); self.randomize_shooting_range_switch.bind("<MouseWheel>", mousewheel_func)
        self.randomize_shooting_range_switch.grid(row=0, column=0, padx=(0,5))
        srhf_label = ctk.CTkLabel(shooting_range_header_frame, text="Randomize Shooting Range Items", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR); srhf_label.bind("<MouseWheel>", mousewheel_func)
        srhf_label.grid(row=0, column=1, sticky="w")
        self.shooting_range_options_frame = ctk.CTkFrame(shooting_range_frame, fg_color="transparent"); self.shooting_range_options_frame.bind("<MouseWheel>", mousewheel_func)
        self.shooting_range_options_frame.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
        self.randomize_shooting_range_checkbox = ctk.CTkCheckBox(self.shooting_range_options_frame, text="Shuffle all shooting range items")
        self.randomize_shooting_range_checkbox.grid(row=0, column=0, pady=5, sticky="w"); self.randomize_shooting_range_checkbox.select(); self.randomize_shooting_range_checkbox.bind("<MouseWheel>", mousewheel_func)
        
        money_health_frame = ctk.CTkFrame(scroll_frame, border_width=1, border_color="gray25"); money_health_frame.bind("<MouseWheel>", mousewheel_func)
        money_health_frame.grid(row=9, column=0, padx=5, pady=10, sticky="ew")
        money_health_frame.grid_columnconfigure(0, weight=1)
        money_health_header_frame = ctk.CTkFrame(money_health_frame, fg_color="transparent"); money_health_header_frame.bind("<MouseWheel>", mousewheel_func)
        money_health_header_frame.grid(row=0, column=0, padx=10, pady=(5,10), sticky="ew")
        money_health_header_frame.grid_columnconfigure(1, weight=1)
        self.randomize_money_health_switch = ctk.CTkSwitch(money_health_header_frame, text="", onvalue=1, offvalue=0, command=self._toggle_money_health_randomizer_widgets, progress_color=self.THEME_COLOR); self.randomize_money_health_switch.bind("<MouseWheel>", mousewheel_func)
        self.randomize_money_health_switch.grid(row=0, column=0, padx=(0,5))
        mhhf_label = ctk.CTkLabel(money_health_header_frame, text="Randomize Starter Money & Health", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.THEME_COLOR); mhhf_label.bind("<MouseWheel>", mousewheel_func)
        mhhf_label.grid(row=0, column=1, sticky="w")
        self.money_health_options_frame = ctk.CTkFrame(money_health_frame, fg_color="transparent"); self.money_health_options_frame.bind("<MouseWheel>", mousewheel_func)
        self.money_health_options_frame.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
        self.money_health_options_frame.grid_columnconfigure(1, weight=1)
        self.randomize_money_checkbox = ctk.CTkCheckBox(self.money_health_options_frame, text="Randomize Leon's Starting Money (Range: 1 to 100,000)"); self.randomize_money_checkbox.grid(row=0, column=0, pady=5, sticky="w"); self.randomize_money_checkbox.select()
        self.randomize_health_checkbox = ctk.CTkCheckBox(self.money_health_options_frame, text="Randomize Leon/Ashley Health (Range: 100 to 2400)"); self.randomize_health_checkbox.grid(row=1, column=0, pady=5, sticky="w"); self.randomize_health_checkbox.select()
        
        # --- Action Button ---
        bottom_frame = ctk.CTkFrame(randomizer_tab)
        bottom_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        self.randomize_button = ctk.CTkButton(bottom_frame, text="RANDOMIZE!", font=ctk.CTkFont(size=16, weight="bold"), fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=self._execute_randomization)
        self.randomize_button.grid(row=0, column=0, padx=10, pady=10, ipady=10, sticky="ew")
        
        self._toggle_price_randomizer_widgets()
        self._toggle_upgrade_price_randomizer_widgets()
        self._toggle_weapon_stat_randomizer_widgets()
        self._toggle_merchant_randomizer_widgets()
        self._toggle_item_type_randomizer_widgets()
        self._toggle_item_size_randomizer_widgets()
        self._toggle_item_combination_randomizer_widgets()
        self._toggle_starter_inv_randomizer_widgets()
        self._toggle_shooting_range_randomizer_widgets()
        self._toggle_money_health_randomizer_widgets()
        
    def _toggle_shooting_range_randomizer_widgets(self):
        state = "normal" if self.randomize_shooting_range_switch.get() == 1 else "disabled"
        for widget in self.shooting_range_options_frame.winfo_children():
            widget.configure(state=state)

    def _toggle_money_health_randomizer_widgets(self):
        state = "normal" if self.randomize_money_health_switch.get() == 1 else "disabled"
        for widget in self.money_health_options_frame.winfo_children():
            widget.configure(state=state)

    def _randomize_weapon_stats(self):
        writes_to_perform = {}
        with open(self.active_backup_path, 'rb') as bak_f:
            for weapon_name, weapon_data in self.all_data["weapons"].items():
                if "---" in weapon_name: continue

                # --- Randomize Firepower ---
                fp_widgets = self.randomizer_stat_widgets['fp']
                if fp_widgets['checkbox'].get() == 1 and "firepower_base_offset" in weapon_data:
                    min_var, max_var = int(fp_widgets['min'].get())/100, int(fp_widgets['max'].get())/100
                    base_offset = int(weapon_data["firepower_base_offset"], 16)
                    for i in range(7): # 7 levels
                        # EXCEPTION: Skip Handgun's Level 1 Firepower to fix ingame crashes
                        if weapon_name == "Handgun" and i == 0:
                            continue
                        offset = base_offset + (i * 4)
                        bak_f.seek(offset)
                        original_val = struct.unpack('<f', bak_f.read(4))[0]
                        if original_val > 0:
                            new_val = _random.uniform(original_val * min_var, original_val * max_var)
                            writes_to_perform[offset] = struct.pack('<f', new_val)

                # --- Randomize Capacity ---
                cap_widgets = self.randomizer_stat_widgets['cap']
                if cap_widgets['checkbox'].get() == 1 and "capacity_base_offset" in weapon_data:
                    min_var, max_var = int(cap_widgets['min'].get())/100, int(cap_widgets['max'].get())/100
                    base_offset = int(weapon_data["capacity_base_offset"], 16) + 8
                    for i in range(7): # 7 levels
                        # No exception here, Lvl 1 Capacity will be randomized.
                        offset = base_offset + (i * 2)
                        bak_f.seek(offset)
                        original_val = struct.unpack('<h', bak_f.read(2))[0]
                        if original_val > 0:
                            new_val_float = _random.uniform(original_val * min_var, original_val * max_var)
                            new_val = max(1, round(new_val_float))
                            writes_to_perform[offset] = struct.pack('<h', new_val)

                # --- Randomize Firing Speed ---
                fs_widgets = self.randomizer_stat_widgets['fs']
                if fs_widgets['checkbox'].get() == 1 and "firing_speed_offsets" in weapon_data:
                    min_var, max_var = int(fs_widgets['min'].get())/100, int(fs_widgets['max'].get())/100
                    for base_offset_str in weapon_data["firing_speed_offsets"]:
                        base_offset = int(base_offset_str, 16)
                        for i in range(5): # 5 levels
                            # No exception here, Lvl 1 Firing Speed will be randomized.
                            offset = base_offset + (i * 4)
                            bak_f.seek(offset)
                            original_val = struct.unpack('<f', bak_f.read(4))[0]
                            if original_val > 0:
                                new_val = _random.uniform(original_val * min_var, original_val * max_var)
                                writes_to_perform[offset] = struct.pack('<f', new_val)

                # --- Randomize Reload Speed ---
                rs_widgets = self.randomizer_stat_widgets['rs']
                if rs_widgets['checkbox'].get() == 1 and "reload_speed_base_offset" in weapon_data:
                    min_var, max_var = int(rs_widgets['min'].get())/100, int(rs_widgets['max'].get())/100
                    base_offset = int(weapon_data["reload_speed_base_offset"], 16)
                    for i in range(3): # 3 levels
                        # No exception here, Lvl 1 Reload Speed will be randomized.
                        offset = base_offset + (i * 4)
                        bak_f.seek(offset)
                        original_val = struct.unpack('<f', bak_f.read(4))[0]
                        if original_val > 0:
                            new_val = _random.uniform(original_val * min_var, original_val * max_var)
                            writes_to_perform[offset] = struct.pack('<f', new_val)

        if writes_to_perform:
            with open(self.exe_path, 'rb+') as exe_f:
                for offset, data_bytes in writes_to_perform.items():
                    exe_f.seek(offset)
                    exe_f.write(data_bytes)
                    
    def _create_stat_randomizer_row(self, parent, row, text, default_min, default_max, mousewheel_func):
        checkbox = ctk.CTkCheckBox(parent, text=text); checkbox.bind("<MouseWheel>", mousewheel_func)
        checkbox.grid(row=row, column=0, sticky="w", pady=4)
        variance_frame = ctk.CTkFrame(parent, fg_color="transparent"); variance_frame.bind("<MouseWheel>", mousewheel_func)
        variance_frame.grid(row=row, column=1, sticky="ew")
        min_entry = ctk.CTkEntry(variance_frame, width=80); min_entry.bind("<MouseWheel>", mousewheel_func)
        min_entry.pack(side="left", padx=(5,0))
        min_entry.insert(0, default_min)
        label1 = ctk.CTkLabel(variance_frame, text="% to"); label1.pack(side="left", padx=5); label1.bind("<MouseWheel>", mousewheel_func)
        max_entry = ctk.CTkEntry(variance_frame, width=80); max_entry.bind("<MouseWheel>", mousewheel_func)
        max_entry.pack(side="left", padx=(0,5))
        max_entry.insert(0, default_max)
        label2 = ctk.CTkLabel(variance_frame, text="% of original"); label2.pack(side="left"); label2.bind("<MouseWheel>", mousewheel_func)
        return {"checkbox": checkbox, "min": min_entry, "max": max_entry}

    def _toggle_price_randomizer_widgets(self):
        state = "normal" if self.randomize_prices_switch.get() == 1 else "disabled"
        for widget in self.price_options_frame.winfo_children():
            if not isinstance(widget, ctk.CTkFrame): widget.configure(state=state)
            if isinstance(widget, ctk.CTkFrame):
                for sub_widget in widget.winfo_children(): sub_widget.configure(state=state)

    def _toggle_upgrade_price_randomizer_widgets(self):
        state = "normal" if self.randomize_upgrade_prices_switch.get() == 1 else "disabled"
        for widget in self.upgrade_price_options_frame.winfo_children():
            if not isinstance(widget, ctk.CTkFrame): widget.configure(state=state)
            if isinstance(widget, ctk.CTkFrame):
                for sub_widget in widget.winfo_children(): sub_widget.configure(state=state)

    def _toggle_weapon_stat_randomizer_widgets(self):
        state = "normal" if self.randomize_weapon_stats_switch.get() == 1 else "disabled"
        for row_widgets in self.randomizer_stat_widgets.values():
            row_widgets["checkbox"].configure(state=state)
            row_widgets["min"].configure(state=state)
            row_widgets["max"].configure(state=state)
            parent_frame = row_widgets["min"].master
            for widget in parent_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel):
                    widget.configure(state=state)

    def _toggle_merchant_randomizer_widgets(self):
        state = "normal" if self.randomize_merchant_switch.get() == 1 else "disabled"
        for widget in self.merchant_options_frame.winfo_children():
            widget.configure(state=state)

    def _toggle_item_type_randomizer_widgets(self):
        state = "normal" if self.randomize_item_types_switch.get() == 1 else "disabled"
        for widget in self.item_type_options_frame.winfo_children():
            widget.configure(state=state)
            
    def _toggle_item_size_randomizer_widgets(self):
        state = "normal" if self.randomize_item_sizes_switch.get() == 1 else "disabled"
        for widget in self.item_size_options_frame.winfo_children():
            if not isinstance(widget, ctk.CTkFrame): widget.configure(state=state)
            if isinstance(widget, ctk.CTkFrame):
                for sub_widget in widget.winfo_children(): sub_widget.configure(state=state)

    def _toggle_item_combination_randomizer_widgets(self):
        state = "normal" if self.randomize_combinations_switch.get() == 1 else "disabled"
        for widget in self.combination_options_frame.winfo_children():
            widget.configure(state=state)

    def _toggle_starter_inv_randomizer_widgets(self):
        state = "normal" if self.randomize_starter_inv_switch.get() == 1 else "disabled"
        for widget in self.starter_inv_options_frame.winfo_children():
            widget.configure(state=state)

    def _read_all_merchant_data_from_file(self, filepath):
        stock_pool, upgrade_pool = [], []
        include_key_items = self.merchant_include_key_items_checkbox.get() == 1
        sorted_merchants = sorted(self.all_data["merchant"].items(), key=lambda item: item[1].get("sort_order", 999))
        with open(filepath, 'rb') as f:
            for _, chapter_info in sorted_merchants:
                if int(chapter_info["stock_offset"], 16) > 0 and chapter_info["stock_slots"] > 0:
                    f.seek(int(chapter_info["stock_offset"], 16))
                    for _ in range(chapter_info["stock_slots"]):
                        item_id, qty, _ = struct.unpack('<HHI', f.read(8))
                        if item_id == 0xFFFF: break
                        item_name = self.item_id_to_name.get(item_id, "")
                        if not include_key_items and item_name in self.key_items: continue
                        stock_pool.append({"id": item_id, "qty": qty})
                if int(chapter_info["upgrades_offset"], 16) > 0 and chapter_info["upgrade_slots"] > 0:
                    f.seek(int(chapter_info["upgrades_offset"], 16))
                    for _ in range(chapter_info["upgrade_slots"]):
                        weapon_id, fp, fs, rs, cap, _ = struct.unpack('<HBBBBH', f.read(8))
                        if weapon_id == 0xFFFF: break
                        upgrade_pool.append({"id": weapon_id, "fp": fp, "fs": fs, "rs": rs, "cap": cap})
        return stock_pool, upgrade_pool
        
    def _randomize_merchant_stock(self):
        stock_pool, upgrade_pool = self._read_all_merchant_data_from_file(self.active_backup_path)
        if self.merchant_stock_checkbox.get() == 1: _random.shuffle(stock_pool)
        if self.merchant_upgrades_checkbox.get() == 1: _random.shuffle(upgrade_pool)
        sorted_merchants = sorted(self.all_data["merchant"].items(), key=lambda item: item[1].get("sort_order", 999))
        with open(self.exe_path, 'rb+') as f:
            for _, chapter_info in sorted_merchants:
                if int(chapter_info["stock_offset"], 16) > 0 and chapter_info["stock_slots"] > 0:
                    offset = int(chapter_info["stock_offset"], 16)
                    for i in range(chapter_info["stock_slots"]):
                        item = stock_pool.pop(0) if stock_pool else {"id": 0xFFFF, "qty": 0}
                        data = struct.pack('<HHI', item["id"], item["qty"], 0)
                        f.seek(offset + (i * 8)); f.write(data)
                if int(chapter_info["upgrades_offset"], 16) > 0 and chapter_info["upgrade_slots"] > 0:
                    offset = int(chapter_info["upgrades_offset"], 16)
                    for i in range(chapter_info["upgrade_slots"]):
                        item = upgrade_pool.pop(0) if upgrade_pool else {"id": 0xFFFF, "fp": 0, "fs": 0, "rs": 0, "cap": 0}
                        data = struct.pack('<HBBBBH', item["id"], item["fp"], item["fs"], item["rs"], item["cap"], 0)
                        f.seek(offset + (i * 8)); f.write(data)

    def _generate_seed(self):
        self.seed_entry.delete(0, "end")
        self.seed_entry.insert(0, str(_random.randint(1000000, 9999999)))
        
    def _execute_randomization(self):
        if not self.exe_path or not os.path.exists(self.active_backup_path):
            messagebox.showerror("Error", "Please select a valid bio4.exe and ensure a valid backup source is selected before randomizing.")
            return
        try:
            seed = int(self.seed_entry.get())
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Seed", "Please enter a valid number for the seed, or generate a new one.")
            return

        # --- NEW VALIDATION BLOCK ---
        def validate_variance(min_entry, max_entry, name):
            try:
                min_val = int(min_entry.get())
                max_val = int(max_entry.get())
                if min_val > max_val:
                    messagebox.showerror("Invalid Variance", f"Error in '{name}':\n\nMinimum variance cannot be greater than the maximum variance.")
                    return False
                return True
            except (ValueError, TypeError):
                messagebox.showerror("Invalid Variance", f"Error in '{name}':\n\nPlease enter valid integer percentages.")
                return False

        if self.randomize_prices_switch.get() == 1 and not validate_variance(self.price_variance_min_entry, self.price_variance_max_entry, "Item Prices"): return
        if self.randomize_upgrade_prices_switch.get() == 1 and not validate_variance(self.upgrade_price_variance_min_entry, self.upgrade_price_variance_max_entry, "Upgrade Prices"): return
        if self.randomize_item_sizes_switch.get() == 1 and not (validate_variance(self.item_size_w_min_entry, self.item_size_w_max_entry, "Item Size Width") and validate_variance(self.item_size_h_min_entry, self.item_size_h_max_entry, "Item Size Height")): return
        if self.randomize_weapon_stats_switch.get() == 1:
            for key, widgets in self.randomizer_stat_widgets.items():
                if widgets['checkbox'].get() == 1 and not validate_variance(widgets['min'], widgets['max'], widgets['checkbox'].cget("text")): return
        # --- END OF VALIDATION BLOCK ---

        _random.seed(seed)
        if not messagebox.askyesno("Confirm Randomization", f"This will modify your bio4.exe based on the selected settings using seed: {seed}.\n\nYour original data will be read from the backup file.\n\nAre you sure you want to proceed?"):
            return
        try:
            if self.randomize_prices_switch.get() == 1: self._randomize_item_prices()
            if self.randomize_upgrade_prices_switch.get() == 1: self._randomize_upgrade_prices()
            if self.randomize_weapon_stats_switch.get() == 1: self._randomize_weapon_stats()
            if self.randomize_merchant_switch.get() == 1: self._randomize_merchant_stock()
            if self.randomize_item_types_switch.get() == 1: self._randomize_item_types()
            if self.randomize_item_sizes_switch.get() == 1: self._randomize_item_sizes()
            if self.randomize_combinations_switch.get() == 1: self._randomize_item_combinations()
            if self.randomize_starter_inv_switch.get() == 1: self._randomize_starter_inventories()
            if self.randomize_shooting_range_switch.get() == 1: self._randomize_shooting_range()
            if self.randomize_money_health_switch.get() == 1: self._randomize_money_health()
            
            def post_randomize_refresh():
                if self.price_editor_loaded: self._refresh_price_data_and_labels(read_exe=True)
                if self.upgrade_editor_loaded: self._on_upgrade_weapon_selected(self.upgrade_weapon_entry.get())
                if self.last_selected_weapon != "-": self.on_weapon_selected(self.last_selected_weapon)
                if self.item_type_editor_loaded:
                    for widget_set in self.item_type_widgets.values():
                        if widget_set.get("is_divider"): widget_set["frame"].destroy()
                        else: widget_set["label"].destroy(); widget_set["dropdown"].destroy()
                    self._build_item_type_editor_once()
                if self.item_size_editor_loaded: self._refresh_item_size_editor()
                if self.combinations_editor_loaded: self._refresh_combinations_editor()
                if self.new_game_editor_loaded: self.read_new_game_data()
                if self.shooting_range_editor_loaded: self.read_shooting_range_data()
                if self.money_health_editor_loaded: self.read_money_health_data()

            self._show_success_message("Randomization complete!", callback=post_randomize_refresh)

        except Exception as e:
            messagebox.showerror("Randomization Error", f"An unexpected error occurred during randomization:\n\n{e}")
            
    def _randomize_item_prices(self):
        protect_treasures = self.treasure_protect_checkbox.get() == 1
        min_var = int(self.price_variance_min_entry.get()) / 100
        max_var = int(self.price_variance_max_entry.get()) / 100
        original_prices = {}
        with open(self.active_backup_path, 'rb') as f:
            for item_name, offsets in self.all_data["master_item_prices"].items():
                if offsets:
                    f.seek(int(offsets[0], 16) + 2)
                    original_prices[item_name] = struct.unpack('<H', f.read(2))[0] * 10
        
        writes_to_perform = {}
        for item_name, original_price in original_prices.items():
            if protect_treasures and item_name in self.treasure_items:
                continue
            
            if original_price == 0:
                new_price = 0
            else:
                new_price_float = _random.uniform(original_price * min_var, original_price * max_var)
                new_price = max(10, round(new_price_float / 10) * 10)

            new_price = min(new_price, 655350)
            
            writes_to_perform[item_name] = struct.pack('<H', new_price // 10)

        with open(self.exe_path, 'rb+') as f:
            for item_name, price_bytes in writes_to_perform.items():
                for offset_str in self.all_data["master_item_prices"][item_name]:
                    f.seek(int(offset_str, 16) + 2); f.write(price_bytes)
                    
    def _randomize_upgrade_prices(self):
        min_var = int(self.upgrade_price_variance_min_entry.get()) / 100
        max_var = int(self.upgrade_price_variance_max_entry.get()) / 100
        writes_to_perform = {}
        
        with open(self.active_backup_path, 'rb') as bak_f:
            for weapon_name, offset_str in self.all_data["upgrade_prices"].items():
                offset = int(offset_str, 16) + 2
                bak_f.seek(offset)
                original_block = bak_f.read(40)

                def randomize_price_list(prices):
                    new_prices = []
                    for price in prices:
                        if price == 0:
                            new_prices.append(0)
                            continue
                        
                        new_val_float = _random.uniform(price * min_var, price * max_var)
                        new_val = max(1, round(new_val_float))
                        new_val = min(new_val, 65535)
                        new_prices.append(new_val)
                    return new_prices

                fp_prices_orig = struct.unpack('<6H', original_block[0:12])
                fs_prices_orig = struct.unpack('<2H', original_block[14:18])
                rs_prices_orig = struct.unpack('<2H', original_block[20:24])
                cap_prices_orig = struct.unpack('<6H', original_block[26:38])
                
                fp_prices_new = randomize_price_list(fp_prices_orig)
                fs_prices_new = randomize_price_list(fs_prices_orig)
                rs_prices_new = randomize_price_list(rs_prices_orig)
                cap_prices_new = randomize_price_list(cap_prices_orig)

                new_bytes = bytearray()
                new_bytes.extend(struct.pack('<6H', *fp_prices_new))
                new_bytes.extend(original_block[12:14])
                new_bytes.extend(struct.pack('<2H', *fs_prices_new))
                new_bytes.extend(original_block[18:20])
                new_bytes.extend(struct.pack('<2H', *rs_prices_new))
                new_bytes.extend(original_block[24:26])
                new_bytes.extend(struct.pack('<6H', *cap_prices_new))
                new_bytes.extend(original_block[38:40])
                
                writes_to_perform[offset] = new_bytes

        with open(self.exe_path, 'rb+') as exe_f:
            for offset, data_bytes in writes_to_perform.items():
                if len(data_bytes) != 40:
                    messagebox.showerror("FATAL ERROR", "Randomizer attempted to write a corrupt upgrade price block. Aborting.")
                    return
                exe_f.seek(offset)
                exe_f.write(data_bytes)
                                
    def _randomize_item_types(self):
        item_pool = []
        if self.item_type_full_random_checkbox.get() == 1:
            item_pool = list(self.item_name_to_id.keys())
        elif self.item_type_safe_swap_checkbox.get() == 1:
            item_pool = list(self.treasure_items | self.key_items)
        else:
            return

        valid_items_to_randomize = []
        original_types = []
        with open(self.active_backup_path, 'rb') as bak_f:
            for item_name in item_pool:
                item_id = self.item_name_to_id.get(item_name)
                if item_id is None:
                    continue 
                
                valid_items_to_randomize.append(item_name)
                bak_f.seek(self.item_type_base_offset + item_id)
                original_types.append(struct.unpack('<B', bak_f.read(1))[0])
        
        _random.shuffle(original_types)
        
        writes_to_perform = {}
        for i, item_name in enumerate(valid_items_to_randomize):
            item_id = self.item_name_to_id.get(item_name)
            offset = self.item_type_base_offset + item_id
            writes_to_perform[offset] = struct.pack('<B', original_types[i])
            
        with open(self.exe_path, 'rb+') as exe_f:
            for offset, data_bytes in writes_to_perform.items():
                exe_f.seek(offset); exe_f.write(data_bytes)
                
    def _randomize_item_sizes(self):
        min_w_var = int(self.item_size_w_min_entry.get()) / 100
        max_w_var = int(self.item_size_w_max_entry.get()) / 100
        min_h_var = int(self.item_size_h_min_entry.get()) / 100
        max_h_var = int(self.item_size_h_max_entry.get()) / 100

        writes_to_perform = {}
        with open(self.active_backup_path, 'rb') as bak_f:
            for item_name, offset_str in self.item_size_offsets.items():
                offset = int(offset_str, 16)
                bak_f.seek(offset)
                original_block_16 = bak_f.read(16)
                
                item_id, original_w, original_h, _, _ = struct.unpack('<I B B 2x f f', original_block_16)
                
                if original_w <= 2:
                    new_w = original_w + _random.choice([-1, 0, 0, 1])
                else:
                    new_w = int(round(_random.uniform(original_w * min_w_var, original_w * max_w_var)))

                if original_h <= 2:
                    new_h = original_h + _random.choice([-1, 0, 0, 1])
                else:
                    new_h = int(round(_random.uniform(original_h * min_h_var, original_h * max_h_var)))
                
                new_w = max(1, min(new_w, 15))
                new_h = max(1, min(new_h, 15))
                
                float_x = (new_w - 1.0) / 2.0
                float_y = (new_h - 1.0) / 2.0
                
                num_31s = new_w * new_h
                num_31s = min(num_31s, 16)
                num_00s = 16 - num_31s
                post_block = (b'\x31' * num_31s) + (b'\x00' * num_00s)

                dynamic_block = struct.pack('<I B B 2x f f', item_id, new_w, new_h, float_x, float_y)
                new_32_byte_block = dynamic_block + post_block
                writes_to_perform[offset] = new_32_byte_block
                
        with open(self.exe_path, 'rb+') as exe_f:
            for offset, data_bytes in writes_to_perform.items():
                exe_f.seek(offset); exe_f.write(data_bytes)
                
    def _randomize_item_combinations(self):
        default_combos = self.combination_data["default_combinations"]
        
        if self.randomize_combo_logic_checkbox.get() == 1:
            # --- LOGICAL FUSING ENABLED ---
            pools = {
                'GEMS': [], 'KEYS': [], 'HEALING': [], 'WEAPONS_AND_ATTACHMENTS': [], 'OTHER': []
            }
            gem_names = {"Green Catseye", "Red Catseye", "Yellow Catseye", "Green Eye", "Red Eye", "Blue Eye", "Green Gem", "Red Gem", "Purple Gem", "Green Stone of Judgement", "Red Stone of Faith", "Blue Stone of Treason"}
            key_names = {"Emblem (Right Half)", "Emblem (Left Half)", "Moonstone (Right Half)", "Moonstone (Left Half)", "Crown Jewel", "Royal Insignia"}
            healing_names = {"Green Herb", "Red Herb", "Yellow Herb", "Mixed Herbs (G+G)", "Mixed Herbs (G+R)", "Mixed Herbs (G+Y)", "Mixed Herbs (R+Y)"}
            
            def get_pool_key(item_name):
                if item_name in gem_names: return 'GEMS'
                if item_name in key_names: return 'KEYS'
                if item_name in healing_names: return 'HEALING'
                if item_name in self.all_data["weapons"] or item_name in self.all_data["items"]["categories"]["Attachments"]: return 'WEAPONS_AND_ATTACHMENTS'
                return 'OTHER'
            
            all_ingredients = []
            all_results = []
            for combo in default_combos:
                all_ingredients.append(combo["item_a"])
                all_ingredients.append(combo["item_b"])
                all_results.append(combo["result"])
            
            for item_name in set(all_ingredients + all_results):
                pools[get_pool_key(item_name)].append(self.item_name_to_id.get(item_name, 0xFFFF))
            
            for pool in pools.values():
                _random.shuffle(pool)

            final_bytes = bytearray()
            for combo in default_combos:
                id_a = self.item_name_to_id.get(combo["item_a"], 0xFFFF)
                id_b = self.item_name_to_id.get(combo["item_b"], 0xFFFF)
                id_r = self.item_name_to_id.get(combo["result"], 0xFFFF)
                
                key_a = get_pool_key(combo["item_a"])
                key_b = get_pool_key(combo["item_b"])
                key_r = get_pool_key(combo["result"])
                
                new_id_a = pools[key_a].pop(0) if pools[key_a] else id_a
                new_id_b = pools[key_b].pop(0) if pools[key_b] else id_b
                new_id_r = pools[key_r].pop(0) if pools[key_r] else id_r

                final_bytes.extend(struct.pack('<HHH', new_id_a, new_id_b, new_id_r))

        else:
            # --- LOGICAL FUSING DISABLED (Original Behavior) ---
            ingredients_a, ingredients_b, results = [], [], []
            for combo in default_combos:
                ingredients_a.append(self.item_name_to_id.get(combo["item_a"], 0xFFFF))
                ingredients_b.append(self.item_name_to_id.get(combo["item_b"], 0xFFFF))
                results.append(self.item_name_to_id.get(combo["result"], 0xFFFF))

            if self.randomize_combo_ingredients_checkbox.get() == 1:
                _random.shuffle(ingredients_a)
                _random.shuffle(ingredients_b)
            
            if self.randomize_combo_results_checkbox.get() == 1:
                _random.shuffle(results)
                
            final_bytes = bytearray()
            for i in range(len(default_combos)):
                final_bytes.extend(struct.pack('<HHH', ingredients_a[i], ingredients_b[i], results[i]))
            
        with open(self.exe_path, 'rb+') as f:
            list_offset = int(self.combination_data["list_base_offset"], 16)
            f.seek(list_offset)
            f.write(final_bytes)
            
    def _randomize_starter_inventories(self):
        if not self.randomize_starter_inv_checkbox.get() == 1: return

        writes_to_perform = {}
        with open(self.active_backup_path, 'rb') as bak_f:
            all_modes_data = self.all_data["game_mode_starters"]
            for mode_name, slots in all_modes_data.items():
                if not isinstance(slots, list): continue

                item_pools = {"Weapon": [], "Ammo": [], "Healing": [], "Case": [], "Grenade": [], "Attachment": []}
                for slot in slots:
                    bak_f.seek(int(slot['id_offset'], 16))
                    item_id = struct.unpack('<B', bak_f.read(1))[0]
                    
                    pool_key = "Weapon" # Default
                    slot_name_lower = slot['name'].lower()
                    if "ammo" in slot_name_lower: pool_key = "Ammo"
                    elif "healing" in slot_name_lower: pool_key = "Healing"
                    elif "case" in slot_name_lower: pool_key = "Case"
                    elif "grenade" in slot_name_lower: pool_key = "Grenade"
                    elif "attachment" in slot_name_lower: pool_key = "Attachment"

                    item_pools[pool_key].append(item_id)
                
                for pool in item_pools.values():
                    _random.shuffle(pool)

                for slot in slots:
                    pool_key = "Weapon"
                    slot_name_lower = slot['name'].lower()
                    if "ammo" in slot_name_lower: pool_key = "Ammo"
                    elif "healing" in slot_name_lower: pool_key = "Healing"
                    elif "case" in slot_name_lower: pool_key = "Case"
                    elif "grenade" in slot_name_lower: pool_key = "Grenade"
                    elif "attachment" in slot_name_lower: pool_key = "Attachment"
                    
                    if item_pools[pool_key]:
                        new_id = item_pools[pool_key].pop(0)
                        writes_to_perform[int(slot['id_offset'], 16)] = struct.pack('<B', new_id)

        with open(self.exe_path, 'rb+') as exe_f:
            for offset, data_byte in writes_to_perform.items():
                exe_f.seek(offset); exe_f.write(data_byte)
            
    def _randomize_shooting_range(self):
        slots_data = self.all_data["shooting_range"]["slots"]
        item_id_pool = []
        processed_group_ids = set()

        with open(self.active_backup_path, 'rb') as bak_f:
            for slot in slots_data:
                group_key = slot.get("pair_id")
                if group_key and group_key in processed_group_ids:
                    continue
                if group_key:
                    processed_group_ids.add(group_key)
                
                bak_f.seek(int(slot['id_offset'], 16))
                item_id_pool.append(struct.unpack('<B', bak_f.read(1))[0])
        
        _random.shuffle(item_id_pool)
        
        writes_to_perform = {}
        processed_group_ids.clear()
        
        for slot in slots_data:
            group_key = slot.get("pair_id")
            if group_key:
                if group_key in processed_group_ids: continue
                processed_group_ids.add(group_key)
                
                if not item_id_pool: break
                new_id = item_id_pool.pop(0)
                group_members = [s for s in slots_data if s.get("pair_id") == group_key]
                for member in group_members:
                    writes_to_perform[int(member['id_offset'], 16)] = struct.pack('<B', new_id)
            else:
                if not item_id_pool: break
                new_id = item_id_pool.pop(0)
                writes_to_perform[int(slot['id_offset'], 16)] = struct.pack('<B', new_id)
                
        with open(self.exe_path, 'rb+') as exe_f:
            for offset, data_byte in writes_to_perform.items():
                exe_f.seek(offset); exe_f.write(data_byte)
                
    def _randomize_money_health(self):
        stats_to_randomize = []
        if self.randomize_money_checkbox.get():
            stats_to_randomize.append({"name": "Leon's Starting Money", "min": 1, "max": 100000})
        if self.randomize_health_checkbox.get():
            stats_to_randomize.append({"name": "Leon's Starting Health", "min": 100, "max": 2400})
            stats_to_randomize.append({"name": "Ashley's Starting Health", "min": 100, "max": 2400})

        if not stats_to_randomize: return

        all_stats_config = self.all_data["starter_money_health"]["stats"]
        writes_to_perform = []

        for random_config in stats_to_randomize:
            stat_name = random_config["name"]
            stat_info = next((s for s in all_stats_config if s["name"] == stat_name), None)
            if stat_info:
                new_value = _random.randint(random_config["min"], random_config["max"])
                data_bytes = struct.pack(stat_info["dtype"], new_value)
                writes_to_perform.append({"bytes": data_bytes, "offsets": stat_info["offsets"]})

        if writes_to_perform:
            with open(self.exe_path, 'rb+') as f:
                for write in writes_to_perform:
                    for offset_str in write["offsets"]:
                        f.seek(int(offset_str, 16)); f.write(write["bytes"])
                        
    # --- END OF RANDOMIZER SECTION ---
    

    # --- START OF ITEM TYPE EDITOR SECTION ---
    def _create_item_type_editor_tab(self, parent_frame):
        self.item_type_placeholder_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.item_type_placeholder_frame.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(self.item_type_placeholder_frame, text="Item Type Editor", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.THEME_COLOR).pack(pady=(10, 20))
        ctk.CTkLabel(self.item_type_placeholder_frame, text="This section allows you to change the fundamental type of an item (e.g., from a Treasure to a Key).\n\nSelect an executable to load the editor.",
                     justify="center", wraplength=500).pack(pady=10)

    def _build_item_type_editor_once(self):
        self.item_type_placeholder_frame.destroy()
        type_tab = self.tabs["Item Type Editor"]
        type_tab.grid_rowconfigure(1, weight=1)
        type_tab.grid_columnconfigure(0, weight=1)
        
        top_controls = ctk.CTkFrame(type_tab, fg_color="transparent")
        top_controls.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")

        # --- MODIFIED LOGIC ---
        self.item_type_search_entry = ctk.CTkEntry(top_controls, placeholder_text="Search by Name or ID...")
        self.item_type_search_entry.pack(fill="x", expand=True)
        self.item_type_search_entry.bind("<KeyRelease>", self._update_item_type_display)
        
        self.item_type_frame = ctk.CTkScrollableFrame(type_tab)
        self.item_type_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
        self.item_type_frame.grid_columnconfigure(0, weight=1)
        self.item_type_frame.grid_columnconfigure(1, minsize=300)

        bottom_frame = ctk.CTkFrame(type_tab)
        bottom_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        self.reset_types_button = ctk.CTkButton(bottom_frame, text="Reset All Types from Backup", state="disabled", command=self.reset_item_type_changes, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        self.reset_types_button.pack(side="left", padx=(10,5), pady=10, expand=True, fill="x")
        self.apply_types_button = ctk.CTkButton(bottom_frame, text="Apply All Type Changes", state="disabled", command=self.apply_item_type_changes, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
        self.apply_types_button.pack(side="left", padx=(5,10), pady=10, expand=True, fill="x")
        
        dropdown_kwargs = {"fg_color": self.THEME_COLOR, "button_color": self.THEME_COLOR, "button_hover_color": self.THEME_COLOR_HOVER}
        
        self.item_type_widgets = {}
        all_item_types = sorted(self.item_type_map.values())
        
        mousewheel_func = lambda event: self._on_mousewheel(event, self.item_type_frame)
        
        with open(self.exe_path, 'rb') as f:
            for cat_name, cat_items in self.all_data["items"]["categories"].items():
                sorted_cat_items = sorted(cat_items)
                
                div_frame = ctk.CTkFrame(self.item_type_frame, fg_color=self.SECONDARY_COLOR); div_frame.bind("<MouseWheel>", mousewheel_func)
                div_label = ctk.CTkLabel(div_frame, text=cat_name, font=ctk.CTkFont(weight="bold")); div_label.bind("<MouseWheel>", mousewheel_func)
                div_label.pack(side="left", padx=10, pady=3)
                self.item_type_widgets[f"---{cat_name}---"] = {"frame": div_frame, "is_divider": True}

                for item_name in sorted_cat_items:
                    if item_name not in self.item_name_to_id: continue
                    item_id = self.item_name_to_id[item_name]
                    
                    offset = self.item_type_base_offset + item_id
                    f.seek(offset)
                    type_val = struct.unpack('<B', f.read(1))[0]
                    self.original_item_types[item_name] = type_val
                    current_type_name = self.item_type_map.get(type_val, "Unknown")
                    
                    label = ctk.CTkLabel(self.item_type_frame, text=item_name, anchor="w"); label.bind("<MouseWheel>", mousewheel_func)
                    dropdown = ctk.CTkOptionMenu(self.item_type_frame, values=all_item_types, **dropdown_kwargs); dropdown.bind("<MouseWheel>", mousewheel_func)
                    dropdown.set(current_type_name)
                    self.item_type_widgets[item_name] = {"label": label, "dropdown": dropdown}

        self.item_type_editor_loaded = True
        self.apply_types_button.configure(state="normal")
        self._update_reset_button_states()
        self._update_item_type_display()
        self._update_stable_status()
        
    def apply_item_type_changes(self):
        if not self.exe_path: return
        writes_to_perform = {}
        for item_name, widgets in self.item_type_widgets.items():
            if widgets.get("is_divider"): continue
            selected_type_name = widgets["dropdown"].get()
            new_type_val = self.item_type_reverse_map.get(selected_type_name)
            if new_type_val is not None and new_type_val != self.original_item_types.get(item_name):
                item_id = self.item_name_to_id[item_name]
                offset = self.item_type_base_offset + item_id
                writes_to_perform[offset] = new_type_val
        if not writes_to_perform: 
            self.status_bar.configure(text="No item type changes to apply.")
            return
        try:
            with open(self.exe_path, 'rb+') as f:
                for offset, type_val in writes_to_perform.items():
                    f.seek(offset); f.write(struct.pack('<B', type_val))
            
            for offset, type_val in writes_to_perform.items():
                item_id = offset - self.item_type_base_offset
                item_name = self.item_id_to_name.get(item_id)
                if item_name: self.original_item_types[item_name] = type_val
            
            self._update_stable_status()
            self._show_success_message(f"Applied {len(writes_to_perform)} item type change(s)!")
        except Exception as e:
            messagebox.showerror("Write Error", f"Could not apply item type changes: {e}")
            
    def reset_item_type_changes(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path): messagebox.showerror("Error", "Valid backup source not found."); return
        if not messagebox.askyesno("Confirm Reset", "Are you sure you want to reset ALL item types to their original values?"): return
        try:
            max_id = max(self.item_name_to_id.values())
            bytes_to_read = max_id + 1
            with open(self.active_backup_path, 'rb') as bak_f:
                bak_f.seek(self.item_type_base_offset); original_bytes = bak_f.read(bytes_to_read)
            with open(self.exe_path, 'rb+') as exe_f:
                exe_f.seek(self.item_type_base_offset); exe_f.write(original_bytes)
            
            for widget_set in self.item_type_widgets.values():
                if widget_set.get("is_divider"): widget_set["frame"].destroy()
                else: widget_set["label"].destroy(); widget_set["dropdown"].destroy()
            self._build_item_type_editor_once()
            
            self._show_success_message("Successfully reset all item types from backup.")
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset item types: {e}")
            
    # --- END OF ITEM TYPE EDITOR SECTION ---
    
    # --- START OF ITEM SIZE EDITOR SECTION ---
    def _create_item_size_editor_tab(self, parent_frame):
        self.item_size_placeholder_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.item_size_placeholder_frame.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(self.item_size_placeholder_frame, text="Item Size Editor", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.THEME_COLOR).pack(pady=(10, 20))
        ctk.CTkLabel(self.item_size_placeholder_frame, text="This section allows you to change the inventory grid size of items.\nSelect an executable to load the editor.",
                     justify="center", wraplength=500).pack(pady=10)

    def _build_item_size_editor_once(self):
        self.item_size_placeholder_frame.destroy()
        size_tab = self.tabs["Item Size Editor"]
        size_tab.grid_rowconfigure(1, weight=1)
        size_tab.grid_columnconfigure(0, weight=1)
        
        top_controls = ctk.CTkFrame(size_tab, fg_color="transparent")
        top_controls.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        top_controls.grid_columnconfigure(0, weight=1)
        
        # --- MODIFIED LOGIC ---
        self.item_size_search_entry = ctk.CTkEntry(top_controls, placeholder_text="Search by Name or ID...")
        self.item_size_search_entry.grid(row=0, column=0, padx=(0,10), sticky="ew")
        self.item_size_search_entry.bind("<KeyRelease>", self._update_item_size_display)
        
        self.item_size_read_button = ctk.CTkButton(top_controls, text="Read/Refresh", width=120, command=self._refresh_item_size_editor, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        self.item_size_read_button.grid(row=0, column=1, sticky="e")
        
        self.item_size_frame = ctk.CTkScrollableFrame(size_tab)
        self.item_size_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
        self.item_size_frame.grid_columnconfigure(0, weight=1)
        self.item_size_frame.grid_columnconfigure(1, minsize=150)
        
        bottom_frame = ctk.CTkFrame(size_tab)
        bottom_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure((0,1), weight=1)
        self.reset_sizes_button = ctk.CTkButton(bottom_frame, text="Reset All Sizes from Backup", state="disabled", command=self.reset_all_item_sizes, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        self.reset_sizes_button.grid(row=0, column=0, padx=(10,5), pady=10, sticky="ew")
        self.apply_sizes_button = ctk.CTkButton(bottom_frame, text="Apply All Size Changes", state="disabled", command=self.apply_item_size_changes, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
        self.apply_sizes_button.grid(row=0, column=1, padx=(5,10), pady=10, sticky="ew")
        
        mousewheel_func = lambda event: self._on_mousewheel(event, self.item_size_frame)
        self.item_size_widgets = {}
        for item_name in self.sorted_sizable_items:
            label = ctk.CTkLabel(self.item_size_frame, text=item_name, anchor="w"); label.bind("<MouseWheel>", mousewheel_func)
            size_frame = ctk.CTkFrame(self.item_size_frame, fg_color="transparent"); size_frame.bind("<MouseWheel>", mousewheel_func)
            width_entry = ctk.CTkEntry(size_frame, width=50); width_entry.bind("<MouseWheel>", mousewheel_func)
            width_entry.pack(side="left", padx=(0,5))
            x_label = ctk.CTkLabel(size_frame, text="x"); x_label.pack(side="left"); x_label.bind("<MouseWheel>", mousewheel_func)
            height_entry = ctk.CTkEntry(size_frame, width=50); height_entry.bind("<MouseWheel>", mousewheel_func)
            height_entry.pack(side="left", padx=(5,0))
            self.item_size_widgets[item_name] = {"label": label, "size_frame": size_frame, "width": width_entry, "height": height_entry}

        self.item_size_editor_loaded = True
        self.apply_sizes_button.configure(state="normal")
        self._update_reset_button_states()
            
        self._refresh_item_size_editor()
        self._update_item_size_display()

    def _refresh_item_size_editor(self):
        if not self.item_size_editor_loaded or not self.exe_path:
            return
        try:
            with open(self.exe_path, 'rb') as f:
                for item_name in self.sorted_sizable_items:
                    offset = int(self.item_size_offsets[item_name], 16)
                    f.seek(offset)
                    block = f.read(32)
                    self.original_item_sizes[item_name] = block
                    
                    _, width, height, _, _ = struct.unpack('<I B B 2x f f', block[:16])
                    
                    widgets = self.item_size_widgets[item_name]
                    widgets["width"].delete(0, "end"); widgets["width"].insert(0, str(width))
                    widgets["height"].delete(0, "end"); widgets["height"].insert(0, str(height))
            self._update_stable_status()
        except Exception as e:
            messagebox.showerror("Read Error", f"Could not read item sizes from the EXE: {e}")

    def apply_item_size_changes(self):
        if not self.exe_path: return
        writes_to_perform = {}
        try:
            for item_name, widgets in self.item_size_widgets.items():
                new_w = int(widgets["width"].get())
                new_h = int(widgets["height"].get())

                float_x = (new_w - 1.0) / 2.0
                float_y = (new_h - 1.0) / 2.0
                
                item_id = self.item_name_to_id[item_name]
                
                num_31s = new_w * new_h
                num_31s = min(num_31s, 16)
                num_00s = 16 - num_31s
                post_block = (b'\x31' * num_31s) + (b'\x00' * num_00s)

                dynamic_block = struct.pack('<I B B 2x f f', item_id, new_w, new_h, float_x, float_y)
                new_block = dynamic_block + post_block
                
                if new_block != self.original_item_sizes.get(item_name):
                    offset = int(self.item_size_offsets[item_name], 16)
                    writes_to_perform[offset] = (item_name, new_block)
        except ValueError:
            messagebox.showerror("Invalid Input", "Width and Height must be valid integers.")
            return
        except KeyError:
            messagebox.showerror("Item ID Error", f"Could not find the Item ID for '{item_name}'. Check re4_data.json.")
            return

        if not writes_to_perform:
            self.status_bar.configure(text="No item size changes to apply.")
            return

        try:
            with open(self.exe_path, 'rb+') as f:
                for offset, (item_name, block) in writes_to_perform.items():
                    f.seek(offset)
                    f.write(block)
                    self.original_item_sizes[item_name] = block
            
            self._refresh_item_size_editor()
            self._show_success_message(f"Applied {len(writes_to_perform)} item size change(s)!")
        except Exception as e:
            messagebox.showerror("Write Error", f"Could not apply item size changes: {e}")
            
    def reset_all_item_sizes(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path): messagebox.showerror("Error", "Valid backup source not found."); return
        if not messagebox.askyesno("Confirm Reset", "Are you sure you want to reset ALL item sizes to their original values?"):
            return
        
        try:
            with open(self.active_backup_path, 'rb') as bak_f, open(self.exe_path, 'rb+') as exe_f:
                for item_name, offset_str in self.item_size_offsets.items():
                    offset = int(offset_str, 16)
                    bak_f.seek(offset)
                    original_block = bak_f.read(32)
                    exe_f.seek(offset)
                    exe_f.write(original_block)
            
            self._refresh_item_size_editor()
            self._show_success_message("Successfully reset all item sizes from backup.")
                
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset item sizes: {e}")
            
    # --- END OF ITEM SIZE EDITOR SECTION ---
    
    # --- START OF SHOOTING RANGE EDITOR SECTION ---
    def _create_shooting_range_tab(self, parent_frame):
        self.shooting_range_placeholder_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.shooting_range_placeholder_frame.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(self.shooting_range_placeholder_frame, text="Shooting Range Editor", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.THEME_COLOR).pack(pady=(10, 20))
        ctk.CTkLabel(self.shooting_range_placeholder_frame, text="This section allows you to edit the weapons and items available in the Shooting Range.\n\nSelect an executable to load the editor.",
                     justify="center", wraplength=500).pack(pady=10)

    def _build_shooting_range_editor_once(self):
        self.shooting_range_placeholder_frame.destroy()
        sr_tab = self.tabs["Shooting Range Items"]
        sr_tab.grid_rowconfigure(0, weight=1); sr_tab.grid_columnconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(sr_tab)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1); main_frame.grid_columnconfigure(0, weight=1)

        self.shooting_range_items_frame = ctk.CTkScrollableFrame(main_frame, label_text="Shooting Range Items")
        self.shooting_range_items_frame.grid(row=0, column=0, padx=10, pady=(0,10), sticky="nsew")

        processed_pair_ids = set()
        slots_data = self.all_data["shooting_range"]["slots"]

        for slot_info in slots_data:
            pair_id = slot_info.get("pair_id")

            if pair_id:
                if pair_id in processed_pair_ids:
                    continue 
                
                processed_pair_ids.add(pair_id)
                
                pair_members = [s for s in slots_data if s.get("pair_id") == pair_id]
                
                first_member = pair_members[0]
                display_name = first_member["name"].replace(" Pair A", "").replace(" Pair B", "")

                combined_slot_info = {
                    "name": display_name,
                    "is_group": True,
                    "offsets": [s["id_offset"] for s in pair_members],
                    "default_id": first_member["default_id"]
                }
                self._create_shooting_range_row(self.shooting_range_items_frame, combined_slot_info)
            else:
                self._create_shooting_range_row(self.shooting_range_items_frame, slot_info)

        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        bottom_frame.grid_columnconfigure((0, 1), weight=1)
        self.reset_shooting_range_button = ctk.CTkButton(bottom_frame, text="Reset From Backup ↺", state="disabled", command=self.reset_shooting_range_data, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        self.reset_shooting_range_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.apply_shooting_range_button = ctk.CTkButton(bottom_frame, text="Apply All Changes", state="disabled", command=self.apply_shooting_range_data, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
        self.apply_shooting_range_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")

        self.shooting_range_editor_loaded = True
        if self.exe_path:
            self.apply_shooting_range_button.configure(state="normal")
            self.reset_shooting_range_button.configure(state="normal")
            self.read_shooting_range_data()
            
    def _create_shooting_range_row(self, parent, slot_info):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=5)
        frame.grid_columnconfigure(1, weight=1)

        label_text = slot_info["name"]
        if slot_info.get("comment"):
            label_text += f" ({slot_info['comment']})"
        
        main_label = ctk.CTkLabel(frame, text=label_text + ":", width=250, anchor="w")
        main_label.grid(row=0, column=0, padx=(10,5), pady=10)
        
        entry_item = ctk.CTkEntry(frame, state="disabled", placeholder_text="<Empty>")
        entry_item.grid(row=0, column=1, sticky="ew", padx=5, pady=10)
        
        widget_dict = {"frame": frame, "label": main_label, "item_entry": entry_item, "slot_info": slot_info}

        button_item = ctk.CTkButton(frame, text="...", width=30, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda e=entry_item: self._open_shooting_range_item_selector(e))
        button_item.grid(row=0, column=2, padx=(0,10), pady=10)

        self.shooting_range_widgets.append(widget_dict)

    def _open_shooting_range_item_selector(self, entry_widget):
        def callback(selected_item):
            entry_widget.configure(state="normal")
            entry_widget.delete(0, "end")
            entry_widget.insert(0, selected_item)
            entry_widget.configure(state="disabled")
        ItemSelector(self, self.all_items_categorized, callback, title="Select Item")

    def read_shooting_range_data(self):
        if not self.shooting_range_editor_loaded or not self.exe_path: return
        try:
            with open(self.exe_path, 'rb') as f:
                for widgets in self.shooting_range_widgets:
                    slot_info = widgets["slot_info"]
                    
                    if slot_info.get("is_group"):
                        offset_to_read = int(slot_info["offsets"][0], 16)
                    else:
                        offset_to_read = int(slot_info["id_offset"], 16)

                    f.seek(offset_to_read)
                    item_id = struct.unpack('<B', f.read(1))[0]
                    item_name = self.item_id_to_name.get(item_id, "None")
                    
                    entry = widgets["item_entry"]
                    entry.configure(state="normal"); entry.delete(0, "end"); entry.insert(0, item_name); entry.configure(state="disabled")

            self._update_stable_status()
        except Exception as e:
            messagebox.showerror("Read Error", f"Could not read Shooting Range data: {e}")
            
    def apply_shooting_range_data(self):
        if not self.exe_path: return
        try:
            with open(self.exe_path, 'rb+') as f:
                for widgets in self.shooting_range_widgets:
                    slot_info = widgets["slot_info"]
                    item_name = widgets["item_entry"].get() or "None"
                    item_id = self.item_name_to_id.get(item_name, 0xFF)
                    
                    if slot_info.get("is_group"):
                        for offset_str in slot_info["offsets"]:
                            f.seek(int(offset_str, 16)); f.write(struct.pack('<B', item_id))
                    else:
                        f.seek(int(slot_info["id_offset"], 16)); f.write(struct.pack('<B', item_id))

            self._show_success_message("Applied all Shooting Range changes successfully!", callback=self.read_shooting_range_data)
        except Exception as e:
            messagebox.showerror("Write Error", f"Could not apply Shooting Range data changes: {e}")
            
    def reset_shooting_range_data(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path):
            messagebox.showerror("Error", "Valid backup source not found.")
            return
        if not messagebox.askyesno("Confirm Reset", "Are you sure you want to restore all Shooting Range items from your backup file?\n\nThis will overwrite any unsaved changes in this tab."):
            return
        try:
            with open(self.active_backup_path, 'rb') as f_bak, open(self.exe_path, 'rb+') as f_exe:
                slots_to_reset = self.all_data["shooting_range"]["slots"]
                
                for slot_info in slots_to_reset:
                    offset = int(slot_info["id_offset"], 16)
                    f_bak.seek(offset)
                    original_byte = f_bak.read(1)
                    f_exe.seek(offset)
                    f_exe.write(original_byte)

            self._show_success_message("Successfully restored Shooting Range data from backup.", callback=self.read_shooting_range_data)
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not restore Shooting Range data from backup: {e}")
           
    # --- END OF SHOOTING RANGE EDITOR SECTION ---
    
    # --- START OF STARTER MONEY-HEALTH EDITOR SECTION ---
    def _create_money_health_tab(self, parent_frame):
        self.money_health_placeholder_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.money_health_placeholder_frame.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(self.money_health_placeholder_frame, text="Starter Money & Health", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.THEME_COLOR).pack(pady=(10, 20))
        ctk.CTkLabel(self.money_health_placeholder_frame, text="This section allows you to edit the starting money and health for characters.\n\nSelect an executable to load the editor.",
                     justify="center", wraplength=500).pack(pady=10)

    def _build_money_health_editor_once(self):
        self.money_health_placeholder_frame.destroy()
        mh_tab = self.tabs["Starter Money-Health"]
        mh_tab.grid_rowconfigure(0, weight=1); mh_tab.grid_columnconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(mh_tab)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1); main_frame.grid_columnconfigure(0, weight=1)

        scroll_frame = ctk.CTkScrollableFrame(main_frame, label_text="Character Starting Stats")
        scroll_frame.grid(row=0, column=0, padx=10, pady=(0,10), sticky="nsew")
        scroll_frame.grid_columnconfigure(1, weight=1) # Let the entry field expand
        
        self.money_health_widgets = {}
        stats_to_edit = self.all_data["starter_money_health"]["stats"]
        
        # --- NEW: Define the max health values to display ---
        max_health_map = {
            "Leon's Starting Health": "(Max: 2400)",
            "Ashley's Starting Health": "(Max: 1200)"
        }

        for i, stat_info in enumerate(stats_to_edit):
            label = ctk.CTkLabel(scroll_frame, text=f"{stat_info['name']}:", anchor="w")
            label.grid(row=i, column=0, padx=10, pady=10, sticky="w")
            
            entry = ctk.CTkEntry(scroll_frame, placeholder_text="Enter value...")
            entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew")
            self.money_health_widgets[stat_info['name']] = entry
            
            # --- NEW: Check if this stat has a max health label to add ---
            if stat_info['name'] in max_health_map:
                max_health_text = max_health_map[stat_info['name']]
                max_label = ctk.CTkLabel(scroll_frame, text=max_health_text, anchor="w", text_color="gray50")
                max_label.grid(row=i, column=2, padx=10, pady=10, sticky="w")

        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        bottom_frame.grid_columnconfigure((0, 1), weight=1)
        self.reset_money_health_button = ctk.CTkButton(bottom_frame, text="Reset From Backup ↺", state="disabled", command=self.reset_money_health_data, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        self.reset_money_health_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.apply_money_health_button = ctk.CTkButton(bottom_frame, text="Apply All Changes", state="disabled", command=self.apply_money_health_data, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
        self.apply_money_health_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")

        self.money_health_editor_loaded = True
        if self.exe_path:
            self.apply_money_health_button.configure(state="normal")
            self.reset_money_health_button.configure(state="normal")
            self.read_money_health_data()

    def read_money_health_data(self):
        if not self.money_health_editor_loaded or not self.exe_path: return
        try:
            with open(self.exe_path, 'rb') as f:
                for stat_info in self.all_data["starter_money_health"]["stats"]:
                    f.seek(int(stat_info["offsets"][0], 16))
                    val, = struct.unpack(stat_info["dtype"], f.read(struct.calcsize(stat_info["dtype"])))
                    entry = self.money_health_widgets[stat_info["name"]]
                    entry.delete(0, "end"); entry.insert(0, str(val))
            self._update_stable_status()
        except Exception as e:
            messagebox.showerror("Read Error", f"Could not read money/health data: {e}")

    def apply_money_health_data(self):
        if not self.exe_path: return
        try:
            writes_to_perform = []
            for stat_info in self.all_data["starter_money_health"]["stats"]:
                entry = self.money_health_widgets[stat_info["name"]]
                val = int(entry.get())
                data_bytes = struct.pack(stat_info["dtype"], val)
                writes_to_perform.append({"bytes": data_bytes, "offsets": stat_info["offsets"]})

            with open(self.exe_path, 'rb+') as f:
                for write in writes_to_perform:
                    for offset_str in write["offsets"]:
                        f.seek(int(offset_str, 16)); f.write(write["bytes"])
            
            self._show_success_message("Applied starter money and health changes successfully!", callback=self.read_money_health_data)
        except ValueError:
            messagebox.showerror("Invalid Input", "All values must be valid integers.")
        except Exception as e:
            messagebox.showerror("Write Error", f"Could not apply money/health changes: {e}")
            
    def reset_money_health_data(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path): messagebox.showerror("Error", "Valid backup source not found."); return
        if not messagebox.askyesno("Confirm Reset", "Are you sure you want to reset starter money and health to their original values from the backup?"): return
        try:
            with open(self.active_backup_path, 'rb') as f_bak, open(self.exe_path, 'rb+') as f_exe:
                for stat_info in self.all_data["starter_money_health"]["stats"]:
                    data_size = struct.calcsize(stat_info["dtype"])
                    for offset_str in stat_info["offsets"]:
                        offset = int(offset_str, 16)
                        f_bak.seek(offset); original_bytes = f_bak.read(data_size)
                        f_exe.seek(offset); f_exe.write(original_bytes)
            
            self._show_success_message("Successfully reset money and health from backup.", callback=self.read_money_health_data)
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset money/health data: {e}")
            
    # --- END OF STARTER MONEY-HEALTH EDITOR SECTION ---
    
    # --- START OF ITEM COMBINATIONS EDITOR SECTION ---
    def _create_item_combinations_tab(self, parent_frame):
        self.combinations_placeholder_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.combinations_placeholder_frame.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(self.combinations_placeholder_frame, text="Item Combinations Editor", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.THEME_COLOR).pack(pady=(10, 20))
        ctk.CTkLabel(self.combinations_placeholder_frame, text="This section allows you to edit, add, and delete item combination recipes.\n\nSelect an executable to load the editor.",
                     justify="center", wraplength=500).pack(pady=10)
                     
    def _build_item_combinations_editor_once(self):
        self.combinations_placeholder_frame.destroy()
        combo_tab = self.tabs["Item Combinations Editor"]
        combo_tab.grid_rowconfigure(0, weight=1); combo_tab.grid_columnconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(combo_tab)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1); main_frame.grid_columnconfigure(0, weight=1)

        self.combinations_frame = ctk.CTkScrollableFrame(main_frame, label_text="Item A + Item B = Result")
        self.combinations_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        self.reset_combinations_button = ctk.CTkButton(bottom_frame, text="Reset All from Backup", state="disabled", command=self.reset_all_item_combinations, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        self.reset_combinations_button.pack(side="left", padx=(10,5), pady=10, expand=True, fill="x")
        self.apply_combinations_button = ctk.CTkButton(bottom_frame, text="Apply All Combination Changes", state="disabled", command=self.apply_item_combination_changes, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
        self.apply_combinations_button.pack(side="left", padx=(5,10), pady=10, expand=True, fill="x")

        self.combinations_editor_loaded = True
        self.apply_combinations_button.configure(state="normal")
        self._update_reset_button_states()
        
        self._refresh_combinations_editor()
        
    def _refresh_combinations_editor(self):
        if not self.combinations_editor_loaded or not self.exe_path: return
        
        for widget_dict in self.combination_widgets:
            widget_dict['frame'].destroy()
        self.combination_widgets = []
        
        if hasattr(self, 'add_combo_button'):
            self.add_combo_button.destroy()

        try:
            with open(self.exe_path, 'rb') as f:
                f.seek(int(self.combination_data["counter_offsets"][0], 16))
                current_count = struct.unpack('<B', f.read(1))[0]
                
                list_offset = int(self.combination_data["list_base_offset"], 16)
                for i in range(current_count):
                    f.seek(list_offset + (i * 6))
                    id_a, id_b, id_r = struct.unpack('<HHH', f.read(6))
                    name_a = self.item_id_to_name.get(id_a, "None")
                    name_b = self.item_id_to_name.get(id_b, "None")
                    name_r = self.item_id_to_name.get(id_r, "None")
                    self._create_combination_row(self.combinations_frame, i, (name_a, name_b, name_r))

            self.add_combo_button = ctk.CTkButton(self.combinations_frame, text="Add New Combination", fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=self._add_new_combination_row)
            self.add_combo_button.pack(fill="x", padx=10, pady=20)
            self.add_combo_button.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, self.combinations_frame))
            self._update_stable_status()

        except Exception as e:
            messagebox.showerror("Read Error", f"Could not read item combinations: {e}")
            
    def _add_new_combination_row(self):
        current_visible_rows = sum(1 for w in self.combination_widgets if not w['deleted'])
        if current_visible_rows >= self.combination_data.get("max_slots", 125):
            messagebox.showwarning("Limit Reached", f"Maximum of {self.combination_data.get('max_slots', 125)} combinations reached.")
            return
        self.add_combo_button.pack_forget()
        self._create_combination_row(self.combinations_frame, len(self.combination_widgets), ("None", "None", "None"))
        self.add_combo_button.pack(fill="x", padx=10, pady=20)
    
    def _delete_combination_row(self, frame_to_delete):
        for widget_dict in self.combination_widgets:
            if widget_dict["frame"] == frame_to_delete:
                widget_dict["deleted"] = True
                frame_to_delete.pack_forget()
                break
                
    def _create_combination_row(self, parent, index, data_tuple):
        name_a, name_b, name_r = data_tuple
        
        mousewheel_func = lambda event: self._on_mousewheel(event, parent)

        frame = ctk.CTkFrame(parent); frame.bind("<MouseWheel>", mousewheel_func)
        frame.pack(fill="x", padx=5, pady=5)
        frame.grid_columnconfigure((1, 4, 7), weight=1)

        label_idx = ctk.CTkLabel(frame, text=f"{index+1}."); label_idx.pack(side="left", padx=(10,5)); label_idx.bind("<MouseWheel>", mousewheel_func)
        
        entry_a = ctk.CTkEntry(frame, state="disabled"); entry_a.pack(side="left", expand=True, fill="x", padx=(0,2)); entry_a.bind("<MouseWheel>", mousewheel_func)
        entry_a.configure(state="normal"); entry_a.insert(0, name_a); entry_a.configure(state="disabled")
        
        entry_b = ctk.CTkEntry(frame, state="disabled"); entry_b.pack(side="left", expand=True, fill="x", padx=(0,2)); entry_b.bind("<MouseWheel>", mousewheel_func)
        entry_b.configure(state="normal"); entry_b.insert(0, name_b); entry_b.configure(state="disabled")

        entry_r = ctk.CTkEntry(frame, state="disabled"); entry_r.pack(side="left", expand=True, fill="x", padx=(0,2)); entry_r.bind("<MouseWheel>", mousewheel_func)
        entry_r.configure(state="normal"); entry_r.insert(0, name_r); entry_r.configure(state="disabled")
        
        # --- START OF THE FIX ---
        
        def create_callback(widget):
            def callback(selected_item):
                widget.configure(state="normal")
                widget.delete(0, "end")
                widget.insert(0, selected_item)
                widget.configure(state="disabled")
            return callback

        button_a = ctk.CTkButton(frame, text="...", width=30, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda w=entry_a: ItemSelector(self, self.all_items_categorized, create_callback(w), title="Select Combination Item"))
        button_a.pack(side="left"); button_a.bind("<MouseWheel>", mousewheel_func)
        
        label_plus = ctk.CTkLabel(frame, text="+", font=ctk.CTkFont(size=14)); label_plus.pack(side="left", padx=10); label_plus.bind("<MouseWheel>", mousewheel_func)
        
        # Move entry_b pack call after button_a pack call to restore order
        entry_b.pack_forget(); entry_b.pack(side="left", expand=True, fill="x", padx=(0,2))

        button_b = ctk.CTkButton(frame, text="...", width=30, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda w=entry_b: ItemSelector(self, self.all_items_categorized, create_callback(w), title="Select Combination Item"))
        button_b.pack(side="left"); button_b.bind("<MouseWheel>", mousewheel_func)

        label_equals = ctk.CTkLabel(frame, text="=", font=ctk.CTkFont(size=14, weight="bold")); label_equals.pack(side="left", padx=10); label_equals.bind("<MouseWheel>", mousewheel_func)

        # Move entry_r pack call after button_b pack call
        entry_r.pack_forget(); entry_r.pack(side="left", expand=True, fill="x", padx=(0,2))

        button_r = ctk.CTkButton(frame, text="...", width=30, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER, command=lambda w=entry_r: ItemSelector(self, self.all_items_categorized, create_callback(w), title="Select Combination Item"))
        button_r.pack(side="left"); button_r.bind("<MouseWheel>", mousewheel_func)

        # --- END OF THE FIX ---
        
        delete_button = ctk.CTkButton(frame, text="✕", width=30, fg_color="#C75450", hover_color="#A34440", command=lambda f=frame: self._delete_combination_row(f))
        delete_button.pack(side="left", padx=(10,5)); delete_button.bind("<MouseWheel>", mousewheel_func)
        
        # Re-pack the widgets in the correct visual order
        # This is a bit of a dance because pack order matters.
        all_widgets = [label_idx, entry_a, button_a, label_plus, entry_b, button_b, label_equals, entry_r, button_r, delete_button]
        for w in all_widgets:
            w.pack_forget()
        
        label_idx.pack(side="left", padx=(10,5))
        entry_a.pack(side="left", expand=True, fill="x", padx=(0,2))
        button_a.pack(side="left")
        label_plus.pack(side="left", padx=10)
        entry_b.pack(side="left", expand=True, fill="x", padx=(0,2))
        button_b.pack(side="left")
        label_equals.pack(side="left", padx=10)
        entry_r.pack(side="left", expand=True, fill="x", padx=(0,2))
        button_r.pack(side="left")
        delete_button.pack(side="left", padx=(10,5))
        
        widget_dict = {"frame": frame, "entry_a": entry_a, "entry_b": entry_b, "entry_r": entry_r, "deleted": False}
        self.combination_widgets.append(widget_dict)
         
    def _open_starter_item_selector(self, entry_widget):
        def callback(selected_item):
            entry_widget.configure(state="normal")
            entry_widget.delete(0, "end")
            entry_widget.insert(0, selected_item)
            entry_widget.configure(state="disabled")
            self._set_new_game_unsaved_status()
        ItemSelector(self, self.all_items_categorized, callback, title="Select Starter Item")
        
    def _add_new_combination_row(self):
        current_visible_rows = sum(1 for w in self.combination_widgets if not w['deleted'])
        if current_visible_rows >= self.combination_data.get("max_slots", 125):
            messagebox.showwarning("Limit Reached", f"Maximum of {self.combination_data.get('max_slots', 125)} combinations reached.")
            return
        self.add_combo_button.pack_forget()
        self._create_combination_row(self.combinations_frame, len(self.combination_widgets), ("None", "None", "None"))
        self.add_combo_button.pack(fill="x", padx=10, pady=20)
    
    def _delete_combination_row(self, frame_to_delete):
        for widget_dict in self.combination_widgets:
            if widget_dict["frame"] == frame_to_delete:
                widget_dict["deleted"] = True
                frame_to_delete.pack_forget()
                break
                
    def apply_item_combination_changes(self):
        if not self.exe_path: return
        try:
            final_combinations = []
            for widget_dict in self.combination_widgets:
                if widget_dict["deleted"]: continue
                name_a = widget_dict["entry_a"].get(); id_a = self.item_name_to_id.get(name_a, 0)
                name_b = widget_dict["entry_b"].get(); id_b = self.item_name_to_id.get(name_b, 0)
                name_r = widget_dict["entry_r"].get(); id_r = self.item_name_to_id.get(name_r, 0)
                final_combinations.append(struct.pack('<HHH', id_a, id_b, id_r))

            new_count = len(final_combinations)
            with open(self.exe_path, 'rb+') as f:
                list_offset = int(self.combination_data["list_base_offset"], 16)
                for i in range(self.combination_data.get("max_slots", 125)):
                    f.seek(list_offset + (i * 6))
                    if i < new_count: f.write(final_combinations[i])
                    else: f.write(b'\x00\x00\x00\x00\x00\x00')
                
                count_bytes = struct.pack('<B', new_count)
                for offset_str in self.combination_data["counter_offsets"]:
                    f.seek(int(offset_str, 16)); f.write(count_bytes)
            
            self._show_success_message(f"Applied {new_count} item combinations successfully!", callback=self._refresh_combinations_editor)

        except Exception as e:
            messagebox.showerror("Write Error", f"Could not apply item combination changes: {e}")

    def reset_all_item_combinations(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path): messagebox.showerror("Error", "Valid backup source not found."); return
        if not messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all item combinations to their original values from your backup?"): return
        try:
            with open(self.active_backup_path, 'rb') as bak_f, open(self.exe_path, 'rb+') as exe_f:
                # Reset counter bytes
                for offset_str in self.combination_data["counter_offsets"]:
                    offset = int(offset_str, 16)
                    bak_f.seek(offset)
                    original_byte = bak_f.read(1)
                    exe_f.seek(offset)
                    exe_f.write(original_byte)
                
                # Reset list data
                list_offset = int(self.combination_data["list_base_offset"], 16)
                list_size = self.combination_data.get("max_slots", 125) * 6
                bak_f.seek(list_offset)
                original_bytes = bak_f.read(list_size)
                exe_f.seek(list_offset)
                exe_f.write(original_bytes)

            self._show_success_message("Successfully reset all item combinations.", callback=self._refresh_combinations_editor)
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset item combinations: {e}")
            
    # --- END OF ITEM COMBINATIONS EDITOR SECTION ---
    
    # --- START OF RESET TO DEFAULT SECTION ---
    def reset_upgrade_prices(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path):
            messagebox.showerror("Error", "Valid backup source not found.")
            return
        weapon_name = self.upgrade_weapon_entry.get()
        if weapon_name == "-": return
        if not messagebox.askyesno("Confirm Reset", f"Are you sure you want to reset upgrade prices for the '{weapon_name}'?"): return
        offset_str = self.all_data["upgrade_prices"].get(weapon_name)
        if not offset_str: return
        try:
            with open(self.active_backup_path, 'rb') as bak_f:
                bak_f.seek(int(offset_str, 16) + 2)
                original_bytes = bak_f.read(40)
            with open(self.exe_path, 'rb+') as exe_f:
                exe_f.seek(int(offset_str, 16) + 2)
                exe_f.write(original_bytes)
            
            self.read_upgrade_prices()
            self._show_success_message(f"Reset upgrade prices for {weapon_name} to default.")
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset upgrade prices: {e}")

    def reset_all_upgrade_prices(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path):
            messagebox.showerror("Error", "Valid backup source not found.")
            return
        if not messagebox.askyesno("Confirm Global Reset", "⚠️ EXTREME WARNING ⚠️\n\nAre you sure you want to reset ALL upgrade prices for EVERY weapon back to their original values?"): return
        try:
            with open(self.active_backup_path, 'rb') as bak_f, open(self.exe_path, 'rb+') as exe_f:
                for offset_str in self.all_data["upgrade_prices"].values():
                    offset = int(offset_str, 16) + 2
                    bak_f.seek(offset)
                    original_bytes = bak_f.read(40)
                    exe_f.seek(offset)
                    exe_f.write(original_bytes)
            
            self.read_upgrade_prices()
            self._show_success_message("Successfully reset all upgrade prices for all weapons.")
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset all upgrade prices: {e}")

    def _reset_stat_block(self, weapon_name, stat_key, block_size, special_case_size=0):
        try:
            weapon_info = self.all_data["weapons"][weapon_name]
            if stat_key not in weapon_info: return False
            offsets = weapon_info[stat_key] if isinstance(weapon_info[stat_key], list) else [weapon_info[stat_key]]
            with open(self.active_backup_path, 'rb') as bak_f, open(self.exe_path, 'rb+') as exe_f:
                for offset_str in offsets:
                    offset = int(offset_str, 16)
                    size = special_case_size if special_case_size and weapon_name == "Matilda" else block_size
                    bak_f.seek(offset)
                    original_bytes = bak_f.read(size)
                    exe_f.seek(offset)
                    exe_f.write(original_bytes)
            return True
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset {stat_key} for {weapon_name}: {e}")
            return False

    def reset_all_stats(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path):
            messagebox.showerror("Error", "Valid backup source not found.")
            return
        weapon_name = self.weapon_editor_entry.get()
        if weapon_name == "-" or "---" in weapon_name: return
        if not messagebox.askyesno("Confirm Reset", f"Are you sure you want to reset ALL stats for the {weapon_name}?"): return
        
        self._reset_stat_block(weapon_name, "firepower_base_offset", 28)
        self._reset_stat_block(weapon_name, "capacity_base_offset", 22)
        self._reset_stat_block(weapon_name, "firing_speed_offsets", 20)
        self._reset_stat_block(weapon_name, "reload_speed_base_offset", 12)
        self._reset_stat_block(weapon_name, "max_levels_offsets", 4, special_case_size=6)
        
        self.on_weapon_selected(weapon_name)
        self._show_success_message(f"Reset all stats for {weapon_name}.")

    def reset_all_weapons_all_stats(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path):
            messagebox.showerror("Error", "Valid backup source not found.")
            return
        if not messagebox.askyesno("Confirm Global Reset", "⚠️ EXTREME WARNING ⚠️\n\nAre you sure you want to reset ALL stats for EVERY weapon in the game back to their original values?"): return
        
        for weapon_name in self.all_data["weapons"]:
            if "---" in weapon_name: continue
            self._reset_stat_block(weapon_name, "firepower_base_offset", 28)
            self._reset_stat_block(weapon_name, "capacity_base_offset", 22)
            self._reset_stat_block(weapon_name, "firing_speed_offsets", 20)
            self._reset_stat_block(weapon_name, "reload_speed_base_offset", 12)
            self._reset_stat_block(weapon_name, "max_levels_offsets", 4, special_case_size=6)

        self.on_weapon_selected(self.last_selected_weapon)
        self._show_success_message("Reset all stats for ALL weapons successfully.")

    def reset_selected_merchant(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path):
            messagebox.showerror("Error", "Valid backup source not found.")
            return
        selected_display_name = self.merchant_menu.get()
        if selected_display_name == "-": return
        if not messagebox.askyesno("Confirm Reset", f"Are you sure you want to reset the inventory for '{selected_display_name}' to its original state?"): return
        
        try:
            chapter_key = self.merchant_display_to_key[selected_display_name]
            chapter_info = self.all_data["merchant"][chapter_key]
            
            with open(self.active_backup_path, 'rb') as bak_f, open(self.exe_path, 'rb+') as exe_f:
                if chapter_info["stock_slots"] > 0:
                    offset = int(chapter_info["stock_offset"], 16)
                    size = chapter_info["stock_slots"] * 8
                    bak_f.seek(offset)
                    original_bytes = bak_f.read(size)
                    exe_f.seek(offset)
                    exe_f.write(original_bytes)
                if chapter_info["upgrade_slots"] > 0:
                    offset = int(chapter_info["upgrades_offset"], 16)
                    size = chapter_info["upgrade_slots"] * 8
                    bak_f.seek(offset)
                    original_bytes = bak_f.read(size)
                    exe_f.seek(offset)
                    exe_f.write(original_bytes)
            
            self.on_merchant_chapter_selected(selected_display_name)
            self._show_success_message(f"Reset '{selected_display_name}' successfully.")
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset merchant: {e}")

    def reset_all_merchants(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path):
            messagebox.showerror("Error", "Valid backup source not found.")
            return
        if not messagebox.askyesno("Confirm Global Reset", "⚠️ EXTREME WARNING ⚠️\n\nAre you sure you want to reset the inventory for ALL 21 merchants back to their original state?"): return
        
        try:
            with open(self.active_backup_path, 'rb') as bak_f, open(self.exe_path, 'rb+') as exe_f:
                for chapter_info in self.all_data["merchant"].values():
                    if chapter_info["stock_slots"] > 0:
                        offset = int(chapter_info["stock_offset"], 16)
                        size = chapter_info["stock_slots"] * 8
                        bak_f.seek(offset)
                        original_bytes = bak_f.read(size)
                        exe_f.seek(offset)
                        exe_f.write(original_bytes)
                    if chapter_info["upgrade_slots"] > 0:
                        offset = int(chapter_info["upgrades_offset"], 16)
                        size = chapter_info["upgrade_slots"] * 8
                        bak_f.seek(offset)
                        original_bytes = bak_f.read(size)
                        exe_f.seek(offset)
                        exe_f.write(original_bytes)

            self.on_merchant_chapter_selected(self.merchant_menu.get())
            self._show_success_message(f"Reset ALL merchants successfully.")
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset all merchants: {e}")

    def reset_price_group(self, category_name):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path): return
        try:
            start_index = self.sorted_price_item_list.index(category_name)
            end_index = len(self.sorted_price_item_list)
            for i in range(start_index + 1, len(self.sorted_price_item_list)):
                if self.sorted_price_item_list[i].startswith("---"): end_index = i; break
            
            items_to_reset = self.sorted_price_item_list[start_index+1:end_index]
            with open(self.active_backup_path, 'rb') as bak_f, open(self.exe_path, 'rb+') as exe_f:
                for item_name in items_to_reset:
                    offsets = self.all_data["master_item_prices"].get(item_name)
                    if not offsets: continue
                    bak_f.seek(int(offsets[0], 16) + 2); original_price_bytes = bak_f.read(2)
                    for offset_str in offsets: exe_f.seek(int(offset_str, 16) + 2); exe_f.write(original_price_bytes)
                for item_name in items_to_reset:
                    if item_name in self.stacking_offsets:
                        offset = self.stacking_offsets[item_name]
                        bak_f.seek(offset); original_stack_bytes = bak_f.read(2)
                        exe_f.seek(offset); exe_f.write(original_stack_bytes)
            
            self._refresh_price_data_and_labels(read_exe=True)
            self._show_success_message(f"Reset prices & stacking for group '{category_name.strip('- ')}'.")
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset price group: {e}")

    def reset_all_stock_prices(self):
        if not self.active_backup_path or not os.path.exists(self.active_backup_path): messagebox.showerror("Error", "Valid backup source not found."); return
        if not messagebox.askyesno("Confirm Reset", "Are you sure you want to reset ALL item prices and stack sizes to their original default values?"): return
        try:
            all_original_prices = {}
            with open(self.active_backup_path, 'rb') as bak_f:
                for item_name, offsets in self.all_data["master_item_prices"].items():
                    if offsets: bak_f.seek(int(offsets[0], 16) + 2); all_original_prices[item_name] = bak_f.read(2)
            with open(self.exe_path, 'rb+') as exe_f:
                for item_name, offsets in self.all_data["master_item_prices"].items():
                    if item_name in all_original_prices:
                        original_bytes = all_original_prices[item_name]
                        for offset_str in offsets: exe_f.seek(int(offset_str, 16) + 2); exe_f.write(original_bytes)
                with open(self.active_backup_path, 'rb') as bak_f:
                    for offset in set(self.stacking_offsets.values()):
                        bak_f.seek(offset); original_stack_bytes = bak_f.read(2)
                        exe_f.seek(offset); exe_f.write(original_stack_bytes)
            
            self._refresh_price_data_and_labels(read_exe=True)
            self._show_success_message("Successfully reset all item prices and stack sizes from backup.")
        except Exception as e:
            messagebox.showerror("Reset Error", f"Could not reset data: {e}")  
                
    # --- END OF RESET TO DEFAULT SECTION ---

    # --- General Purpose and Helpers ---
    def _on_mousewheel(self, event, scroll_frame):
        scroll_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _set_new_game_unsaved_status(self):
        self.status_bar.configure(text="Unsaved changes pending. Click 'Apply Changes' to save.")
        
    def open_item_selector(self, current_entry_widget, widget_data):
        def item_selection_callback(selected_item):
            previous_sacrifice_info = widget_data["data"].get("sacrifice_info")
            if previous_sacrifice_info:
                sacrificed_item_to_remove = previous_sacrifice_info["sacrificed_item"]
                if sacrificed_item_to_remove in self.pending_sacrifices: del self.pending_sacrifices[sacrificed_item_to_remove]
                del widget_data["data"]["sacrifice_info"]

            if selected_item in self.key_items: self.open_sacrifice_selector(selected_item, current_entry_widget, widget_data)
            else:
                current_entry_widget.configure(state="normal"); current_entry_widget.delete(0, "end"); current_entry_widget.insert(0, selected_item); current_entry_widget.configure(state="disabled")
                if self.price_editor_loaded: self._refresh_price_data_and_labels()
        ItemSelector(self, self.all_items_categorized, item_selection_callback, title="Select Item")
    
    def open_sacrifice_selector(self, key_item_name, current_entry_widget, widget_data):
        def sacrifice_selection_callback(key_item, sacrificed_item):
            display_text = f"{key_item} (via {sacrificed_item})"
            current_entry_widget.configure(state="normal"); current_entry_widget.delete(0, "end"); current_entry_widget.insert(0, display_text); current_entry_widget.configure(state="disabled")
            widget_data["data"]["sacrifice_info"] = {"key_item": key_item, "sacrificed_item": sacrificed_item}
            self.pending_sacrifices[sacrificed_item] = key_item
            if self.price_editor_loaded: self._refresh_price_data_and_labels()
        SacrificeSelector(self, key_item_name, sacrifice_selection_callback)

    def open_weapon_selector(self, current_entry_widget):
        def callback(selected_item): current_entry_widget.configure(state="normal"); current_entry_widget.delete(0, "end"); current_entry_widget.insert(0, selected_item); current_entry_widget.configure(state="disabled")
        all_merchant_weapons = {w for w in self.weapon_name_to_id.keys() if w != "None"}; found_weapons = set()
        categorized_data = {}
        for category, items in self.all_data["items"]["categories"].items():
            weapons_in_category = sorted([item for item in items if item in all_merchant_weapons])
            if weapons_in_category: categorized_data[category] = weapons_in_category; found_weapons.update(weapons_in_category)
        uncategorized_weapons = sorted(list(all_merchant_weapons - found_weapons))
        if uncategorized_weapons: categorized_data["Uncategorized"] = uncategorized_weapons
        weapon_data_for_selector = {"categories": categorized_data}
        ItemSelector(self, weapon_data_for_selector, callback, title="Select Weapon")
        
    def open_weapon_editor_selector(self):
        def callback(selected_weapon):
            self.weapon_editor_entry.configure(state="normal"); self.weapon_editor_entry.delete(0, "end"); self.weapon_editor_entry.insert(0, selected_weapon); self.weapon_editor_entry.configure(state="disabled")
            self.on_weapon_selected(selected_weapon)

        # --- THIS IS THE NEW LOGIC ---
        # Get all weapon names directly from the keys of the new "weapons" dictionary
        all_editable_weapons = {w for w in self.all_data["weapons"].keys() if "---" not in w}
        
        # We will create a simple categorized list for the selector UI
        categorized_data = {
            "Handguns": sorted([w for w in all_editable_weapons if "Handgun" in w or "Red9" in w or "Punisher" in w or "Blacktail" in w or "Matilda" in w]),
            "Shotguns": sorted([w for w in all_editable_weapons if "Shotgun" in w or "Riot" in w or "Striker" in w]),
            "Rifles": sorted([w for w in all_editable_weapons if "Rifle" in w]),
            "Magnums": sorted([w for w in all_editable_weapons if "Butterfly" in w or "Killer7" in w or "Handcannon" in w]),
            "Submachine Guns": sorted([w for w in all_editable_weapons if "TMP" in w or "Chicago" in w]),
            "Special": sorted([w for w in all_editable_weapons if "Mine Thrower" in w or "Bowgun" in w or "Knife" in w or "Rocket" in w or "Melee" in w or "P.R.L" in w])
        }
        # Filter out empty categories
        categorized_data = {k: v for k, v in categorized_data.items() if v}
        
        weapon_data_for_selector = {"categories": categorized_data}
        ItemSelector(self, weapon_data_for_selector, callback, title="Select Weapon")
        
    def open_upgrade_weapon_selector(self):
        def callback(selected_weapon): self._on_upgrade_weapon_selected(selected_weapon)
        upgradable_weapons = set(self.all_data["upgrade_prices"].keys()); found_weapons = set()
        categorized_data = {}
        for category, items in self.all_data["items"]["categories"].items():
            weapons_in_category = sorted([item for item in items if item in upgradable_weapons])
            if weapons_in_category: categorized_data[category] = weapons_in_category; found_weapons.update(weapons_in_category)
        uncategorized = sorted(list(upgradable_weapons - found_weapons))
        if uncategorized: categorized_data["Other"] = uncategorized
        data_for_selector = {"categories": categorized_data}
        ItemSelector(self, data_for_selector, callback, title="Select Upgradable Weapon")
        
    def open_ammo_selector(self):
        def callback(selected_ammo):
            self.ammo_type_entry.configure(state="normal"); self.ammo_type_entry.delete(0, "end"); self.ammo_type_entry.insert(0, selected_ammo); self.ammo_type_entry.configure(state="disabled")
        ItemSelector(self, self.all_data["ammo_types"], callback, title="Select Ammo Type")

    def _auto_load_exe(self):
        """Auto-load the exe from master editor."""
        try:
            if hasattr(self, 'exe_path_entry'):
                self.exe_path_entry.delete(0, "end")
                self.exe_path_entry.insert(0, self._master_exe)
            self.load_exe_data(self._master_exe)
        except Exception:
            pass

    def create_widgets(self):
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.top_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.top_frame, text="Game Executable:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=(20,10), pady=5, sticky="w")
        self.exe_path_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Click 'Browse...' to select your RE4 executable", state="disabled")
        self.exe_path_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.browse_button = ctk.CTkButton(self.top_frame, text="Browse...", command=self.select_exe_file, width=100, fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
        self.browse_button.grid(row=0, column=2, padx=(10, 20), pady=5)
        
        ctk.CTkLabel(self.top_frame, text="Backup Source (.bakp):", font=ctk.CTkFont(size=12)).grid(row=1, column=0, padx=(20,10), pady=5, sticky="w")
        self.backup_path_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Automatically loaded or select a custom backup...", state="disabled")
        self.backup_path_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.backup_browse_button = ctk.CTkButton(self.top_frame, text="Browse...", command=self.select_backup_file, width=100, fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        self.backup_browse_button.grid(row=1, column=2, padx=(10, 20), pady=5)
        
        tab_button_frame = ctk.CTkFrame(self, fg_color="transparent")
        tab_button_frame.grid(row=1, column=0, padx=20, pady=0, sticky="ew")
        self.tab_content_frame = ctk.CTkFrame(self, fg_color="gray17")
        self.tab_content_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.tab_content_frame.grid_rowconfigure(0, weight=1)
        self.tab_content_frame.grid_columnconfigure(0, weight=1)

        tab_names = [
            "Weapon Stat Editor", "Upgrades Prices Editor", "Merchant Stock Editor", 
            "Items Prices-Stacking", "Item Type Editor", "Item Size Editor", "Item Combinations Editor", 
            "Starter Inventories",  "Shooting Range Items", "Starter Money-Health", "Randomizer", "Mod Analyzer"
        ]
        
        for i in range(6):
            tab_button_frame.grid_columnconfigure(i, weight=1)

        for i, name in enumerate(tab_names):
            row = i // 6
            col = i % 6
            
            button = ctk.CTkButton(tab_button_frame, text=name, 
                                   command=lambda n=name: self.switch_tab(n),
                                   fg_color=self.SECONDARY_COLOR,
                                   hover_color=self.SECONDARY_COLOR_HOVER,
                                   corner_radius=4)
            button.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            
            content_frame = ctk.CTkFrame(self.tab_content_frame, fg_color="transparent")
            content_frame.grid(row=0, column=0, sticky="nsew")
            content_frame.grid_remove() 
            
            self.tab_buttons[name] = button
            self.tabs[name] = content_frame
                    
        self._create_weapon_stat_editor_tab(self.tabs["Weapon Stat Editor"])
        self._create_upgrade_prices_editor_tab(self.tabs["Upgrades Prices Editor"])
        self._create_merchant_stock_editor_tab(self.tabs["Merchant Stock Editor"])
        self._create_items_prices_stacking_tab(self.tabs["Items Prices-Stacking"])
        self._create_item_type_editor_tab(self.tabs["Item Type Editor"])
        self._create_item_size_editor_tab(self.tabs["Item Size Editor"])
        self._create_item_combinations_tab(self.tabs["Item Combinations Editor"])
        self._create_new_game_editor_tab(self.tabs["Starter Inventories"])
        self._create_money_health_tab(self.tabs["Starter Money-Health"])
        self._create_shooting_range_tab(self.tabs["Shooting Range Items"])
        self._create_randomizer_tab(self.tabs["Randomizer"])
        self._create_analyzer_tab(self.tabs["Mod Analyzer"])

        # --- NEW CONTAINER FRAME for status bar and link ---
        bottom_bar_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        bottom_bar_frame.grid_columnconfigure(0, weight=1) # Make status bar expand

        # --- PLACE EXISTING STATUS BAR into the new frame ---
        self.status_bar = ctk.CTkLabel(bottom_bar_frame, text="Ready.", anchor="w")
        self.status_bar.grid(row=0, column=0, sticky="w")
        self.default_status_color = self.status_bar.cget("text_color")
        
        # --- CREATE CLICKABLE CHANNEL LINK ---
        link_font = ctk.CTkFont(underline=True)
        link_color = "#66B2FF"
        link_hover_color = "#80C6FF"
        
        channel_label = ctk.CTkLabel(bottom_bar_frame, text="by Player7z", text_color=link_color, font=link_font, cursor="hand2")
        channel_label.grid(row=0, column=1, sticky="e")
        channel_label.bind("<Button-1>", lambda e: self._open_channel_link())
        channel_label.bind("<Enter>", lambda e: channel_label.configure(text_color=link_hover_color))
        channel_label.bind("<Leave>", lambda e: channel_label.configure(text_color=link_color))
        
        self.switch_tab("Weapon Stat Editor")

        self.firepower_entry.bind("<Return>", self.apply_firepower)
        self.capacity_entry.bind("<Return>", self.apply_capacity)
        self.fs_raw_entry.bind("<Return>", self.apply_firing_speed)
        self.rs_raw_entry.bind("<Return>", self.apply_reload_speed)
        for entry in [self.max_fp_entry, self.max_fs_entry, self.max_rs_entry, self.max_cap_entry]:
            entry.bind("<Return>", self.apply_max_levels)
            
    def switch_tab(self, name):
        if name == self.current_tab_name:
            return
            
        self.current_tab_name = name
        
        for btn_name, button in self.tab_buttons.items():
            if btn_name == name:
                button.configure(fg_color=self.THEME_COLOR, hover_color=self.THEME_COLOR_HOVER)
            else:
                button.configure(fg_color=self.SECONDARY_COLOR, hover_color=self.SECONDARY_COLOR_HOVER)
        
        for frame in self.tabs.values():
            frame.grid_remove()
        
        self.tabs[name].grid()
        
        self._on_tab_change()
        self._update_stable_status()

    def _on_tab_change(self):
        if not self.exe_path and self.current_tab_name not in ["Weapon Stat Editor", "Randomizer", "Mod Analyzer"]:
            messagebox.showwarning("EXE Not Found", "Please select an executable to use this feature.")
            return

        # --- BUILD LOGIC ---
        if self.current_tab_name in self.tab_build_functions:
            builder_info = self.tab_build_functions[self.current_tab_name]
            if not builder_info['loaded_flag']():
                builder_info['build_func']()
        
        # --- REFRESH LOGIC for tabs that need it upon switching ---
        if self.current_tab_name == "Items Prices-Stacking" and self.price_editor_loaded:
            self._refresh_price_data_and_labels()
        elif self.current_tab_name == "Upgrades Prices Editor" and self.upgrade_editor_loaded:
            self._on_upgrade_weapon_selected(self.upgrade_weapon_entry.get())
        elif self.current_tab_name == "Shooting Range Items" and self.shooting_range_editor_loaded:
            self.read_shooting_range_data()
        elif self.current_tab_name == "Starter Money-Health" and self.money_health_editor_loaded:
            self.read_money_health_data()
        # --- THIS IS THE MISSING LINE THAT FIXES THE BLANK TAB ---
        elif self.current_tab_name == "Item Combinations Editor" and self.combinations_editor_loaded:
            self._refresh_combinations_editor()
        # --- END OF FIX ---
        elif self.current_tab_name == "Starter Inventories" and self.new_game_editor_loaded:
            self.read_new_game_data()
        elif self.current_tab_name == "Item Size Editor" and self.item_size_editor_loaded:
            self._refresh_item_size_editor()
        elif self.current_tab_name == "Item Type Editor" and self.item_type_editor_loaded:
            self._update_stable_status()
            
    def _analyzer_compare_shooting_range(self, f_mod, f_base):
        changes = []
        slots_data = self.all_data["shooting_range"]["slots"]
        processed_group_ids = set()
        
        all_labels = []
        for slot_info in slots_data:
            group_key = slot_info.get("pair_id")
            if group_key and group_key in processed_group_ids: continue
            
            if group_key:
                processed_group_ids.add(group_key)
                first_member = next(s for s in slots_data if s.get("pair_id") == group_key)
                display_name = first_member["name"].replace(" Pair A", "")
                all_labels.append(display_name)
            else:
                all_labels.append(slot_info["name"])
        
        max_label_length = max(len(label) for label in all_labels) if all_labels else 0
        processed_group_ids.clear()

        for slot_info in slots_data:
            group_key = slot_info.get("pair_id")
            if group_key:
                if group_key in processed_group_ids: continue
                processed_group_ids.add(group_key)
                
                group_members = [s for s in slots_data if s.get("pair_id") == group_key]
                first_member = group_members[0]
                offset = int(first_member["id_offset"], 16)
                
                display_name = first_member["name"].replace(" Pair A", "")
                
                f_mod.seek(offset); mod_id = struct.unpack('<B', f_mod.read(1))[0]
                f_base.seek(offset); base_id = struct.unpack('<B', f_base.read(1))[0]
                
                if mod_id != base_id:
                    mod_name = self.item_id_to_name.get(mod_id, f"ID:{hex(mod_id)}")
                    base_name = self.item_id_to_name.get(base_id, f"ID:{hex(base_id)}")
                    changes.append(f'- {display_name:<{max_label_length}}: "{base_name}" -> "{mod_name}"')
            else:
                offset = int(slot_info["id_offset"], 16)
                f_mod.seek(offset); mod_id = struct.unpack('<B', f_mod.read(1))[0]
                f_base.seek(offset); base_id = struct.unpack('<B', f_base.read(1))[0]
                if mod_id != base_id:
                    mod_name = self.item_id_to_name.get(mod_id, f"ID:{hex(mod_id)}")
                    base_name = self.item_id_to_name.get(base_id, f"ID:{hex(base_id)}")
                    changes.append(f'- {slot_info["name"]:<{max_label_length}}: "{base_name}" -> "{mod_name}"')

        return changes
    
    def _analyzer_compare_money_health(self, f_mod, f_base):
        changes = []
        stats_data = self.all_data.get("starter_money_health", {}).get("stats", [])
        if not stats_data: return []

        max_label_len = max(len(s["name"]) for s in stats_data) if stats_data else 0

        for stat_info in stats_data:
            dtype = stat_info["dtype"]
            dsize = struct.calcsize(dtype)
            offset = int(stat_info["offsets"][0], 16)
            
            f_mod.seek(offset); mod_val, = struct.unpack(dtype, f_mod.read(dsize))
            f_base.seek(offset); base_val, = struct.unpack(dtype, f_base.read(dsize))
            
            if mod_val != base_val:
                changes.append(f'- {stat_info["name"]:<{max_label_len}}: {base_val} -> {mod_val}')
        return changes
    
    def load_all_data(self, initial_load=False):
        try:
            # --- EMBEDDED JSON DATA ---
            json_string = """
            {
  "game_mode_starters": {
    "comment": "Accurate offsets for starting items in various game modes. Structure is single-byte writes.",
    "difficulty_flag_offset": "0x307D21",
    "Story Mode": [
      {
        "name": "Attache Case", "id_offset": "0x307CED", "qty_offset": null,
        "difficulty": "All", "default_id": "0x7C", "default_qty": 1
      },
      {
        "name": "Slot 1: Weapon", "id_offset": "0x307CFC", "qty_offset": null,
        "difficulty": "All", "default_id": "0x23", "default_qty": 1
      },
      {
        "name": "Slot 2: Healing Item (Normal/Pro)", "id_offset": "0x307D63", "qty_offset": null,
        "difficulty": "Normal/Pro", "default_id": "0x05", "default_qty": 1
      },
      {
        "name": "Slot 2: Healing Item (Easy)", "id_offset": "0x307D32", "qty_offset": null, 
        "difficulty": "Easy", "default_id": "0x05", "default_qty": 1
      },
      {
        "name": "Slot 3: Ammo", "id_offset": "0x307D56", "qty_offset": "0x307D54",
        "difficulty": "Normal/Pro", "default_id": "0x04", "default_qty": 20
      },
      {
        "name": "Slot 1: Weapon (Easy)", "id_offset": "0x307D28", "qty_offset": null,
        "difficulty": "Easy", "default_id": "0x2C", "default_qty": 1
      },
      {
        "name": "Slot 3: Ammo (Easy)", "id_offset": "0x307D3D", "qty_offset": "0x307D3B",
        "difficulty": "Easy", "default_id": "0x04", "default_qty": 20
      },
      {
        "name": "Slot 4: Ammo (Easy)", "id_offset": "0x307D48", "qty_offset": "0x307D46",
        "difficulty": "Easy", "default_id": "0x18", "default_qty": 15
      }
    ],
    "Separate Ways": [
      {
        "name": "Attache Case", "id_offset": "0x307F47", "qty_offset": null, "difficulty": "All", "default_id": "0x7C", "default_qty": 1
      },
      {
        "name": "Slot 1: Weapon", "id_offset": "0x307F50", "qty_offset": null, "difficulty": "All", "default_id": "0x27", "default_qty": 1
      },
      {
        "name": "Slot 2: Weapon", "id_offset": "0x307F55", "qty_offset": null, "difficulty": "All", "default_id": "0x47", "default_qty": 1
      },
      {
        "name": "Slot 3: Healing", "id_offset": "0x307F66", "qty_offset": null, "difficulty": "All", "default_id": "0x05", "default_qty": 1
      },
      {
        "name": "Slot 4: Ammo", "id_offset": "0x307F75", "qty_offset": "0x307F77", "difficulty": "All", "default_id": "0x04", "default_qty": 30
      },
      {
        "name": "Slot 5: Ammo", "id_offset": "0x307F7C", "qty_offset": "0x307F7E", "difficulty": "All", "default_id": "0x18", "default_qty": 15
      }
    ],
    "Assignment Ada": [
      {
        "name": "Attache Case", "id_offset": "0x308156", "qty_offset": null, "difficulty": "All", "default_id": "0x7C", "default_qty": 1
      },
      {
        "name": "Slot 1: Grenade", "id_offset": "0x30815F", "qty_offset": null, "difficulty": "All", "default_id": "0x01", "default_qty": 1
      },
      {
        "name": "Slot 2: Weapon", "id_offset": "0x308164", "qty_offset": null, "difficulty": "All", "default_id": "0x21", "default_qty": 1
      },
      {
        "name": "Slot 3: Weapon", "id_offset": "0x308175", "qty_offset": null, "difficulty": "All", "default_id": "0x2F", "default_qty": 1
      },
      {
        "name": "Slot 4: Weapon", "id_offset": "0x308182", "qty_offset": null, "difficulty": "All", "default_id": "0x30", "default_qty": 1
      },
      {
        "name": "Slot 5: Attachment", "id_offset": "0x308187", "qty_offset": null, "difficulty": "All", "default_id": "0x45", "default_qty": 1
      },
      {
        "name": "Slot 6: Healing", "id_offset": "0x30819E", "qty_offset": null, "difficulty": "All", "default_id": "0x05", "default_qty": 1
      },
      {
        "name": "Slot 7: Ammo", "id_offset": "0x3081A9", "qty_offset": "0x3081AB", "difficulty": "All", "default_id": "0x04", "default_qty": 30
      },
      {
        "name": "Slot 8: Ammo", "id_offset": "0x3081B0", "qty_offset": "0x3081B2", "difficulty": "All", "default_id": "0x20", "default_qty": 50
      },
      {
        "name": "Slot 9: Ammo", "id_offset": "0x3081B7", "qty_offset": "0x3081B9", "difficulty": "All", "default_id": "0x07", "default_qty": 5
      }
    ],
    "The Mercenaries (Leon)": [
      {
        "name": "Attache Case", "id_offset": "0x3085AC", "qty_offset": null,
        "difficulty": "All", "default_id": "0x7C", "default_qty": 1
      },
      {
        "name": "Slot 1: Weapon", "id_offset": "0x3085B7", "qty_offset": null,
        "difficulty": "All", "default_id": "0x27", "default_qty": 1
      },
      {
        "name": "Slot 2: Weapon", "id_offset": "0x3085BE", "qty_offset": null,
        "difficulty": "All", "default_id": "0x94", "default_qty": 1
      },
      {
        "name": "Slot 3: Healing", "id_offset": "0x3093D2", "qty_offset": null,
        "difficulty": "All", "default_id": "0x05", "default_qty": 1
      },
      {
        "name": "Slot 4: Ammo", "id_offset": "0x3085C5", "qty_offset": "0x3085C7",
        "difficulty": "All", "default_id": "0x04", "default_qty": 30
      },
      {
        "name": "Slot 5: Ammo", "id_offset": "0x30ADDC", "qty_offset": "0x30ADDE",
        "difficulty": "All", "default_id": "0x18", "default_qty": 10
      }
    ],
    "The Mercenaries (Ada)": [
      {
        "name": "Attache Case", "id_offset": "0x3086B2", "qty_offset": null,
        "difficulty": "All", "default_id": "0x7C", "default_qty": 1
      },
      {
        "name": "Slot 1: Weapon", "id_offset": "0x3086BD", "qty_offset": null,
        "difficulty": "All", "default_id": "0x21", "default_qty": 1
      },
      {
        "name": "Slot 2: Weapon", "id_offset": "0x3086C4", "qty_offset": null,
        "difficulty": "All", "default_id": "0x30", "default_qty": 1
      },
      {
        "name": "Slot 3: Weapon", "id_offset": "0x3086CB", "qty_offset": null,
        "difficulty": "All", "default_id": "0x2F", "default_qty": 1
      },
      {
        "name": "Slot 4: Attachment", "id_offset": "0x3086D2", "qty_offset": null,
        "difficulty": "All", "default_id": "0x45", "default_qty": 1
      },
      {
        "name": "Slot 5: Ammo", "id_offset": "0x3086D9", "qty_offset": "0x3086DB",
        "difficulty": "All", "default_id": "0x04", "default_qty": 30
      },
      {
        "name": "Slot 6: Ammo", "id_offset": "0x3086E0", "qty_offset": "0x3086E2",
        "difficulty": "All", "default_id": "0x20", "default_qty": 100
      },
      {
        "name": "Slot 7: Ammo", "id_offset": "0x3086E7", "qty_offset": "0x3086E9",
        "difficulty": "All", "default_id": "0x07", "default_qty": 5
      },
      {
        "name": "Slot 8: Grenade", "id_offset": "0x3086EE", "qty_offset": "0x3086F0",
        "difficulty": "All", "default_id": "0x02", "default_qty": 1
      },
      {
        "name": "Slot 9: Grenade", "id_offset": "0x3086F5", "qty_offset": "0x3086F7",
        "difficulty": "All", "default_id": "0x02", "default_qty": 1
      },
      {
        "name": "Slot 10: Grenade", "id_offset": "0x3086FC", "qty_offset": "0x3086FE",
        "difficulty": "All", "default_id": "0x02", "default_qty": 1
      },
      {
        "name": "Slot 11: Healing", "id_offset": "0x308703", "qty_offset": "0x308705",
        "difficulty": "All", "default_id": "0x05", "default_qty": 1
      }
    ],
    "The Mercenaries (Krauser)": [
      {
        "name": "Attache Case", "id_offset": "0x30892B", "qty_offset": null,
        "difficulty": "All", "default_id": "0x7C", "default_qty": 1
      },
      {
        "name": "Slot 1: Weapon", "id_offset": "0x308936", "qty_offset": null,
        "difficulty": "All", "default_id": "0x52", "default_qty": 1
      },
      {
        "name": "Slot 2: Ammo", "id_offset": "0x30893D", "qty_offset": "0x30893F",
        "difficulty": "All", "default_id": "0x72", "default_qty": 20
      },
      {
        "name": "Slot 3: Ammo", "id_offset": "0x308944", "qty_offset": "0x308946",
        "difficulty": "All", "default_id": "0x72", "default_qty": 10
      },
      {
        "name": "Slot 4: Grenade", "id_offset": "0x30894B", "qty_offset": "0x30894D",
        "difficulty": "All", "default_id": "0x0E", "default_qty": 1
      },
      {
        "name": "Slot 5: Grenade", "id_offset": "0x308952", "qty_offset": "0x308954",
        "difficulty": "All", "default_id": "0x0E", "default_qty": 1
      },
      {
        "name": "Slot 6: Grenade", "id_offset": "0x308959", "qty_offset": "0x30895B",
        "difficulty": "All", "default_id": "0x0E", "default_qty": 1
      },
      {
        "name": "Slot 7: Healing", "id_offset": "0x308960", "qty_offset": "0x308962",
        "difficulty": "All", "default_id": "0x05", "default_qty": 1
      }
    ],
    "The Mercenaries (Hunk)": [
      {
        "name": "Attache Case", "id_offset": "0x308861", "qty_offset": null,
        "difficulty": "All", "default_id": "0x7C", "default_qty": 1
      },
      {
        "name": "Slot 1: Weapon", "id_offset": "0x30886C", "qty_offset": null,
        "difficulty": "All", "default_id": "0x3E", "default_qty": 1
      },
      {
        "name": "Slot 2: Ammo", "id_offset": "0x308873", "qty_offset": "0x308875",
        "difficulty": "All", "default_id": "0x20", "default_qty": 50
      },
      {
        "name": "Slot 3: Grenade", "id_offset": "0x30887A", "qty_offset": "0x3086F0",
        "difficulty": "All", "default_id": "0x01", "default_qty": 1
      },
      {
        "name": "Slot 4: Grenade", "id_offset": "0x308881", "qty_offset": "0x3086F7",
        "difficulty": "All", "default_id": "0x01", "default_qty": 1
      },
      {
        "name": "Slot 5: Grenade", "id_offset": "0x308888", "qty_offset": "0x3086FE",
        "difficulty": "All", "default_id": "0x01", "default_qty": 1
      },
      {
        "name": "Slot 6: Healing", "id_offset": "0x30888F", "qty_offset": "0x308891",
        "difficulty": "All", "default_id": "0x05", "default_qty": 1
      }
    ],
    "The Mercenaries (Wesker)": [
      {
        "name": "Attache Case", "id_offset": "0x3089B8", "qty_offset": null,
        "difficulty": "All", "default_id": "0x7C", "default_qty": 1
      },
      {
        "name": "Slot 1: Weapon", "id_offset": "0x3089C3", "qty_offset": null,
        "difficulty": "All", "default_id": "0x23", "default_qty": 1
      },
      {
        "name": "Slot 2: Weapon", "id_offset": "0x3089CA", "qty_offset": null,
        "difficulty": "All", "default_id": "0x2A", "default_qty": 1
      },
      {
        "name": "Slot 3: Weapon", "id_offset": "0x3089D1", "qty_offset": null,
        "difficulty": "All", "default_id": "0x2F", "default_qty": 1
      },
      {
        "name": "Slot 4: Attachment", "id_offset": "0x3089D8", "qty_offset": null,
        "difficulty": "All", "default_id": "0x3F", "default_qty": 1
      },
      {
        "name": "Slot 5: Grenade", "id_offset": "0x3089DF", "qty_offset": "0x3089E1",
        "difficulty": "All", "default_id": "0x01", "default_qty": 1
      },
      {
        "name": "Slot 6: Grenade", "id_offset": "0x3089E6", "qty_offset": "0x3089E8",
        "difficulty": "All", "default_id": "0x01", "default_qty": 1
      },
      {
        "name": "Slot 7: Grenade", "id_offset": "0x3089ED", "qty_offset": "0x3089EF",
        "difficulty": "All", "default_id": "0x01", "default_qty": 1
      },
      {
        "name": "Slot 8: Grenade", "id_offset": "0x3089F4", "qty_offset": "0x3089F6",
        "difficulty": "All", "default_id": "0x01", "default_qty": 1
      },
      {
        "name": "Slot 9: Grenade", "id_offset": "0x3089FB", "qty_offset": "0x3089FD",
        "difficulty": "All", "default_id": "0x0E", "default_qty": 1
      },
      {
        "name": "Slot 10: Grenade", "id_offset": "0x308A02", "qty_offset": "0x308A04",
        "difficulty": "All", "default_id": "0x0E", "default_qty": 1
      },
      {
        "name": "Slot 11: Grenade", "id_offset": "0x308A09", "qty_offset": "0x308A0B",
        "difficulty": "All", "default_id": "0x0E", "default_qty": 1
      },
      {
        "name": "Slot 12: Grenade", "id_offset": "0x3086FC", "qty_offset": "0x3086FE",
        "difficulty": "All", "default_id": "0x02", "default_qty": 1
      },
      {
        "name": "Slot 13: Healing", "id_offset": "0x308703", "qty_offset": "0x308705",
        "difficulty": "All", "default_id": "0x05", "default_qty": 1
      }
    ]
  },
  "weapons": {
    "Handgun": { "firepower_base_offset": "0x7FE550", "capacity_base_offset": "0x721A58", "max_levels_offsets": ["0x721E12", "0x811AC2"], "firing_speed_offsets": ["0x71AD48", "0x71B018"], "reload_speed_base_offset": "0x71A898" },
    "Handgun + Silencer": { "base_weapon": "Handgun", "capacity_base_offset": "0x721A6E", "max_levels_offsets": ["0x721E18"] },
    "Red9": { "firepower_base_offset": "0x7FE56C", "capacity_base_offset": "0x721A84", "max_levels_offsets": ["0x721E1E", "0x811B8A"], "firing_speed_offsets": ["0x71AD5C"], "reload_speed_base_offset": "0x71A8A4" },
    "Red9 + Stock": { "base_weapon": "Red9", "capacity_base_offset": "0x721A9A", "max_levels_offsets": ["0x721E24"] },
    "Punisher": { "firepower_base_offset": "0x7FE534", "capacity_base_offset": "0x721AC6", "max_levels_offsets": ["0x721E30", "0x811B3A"], "firing_speed_offsets": ["0x71AD34"], "reload_speed_base_offset": "0x71A88C" },
    "Punisher FREE ID40": { "base_weapon": "Punisher", "capacity_base_offset": "0x721ADC", "max_levels_offsets": ["0x721E36"] },
    "Blacktail": { "firepower_base_offset": "0x7FE588", "capacity_base_offset": "0x721AF2", "max_levels_offsets": ["0x721E3C", "0x811B9A"], "firing_speed_offsets": ["0x71AD70"], "reload_speed_base_offset": "0x71A8B0" },
    "Matilda": { "firepower_base_offset": "0x7FE6F4", "capacity_base_offset": "0x721AB0", "max_levels_offsets": ["0x721E28"], "firing_speed_offsets": ["0x71AE74"], "reload_speed_base_offset": "0x71A94C" },
    "Broken Butterfly": { "firepower_base_offset": "0x7FE5A4", "capacity_base_offset": "0x721B08", "max_levels_offsets": ["0x721E42", "0x811C4A"], "firing_speed_offsets": ["0x71AD84"], "reload_speed_base_offset": "0x71A8BC" },
    "Killer7": { "firepower_base_offset": "0x7FE5C0", "capacity_base_offset": "0x721C26", "max_levels_offsets": ["0x721EA2", "0x811C52"], "firing_speed_offsets": ["0x71AD98"], "reload_speed_base_offset": "0x71A8C8" },
    "Shotgun": { "firepower_base_offset": "0x7FE5DC", "capacity_base_offset": "0x721B1E", "max_levels_offsets": ["0x721E48", "0x811B52"], "firing_speed_offsets": ["0x71ADAC"], "reload_speed_base_offset": "0x71A8D4" },
    "Riot Gun": { "firepower_base_offset": "0x7FE8B4", "capacity_base_offset": "0x721D5A", "max_levels_offsets": ["0x721E54", "0x811BAA"], "firing_speed_offsets": ["0x71AFB4"], "reload_speed_base_offset": "0x71AA0C" },
    "Striker": { "firepower_base_offset": "0x7FE5F8", "capacity_base_offset": "0x721B34", "max_levels_offsets": ["0x721E4E", "0x811C2A"], "firing_speed_offsets": ["0x71ADC0"], "reload_speed_base_offset": "0x71A8E0" },
    "Rifle": { "firepower_base_offset": "0x7FE614", "capacity_base_offset": "0x721B4A", "max_levels_offsets": ["0x721E5A", "0x811AEA"], "firing_speed_offsets": ["0x71ADD4"], "reload_speed_base_offset": "0x71A8EC" },
    "Rifle + Scope": { "base_weapon": "Rifle", "capacity_base_offset": "0x721B60", "max_levels_offsets": ["0x721E60"] },
    "Rifle + Infrared Scope": { "base_weapon": "Rifle", "capacity_base_offset": "0x721B76", "max_levels_offsets": ["0x721E66"] },
    "Rifle (semi-auto)": { "firepower_base_offset": "0x7FE630", "capacity_base_offset": "0x721B8C", "max_levels_offsets": ["0x721E6C", "0x811C0A"], "firing_speed_offsets": ["0x71ADE8"], "reload_speed_base_offset": "0x71A8F8" },
    "Rifle(semi-auto)+Scope": { "base_weapon": "Rifle (semi-auto)", "capacity_base_offset": "0x721BA2", "max_levels_offsets": ["0x721E72"] },
    "Rifle(s-a)+InfraredScope": { "base_weapon": "Rifle (semi-auto)", "capacity_base_offset": "0x721BB8", "max_levels_offsets": ["0x721E78"] },
    "TMP": { "firepower_base_offset": "0x7FE64C", "capacity_base_offset": "0x721BCE", "max_levels_offsets": ["0x721E7E", "0x811BB2"], "firing_speed_offsets": ["0x71ADFC", "0x71AE10", "0x71B02C", "0x7F1B40", "0x7FD220", "0x807184", "0x807198"], "firing_speed_notes": "Changes might not work in-game.", "reload_speed_base_offset": "0x71A904" },
    "TMP + Stock": { "base_weapon": "TMP", "capacity_base_offset": "0x721BE4", "max_levels_offsets": ["0x721E84"] },
    "Chicago Typewriter": { "firepower_base_offset": "0x7FE668", "capacity_base_offset": "0x721C3C", "max_levels_offsets": ["0x721E9C"], "firing_speed_offsets": ["0x71ADFC", "0x71AE10", "0x71B02C", "0x7F1B40", "0x7FD220", "0x807184", "0x807198"], "firing_speed_notes": "Shares offsets with TMP. Changes might not work in-game.", "reload_speed_base_offset": "0x71A910" },
    "Handcannon": { "firepower_base_offset": "0x7FE6BC", "capacity_base_offset": "0x721C94", "max_levels_offsets": ["0x721EA8"], "firing_speed_offsets": ["0x71AE4C", "0x7FE5C8", "0x7FE9F0"], "reload_speed_base_offset": "0x71A934" },
    "Mine Thrower": { "capacity_base_offset": "0x721BFA", "max_levels_offsets": ["0x721E90", "0x811BBA"], "firing_speed_offsets": ["0x71AE38"], "reload_speed_base_offset": "0x71A928" },
    "Mine Thrower + Scope": { "base_weapon": "Mine Thrower", "capacity_base_offset": "0x721C10", "max_levels_offsets": ["0x721E96"] },
    "Bowgun": { "reload_speed_base_offset": "0x71AAC0" },
    "Knife (All Characters)": { "firepower_base_offset": "0x7FE6D8", "firing_speed_offsets": ["0x71AE60"], "firing_speed_notes": "Changes might not work in-game." },
    "--- Other Weapons ---": { "notes": "Separator for UI" },
    "Custom TMP": { "firepower_base_offset": "0x7FE64C", "capacity_base_offset": "0x721D86", "max_levels_offsets": ["0x721E8A"] },
    "Chicago Typewriter (Ada)": { "firepower_base_offset": "0x7FE668", "capacity_base_offset": "0x721DF4", "max_levels_offsets": ["0x721EB4", "0x71B3E9"] },
    "--- Special ---": { "notes": "Separator for UI" },
    "Melee Attacks (Standard)": { "firepower_base_offset": "0x7FE748" },
    "Krauser's Double Kick": { "firepower_base_offset": "0x7FE908" },
    "Hand Grenade / Mine Darts": { "firepower_base_offset": "0x7FE72C" },
    "Rocket Launcher (Direct Hit)": { "firepower_base_offset": "0x7FE684", "firing_speed_offsets": ["0x71AE24"], "firing_speed_notes": "Changes might not work in-game." },
    "Rocket Launcher (Explosion Radius)": { "firepower_base_offset": "0x7FE710" },
    "P.R.L. 412 (Flash)": { "firepower_base_offset": "0x7FEA20" }
  },
  "upgrade_prices": {
    "Handgun": "0x8116A8",
    "Red9": "0x8116D2",
    "Punisher": "0x811726",
    "Blacktail": "0x811750",
    "Matilda": "0x8116FC",
    "Broken Butterfly": "0x81177A",
    "Killer7": "0x8118F4",
    "Handcannon": "0x81191E",
    "Shotgun": "0x8117A4",
    "Riot Gun": "0x8117F8",
    "Striker": "0x8117CE",
    "Rifle": "0x811822",
    "Rifle (semi-auto)": "0x81184C",
    "TMP": "0x811876",
    "Chicago Typewriter": "0x8118CA",
    "Mine Thrower": "0x8118A0"
  },
  "merchant": {
    "Merchant 1 (r104)":  { "display_name": "Village Merchant 1 (R104)", "sort_order": 1, "stock_offset": "0x811CA0", "upgrades_offset": "0x811950", "stock_slots": 9, "upgrade_slots": 3 },
    "Merchant 2 (r102)":  { "display_name": "Village Merchant 2 (R102 Cave)", "sort_order": 2, "stock_offset": "0x811CE8", "upgrades_offset": "0x811970", "stock_slots": 3, "upgrade_slots": 1 },
    "Merchant 3 (r112)":  { "display_name": "Village Merchant (R112 Night Cave)", "sort_order": 3, "stock_offset": "0x811D30", "upgrades_offset": "0x8119B0", "stock_slots": 4, "upgrade_slots": 4 },
    "Merchant 4 (r200)":  { "display_name": "Castle Merchant (R200)", "sort_order": 4, "stock_offset": "0x811D90", "upgrades_offset": "0x8119D0", "stock_slots": 20, "upgrade_slots": 11 },
    "Merchant 5 (r202)":  { "display_name": "Castle Merchant (R202 Catapult)", "sort_order": 5, "stock_offset": "0x811E30", "upgrades_offset": "0x811A28", "stock_slots": 2, "upgrade_slots": 2 },
    "Merchant 6 (r204)":  { "display_name": "Castle Merchant (R204 Corridor)", "sort_order": 6, "stock_offset": "0x811D60", "upgrades_offset": "0x811A38", "stock_slots": 2, "upgrade_slots": 8 },
    "Merchant 7 (r20B)":  { "display_name": "Castle Merchant (R20B Maze)", "sort_order": 7, "stock_offset": "0x811E70", "upgrades_offset": "0x811A78", "stock_slots": 2, "upgrade_slots": 5 },
    "Merchant 8 (r20f)":  { "display_name": "Castle Merchant (R20F XL Attache)", "sort_order": 8, "stock_offset": "0x811E40", "upgrades_offset": "0x000000", "stock_slots": 3, "upgrade_slots": 0 },
    "Merchant 9 (r211)":  { "display_name": "Castle Merchant (R211 Main Hall)", "sort_order": 9, "stock_offset": "0x000000", "upgrades_offset": "0x811AA0", "stock_slots": 0, "upgrade_slots": 4 },
    "Merchant 10 (r214)": { "display_name": "Castle Merchant (R214 Clock Tower)", "sort_order": 10, "stock_offset": "0x000000", "upgrades_offset": "0x811AC0", "stock_slots": 0, "upgrade_slots": 9 },
    "Merchant 11 (r229)": { "display_name": "Castle Merchant (R229 Spike Pit)", "sort_order": 11, "stock_offset": "0x811E58", "upgrades_offset": "0x811B08", "stock_slots": 3, "upgrade_slots": 2 },
    "Merchant 12 (r220)": { "display_name": "Castle Merchant (R220 Area)", "sort_order": 12, "stock_offset": "0x000000", "upgrades_offset": "0x811B18", "stock_slots": 0, "upgrade_slots": 3 },
    "Merchant 13 (r225)": { "display_name": "Castle Merchant (R225 Dungeon)", "sort_order": 13, "stock_offset": "0x000000", "upgrades_offset": "0x811B30", "stock_slots": 0, "upgrade_slots": 11 },
    "Merchant 14 (r227)": { "display_name": "Castle Merchant (R227)", "sort_order": 14, "stock_offset": "0x000000", "upgrades_offset": "0x811B88", "stock_slots": 0, "upgrade_slots": 2 },
    "Merchant 15 (r22a)": { "display_name": "Castle Merchant (R22A Tower)", "sort_order": 15, "stock_offset": "0x000000", "upgrades_offset": "0x811B98", "stock_slots": 0, "upgrade_slots": 12 },
    "Merchant 16 (r301)": { "display_name": "Island Merchant (R301)", "sort_order": 16, "stock_offset": "0x811E80", "upgrades_offset": "0x811BF8", "stock_slots": 22, "upgrade_slots": 6 },
    "Merchant 17 (r305)": { "display_name": "Island Merchant (R305 Locker Room)", "sort_order": 17, "stock_offset": "0x000000", "upgrades_offset": "0x811C28", "stock_slots": 0, "upgrade_slots": 4 },
    "Merchant 18 (r31D)": { "display_name": "Island Merchant (R31D Before Saddler)", "sort_order": 18, "stock_offset": "0x000000", "upgrades_offset": "0x811C38", "stock_slots": 0, "upgrade_slots": 2 },
    "Merchant 19 (r31A)": { "display_name": "Island Merchant (R31A Cave)", "sort_order": 19, "stock_offset": "0x000000", "upgrades_offset": "0x811C48", "stock_slots": 0, "upgrade_slots": 3 },
    "Merchant 20 (r329)": { "display_name": "Island Merchant (R329)", "sort_order": 20, "stock_offset": "0x000000", "upgrades_offset": "0x811C60", "stock_slots": 0, "upgrade_slots": 2 },
    "Merchant 21 (r331)": { "display_name": "Final Merchant (R331 End Game)", "sort_order": 21, "stock_offset": "0x000000", "upgrades_offset": "0x811C70", "stock_slots": 0, "upgrade_slots": 2 }
  },
  "master_item_prices": {
    "Attache Case XL": ["0x812080", "0x8123B6"], "Attache Case L": ["0x812086", "0x8123BC"], "Attache Case M": ["0x81208C", "0x8123C2"], "Tactical Vest": ["0x812092"],
    "Treasure Map (Village)": ["0x812098"], "Treasure Map (Castle)": ["0x81209E"], "Treasure Map (Island)": ["0x8120A4"],
    "Handgun Ammo": ["0x8120AA", "0x8123C8"], "Shotgun Shells": ["0x8120B0", "0x8123CE"], "Magnum Ammo": ["0x8120B6", "0x8123D4"], "Rifle Ammo": ["0x8120BC", "0x8123DA"],
    "TMP Ammo": ["0x8120C2", "0x8123E0"], "Mine-darts": ["0x8120C8", "0x8123E6"], "Chicago Typewriter Ammo": ["0x8120CE", "0x8123EC"], "Handcannon Ammo": ["0x8120D4", "0x8123F2"],
    "Flash Grenade": ["0x8120DA", "0x8123F8"], "Incendiary Grenade": ["0x8120E0", "0x8123FE"], "Hand Grenade": ["0x8120E6", "0x812404"],
    "Handgun": ["0x8120EC", "0x81240A"], "Red9": ["0x8120F2", "0x812410"], "Punisher": ["0x8120FE", "0x81241C"],
    "Blacktail": ["0x812104", "0x812422"], "Matilda": ["0x81210A", "0x812428"], "Broken Butterfly": ["0x812110", "0x81242E"], "Killer7": ["0x812116", "0x812434"],
    "Handcannon": ["0x80C71A", "0x80C99A", "0x80CC1A", "0x80CE9A", "0x81211C", "0x81243A"], "Shotgun": ["0x812122"], "Riot Gun": ["0x812128"], "Striker": ["0x81212E"], "Rifle": ["0x812134"],
    "Rifle (semi-auto)": ["0x81213A", "0x81244C"], "TMP": ["0x812140", "0x812446"], "Mine Thrower": ["0x812146"], "Chicago Typewriter (Infinite)": ["0x81214C"],
    "Rocket Launcher": ["0x812152"], "Rocket Launcher (Special)": ["0x812158"], "Infinite Launcher": ["0x81215E"],
    "P.R.L. 412": ["0x80C7A2", "0x80CA22", "0x80CCA2", "0x80CF22", "0x812164"], "Punisher w/ Silencer": ["0x81216A"],
    "Stock (Red9)": ["0x812170"], "Stock (TMP)": ["0x812176"], "Scope (Rifle)": ["0x81217C"], "Scope (Semi-auto Rifle)": ["0x812182", "0x812452"],
    "Scope (Mine-thrower)": ["0x812188"], "Infrared Scope": ["0x81218E"],
    "Chicken Egg": ["0x812194", "0x81246A"], "Brown Chicken Egg": ["0x81219A", "0x812470"], "Gold Chicken Egg": ["0x8121A0", "0x812476"],
    "Black Bass": ["0x8121A6", "0x81247C"], "Black Bass (L)": ["0x8121AC", "0x812482"],
    "Green Herb": ["0x8121B2", "0x812488"], "Red Herb": ["0x8121B8", "0x81248E"], "Yellow Herb": ["0x8121BE", "0x812494"],
    "Mixed Herbs (G+G)": ["0x8121C4", "0x81249A"], "Mixed Herbs (G+G+G)": ["0x8121CA", "0x8124A0"], "Mixed Herbs (G+R)": ["0x8121D0", "0x8124A6"],
    "Mixed Herbs (G+Y)": ["0x8121D6", "0x8124AC"], "Mixed Herbs (R+Y)": ["0x8121DC", "0x8124B2"], "Mixed Herbs (G+R+Y)": ["0x8121E2", "0x8124B8"],
    "First Aid Spray": ["0x8121E8", "0x8124BE"], "Spinel": ["0x8121EE", "0x8124C4"], "Velvet Blue": ["0x8121F4", "0x8124CA"],
    "Emerald": ["0x8121FA", "0x8124D0"], "Ruby": ["0x812200", "0x8124D6"], "Pearl Pendant": ["0x812206", "0x8124DC"],
    "Dirty Pearl Pendant": ["0x81220C", "0x8124E2"], "Brass Pocket Watch": ["0x812212", "0x8124E8"], "Dirty Brass Pocket Watch": ["0x812218", "0x8124EE"],
    "Elegant Headdress": ["0x81221E", "0x8124F4"], "Antique Pipe": ["0x812224", "0x8124FA"], "Gold Bangle w/ Pearls": ["0x81222A", "0x812500"],
    "Amber Ring": ["0x812230", "0x812506"], "Green Catseye": ["0x812236", "0x81250C"], "Red Catseye": ["0x81223C", "0x812512"],
    "Yellow Catseye": ["0x812242", "0x812518"], "Beerstein": ["0x812248", "0x81251E"], "Beerstein w/ (G)": ["0x81224E", "0x812524"],
    "Beerstein w/ (R)": ["0x812254", "0x81252A"], "Beerstein w/ (Y)": ["0x81225A", "0x812530"], "Beerstein w/ (G,R)": ["0x812260", "0x812536"],
    "Beerstein w/ (G,Y)": ["0x812266", "0x81253C"], "Beerstein w/ (R,Y)": ["0x81226C", "0x812542"], "Beerstein w/ (G,R,Y)": ["0x812272", "0x812548"],
    "Green Eye": ["0x812278", "0x81254E"], "Red Eye": ["0x81227E", "0x812554"], "Blue Eye": ["0x812284", "0x81255A"], "Butterfly Lamp": ["0x81228A", "0x812560"],
    "Butterfly Lamp w/ (G)": ["0x812290", "0x812566"], "Butterfly Lamp w/ (R)": ["0x812296", "0x81256C"], "Butterfly Lamp w/ (B)": ["0x81229C", "0x812572"],
    "Butterfly Lamp w/ (G,R)": ["0x8122A2", "0x812578"], "Butterfly Lamp w/ (G,B)": ["0x8122A8", "0x81257E"], "Butterfly Lamp w/ (R,B)": ["0x8122AE", "0x812584"],
    "Butterfly Lamp w/ (R,G,B)": ["0x8122B4", "0x81258A"], "Green Gem": ["0x8122BA", "0x812590"], "Red Gem": ["0x8122C0", "0x812596"],
    "Purple Gem": ["0x8122C6", "0x81259C"], "Elegant Mask": ["0x8122CC", "0x8125A2"], "Elegant Mask w/ (G)": ["0x8122D2", "0x8125A8"],
    "Elegant Mask w/ (R)": ["0x8122D8", "0x8125AE"], "Elegant Mask w/ (P)": ["0x8122DE", "0x8125B4"], "Elegant Mask w/ (G,R)": ["0x8122E4", "0x8125BA"],
    "Elegant Mask w/ (G,P)": ["0x8122EC", "0x8125C0"], "Elegant Mask w/ (R,P)": ["0x8122F2", "0x8125C6"], "Elegant Mask w/ (R,G,P)": ["0x8122F8", "0x8125CC"],
    "Gold Bangle": ["0x8122FC", "0x8125D2"], "Illuminados Pendant": ["0x812302", "0x8125D8"], "Staff of Royalty": ["0x812308", "0x8125DE"],
    "Elegant Chessboard": ["0x81230E", "0x8125E4"], "Elegant Perfume Bottle": ["0x812314", "0x8125EA"], "Mirror w/ Pearls & Rubies": ["0x81231A", "0x8125F0"],
    "Hourglass w/ Gold Decor": ["0x812320", "0x8125F6"], "Crown Jewel": ["0x812326", "0x8125FC"], "Royal Insignia": ["0x81232C", "0x812602"],
    "Crown": ["0x812332", "0x812608"], "Crown with Jewels": ["0x812338", "0x81260E"], "Crown with an Insignia": ["0x81233E", "0x812616"],
    "Salazar Family Crown": ["0x812344", "0x81261A"], "Green Stone of Judgement": ["0x81234A", "0x812620"], "Red Stone of Faith": ["0x812350", "0x812626"],
    "Blue Stone of Treason": ["0x812356", "0x81262C"], "Golden Lynx": ["0x81235C", "0x812632"], "Golden Lynx w/ (G)": ["0x812362", "0x81263A"],
    "Golden Lynx w/ (R)": ["0x812368", "0x812640"], "Golden Lynx w/ (B)": ["0x81236E", "0x812646"], "Golden Lynx w/ (G,R)": ["0x812374", "0x81264C"],
    "Golden Lynx w/ (G,B)": ["0x81237A", "0x812652"], "Golden Lynx w/ (R,B)": ["0x812380", "0x812658"], "Golden Lynx w/ (G,R,B)": ["0x812386", "0x81265E"]
  },
  "treasure_items": [
    "Velvet Blue", "Spinel", "Ruby", "Emerald", "Pearl Pendant", "Dirty Pearl Pendant", "Brass Pocket Watch", "Dirty Brass Pocket Watch", "Elegant Headdress", "Antique Pipe", "Gold Bangle", "Gold Bangle w/ Pearls", "Amber Ring", "Beerstein", "Green Catseye", "Red Catseye", "Yellow Catseye", "Butterfly Lamp", "Green Eye", "Red Eye", "Blue Eye", "Elegant Mask", "Green Gem", "Red Gem", "Purple Gem", "Crown", "Crown Jewel",
    "Royal Insignia", "Salazar Family Crown", "Golden Lynx", "Green Stone of Judgement", "Red Stone of Faith", "Blue Stone of Treason", "Illuminados Pendant", "Staff of Royalty", "Gold Bars", "Beerstein w/ (G)", "Beerstein w/ (R)", "Beerstein w/ (Y)", "Beerstein w/ (G,R)", "Beerstein w/ (G,Y)", "Beerstein w/ (R,Y)", "Beerstein w/ (G,R,Y)", "Butterfly Lamp w/ (G)", "Butterfly Lamp w/ (R)", "Butterfly Lamp w/ (B)",
    "Butterfly Lamp w/ (G,R)", "Butterfly Lamp w/ (G,B)", "Butterfly Lamp w/ (R,B)", "Butterfly Lamp w/ (R,G,B)", "Elegant Mask w/ (G)", "Elegant Mask w/ (R)", "Elegant Mask w/ (P)", "Elegant Mask w/ (G,R)", "Elegant Mask w/ (G,P)", "Elegant Mask w/ (R,P)", "Elegant Mask w/ (R,G,P)", "Golden Lynx w/ (G)", "Golden Lynx w/ (R)", "Golden Lynx w/ (B)", "Golden Lynx w/ (G,R)", "Golden Lynx w/ (G,B)", "Golden Lynx w/ (R,B)",
    "Golden Lynx w/ (G,R,B)", "Hourglass w/ Gold Decor", "Mirror w/ Pearls & Rubies", "Elegant Chessboard", "Elegant Perfume Bottle", "Crown with Jewels", "Crown with an Insignia", "Blue Moonstone"
  ],
  "key_items": [
    "Plaga Sample", "Salazar Family Insignia", "Stone Tablet", "Lion Ornament", "Goat Ornament", "Serpent Ornament", "Moonstone (Right Half)", "Moonstone (Left Half)", "Insignia Key", "Round Insignia", "False Eye", "King's Grail", "Queen's Grail", "Key to the Mine", "Old Key", "Camp Key", "Dynamite", "Lift Activation Key", "Gallery Key", "Emblem (Right Half)", "Emblem (Left Half)", "Hexagonal Emblem", "Castle Gate Key", "Prison Key", "Platinum Sword",
    "Golden Sword", "Stone of Sacrifice", "Storage Room Card Key", "Freezer Card Key", "Waste Disposal Card Key", "Piece of the Holy Beast, Panther", "Piece of the Holy Beast, Serpent", "Piece of the Holy Beast, Eagle", "Jet-ski Key", "Activation Key (Blue)", "Activation Key (Red)", "Emergency Lock Card Key", "Iron Key"
  ],
  "ammo_types": {
    "categories": {
      "Ammo": ["Handgun Ammo", "Shotgun Shells", "Rifle Ammo", "TMP Ammo", "Magnum Ammo", "Mine-darts", "Handcannon Ammo", "Bowgun Bolts", "Arrows", "Chicago Typewriter Ammo", "Rifle Ammo (infrared)"],
      "Special": ["Hand Grenade", "Incendiary Grenade", "Flash Grenade", "Chicken Egg", "Brown Chicken Egg", "Gold Chicken Egg"]
    }
  },
  "items": {
    "categories": {
      "Handguns": ["Handgun", "Handgun w/ Silencer", "Punisher", "Punisher w/ Silencer", "Red9", "Red9 w/ Stock", "Blacktail", "Blacktail w/ Silencer", "Matilda"], 
      "Shotguns": ["Shotgun", "Riot Gun", "Striker", "Ada's Shotgun"],
      "Rifles": ["Rifle", "Rifle + Scope", "Rifle (semi-auto)", "Rifle (semi-auto) w/ Scope", "Rifle (semi-auto) w/ Infrared Scope", "Rifle w/ Infrared Scope"], 
      "Magnums": ["Broken Butterfly", "Killer7", "Killer7 w/ Silencer", "Handcannon"], 
      "Submachine Guns": ["TMP", "TMP w/ Stock", "Custom TMP", "Chicago Typewriter", "Chicago Typewriter (Infinite)"], 
      "Special Weapons": ["Mine Thrower", "Mine-thrower + Scope", "Bowgun", "Rocket Launcher", "Rocket Launcher (Special)", "Infinite Launcher", "P.R.L. 412", "Krauser's Bow", "Combat Knife", "Krauser's Knife"], 
      "Attachments": ["Silencer (Handgun)", "Stock (Red9)", "Stock (TMP)", "Scope (Rifle)", "Scope (Semi-auto Rifle)", "Infrared Scope", "Scope (Mine-thrower)"], 
      "Ammo": ["Handgun Ammo", "Shotgun Shells", "Rifle Ammo", "TMP Ammo", "Magnum Ammo", "Mine-darts", "Handcannon Ammo", "Bowgun Bolts", "Arrows", "Chicago Typewriter Ammo", "Rifle Ammo (infrared)"], 
      "Healing Items": ["Green Herb", "Red Herb", "Yellow Herb", "First Aid Spray", "Mixed Herbs (G+G)", "Mixed Herbs (G+G+G)", "Mixed Herbs (G+R)", "Mixed Herbs (G+Y)", "Mixed Herbs (R+Y)", "Mixed Herbs (G+R+Y)"], 
      "Grenades": ["Hand Grenade", "Incendiary Grenade", "Flash Grenade"], 
      "Treasures": ["Velvet Blue", "Spinel", "Ruby", "Emerald", "Pearl Pendant", "Dirty Pearl Pendant", "Brass Pocket Watch", "Dirty Brass Pocket Watch", "Elegant Headdress", "Antique Pipe", "Gold Bangle", "Gold Bangle w/ Pearls", "Amber Ring", "Beerstein", "Beerstein w/ (G)", "Beerstein w/ (R)", "Beerstein w/ (Y)", "Beerstein w/ (G,R)", "Beerstein w/ (G,Y)", "Beerstein w/ (R,Y)",
      "Beerstein w/ (G,R,Y)", "Green Catseye", "Red Catseye", "Yellow Catseye", "Butterfly Lamp", "Butterfly Lamp w/ (G)", "Butterfly Lamp w/ (R)", "Butterfly Lamp w/ (B)", "Butterfly Lamp w/ (G,R)", "Butterfly Lamp w/ (G,B)", "Butterfly Lamp w/ (R,B)", "Butterfly Lamp w/ (R,G,B)", "Green Eye", "Red Eye", "Blue Eye", "Elegant Mask", "Elegant Mask w/ (G)", "Elegant Mask w/ (R)", "Elegant Mask w/ (P)", "Elegant Mask w/ (G,R)",
      "Elegant Mask w/ (G,P)", "Elegant Mask w/ (R,P)", "Elegant Mask w/ (R,G,P)", "Green Gem", "Red Gem", "Purple Gem", "Crown", "Crown with Jewels", "Crown with an Insignia", "Crown Jewel", "Royal Insignia", "Salazar Family Crown", "Golden Lynx", "Golden Lynx w/ (G)", "Golden Lynx w/ (R)", "Golden Lynx w/ (B)", "Golden Lynx w/ (G,R)", "Golden Lynx w/ (G,B)", "Golden Lynx w/ (R,B)", "Golden Lynx w/ (G,R,B)", "Green Stone of Judgement",
      "Red Stone of Faith", "Blue Stone of Treason", "Illuminados Pendant", "Staff of Royalty", "Gold Bars", "Hourglass w/ Gold Decor", "Mirror w/ Pearls & Rubies", "Elegant Chessboard", "Elegant Perfume Bottle", "Blue Moonstone"], 
      "Key Items": ["Plaga Sample", "Salazar Family Insignia", "Stone Tablet", "Lion Ornament", "Goat Ornament", "Serpent Ornament", "Moonstone (Right Half)", "Moonstone (Left Half)", "Insignia Key", "Round Insignia", "False Eye", "King's Grail", "Queen's Grail", "Key to the Mine", "Old Key", "Camp Key", "Dynamite", "Lift Activation Key", "Gallery Key", "Emblem (Right Half)", "Emblem (Left Half)", "Hexagonal Emblem",
      "Castle Gate Key", "Prison Key", "Platinum Sword", "Golden Sword", "Stone of Sacrifice", "Storage Room Card Key", "Freezer Card Key", "Waste Disposal Card Key", "Piece of the Holy Beast, Panther", "Piece of the Holy Beast, Serpent", "Piece of the Holy Beast, Eagle", "Jet-ski Key", "Activation Key (Blue)", "Activation Key (Red)", "Emergency Lock Card Key", "Iron Key"], 
      "Other": ["Attache Case S", "Attache Case M", "Attache Case L", "Attache Case XL", "Tactical Vest", "Chicken Egg", "Brown Chicken Egg", "Gold Chicken Egg", "Black Bass", "Black Bass (L)", "Treasure Map (Village)", "Treasure Map (Castle)", "Treasure Map (Island)"],
      "Files": ["Luis' Memo", "Castellan Memo", "Female Intruder", "Butler's Memo", "Sample Retrieved", "Ritual Preparation", "Luis' Memo 2", "Playing Manual 1", "Info on Ashley", "Playing Manual 2", "Alert Order", "About the Blue Medallions", "Chief's Note", "Closure of the Church", "Anonymous Letter", "Playing Manual 3", "Sera and the 3rd Party", "Two Routes", "Village's Last Defense", "Letter from Ada", "Luis' Memo 3",
      "Paper Airplane", "Our Plan", "Luis' Memo 4", "Krauser's Note", "Luis' Memo 5", "Our Mission"],
      "Bottle Caps": ["Leon w/ Rocket Launcher", "Leon w/ Shotgun", "Leon w/ Handgun", "Ashley Graham", "Luis Sera", "Don Jose", "Don Diego", "Don Esteban", "Don Manuel", "Dr. Salvador", "Merchant", "Zealot w/ Scythe", "Zealot w/ Shield", "Zealot w/ Bowgun", "Leader Zealot", "Soldier w/ Dynamite", "Soldier w/ Stun-rod", "Soldier w/ Hammer", "Isabel", "Maria", "Ada Wong", "Bella Sisters", "Don Pedro", "J.J."],
      "Unused/Miscellaneous": ["Silencer (???)" , "Capture Luis Sera", "Target Practice", "Bonus Time", "Emergency Lock Card Key", "Bonus Points", "Treasure Box (S)", "Treasure Box (L)", "Bottle Caps"]
    }
  },
  "item_hex_ids": {
    "Magnum Ammo": "0x00", "Hand Grenade": "0x01", "Incendiary Grenade": "0x02", "Matilda": "0x03", "Handgun Ammo": "0x04", "First Aid Spray": "0x05", "Green Herb": "0x06", "Rifle Ammo": "0x07", "Chicken Egg": "0x08", "Brown Chicken Egg": "0x09", "Gold Chicken Egg": "0x0A", "Plaga Sample": "0x0C", "Krauser's Knife": "0x0D", "Flash Grenade": "0x0E", "Salazar Family Insignia": "0x0F", "Bowgun": "0x10", "Bowgun Bolts": "0x11",
    "Mixed Herbs (G+G)": "0x12", "Mixed Herbs (G+G+G)": "0x13", "Mixed Herbs (G+R)": "0x14", "Mixed Herbs (G+R+Y)": "0x15", "Mixed Herbs (G+Y)": "0x16", "Rocket Launcher (Special)": "0x17", "Shotgun Shells": "0x18", "Red Herb": "0x19", "Handcannon Ammo": "0x1A", "Hourglass w/ Gold Decor": "0x1B", "Yellow Herb": "0x1C", "Stone Tablet": "0x1D", "Lion Ornament": "0x1E", "Goat Ornament": "0x1F", "TMP Ammo": "0x20", "Punisher": "0x21",
    "Punisher w/ Silencer": "0x22", "Handgun": "0x23", "Handgun w/ Silencer": "0x24", "Red9": "0x25", "Red9 w/ Stock": "0x26", "Blacktail": "0x27", "Blacktail w/ Silencer": "0x28", "Broken Butterfly": "0x29", "Killer7": "0x2A", "Killer7 w/ Silencer": "0x2B", "Shotgun": "0x2C", "Striker": "0x2D", "Ada's Shotgun": "0x47", "Rifle": "0x2E", "Rifle (semi-auto)": "0x2F", "TMP": "0x30", "Activation Key (Blue)": "0x31", "TMP w/ Stock": "0x32",
    "Activation Key (Red)": "0x33", "Chicago Typewriter (Infinite)": "0x34", "Rocket Launcher": "0x35", "Mine Thrower": "0x36", "Handcannon": "0x37", "Combat Knife": "0x38", "Serpent Ornament": "0x39", "Moonstone (Right Half)": "0x3A", "Insignia Key": "0x3B", "Round Insignia": "0x3C", "False Eye": "0x3D", "Custom TMP": "0x3E", "Silencer (Handgun)": "0x3F", "Silencer (???)": "0x40", "P.R.L. 412": "0x41", "Stock (Red9)": "0x42",
    "Stock (TMP)": "0x43", "Scope (Rifle)": "0x44", "Scope (Semi-auto Rifle)": "0x45", "Mine-darts": "0x46", "Capture Luis Sera": "0x48", "Target Practice": "0x49", "Luis' Memo": "0x4A", "Castellan Memo": "0x4B", "Female Intruder": "0x4C", "Butler's Memo": "0x4D", "Sample Retrieved": "0x4E", "Ritual Preparation": "0x4F", "Luis' Memo 2": "0x50", "Rifle (semi-auto) w/ Infrared Scope": "0x51", "Krauser's Bow": "0x52",
    "Chicago Typewriter": "0x53", "Treasure Map (Castle)": "0x54", "Treasure Map (Island)": "0x55", "Velvet Blue": "0x56", "Spinel": "0x57", "Pearl Pendant": "0x58", "Brass Pocket Watch": "0x59", "Elegant Headdress": "0x5A", "Antique Pipe": "0x5B", "Gold Bangle w/ Pearls": "0x5C", "Amber Ring": "0x5D", "Beerstein": "0x5E", "Green Catseye": "0x5F", "Red Catseye": "0x60", "Yellow Catseye": "0x61", "Beerstein w/ (G)": "0x62",
    "Beerstein w/ (R)": "0x63", "Beerstein w/ (Y)": "0x64", "Beerstein w/ (G,R)": "0x65", "Beerstein w/ (G,Y)": "0x66", "Beerstein w/ (R,Y)": "0x67", "Beerstein w/ (G,R,Y)": "0x68", "Moonstone (Left Half)": "0x69", "Chicago Typewriter Ammo": "0x6A", "Rifle + Scope": "0x6B", "Rifle (semi-auto) w/ Scope": "0x6C", "Infinite Launcher": "0x6D", "King's Grail": "0x6E", "Queen's Grail": "0x6F", "Staff of Royalty": "0x70",
    "Gold Bars": "0x71", "Arrows": "0x72", "Bonus Time": "0x73", "Emergency Lock Card Key": "0x74", "Bonus Points": "0x75", "Ruby": "0x77", "Treasure Box (S)": "0x78", "Treasure Box (L)": "0x79", "Blue Moonstone": "0x7A", "Key to the Mine": "0x7B", "Attache Case S": "0x7C", "Attache Case M": "0x7D", "Attache Case L": "0x7E", "Attache Case XL": "0x7F", "Golden Sword": "0x80", "Iron Key": "0x81", "Stone of Sacrifice": "0x82",
    "Storage Room Card Key": "0x83", "Freezer Card Key": "0x84", "Piece of the Holy Beast, Panther": "0x85", "Piece of the Holy Beast, Serpent": "0x86", "Piece of the Holy Beast, Eagle": "0x87", "Jet-ski Key": "0x88", "Dirty Pearl Pendant": "0x89", "Dirty Brass Pocket Watch": "0x8A", "Old Key": "0x8B", "Camp Key": "0x8C", "Dynamite": "0x8D", "Lift Activation Key": "0x8E", "Gold Bangle": "0x8F", "Elegant Perfume Bottle": "0x90",
    "Mirror w/ Pearls & Rubies": "0x91", "Waste Disposal Card Key": "0x92", "Elegant Chessboard": "0x93", "Riot Gun": "0x94", "Black Bass": "0x95", "Black Bass (L)": "0x97", "Illuminados Pendant": "0x98", "Rifle w/ Infrared Scope": "0x99", "Crown": "0x9A", "Crown Jewel": "0x9B", "Royal Insignia": "0x9C", "Crown with Jewels": "0x9D", "Crown with an Insignia": "0x9E", "Salazar Family Crown": "0x9F", "Rifle Ammo (infrared)": "0xA0",
    "Emerald": "0xA1", "Bottle Caps": "0xA2", "Gallery Key": "0xA3", "Emblem (Right Half)": "0xA4", "Emblem (Left Half)": "0xA5", "Hexagonal Emblem": "0xA6", "Castle Gate Key": "0xA7", "Mixed Herbs (R+Y)": "0xA8", "Treasure Map (Village)": "0xA9", "Scope (Mine-thrower)": "0xAA", "Mine-thrower + Scope": "0xAB", "Playing Manual 1": "0xAC", "Info on Ashley": "0xAD", "Playing Manual 2": "0xAE", "Alert Order": "0xAF",
    "About the Blue Medallions": "0xB0", "Chief's Note": "0xB1", "Closure of the Church": "0xB2", "Anonymous Letter": "0xB3", "Playing Manual 3": "0xB4", "Sera and the 3rd Party": "0xB5", "Two Routes": "0xB6", "Village's Last Defense": "0xB7", "Butterfly Lamp": "0xB8", "Green Eye": "0xB9", "Red Eye": "0xBA", "Blue Eye": "0xBB", "Butterfly Lamp w/ (G)": "0xBC", "Butterfly Lamp w/ (R)": "0xBD", "Butterfly Lamp w/ (B)": "0xBE",
    "Butterfly Lamp w/ (G,R)": "0xBF", "Butterfly Lamp w/ (G,B)": "0xC0", "Butterfly Lamp w/ (R,B)": "0xC1", "Butterfly Lamp w/ (R,G,B)": "0xC2", "Prison Key": "0xC3", "Platinum Sword": "0xC4", "Infrared Scope": "0xC5", "Elegant Mask": "0xC6", "Green Gem": "0xC7", "Red Gem": "0xC8", "Purple Gem": "0xC9", "Elegant Mask w/ (G)": "0xCA", "Elegant Mask w/ (R)": "0xCB", "Elegant Mask w/ (P)": "0xCC", "Elegant Mask w/ (G,R)": "0xCD",
    "Elegant Mask w/ (G,P)": "0xCE", "Elegant Mask w/ (R,P)": "0xCF", "Elegant Mask w/ (R,G,P)": "0xD0", "Golden Lynx": "0xD1", "Green Stone of Judgement": "0xD2", "Red Stone of Faith": "0xD3", "Blue Stone of Treason": "0xD4", "Golden Lynx w/ (G)": "0xD5", "Golden Lynx w/ (R)": "0xD6", "Golden Lynx w/ (B)": "0xD7", "Golden Lynx w/ (G,R)": "0xD8", "Golden Lynx w/ (G,B)": "0xD9", "Golden Lynx w/ (R,B)": "0xDA", "Golden Lynx w/ (G,R,B)": "0xDB",
    "Leon w/ Rocket Launcher": "0xDC", "Leon w/ Shotgun": "0xDD", "Leon w/ Handgun": "0xDE", "Ashley Graham": "0xDF", "Luis Sera": "0xE0", "Don Jose": "0xE1", "Don Diego": "0xE2", "Don Esteban": "0xE3", "Don Manuel": "0xE4", "Dr. Salvador": "0xE5", "Merchant": "0xE6", "Zealot w/ Scythe": "0xE7", "Zealot w/ Shield": "0xE8", "Zealot w/ Bowgun": "0xE9", "Leader Zealot": "0xEA", "Soldier w/ Dynamite": "0xEB", "Soldier w/ Stun-rod": "0xEC",
    "Soldier w/ Hammer": "0xED", "Isabel": "0xEE", "Maria": "0xEF", "Ada Wong": "0xF0", "Bella Sisters": "0xF1", "Don Pedro": "0xF2", "J.J.": "0xF3", "Letter from Ada": "0xF4", "Luis' Memo 3": "0xF5", "Paper Airplane": "0xF6", "Our Plan": "0xF7", "Luis' Memo 4": "0xF8", "Krauser's Note": "0xF9", "Luis' Memo 5": "0xFA", "Our Mission": "0xFB", "Tactical Vest": "0xFE"
  },
  "weapon_ammo_map": {
    "Handgun": "Handgun Ammo",
    "Red9": "Handgun Ammo",
    "Punisher": "Handgun Ammo",
    "Blacktail": "Handgun Ammo",
    "Matilda": "Handgun Ammo",
    "Shotgun": "Shotgun Shells",
    "Riot Gun": "Shotgun Shells",
    "Striker": "Shotgun Shells",
    "Ada's Shotgun": "Shotgun Shells",
    "Rifle": "Rifle Ammo",
    "Rifle (semi-auto)": "Rifle Ammo",
    "Broken Butterfly": "Magnum Ammo",
    "Killer7": "Magnum Ammo",
    "TMP": "TMP Ammo",
    "Chicago Typewriter": "Chicago Typewriter Ammo",
    "Handcannon": "Handcannon Ammo",
    "Mine Thrower": "Mine-darts"
  },
  "ammo_stacking_offsets": {
    "individual": {
      "Handgun Ammo": "0x3041F0",
      "Shotgun Shells": "0x304264",
      "Chicago Typewriter Ammo": "0x3042DB",
      "TMP Ammo": "0x304307",
      "Magnum Ammo": "0x30421C",
      "Rifle Ammo": "0x3042B2",
      "Handcannon Ammo": "0x304333",
      "Bowgun Bolts": "0x3043A3",
      "Arrows": "0x3043CF",
      "Mine-darts": "0x30437B"
    },
    "groups": {
      "Explosives": {
        "offset": "0x3041E4",
        "items": [
          "Hand Grenade",
          "Incendiary Grenade",
          "Flash Grenade"
        ]
      },
      "Heals": {
        "offset": "0x304407",
        "items": [
          "Green Herb",
          "Red Herb",
          "Yellow Herb",
          "Mixed Herbs (G+G)",
          "Mixed Herbs (G+G+G)",
          "Mixed Herbs (G+R)",
          "Mixed Herbs (G+Y)",
          "Mixed Herbs (R+Y)",
          "Mixed Herbs (G+R+Y)",
          "First Aid Spray",
          "Chicken Egg",
          "Brown Chicken Egg",
          "Gold Chicken Egg",
          "Black Bass",
          "Black Bass (L)"
        ]
      }
    }
  },
  "item_type_definitions": {
    "base_offset": "0x3044E4",
    "types": {
      "0": "Magnum Ammo",
      "1": "Grenades/Explosives",
      "2": "Weapons",
      "3": "Handgun Ammo",
      "4": "Healing Items",
      "5": "Rifle Ammo",
      "6": "Plaga Sample",
      "7": "Bowgun Bolts",
      "8": "Shotgun Shells",
      "9": "Handcannon Ammo",
      "10": "TMP Ammo",
      "11": "Accessories",
      "12": "Mine Darts",
      "13": "Files",
      "14": "Treasure Map / Attache Cases",
      "15": "Treasure (Standard)",
      "16": "Treasure (Larger)",
      "17": "Chicago Typewriter Ammo",
      "18": "Gold Bars",
      "19": "Arrows",
      "20": "Bonus Items",
      "21": "Bottle Caps (Treasure)",
      "22": "Bottle Caps (Piece)",
      "23": "Key"
    },
    "safe_swaps": {
      "key_treasure_group": [
        "Key",
        "Treasure (Standard)",
        "Treasure (Larger)",
        "Bottle Caps (Treasure)"
      ]
    }
  },
  "item_sizes": {
    "comment": "Each entry is a 16-byte block: 4b ID, 1b Width, 1b Height, 2b Pad, 4b FloatX, 4b FloatY. Float = (slots - 1) / 2.0",
    "offsets": {
      "Punisher": "0x808C10",
      "Handgun": "0x808CC0",
      "Red9": "0x808D18",
      "Blacktail": "0x808D70",
      "Matilda": "0x808BB8",
      "Broken Butterfly": "0x808DC8",
      "Killer7": "0x808E20",
      "Handcannon": "0x809138",
      "Shotgun": "0x808E78",
      "Striker": "0x808ED0",
      "Riot Gun": "0x8091E8",
      "Rifle": "0x808F28",
      "Rifle (semi-auto)": "0x808F80",
      "TMP": "0x808FD8",
      "Chicago Typewriter (Infinite)": "0x809030",
      "Mine Thrower": "0x8090E0",
      "P.R.L. 412": "0x809FA8",
      "Rocket Launcher": "0x809088",
      "Infinite Launcher": "0x809298",
      "Rocket Launcher (Special)": "0x809240",
      "Silencer (Handgun)": "0x8096B8",
      "Stock (Red9)": "0x809710",
      "Stock (TMP)": "0x809768",
      "Scope (Rifle)": "0x8097C0",
      "Scope (Semi-auto Rifle)": "0x809818",
      "Scope (Mine-thrower)": "0x809870",
      "Infrared Scope": "0x8098C8",
      "Hand Grenade": "0x809920",
      "Incendiary Grenade": "0x809978",
      "Flash Grenade": "0x8099D0",
      "First Aid Spray": "0x809A28",
      "Green Herb": "0x809C38",
      "Yellow Herb": "0x809CE8",
      "Red Herb": "0x809C90",
      "Mixed Herbs (G+G)": "0x809E48",
      "Mixed Herbs (G+G+G)": "0x809EA0",
      "Mixed Herbs (G+Y)": "0x809D98",
      "Mixed Herbs (G+R)": "0x809D40",
      "Mixed Herbs (G+R+Y)": "0x809EF8",
      "Black Bass": "0x809B88",
      "Black Bass (L)": "0x809BE0",
      "Chicken Egg": "0x809A80",
      "Brown Chicken Egg": "0x809AD8",
      "Gold Chicken Egg": "0x809B30",
      "Magnum Ammo": "0x8095B0",
      "Handgun Ammo": "0x8093A0",
      "TMP Ammo": "0x8093F8",
      "Shotgun Shells": "0x809450",
      "Rifle Ammo": "0x8094A8",
      "Chicago Typewriter Ammo": "0x809500",
      "Handcannon Ammo": "0x809558",
      "Mine-darts": "0x809608",
      "Arrows": "0x809660",
      "Bowgun Bolts": "0x80A058"
    }
  },
  "item_combinations": {
    "counter_offsets": ["0x304C98", "0x304CB3"],
    "list_base_offset": "0x721EC8",
    "default_count": 75,
    "max_slots": 125,
    "comment": "Max slots calculated from available space up to 0x7221BF.",
    "default_combinations": [
      { "item_a": "Handgun", "item_b": "Silencer (Handgun)", "result": "Handgun w/ Silencer" },
      { "item_a": "Red9", "item_b": "Stock (Red9)", "result": "Red9 w/ Stock" },
      { "item_a": "TMP", "item_b": "Stock (TMP)", "result": "TMP w/ Stock" },
      { "item_a": "Rifle", "item_b": "Scope (Rifle)", "result": "Rifle + Scope" },
      { "item_a": "Rifle w/ Infrared Scope", "item_b": "Scope (Rifle)", "result": "Rifle + Scope" },
      { "item_a": "Rifle", "item_b": "Infrared Scope", "result": "Rifle w/ Infrared Scope" },
      { "item_a": "Rifle + Scope", "item_b": "Infrared Scope", "result": "Rifle w/ Infrared Scope" },
      { "item_a": "Rifle (semi-auto)", "item_b": "Scope (Semi-auto Rifle)", "result": "Rifle (semi-auto) w/ Scope" },
      { "item_a": "Rifle (semi-auto) w/ Infrared Scope", "item_b": "Scope (Semi-auto Rifle)", "result": "Rifle (semi-auto) w/ Scope" },
      { "item_a": "Rifle (semi-auto)", "item_b": "Infrared Scope", "result": "Rifle (semi-auto) w/ Infrared Scope" },
      { "item_a": "Rifle (semi-auto) w/ Scope", "item_b": "Infrared Scope", "result": "Rifle (semi-auto) w/ Infrared Scope" },
      { "item_a": "Mine Thrower", "item_b": "Scope (Mine-thrower)", "result": "Mine-thrower + Scope" },
      { "item_a": "P.R.L. 412", "item_b": "Punisher w/ Silencer", "result": "Blacktail w/ Silencer" },
      { "item_a": "Green Herb", "item_b": "Green Herb", "result": "Mixed Herbs (G+G)" },
      { "item_a": "Mixed Herbs (G+G)", "item_b": "Green Herb", "result": "Mixed Herbs (G+G+G)" },
      { "item_a": "Green Herb", "item_b": "Red Herb", "result": "Mixed Herbs (G+R)" },
      { "item_a": "Green Herb", "item_b": "Yellow Herb", "result": "Mixed Herbs (G+Y)" },
      { "item_a": "Red Herb", "item_b": "Yellow Herb", "result": "Mixed Herbs (R+Y)" },
      { "item_a": "Mixed Herbs (G+R)", "item_b": "Yellow Herb", "result": "Mixed Herbs (G+R+Y)" },
      { "item_a": "Mixed Herbs (G+Y)", "item_b": "Red Herb", "result": "Mixed Herbs (G+R+Y)" },
      { "item_a": "Mixed Herbs (R+Y)", "item_b": "Green Herb", "result": "Mixed Herbs (G+R+Y)" },
      { "item_a": "Beerstein", "item_b": "Green Catseye", "result": "Beerstein w/ (G)" },
      { "item_a": "Beerstein", "item_b": "Red Catseye", "result": "Beerstein w/ (R)" },
      { "item_a": "Beerstein", "item_b": "Yellow Catseye", "result": "Beerstein w/ (Y)" },
      { "item_a": "Beerstein w/ (R)", "item_b": "Green Catseye", "result": "Beerstein w/ (G,R)" },
      { "item_a": "Beerstein w/ (Y)", "item_b": "Green Catseye", "result": "Beerstein w/ (G,Y)" },
      { "item_a": "Beerstein w/ (G)", "item_b": "Red Catseye", "result": "Beerstein w/ (G,R)" },
      { "item_a": "Beerstein w/ (Y)", "item_b": "Red Catseye", "result": "Beerstein w/ (R,Y)" },
      { "item_a": "Beerstein w/ (G)", "item_b": "Yellow Catseye", "result": "Beerstein w/ (G,Y)" },
      { "item_a": "Beerstein w/ (R)", "item_b": "Yellow Catseye", "result": "Beerstein w/ (R,Y)" },
      { "item_a": "Beerstein w/ (R,Y)", "item_b": "Green Catseye", "result": "Beerstein w/ (G,R,Y)" },
      { "item_a": "Beerstein w/ (G,Y)", "item_b": "Red Catseye", "result": "Beerstein w/ (G,R,Y)" },
      { "item_a": "Beerstein w/ (G,R)", "item_b": "Yellow Catseye", "result": "Beerstein w/ (G,R,Y)" },
      { "item_a": "Crown", "item_b": "Crown Jewel", "result": "Crown with Jewels" },
      { "item_a": "Crown", "item_b": "Royal Insignia", "result": "Crown with an Insignia" },
      { "item_a": "Crown with Jewels", "item_b": "Royal Insignia", "result": "Salazar Family Crown" },
      { "item_a": "Crown with an Insignia", "item_b": "Crown Jewel", "result": "Salazar Family Crown" },
      { "item_a": "Butterfly Lamp", "item_b": "Green Eye", "result": "Butterfly Lamp w/ (G)" },
      { "item_a": "Butterfly Lamp", "item_b": "Red Eye", "result": "Butterfly Lamp w/ (R)" },
      { "item_a": "Butterfly Lamp", "item_b": "Blue Eye", "result": "Butterfly Lamp w/ (B)" },
      { "item_a": "Butterfly Lamp w/ (R)", "item_b": "Green Eye", "result": "Butterfly Lamp w/ (G,R)" },
      { "item_a": "Butterfly Lamp w/ (B)", "item_b": "Green Eye", "result": "Butterfly Lamp w/ (G,B)" },
      { "item_a": "Butterfly Lamp w/ (G)", "item_b": "Red Eye", "result": "Butterfly Lamp w/ (G,R)" },
      { "item_a": "Butterfly Lamp w/ (B)", "item_b": "Red Eye", "result": "Butterfly Lamp w/ (R,B)" },
      { "item_a": "Butterfly Lamp w/ (G)", "item_b": "Blue Eye", "result": "Butterfly Lamp w/ (G,B)" },
      { "item_a": "Butterfly Lamp w/ (R)", "item_b": "Blue Eye", "result": "Butterfly Lamp w/ (R,B)" },
      { "item_a": "Butterfly Lamp w/ (R,B)", "item_b": "Green Eye", "result": "Butterfly Lamp w/ (R,G,B)" },
      { "item_a": "Butterfly Lamp w/ (G,B)", "item_b": "Red Eye", "result": "Butterfly Lamp w/ (R,G,B)" },
      { "item_a": "Butterfly Lamp w/ (G,R)", "item_b": "Blue Eye", "result": "Butterfly Lamp w/ (R,G,B)" },
      { "item_a": "Elegant Mask", "item_b": "Green Gem", "result": "Elegant Mask w/ (G)" },
      { "item_a": "Elegant Mask", "item_b": "Red Gem", "result": "Elegant Mask w/ (R)" },
      { "item_a": "Elegant Mask", "item_b": "Purple Gem", "result": "Elegant Mask w/ (P)" },
      { "item_a": "Elegant Mask w/ (R)", "item_b": "Green Gem", "result": "Elegant Mask w/ (G,R)" },
      { "item_a": "Elegant Mask w/ (P)", "item_b": "Green Gem", "result": "Elegant Mask w/ (G,P)" },
      { "item_a": "Elegant Mask w/ (G)", "item_b": "Red Gem", "result": "Elegant Mask w/ (G,R)" },
      { "item_a": "Elegant Mask w/ (P)", "item_b": "Red Gem", "result": "Elegant Mask w/ (R,P)" },
      { "item_a": "Elegant Mask w/ (G)", "item_b": "Purple Gem", "result": "Elegant Mask w/ (G,P)" },
      { "item_a": "Elegant Mask w/ (R)", "item_b": "Purple Gem", "result": "Elegant Mask w/ (R,P)" },
      { "item_a": "Elegant Mask w/ (R,P)", "item_b": "Green Gem", "result": "Elegant Mask w/ (R,G,P)" },
      { "item_a": "Elegant Mask w/ (G,P)", "item_b": "Red Gem", "result": "Elegant Mask w/ (R,G,P)" },
      { "item_a": "Elegant Mask w/ (G,R)", "item_b": "Purple Gem", "result": "Elegant Mask w/ (R,G,P)" },
      { "item_a": "Golden Lynx", "item_b": "Green Stone of Judgement", "result": "Golden Lynx w/ (G)" },
      { "item_a": "Golden Lynx", "item_b": "Red Stone of Faith", "result": "Golden Lynx w/ (R)" },
      { "item_a": "Golden Lynx", "item_b": "Blue Stone of Treason", "result": "Golden Lynx w/ (B)" },
      { "item_a": "Golden Lynx w/ (R)", "item_b": "Green Stone of Judgement", "result": "Golden Lynx w/ (G,R)" },
      { "item_a": "Golden Lynx w/ (B)", "item_b": "Green Stone of Judgement", "result": "Golden Lynx w/ (G,B)" },
      { "item_a": "Golden Lynx w/ (G)", "item_b": "Red Stone of Faith", "result": "Golden Lynx w/ (G,R)" },
      { "item_a": "Golden Lynx w/ (B)", "item_b": "Red Stone of Faith", "result": "Golden Lynx w/ (R,B)" },
      { "item_a": "Golden Lynx w/ (G)", "item_b": "Blue Stone of Treason", "result": "Golden Lynx w/ (G,B)" },
      { "item_a": "Golden Lynx w/ (R)", "item_b": "Blue Stone of Treason", "result": "Golden Lynx w/ (R,B)" },
      { "item_a": "Golden Lynx w/ (R,B)", "item_b": "Green Stone of Judgement", "result": "Golden Lynx w/ (G,R,B)" },
      { "item_a": "Golden Lynx w/ (G,B)", "item_b": "Red Stone of Faith", "result": "Golden Lynx w/ (G,R,B)" },
      { "item_a": "Golden Lynx w/ (G,R)", "item_b": "Blue Stone of Treason", "result": "Golden Lynx w/ (G,R,B)" },
      { "item_a": "Emblem (Right Half)", "item_b": "Emblem (Left Half)", "result": "Hexagonal Emblem" },
      { "item_a": "Moonstone (Right Half)", "item_b": "Moonstone (Left Half)", "result": "Blue Moonstone" }
    ]
  },
  "shooting_range": {
    "comment": "Offsets for items in the shooting range. Paired items MUST have the same item ID.",
    "slots": [
      { "name": "Weapon 1 (Handgun Pair A)", "id_offset": "0x30AB82", "default_id": "0x23", "pair_id": "handgun" },
      { "name": "Weapon 1 (Handgun Pair B)", "id_offset": "0x30ABF1", "default_id": "0x23", "pair_id": "handgun" },
      { "name": "Weapon 2 (Rifle Pair A)",   "id_offset": "0x30AC61", "default_id": "0x2E", "pair_id": "rifle" },
      { "name": "Weapon 2 (Rifle Pair B)",   "id_offset": "0x30AB89", "default_id": "0x2E", "pair_id": "rifle" },
      { "name": "Weapon 3 (Shotgun Pair A)", "id_offset": "0x30ADAB", "default_id": "0x2C", "pair_id": "shotgun" },
      { "name": "Weapon 3 (Shotgun Pair B)", "id_offset": "0x30AE28", "default_id": "0x2C", "pair_id": "shotgun" },
      { "name": "Weapon 4 (TMP Pair A)",     "id_offset": "0x30ADB0", "default_id": "0x30", "pair_id": "tmp" },
      { "name": "Weapon 4 (TMP Pair B)",     "id_offset": "0x30AE98", "default_id": "0x30", "pair_id": "tmp" },
      { "name": "Ammo Slot 1", "id_offset": "0x30ADDC", "default_id": "0x18", "comment": "Shotgun Shells (10 ammo)" },
      { "name": "Ammo Slot 2", "id_offset": "0x30ADE3", "default_id": "0x18", "comment": "Shotgun Shells (10 ammo)" },
      { "name": "Ammo Slot 3", "id_offset": "0x30ADD5", "default_id": "0x20", "comment": "TMP Ammo (100 ammo)" },
      { "name": "Grenade Slot", "id_offset": "0x30AB90", "default_id": "0x01", "comment": "Explosive Grenade (Sniping)" },
      { "name": "Ammo Slot 4", "id_offset": "0x30AB97", "default_id": "0x04", "comment": "Handgun Ammo (50 ammo)" },
      { "name": "Ammo Slot 5", "id_offset": "0x30AB9E", "default_id": "0x07", "comment": "Rifle Ammo (10pcs)" },
      { "name": "Ammo Slot 6", "id_offset": "0x30ABA5", "default_id": "0x07", "comment": "Rifle Ammo (10pcs)" },
      { "name": "Ammo Slot 7", "id_offset": "0x30ABAC", "default_id": "0x07", "comment": "Rifle Ammo (10pcs)" }
    ]
  },
   "starter_money_health": {
    "comment": "Offsets for starting money and health for Leon and Ashley.",
    "stats": [
      {
        "name": "Leon's Starting Money",
        "offsets": ["0x30C75C"],
        "dtype": "<I",
        "comment": "4-byte integer. 50000 is 0x0000C350."
      },
      {
        "name": "Leon's Starting Health",
        "offsets": ["0x3614D9", "0x361537"],
        "dtype": "<H",
        "comment": "2-byte short. Default is 1200."
      },
      {
        "name": "Ashley's Starting Health",
        "offsets": ["0x361557"],
        "dtype": "<H",
        "comment": "2-byte short. Default is 600."
      }
    ]
  }
}
            """
            self.all_data = json.loads(json_string)
            
            if initial_load:
                self.stackable_items_set = set()
                self.stacking_offsets = {}
                self.stacking_groups = {}
                self.stacking_group_map = {}
                self.weapon_name_to_id={"None":0}
                self.weapon_id_to_name={0:"None"}
                self.ammo_weapon_map = {}

            self.combination_data = self.all_data.get("item_combinations", {})

            self.item_size_offsets = self.all_data.get("item_sizes", {}).get("offsets", {})
            self.sorted_sizable_items = sorted(self.item_size_offsets.keys())

            item_type_data = self.all_data.get("item_type_definitions", {})
            self.item_type_base_offset = int(item_type_data.get("base_offset", "0"), 16)
            self.item_type_map = {int(k): v for k, v in item_type_data.get("types", {}).items()}
            self.item_type_reverse_map = {v: k for k, v in self.item_type_map.items()}

            self.treasure_items = set(self.all_data.get("treasure_items", []))
            self.key_items = set(self.all_data.get("key_items", []))
            self.weapon_ammo_map = self.all_data.get("weapon_ammo_map", {})
            
            self.ammo_weapon_map = {}
            for weapon, ammo in self.weapon_ammo_map.items():
                if ammo not in self.ammo_weapon_map: self.ammo_weapon_map[ammo] = []
                self.ammo_weapon_map[ammo].append(weapon)

            stacking_data = self.all_data.get("ammo_stacking_offsets", {})
            if stacking_data:
                for item_name, offset_str in stacking_data.get("individual", {}).items():
                    self.stacking_offsets[item_name] = int(offset_str, 16); self.stackable_items_set.add(item_name)
                self.stacking_groups = stacking_data.get("groups", {})
                for group_name, group_info in self.stacking_groups.items():
                    offset = int(group_info["offset"], 16)
                    for item_name in group_info["items"]:
                        self.stacking_offsets[item_name] = offset; self.stacking_group_map[item_name] = group_name; self.stackable_items_set.add(item_name)
            
            all_price_items = self.all_data.get("master_item_prices", {})
            all_weapon_names = {item for cat, items in self.all_data["items"]["categories"].items() if "Weapon" in cat or "gun" in cat or "Rifle" in cat or "Magnum" in cat for item in items}
            all_weapons_with_prices = {w for w in all_weapon_names if w in all_price_items}
            all_ammo_with_prices = {a for a in self.weapon_ammo_map.values() if a in all_price_items}
            
            categorized_list, processed_items_cat = [], set()
            for cat_name, cat_items in self.all_data["items"]["categories"].items():
                if any(n in cat_name for n in ["Handguns", "Shotguns", "Rifles", "Magnums", "Submachine", "Special Weapons"]):
                    weapon_group = sorted([w for w in cat_items if w in all_weapons_with_prices])
                    if weapon_group:
                        categorized_list.append(f"--- {cat_name} ---"); categorized_list.extend(weapon_group); processed_items_cat.update(weapon_group)
                        ammo_for_group = sorted({self.weapon_ammo_map.get(w) for w in weapon_group if w in self.weapon_ammo_map and self.weapon_ammo_map.get(w) is not None})
                        categorized_list.extend(ammo_for_group); processed_items_cat.update(ammo_for_group)
            self.sorted_list_ammo_categorized = categorized_list + ["--- Other Items ---"] + sorted([i for i in all_price_items if i not in processed_items_cat])

            grouped_list, processed_items_grp = [], set()
            for cat_name, cat_items in self.all_data["items"]["categories"].items():
                if any(n in cat_name for n in ["Handguns", "Shotguns", "Rifles", "Magnums", "Submachine", "Special Weapons"]):
                    weapon_group = sorted([w for w in cat_items if w in all_weapons_with_prices])
                    if weapon_group: grouped_list.append(f"--- {cat_name} ---"); grouped_list.extend(weapon_group); processed_items_grp.update(weapon_group)
            grouped_list.append("--- Ammo ---"); grouped_list.extend(sorted(list(all_ammo_with_prices))); processed_items_grp.update(all_ammo_with_prices)
            grouped_list.append("--- Other Items ---"); grouped_list.extend(sorted([i for i in all_price_items if i not in processed_items_grp]))
            self.sorted_list_ammo_grouped = grouped_list
            
            self.sorted_price_item_list = self.sorted_list_ammo_grouped if self.ammo_sort_is_grouped else self.sorted_list_ammo_categorized

            merchant_items = self.all_data["merchant"].items()
            sorted_merchant_items = sorted(merchant_items, key=lambda item: item[1].get("sort_order", 999))
            self.merchant_display_to_key = {v.get("display_name", k): k for k, v in sorted_merchant_items}
            display_names = ["-"] + [v.get("display_name", k) for k, v in sorted_merchant_items]
            if initial_load or not hasattr(self, 'merchant_menu'): self.merchant_menu_values = display_names
            else: self.merchant_menu.configure(values=display_names)
            
            self.item_name_to_id = {k: int(v, 16) for k, v in self.all_data["item_hex_ids"].items()}
            self.item_id_to_name = {v: k for k, v in self.item_name_to_id.items()}
            self.item_name_to_id["None"] = 0xFFFF
            self.item_id_to_name[0xFFFF] = "None"
            
            all_items_cats = {}
            all_items_cats.update(self.all_data["items"]["categories"])
            self.all_items_categorized = {"categories": all_items_cats}

            weapon_ids = { "Handgun": 0x23, "Red9": 0x25, "Punisher": 0x21, "Blacktail": 0x27, "Broken Butterfly": 0x29, "Killer7": 0x2A, "Shotgun": 0x2C, "Riot Gun": 0x94, "Striker": 0x2D, "Rifle": 0x2E, "Rifle (semi-auto)": 0x2F, "TMP": 0x30, "Chicago Typewriter": 0x53, "Handcannon": 0x37, "Mine Thrower": 0x36, "Matilda": 0x03 }
            self.weapon_name_to_id.update(weapon_ids)
            self.weapon_id_to_name.update({v: k for k, v in self.weapon_name_to_id.items()})
            if initial_load: self.status_bar.configure(text="All data loaded. Select executable to begin.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load embedded JSON data: {e}"); self.quit()
            
    def select_exe_file(self):
        filepath = filedialog.askopenfilename(title="Select Resident Evil 4 EXE", filetypes=(("Executable files", "*.exe"),));
        
        if filepath:
            if os.path.basename(filepath).lower() != 'bio4.exe':
                if not messagebox.askokcancel("Warning: File Name", "The selected file is not named 'bio4.exe'.\n\nThis can cause errors if it is not a valid RE4 executable.\n\nContinue?", icon=messagebox.WARNING): return

            self.exe_path = filepath
            self.exe_path_entry.configure(state="normal"); self.exe_path_entry.delete(0, "end"); self.exe_path_entry.insert(0, self.exe_path); self.exe_path_entry.configure(state="disabled")
            self.create_backup()
            
            self.load_all_data()
            self.pending_sacrifices = self._get_current_sacrifices_from_exe()

            self.active_backup_path = self.backup_path if os.path.exists(self.backup_path) else ""
            self.backup_path_entry.configure(state="normal")
            self.backup_path_entry.delete(0, "end")
            self.backup_path_entry.insert(0, self.active_backup_path)
            self.backup_path_entry.configure(state="disabled")

            if hasattr(self, 'analyzer_mod_exe_entry'): self.analyzer_mod_exe_entry.delete(0, 'end'); self.analyzer_mod_exe_entry.insert(0, self.exe_path)
            if hasattr(self, 'analyzer_base_exe_entry') and self.active_backup_path: self.analyzer_base_exe_entry.delete(0, 'end'); self.analyzer_base_exe_entry.insert(0, self.active_backup_path)

            self.merchant_menu.configure(state="normal"); self.apply_stock_button.configure(state="normal"); self.weapon_editor_button.configure(state="normal"); self.merchant_refresh_button.configure(state="normal")
            if hasattr(self, 'upgrade_weapon_button'): self.upgrade_weapon_button.configure(state="normal")
            
            self._update_reset_button_states()
            
            if self.current_tab_name == "Merchant Stock Editor": self.on_merchant_chapter_selected(self.merchant_menu.get())
            elif self.last_selected_weapon != "-": self.on_weapon_selected(self.last_selected_weapon)

            self._on_tab_change()
            
    def select_backup_file(self):
        filepath = filedialog.askopenfilename(title="Select Backup Source", filetypes=(("Backup files", "*.bakp"),("All files", "*.*")));
        if filepath:
            self.active_backup_path = filepath
            self.backup_path_entry.configure(state="normal")
            self.backup_path_entry.delete(0, "end")
            self.backup_path_entry.insert(0, self.active_backup_path)
            self.backup_path_entry.configure(state="disabled")
            self._update_reset_button_states()
            self.status_bar.configure(text=f"Loaded new backup source: {os.path.basename(filepath)}")

    def _update_reset_button_states(self):
        is_backup_valid = self.active_backup_path and os.path.exists(self.active_backup_path)
        new_state = "normal" if is_backup_valid else "disabled"

        action_buttons = ['reset_upgrades_button', 'reset_all_upgrades_button', 'reset_all_stats_button', 
                         'reset_all_weapons_all_stats_button', 'reset_selected_merchant_button', 'reset_all_merchants_button',
                         'reset_combinations_button', 'reset_all_new_game_button', 'set_gag_inv_button', 'reset_shooting_range_button', 'reset_money_health_button']
        
        for btn_name in action_buttons:
            if hasattr(self, btn_name):
                getattr(self, btn_name).configure(state=new_state)
        
        if self.price_editor_loaded:
            if hasattr(self, 'reset_all_prices_button'): self.reset_all_prices_button.configure(state=new_state)
            for widget_info in self.price_editor_widgets.values():
                if widget_info.get("is_divider") and 'reset_button' in widget_info: widget_info["reset_button"].configure(state=new_state)
        
        if self.item_type_editor_loaded and hasattr(self, 'reset_types_button'):
            self.reset_types_button.configure(state=new_state)
            
        if self.item_size_editor_loaded and hasattr(self, 'reset_sizes_button'):
            self.reset_sizes_button.configure(state=new_state)
            
        if self.combinations_editor_loaded and hasattr(self, 'reset_combinations_button'):
            self.reset_combinations_button.configure(state=new_state)
            
    def create_backup(self):
        self.backup_path = f"{self.exe_path}.bakp"
        if not os.path.exists(self.backup_path):
            try: shutil.copy2(self.exe_path, self.backup_path); self.status_bar.configure(text="Backup created. Ready to mod.")
            except Exception as e: messagebox.showerror("Backup Failed", f"Could not create backup: {e}")
        else: self.status_bar.configure(text="Backup already exists. Ready to mod.")

    def center_window(self, w, h): self.geometry(f'{w}x{h}+{int((self.winfo_screenwidth()/2)-(w/2))}+{int((self.winfo_screenheight()/2)-(h/2))}')
    def create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Executable...", command=self.select_exe_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about_dialog)
   
    def show_about_dialog(self, is_first_launch=False):
        title = f"Welcome to {self.APP_VERSION}!" if is_first_launch else "About Ultimate Weapons & Merchant Tool"
        
        messagebox.showinfo(
            title,
            f"Ultimate Weapons & Merchant Tool {self.APP_VERSION}\n\n"
            "Developed by Player7z with AI assistance.\n\n"
            "--- Special thanks to---\n"
            "- Modding Community and ME.\n"
            "--- What's New ---\n"
            "- [FIX] Major Weapon Stats Overhaul (Combinable Weapons)\n"
            "- [ENH] Added Shared Upgrades Prices When MAX FS is over 3\n"            
        )
        


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
            elif tid == "weapons_editor":
                panel = WeaponsItemsPanel(self._content, self)
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
            cm = self._cm_app
            if cm is None or not cm.scanned:
                messagebox.showwarning(
                    "Scan Required" if CURRENT_LANG == "en" else "يلزم مسح",
                    ("Please scan bio4.exe from RE4 CODE MANAGER first.\n"
                     "Go to RE4 CODE MANAGER → press SCAN EXE → return here.")
                    if CURRENT_LANG == "en" else
                    ("سوي Scan من RE4 CODE MANAGER أولاً.\n"
                     "روح RE4 CODE MANAGER ← اضغط SCAN EXE ← ارجع هنا.")
                )
            else:
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
