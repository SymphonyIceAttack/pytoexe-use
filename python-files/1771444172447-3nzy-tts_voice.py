import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import json
import torch
import numpy as np
import sounddevice as sd
import queue
import re
import math

# ────────────────────────────────────────────────
#  Настройки
# ────────────────────────────────────────────────

CONFIG_FILE = "tts_chat_config.json"
QUEUE = queue.Queue(maxsize=50)  # items: (name, text, vol_mod)
STOP_EVENT = threading.Event()
SAMPLE_RATE = 48000
MALE_VOICE = 'eugene'
FEMALE_VOICE = 'kseniya'
CURRENT_THREAD = None

NAME_GENDER = {
    'bianca': 'female', 'lillian': 'female', 'li': 'female', 'kim': 'female',
    'anna': 'female', 'anya': 'female', 'maria': 'female', 'sophia': 'female',
    'olivia': 'female', 'emma': 'female', 'ava': 'female', 'mia': 'female',
    'charlotte': 'female', 'amelia': 'female', 'harper': 'female', 'evelyn': 'female',
    'abigail': 'female', 'emily': 'female', 'elizabeth': 'female', 'sofia': 'female',
    'avery': 'female', 'ella': 'female', 'scarlett': 'female', 'grace': 'female',
    'chloe': 'female', 'victoria': 'female', 'riley': 'female', 'aria': 'female',
    'lily': 'female', 'aaliyah': 'female', 'zoey': 'female', 'penelope': 'female',
    'layla': 'female', 'nora': 'female', 'hannah': 'female', 'luna': 'female',
    'john': 'male', 'alex': 'male', 'james': 'male', 'michael': 'male',
    'david': 'male', 'daniel': 'male', 'matthew': 'male', 'andrew': 'male',
    'joseph': 'male', 'christopher': 'male', 'ryan': 'male', 'ethan': 'male',
    'logan': 'male', 'lucas': 'male', 'benjamin': 'male', 'samuel': 'male',
    'johnplon': 'male', 'richie': 'male', 'сourtney': 'female',
}

voice_cache = {}
VOLUME = 1.0  # 0.0 – 1.0

def get_voice_by_name(name: str) -> str:
    if not name:
        return 'kseniya'
    key = name.lower().strip().split()[0]
    if key in voice_cache:
        return voice_cache[key]
    if key in NAME_GENDER:
        voice = FEMALE_VOICE if NAME_GENDER[key] == 'female' else MALE_VOICE
    elif key.endswith(('a', 'ya', 'ia', 'ea', 'na', 'ra', 'sa', 'ta', 'la', 'ma',
                       'ka', 'ja', 'ha', 'va', 'sha', 'lia', 'nia', 'sia', 'tia', 'yna', 'ie')):
        voice = FEMALE_VOICE
    else:
        voice = MALE_VOICE
    voice_cache[key] = voice
    return voice

# ────────────────────────────────────────────────
#  Загрузка модели
# ────────────────────────────────────────────────

print("Загружаем Silero TTS v5_ru...")
try:
    model, _ = torch.hub.load(
        repo_or_dir='snakers4/silero-models',
        model='silero_tts',
        language='ru',
        speaker='v5_ru',
        trust_repo=True
    )
    print("Модель загружена.")
except Exception as e:
    print("Ошибка загрузки:", e)
    exit(1)

# ────────────────────────────────────────────────
#  Синтез речи
# ────────────────────────────────────────────────

# ────────────────────────────────────────────────
#  Цифры → русские слова
# ────────────────────────────────────────────────

_ONES = ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять',
         'десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 'пятнадцать',
         'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать']
_TENS = ['', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят',
         'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто']
_HUNDS = ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот',
          'шестьсот', 'семьсот', 'восемьсот', 'девятьсот']

def _int_to_ru(n: int) -> str:
    if n < 0:
        return 'минус ' + _int_to_ru(-n)
    if n == 0:
        return 'ноль'
    parts = []
    billions = n // 1_000_000_000
    millions = (n % 1_000_000_000) // 1_000_000
    thousands = (n % 1_000_000) // 1_000
    rest = n % 1_000
    if billions:
        parts.append(_three(billions, 'миллиард', 'миллиарда', 'миллиардов', masc=True))
    if millions:
        parts.append(_three(millions, 'миллион', 'миллиона', 'миллионов', masc=True))
    if thousands:
        parts.append(_three(thousands, 'тысяча', 'тысячи', 'тысяч', masc=False))
    if rest:
        parts.append(_below1000(rest, masc=True))
    return ' '.join(parts)

def _below1000(n: int, masc: bool) -> str:
    parts = []
    if n >= 100:
        parts.append(_HUNDS[n // 100])
        n %= 100
    if n >= 20:
        parts.append(_TENS[n // 10])
        n %= 10
    if n > 0:
        if not masc and n == 1: parts.append('одна')
        elif not masc and n == 2: parts.append('две')
        else: parts.append(_ONES[n])
    return ' '.join(parts)

def _three(n: int, one: str, two: str, five: str, masc: bool) -> str:
    w = _below1000(n, masc)
    r = n % 100
    if 11 <= r <= 19:
        return w + ' ' + five
    r = n % 10
    if r == 1: return w + ' ' + one
    if 2 <= r <= 4: return w + ' ' + two
    return w + ' ' + five

def numbers_to_words(text: str) -> str:
    """Заменяет все числа в тексте на русские слова."""
    def replace_num(m):
        return _int_to_ru(int(m.group()))
    return re.sub(r'\b\d+\b', replace_num, text)


def synthesize_and_play(text: str, speaker: str, vol_mod: float = 1.0):
    if not text.strip():
        return
    try:
        text = numbers_to_words(text)
        with torch.no_grad():
            audio = model.apply_tts(text=text + ".", speaker=speaker, sample_rate=SAMPLE_RATE)
        audio_np = audio.cpu().numpy()
        if np.max(np.abs(audio_np)) > 0:
            audio_np = audio_np / np.max(np.abs(audio_np)) * 0.92 * VOLUME * vol_mod
        sd.play(audio_np, SAMPLE_RATE)
        sd.wait()
    except Exception as e:
        print(f"Ошибка синтеза ({speaker}): {e}")

# ────────────────────────────────────────────────
#  Фильтр
# ────────────────────────────────────────────────

BLOCKED_PHRASES = [
    r'ваша\s+репорт\s+был',
    r'ваш\s+репорт\s+находится',
    r'любое\s+злоупотребление',
    r'ваш\s+транспорт\s+уже\s+заспавнен',
    r'.+сменил\s+персонажа',
]

def should_block_line(line: str) -> bool:
    if '/' in line:
        return True
    if re.search(r'\bbank\b', line, re.IGNORECASE):
        return True
    clean = re.sub(r'^\s*\[?\d{1,2}:\d{2}(:\d{2})?\]?\s*', '', line).strip()
    for phrase in BLOCKED_PHRASES:
        if re.match(phrase, clean, re.IGNORECASE | re.UNICODE):
            return True
    return False

def clean_message(line: str):
    original_line = line.strip()
    if not original_line:
        return "", "", 1.0
    if should_block_line(original_line):
        return "", "", 1.0

    # Убираем timestamp [18:09:23]
    line = re.sub(r'^\s*\[?\d{1,2}:\d{2}(:\d{2})?\]?\s*', '', original_line)
    line = re.sub(r'^\s*\[?\d{4}[-/.]\d{2}[-/.]\d{2}.*?\]?\s*', '', line)
    line = line.strip()

    if re.match(r'^(администратор|administrator)\b', line, re.IGNORECASE | re.UNICODE):
        return "", "", 1.0

    # Определяем модификатор громкости по тегу [тихо]
    vol_mod = 1.0
    if re.search(r'\[тихо\]', line, re.IGNORECASE | re.UNICODE):
        vol_mod = 1.0 / 3.5

    # Формат с круглыми скобками: "(Рация) Имя Фамилия говорит: текст"
    radio_match = re.match(
        r'^\([^)]+\)\s+'                      # (Рация) или любой тег в круглых скобках
        r'([A-ZА-ЯЁ][a-zа-яёA-ZА-ЯЁ]+)'     # Имя
        r'.*?:\s*(.+)$',
        line, re.UNICODE
    )
    if radio_match:
        name = radio_match.group(1).strip()
        text = radio_match.group(2).strip()
        text = re.sub(r'^["«„"]\s*', '', text).strip()
        text = re.sub(r'\[.*?\]', '', text).strip()
        text = re.sub(r'\*([^*]+)\*', r'\1', text).strip()
        if text:
            return name, text, vol_mod

    # Универсальный обработчик: любая комбинация префиксов [!], [N], [*] и т.д.
    prefixed = re.match(
        r'^(?:\[[^\]]{0,5}\]\s*)*'
        r'([A-ZА-ЯЁ][a-zа-яёA-ZА-ЯЁ]+)'
        r'.*?:\s*'
        r'(.+)$',
        line, re.UNICODE
    )
    if prefixed:
        name = prefixed.group(1).strip()
        text = prefixed.group(2).strip()
        text = re.sub(r'^["«„"]\s*', '', text).strip()
        text = re.sub(r'\[.*?\]', '', text).strip()
        text = re.sub(r'\*([^*]+)\*', r'\1', text).strip()
        if text:
            return name, text, vol_mod

    # Действие со звёздочкой: * Имя делает что-то
    if line.startswith('*'):
        parts = re.sub(r'^\*\s*', '', line).strip().split(maxsplit=1)
        if len(parts) >= 1:
            return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else ""), vol_mod
        return "", "", 1.0

    # Обычная реплика: Имя Фамилия говорит: текст
    match = re.match(
        r'^([A-ZА-ЯЁ][a-zа-яё]+(?:\s+[A-ZА-ЯЁ][a-zа-яё]+)+)'
        r'\s*(?:говорит\s*:\s*|:\s*|\s+)(.+)$',
        line, re.IGNORECASE | re.UNICODE
    )
    if match:
        name = match.group(1).strip()
        text = re.sub(r'^["«„"]\s*', '', match.group(2).strip()).strip()
        text = re.sub(r'\[.*?\]', '', text).strip()
        text = re.sub(r'\*([^*]+)\*', r'\1', text).strip()
        if text:
            return name, text, vol_mod

    return "", "", 1.0

# ────────────────────────────────────────────────
#  Потоки
# ────────────────────────────────────────────────

def tail_follower(path: str):
    if not os.path.isfile(path):
        return
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        f.seek(0, os.SEEK_END)
        while not STOP_EVENT.is_set():
            line = f.readline()
            if line:
                name, text, vol_mod = clean_message(line)
                if text:
                    try:
                        QUEUE.put_nowait((name, text, vol_mod))
                        print(f"→ [{name or 'действие'}] {text} (vol×{vol_mod:.2f})")
                    except queue.Full:
                        pass
            else:
                time.sleep(0.1)

def speaker_thread_func():
    while not STOP_EVENT.is_set():
        try:
            name, text, vol_mod = QUEUE.get(timeout=0.4)
            voice = get_voice_by_name(name)
            synthesize_and_play(text, voice, vol_mod)
        except queue.Empty:
            continue
        except Exception as e:
            print("Ошибка озвучки:", e)

# ────────────────────────────────────────────────
#  Цвета
# ────────────────────────────────────────────────

BG          = "#09090e"
CARD        = "#0f0f18"
CARD_BORDER = "#1e1e30"
SHINE       = "#252538"
TEXT_PRI    = "#dde1f0"
TEXT_MUT    = "#3a3a55"
TEXT_DIM    = "#22223a"
BTN_BLK     = "#080810"
BTN_BOR     = "#2a2a40"
BTN_HOV     = "#14141f"
GREEN       = "#00e676"
GREEN_DIM   = "#004d26"
BLUE        = "#5b9df5"

# ────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────

def rrect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
           x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
           x1,y2, x1,y2-r, x1,y1+r, x1,y1, x1+r,y1]
    return canvas.create_polygon(pts, smooth=True, **kw)

# ────────────────────────────────────────────────
#  Custom GlassEntry
# ────────────────────────────────────────────────

class GlassEntry(tk.Canvas):
    def __init__(self, parent, w=320, **kw):
        self._ew = w
        super().__init__(parent, width=w, height=36, bg=BG, highlightthickness=0, **kw)
        rrect(self, 0, 0, w, 36, 9, fill=CARD, outline=CARD_BORDER, width=1)
        rrect(self, 1, 1, w-1, 14, 9, fill=SHINE, outline="", width=0)
        self._var = tk.StringVar()
        self._ent = tk.Entry(self, textvariable=self._var, bg=CARD, fg=TEXT_PRI,
                             insertbackground=BLUE, relief='flat', bd=0,
                             font=("Consolas", 9), highlightthickness=0)
        self.create_window(w//2, 18, window=self._ent, width=w-22, height=22)

    def get(self):          return self._var.get()
    def delete(self, a, b): self._ent.delete(a, b)
    def insert(self, i, v): self._ent.insert(i, v)

# ────────────────────────────────────────────────
#  Custom GlassButton
# ────────────────────────────────────────────────

class GlassButton(tk.Canvas):
    def __init__(self, parent, text="", cmd=None, w=110, accent=False, **kw):
        self._bw = w
        self._label = text
        self._cmd   = cmd
        self._accent = accent
        self._over  = False
        super().__init__(parent, width=w, height=36, bg=BG,
                         highlightthickness=0, cursor="hand2", **kw)
        self._render()
        self.bind("<Enter>",           lambda e: self._hover(True))
        self.bind("<Leave>",           lambda e: self._hover(False))
        self.bind("<Button-1>",        lambda e: self._render(pressed=True))
        self.bind("<ButtonRelease-1>", self._release)

    def _render(self, pressed=False):
        self.delete("all")
        w, h, r = self._bw, 36, 18
        if self._accent:
            base = "#1a3a6a" if pressed else ("#1c3f72" if self._over else "#152d55")
            bord = "#4a80d0" if self._over else "#2a5090"
        else:
            base = "#050508" if pressed else (BTN_HOV if self._over else BTN_BLK)
            bord = "#333348" if self._over else BTN_BOR
        rrect(self, 0, 0, w, h, r, fill=base, outline=bord, width=1)
        shine_c = "#1a2a4a" if self._accent else SHINE
        rrect(self, 1, 1, w-1, h//2, r, fill=shine_c, outline="", width=0)
        rrect(self, 2, 2, w-2, h-2, r-2, fill="", outline="#0d0d1a", width=1)
        col = BLUE if self._accent else TEXT_PRI
        self.create_text(w//2, h//2, text=self._label, fill=col,
                         font=("Segoe UI", 9, "bold"))

    def _hover(self, state):
        self._over = state
        self._render()

    def _release(self, e):
        self._render()
        if self._cmd:
            self._cmd()

    def relabel(self, text):
        self._label = text
        self._render()

    def set_accent(self, v):
        self._accent = v
        self._render()

# ────────────────────────────────────────────────
#  Custom GlassSlider
# ────────────────────────────────────────────────

class GlassSlider(tk.Canvas):
    def __init__(self, parent, w=200, from_=0.0, to=1.0, initial=1.0, on_change=None, **kw):
        self._sw   = w
        self._from = from_
        self._to   = to
        self._val  = initial
        self._cb   = on_change
        super().__init__(parent, width=w, height=32, bg=BG, highlightthickness=0, cursor="hand2", **kw)
        self._render()
        self.bind("<Button-1>",        self._click)
        self.bind("<B1-Motion>",       self._drag_move)
        self.bind("<ButtonRelease-1>", lambda e: None)

    def _val_to_x(self, v):
        ratio = (v - self._from) / (self._to - self._from)
        return int(10 + ratio * (self._sw - 20))

    def _x_to_val(self, x):
        ratio = (x - 10) / (self._sw - 20)
        return max(self._from, min(self._to, self._from + ratio * (self._to - self._from)))

    def _render(self):
        self.delete("all")
        w, h = self._sw, 32
        track_y = h // 2
        tx1, tx2 = 10, w - 10
        rrect(self, tx1, track_y-3, tx2, track_y+3, 3,
              fill="#0a0a14", outline=CARD_BORDER, width=1)
        fx = self._val_to_x(self._val)
        if fx > tx1 + 4:
            rrect(self, tx1, track_y-3, fx, track_y+3, 3,
                  fill="#1e3a6e", outline="", width=0)
        tx = self._val_to_x(self._val)
        r = 9
        self.create_oval(tx-r-2, track_y-r-2, tx+r+2, track_y+r+2,
                         fill="", outline="#1a2a4a", width=1)
        rrect(self, tx-r, track_y-r, tx+r, track_y+r, r,
              fill=CARD, outline=BTN_BOR, width=1)
        rrect(self, tx-r+1, track_y-r+1, tx+r-1, track_y, r-1,
              fill=SHINE, outline="", width=0)
        self.create_oval(tx-3, track_y-3, tx+3, track_y+3,
                         fill=BLUE, outline="", width=0)

    def _click(self, e):
        self._val = self._x_to_val(e.x)
        self._render()
        if self._cb: self._cb(self._val)

    def _drag_move(self, e):
        self._val = self._x_to_val(e.x)
        self._render()
        if self._cb: self._cb(self._val)

    def get(self):
        return self._val

# ────────────────────────────────────────────────
#  Pulsing dot
# ────────────────────────────────────────────────

class Dot(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, width=12, height=12, bg=CARD, highlightthickness=0, **kw)
        self._on = False
        self._ph = 0.0
        self._idle()

    def _idle(self):
        self.delete("all")
        self.create_oval(2, 2, 10, 10, fill="#1a1a2a", outline="#222235", width=1)

    def activate(self, state: bool):
        self._on = state
        if state: self._pulse()
        else:     self._idle()

    def _pulse(self):
        if not self._on: return
        self.delete("all")
        self._ph += 0.18
        s = 0.65 + 0.35 * math.sin(self._ph)
        r = int(4 * s) + 1
        self.create_oval(6-r-2, 6-r-2, 6+r+2, 6+r+2, fill="", outline=GREEN_DIM, width=1)
        self.create_oval(2, 2, 10, 10, fill=GREEN, outline="#66ffaa", width=1)
        self.after(55, self._pulse)

# ────────────────────────────────────────────────
#  Logic
# ────────────────────────────────────────────────

def save_cfg():
    try:
        with open(CONFIG_FILE, 'w', encoding='utf8') as f:
            json.dump({"last_file": entry.get().strip()}, f, ensure_ascii=False)
    except: pass

def load_cfg():
    if not os.path.isfile(CONFIG_FILE): return
    try:
        with open(CONFIG_FILE, 'r', encoding='utf8') as f:
            d = json.load(f)
            if "last_file" in d:
                entry.delete(0, tk.END)
                entry.insert(0, d["last_file"])
    except: pass

def browse():
    p = filedialog.askopenfilename(
        title="Выберите лог",
        filetypes=[("Текстовые файлы", "*.log *.txt"), ("Все", "*.*")])
    if p:
        entry.delete(0, tk.END)
        entry.insert(0, p)
        save_cfg()

is_on = False

def toggle():
    global CURRENT_THREAD, is_on
    if not is_on:
        path = entry.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showwarning("Ошибка", "Выберите корректный файл лога")
            return
        STOP_EVENT.clear()
        save_cfg()
        threading.Thread(target=tail_follower, args=(path,), daemon=True).start()
        CURRENT_THREAD = threading.Thread(target=speaker_thread_func, daemon=True)
        CURRENT_THREAD.start()
        is_on = True
        btn_go.relabel("■  СТОП")
        btn_go.set_accent(False)
        dot.activate(True)
        lbl_s.config(text="АКТИВНО", fg=GREEN)
        lbl_sub.config(text="Слушаю чат...")
    else:
        STOP_EVENT.set()
        is_on = False
        btn_go.relabel("▶  СТАРТ")
        btn_go.set_accent(True)
        dot.activate(False)
        lbl_s.config(text="НЕ АКТИВНО", fg=TEXT_MUT)
        lbl_sub.config(text="Нажмите СТАРТ для запуска")

# ────────────────────────────────────────────────
#  Window
# ────────────────────────────────────────────────

W, H = 480, 330
root = tk.Tk()
root.title("TTS Voice")
root.geometry(f"{W}x{H}")
root.resizable(False, False)
root.configure(bg=BG)
root.attributes('-alpha', 0.97)

bg_c = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0)
bg_c.place(x=0, y=0)

for i in range(35, 0, -1):
    t = i / 35
    r_val = int(10 * t); g_val = int(14 * t); b_val = int(28 * t)
    col = f"#{r_val:02x}{g_val:02x}{b_val:02x}"
    cx2, cy2, rx, ry = W//2, 0, 220-i*4, 80-i
    try: bg_c.create_oval(cx2-rx, cy2-ry, cx2+rx, cy2+ry, fill=col, outline="")
    except: pass

cx, cy = 20, 20
cw, ch = W-40, H-40
card_c = tk.Canvas(root, width=cw, height=ch, bg=BG, highlightthickness=0)
card_c.place(x=cx, y=cy)

rrect(card_c, 0, 0, cw, ch, 20, fill=CARD, outline=CARD_BORDER, width=1)
rrect(card_c, 1, 1, cw-1, 55, 20, fill=SHINE, outline="", width=0)
rrect(card_c, 2, 2, cw-2, ch-2, 19, fill="", outline="#0a0a14", width=1)

card_c.create_text(28, 26, text="TTS VOICE READER",
                   fill=TEXT_PRI, font=("Segoe UI", 11, "bold"), anchor="w")
card_c.create_text(28, 43, text="Авто-озвучивание игрового чата",
                   fill=TEXT_MUT, font=("Segoe UI", 8), anchor="w")

card_c.create_line(20, 62, cw-20, 62, fill=CARD_BORDER, width=1)
card_c.create_text(20, 82, text="ЛОГ ФАЙЛ",
                   fill=TEXT_MUT, font=("Segoe UI", 7, "bold"), anchor="w")

entry = GlassEntry(root, w=298)
entry.place(x=cx+20, y=cy+90)

btn_browse = GlassButton(root, text="📁 Обзор", cmd=browse, w=98)
btn_browse.place(x=cx+cw-20-98, y=cy+90)

card_c.create_line(20, 142, cw-20, 142, fill=CARD_BORDER, width=1)
card_c.create_text(20, 160, text="СТАТУС",
                   fill=TEXT_MUT, font=("Segoe UI", 7, "bold"), anchor="w")

spw, sph = 190, 44
sp = tk.Canvas(root, width=spw, height=sph, bg=BG, highlightthickness=0)
sp.place(x=cx+20, y=cy+168)
rrect(sp, 0, 0, spw, sph, 12, fill=CARD, outline=CARD_BORDER, width=1)
rrect(sp, 1, 1, spw-1, 18, 12, fill=SHINE, outline="", width=0)

dot = Dot(root)
dot.place(x=cx+34, y=cy+182)

lbl_s = tk.Label(root, text="НЕ АКТИВНО", bg=CARD, fg=TEXT_MUT,
                 font=("Segoe UI", 10, "bold"))
lbl_s.place(x=cx+52, y=cy+172)

lbl_sub = tk.Label(root, text="Нажмите СТАРТ для запуска",
                   bg=CARD, fg=TEXT_DIM, font=("Segoe UI", 7))
lbl_sub.place(x=cx+52, y=cy+190)

btn_go = GlassButton(root, text="▶  СТАРТ", cmd=toggle, w=150, accent=True)
btn_go.place(x=cx+cw-20-150, y=cy+168)

card_c.create_line(20, 222, cw-20, 222, fill=CARD_BORDER, width=1)
card_c.create_text(20, 240, text="ГРОМКОСТЬ",
                   fill=TEXT_MUT, font=("Segoe UI", 7, "bold"), anchor="w")

def on_volume(val):
    global VOLUME
    VOLUME = val
    lbl_vol.config(text=f"{int(val * 100)}%")

slider = GlassSlider(root, w=340, initial=1.0, on_change=on_volume)
slider.place(x=cx+20, y=cy+248)

lbl_vol = tk.Label(root, text="100%", bg=CARD, fg=TEXT_PRI,
                   font=("Segoe UI", 8, "bold"))
lbl_vol.place(x=cx+cw-55, y=cy+254)

card_c.create_text(cw//2, ch-10, text="Silero TTS v5_ru  ·  powered by snakers4",
                   fill=TEXT_DIM, font=("Segoe UI", 7))

def _start(e): root._dx, root._dy = e.x, e.y
def _move(e):
    root.geometry(f"+{root.winfo_x()+e.x-root._dx}+{root.winfo_y()+e.y-root._dy}")

for w in (bg_c, card_c):
    w.bind("<Button-1>", _start)
    w.bind("<B1-Motion>", _move)

load_cfg()
root.protocol("WM_DELETE_WINDOW",
              lambda: [STOP_EVENT.set(), time.sleep(0.3), root.destroy()])

print("TTS GUI запущен.")
root.mainloop()