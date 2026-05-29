import json
import math
import os
import random
import struct
import sys
import time
import tkinter as tk
from tkinter import filedialog

import pygame

pygame.init()

# =========================================================
# НАСТРОЙКИ И КОНСТАНТЫ
# =========================================================
info = pygame.display.Info()
MONITOR_W, MONITOR_H = info.current_w, info.current_h
WINDOW_W, WINDOW_H = 1024, 768
IMAGES_DIR = "images"
SOUNDS_DIR = "sounds"
RECORDS_FILE = "records.json"
ACHIEVEMENTS_FILE = "achievements.json"
SETTINGS_FILE = "settings.json"
SAVE_FILE = "savegame.json"
CUSTOM_IMAGES_DIR = os.path.join(IMAGES_DIR, "custom")
HINT_TIME_PENALTY = 10
HINT_MOVE_PENALTY = 3

screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
pygame.display.set_caption("Puzzle Game Mega")

THEMES = {
    "dark": {
        "name": "Тёмная",
        "bg": (30, 32, 38),
        "panel": (45, 49, 58),
        "panel2": (44, 58, 71),
        "grid": (55, 60, 70),
        "border": (74, 85, 104),
        "text": (255, 255, 255),
        "accent": (52, 152, 219),
        "success": (46, 204, 113),
        "warning": (241, 196, 15),
        "danger": (231, 76, 60),
        "orange": (230, 126, 34),
    },
    "light": {
        "name": "Светлая",
        "bg": (226, 232, 240),
        "panel": (248, 250, 252),
        "panel2": (241, 245, 249),
        "grid": (203, 213, 225),
        "border": (100, 116, 139),
        "text": (15, 23, 42),
        "accent": (37, 99, 235),
        "success": (22, 163, 74),
        "warning": (202, 138, 4),
        "danger": (220, 38, 38),
        "orange": (234, 88, 12),
    },
    "neon": {
        "name": "Неон",
        "bg": (12, 12, 24),
        "panel": (25, 22, 45),
        "panel2": (31, 30, 64),
        "grid": (48, 42, 88),
        "border": (126, 87, 194),
        "text": (240, 248, 255),
        "accent": (0, 188, 212),
        "success": (0, 230, 118),
        "warning": (255, 214, 0),
        "danger": (255, 82, 82),
        "orange": (255, 145, 0),
    },
}

# =========================================================
# ГЛОБАЛЬНЫЕ ОБЪЕКТЫ И РАЗМЕТКА
# =========================================================
board_w, board_h = 600, 450
board_x = (WINDOW_W - board_w) // 2
board_y = 60

btn_choose = pygame.Rect(0, 0, 1, 1)
btn_easy = pygame.Rect(0, 0, 1, 1)
btn_medium = pygame.Rect(0, 0, 1, 1)
btn_hard = pygame.Rect(0, 0, 1, 1)
btn_box = pygame.Rect(0, 0, 1, 1)
btn_box_5 = pygame.Rect(0, 0, 1, 1)
btn_preview = pygame.Rect(0, 0, 1, 1)
btn_back_to_menu = pygame.Rect(0, 0, 1, 1)
btn_restart = pygame.Rect(0, 0, 1, 1)

btn_menu_play = pygame.Rect(0, 0, 1, 1)
btn_menu_records = pygame.Rect(0, 0, 1, 1)
btn_menu_settings = pygame.Rect(0, 0, 1, 1)
btn_menu_achievements = pygame.Rect(0, 0, 1, 1)
input_nick_rect = pygame.Rect(0, 0, 1, 1)
btn_pop_easy = pygame.Rect(0, 0, 1, 1)
btn_pop_medium = pygame.Rect(0, 0, 1, 1)
btn_pop_hard = pygame.Rect(0, 0, 1, 1)
btn_close_popup = pygame.Rect(0, 0, 1, 1)
btn_victory_again = pygame.Rect(0, 0, 1, 1)
btn_victory_menu = pygame.Rect(0, 0, 1, 1)
btn_victory_next = pygame.Rect(0, 0, 1, 1)
btn_music_toggle = pygame.Rect(0, 0, 1, 1)
btn_theme_toggle = pygame.Rect(0, 0, 1, 1)
volume_slider_rect = pygame.Rect(0, 0, 1, 1)
volume_knob_rect = pygame.Rect(0, 0, 1, 1)
btn_custom_minus = pygame.Rect(0, 0, 1, 1)
btn_custom_plus = pygame.Rect(0, 0, 1, 1)
btn_custom_start = pygame.Rect(0, 0, 1, 1)
btn_mode_toggle = pygame.Rect(0, 0, 1, 1)
btn_gallery_open = pygame.Rect(0, 0, 1, 1)
btn_continue = pygame.Rect(0, 0, 1, 1)
btn_save_game = pygame.Rect(0, 0, 1, 1)
btn_load_game = pygame.Rect(0, 0, 1, 1)
btn_controls_toggle = pygame.Rect(0, 0, 1, 1)
btn_hint_key_toggle = pygame.Rect(0, 0, 1, 1)
btn_right_rotate_toggle = pygame.Rect(0, 0, 1, 1)
gallery_rects = []

# =========================================================
# УТИЛИТЫ UI
# =========================================================
def clamp_color(color, delta):
    return tuple(max(0, min(255, x + delta)) for x in color)


def draw_text_center(text, font, color, surface, x, y):
    render = font.render(text, True, color)
    rect = render.get_rect(center=(x, y))
    surface.blit(render, rect)


def draw_button(surface, rect, text, font, base_color, text_color=(255, 255, 255), hovered=False, border_color=None):
    color = clamp_color(base_color, -25 if hovered else 0)
    pygame.draw.rect(surface, color, rect, border_radius=6)
    if border_color:
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=6)
    label = font.render(text, True, text_color)
    surface.blit(label, label.get_rect(center=rect.center))


def format_time(seconds):
    minutes = seconds // 60
    sec = seconds % 60
    return f"{minutes:02d}:{sec:02d}"


def difficulty_name(rows, cols):
    if rows == 3 and cols == 3:
        return "Лёгкий 3x3"
    if rows == 4 and cols == 4:
        return "Средний 4x4"
    if rows == 6 and cols == 6:
        return "Сложный 6x6"
    return f"{rows}x{cols}"


def update_layout_sizes(w, h):
    global board_w, board_h, board_x, board_y
    board_h = int(h * 0.55)
    board_w = int(board_h * 1.333)
    board_x = (w - board_w) // 2
    board_y = int(h * 0.06)

    btn_choose.update(board_x, h - 115, 230, 35)
    btn_easy.update(board_x, h - 65, 110, 35)
    btn_medium.update(board_x + 120, h - 65, 110, 35)
    btn_hard.update(board_x + 240, h - 65, 110, 35)
    btn_preview.update(board_x + 360, h - 65, 160, 35)
    btn_back_to_menu.update(board_x + 530, h - 65, 100, 35)
    btn_restart.update(board_x + 640, h - 65, 110, 35)
    btn_box.update(20, h - 140, 150, 110)
    btn_box_5.update(20, h - 178, 150, 32)

    input_nick_rect.update(w // 2 - 150, h // 2 - 95, 300, 45)
    btn_menu_play.update(w // 2 - 150, h // 2 - 35, 300, 50)
    btn_menu_records.update(w // 2 - 150, h // 2 + 25, 145, 42)
    btn_menu_settings.update(w // 2 + 5, h // 2 + 25, 145, 42)
    btn_menu_achievements.update(w // 2 - 150, h // 2 + 78, 300, 42)
    btn_continue.update(w // 2 - 150, h // 2 + 130, 300, 38)

    cx, cy = w // 2, h // 2
    btn_pop_easy.update(cx - 130, cy - 25, 260, 35)
    btn_pop_medium.update(cx - 130, cy + 20, 260, 35)
    btn_pop_hard.update(cx - 130, cy + 54, 260, 32)
    btn_custom_minus.update(cx - 130, cy + 94, 46, 30)
    btn_custom_plus.update(cx + 84, cy + 94, 46, 30)
    btn_custom_start.update(cx - 76, cy + 94, 152, 30)
    btn_mode_toggle.update(cx - 130, cy + 132, 260, 30)
    btn_gallery_open.update(cx - 130, cy + 168, 260, 30)
    btn_close_popup.update(cx + 112, cy - 102, 26, 26)
    btn_victory_again.update(cx - 195, cy + 65, 125, 36)
    btn_victory_menu.update(cx - 60, cy + 65, 120, 36)
    btn_victory_next.update(cx + 70, cy + 65, 125, 36)
    btn_music_toggle.update(cx - 135, cy - 35, 270, 38)
    btn_theme_toggle.update(cx - 135, cy + 15, 270, 38)
    volume_slider_rect.update(cx - 115, cy + 120, 230, 8)
    btn_controls_toggle.update(cx - 135, cy + 62, 270, 32)
    btn_hint_key_toggle.update(cx - 135, cy + 98, 130, 28)
    btn_right_rotate_toggle.update(cx + 5, cy + 98, 130, 28)
    btn_save_game.update(board_x + 240, h - 115, 110, 35)
    btn_load_game.update(board_x + 360, h - 115, 120, 35)


# =========================================================
# НАСТРОЙКИ, СОХРАНЕНИЕ И ГАЛЕРЕЯ
# =========================================================
def load_settings():
    default = {"theme": "dark", "volume": 0.75, "music": False, "rotate_key": "R", "hint_key": "SPACE", "right_click_rotate": True, "nickname": "Игрок"}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                default.update(data)
    except (OSError, json.JSONDecodeError):
        pass
    return default


def save_settings_dict(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def save_game_data(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def load_game_data():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def list_gallery_images():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(CUSTOM_IMAGES_DIR, exist_ok=True)
    result = []
    for folder in [IMAGES_DIR, CUSTOM_IMAGES_DIR]:
        try:
            for name in sorted(os.listdir(folder)):
                if name.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
                    path = os.path.join(folder, name)
                    if os.path.isfile(path):
                        result.append(path)
        except OSError:
            pass
    seen = set()
    unique = []
    for path in result:
        ap = os.path.abspath(path)
        if ap not in seen:
            seen.add(ap)
            unique.append(path)
    return unique[:12]


def make_window_icon():
    path = os.path.join(IMAGES_DIR, "icon.png")
    try:
        os.makedirs(IMAGES_DIR, exist_ok=True)
        if not os.path.exists(path):
            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 0))
            pygame.draw.rect(surf, (52, 152, 219), (8, 8, 22, 22), border_radius=5)
            pygame.draw.rect(surf, (46, 204, 113), (34, 8, 22, 22), border_radius=5)
            pygame.draw.rect(surf, (241, 196, 15), (8, 34, 22, 22), border_radius=5)
            pygame.draw.rect(surf, (231, 76, 60), (34, 34, 22, 22), border_radius=5)
            pygame.draw.circle(surf, (30, 32, 38), (31, 19), 6)
            pygame.draw.circle(surf, (30, 32, 38), (19, 31), 6)
            pygame.image.save(surf, path)
        pygame.display.set_icon(pygame.image.load(path))
    except Exception:
        pass

MODES = [
    ("normal", "Обычный"),
    ("timed", "На время"),
    ("no_hints", "Без подсказок"),
    ("kids", "Детский"),
    ("hardcore", "Хардкор"),
]

def mode_title(key):
    return dict(MODES).get(key, "Обычный")

# =========================================================
# ЗВУКИ И МУЗЫКА
# =========================================================
class SoundManager:
    def __init__(self):
        self.enabled = True
        self.music_enabled = False
        self.volume = 0.75
        self.sounds = {}
        try:
            pygame.mixer.init()
            self.available = True
        except pygame.error:
            self.available = False
        self.load_sounds()
        self.set_volume(self.volume)

    def make_tone(self, frequency=440, duration=0.12, volume=0.25):
        if not self.available:
            return None
        sample_rate = 22050
        frames = int(duration * sample_rate)
        buf = bytearray()
        for i in range(frames):
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * i / sample_rate))
            buf.extend(struct.pack("<h", value))
        try:
            return pygame.mixer.Sound(buffer=bytes(buf))
        except pygame.error:
            return None

    def load_sounds(self):
        if not self.available:
            return
        defaults = {
            "click": self.make_tone(520, 0.06, 0.18),
            "pick": self.make_tone(660, 0.07, 0.18),
            "lock": self.make_tone(880, 0.10, 0.20),
            "win": self.make_tone(1040, 0.30, 0.22),
        }
        self.sounds.update(defaults)
        # Если рядом с игрой есть папка sounds, реальные wav/ogg/mp3 заменят встроенные короткие звуки.
        if os.path.isdir(SOUNDS_DIR):
            for name in ["click", "pick", "lock", "win"]:
                for ext in ["wav", "ogg", "mp3"]:
                    path = os.path.join(SOUNDS_DIR, f"{name}.{ext}")
                    if os.path.exists(path):
                        try:
                            self.sounds[name] = pygame.mixer.Sound(path)
                            break
                        except pygame.error:
                            pass
        self.set_volume(self.volume)

    def set_volume(self, value):
        self.volume = max(0.0, min(1.0, float(value)))
        if not self.available:
            return
        for sound in self.sounds.values():
            if sound:
                try:
                    sound.set_volume(self.volume)
                except pygame.error:
                    pass
        try:
            pygame.mixer.music.set_volume(self.volume)
        except pygame.error:
            pass

    def play(self, name):
        if self.enabled and self.available and self.sounds.get(name):
            try:
                self.sounds[name].play()
            except pygame.error:
                pass

    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if not self.available:
            return
        music_path = None
        for filename in ["menu_music.mp3", "menu_music.ogg", "menu_music.wav"]:
            candidate = os.path.join(SOUNDS_DIR, filename)
            if os.path.exists(candidate):
                music_path = candidate
                break
        try:
            if self.music_enabled and music_path:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1)
            else:
                pygame.mixer.music.stop()
        except pygame.error:
            self.music_enabled = False

# =========================================================
# РЕКОРДЫ
# =========================================================
def load_records():
    if not os.path.exists(RECORDS_FILE):
        return []
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_records(records):
    try:
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def add_record(nickname, rows, cols, seconds, moves, stars=0, hints=0):
    records = load_records()
    records.append({
        "nickname": nickname or "Игрок",
        "difficulty": difficulty_name(rows, cols),
        "rows": rows,
        "cols": cols,
        "time": int(seconds),
        "moves": int(moves),
        "stars": int(stars),
        "hints": int(hints),
        "date": time.strftime("%Y-%m-%d %H:%M"),
    })
    records.sort(key=lambda r: (r.get("rows", 99) * r.get("cols", 99), r.get("time", 999999), r.get("moves", 999999)))
    save_records(records[:30])


def best_records_for(rows, cols, limit=5):
    records = [r for r in load_records() if r.get("rows") == rows and r.get("cols") == cols]
    records.sort(key=lambda r: (r.get("time", 999999), r.get("moves", 999999)))
    return records[:limit]


# =========================================================
# ДОСТИЖЕНИЯ
# =========================================================
ACHIEVEMENTS = {
    "first_win": {"title": "Первый пазл", "desc": "Собери любой пазл."},
    "no_hint": {"title": "Без подсказок", "desc": "Собери пазл без подсказок."},
    "speed_3x3": {"title": "Скоростной сборщик", "desc": "Собери 3x3 быстрее 45 секунд."},
    "master_6x6": {"title": "Мастер пазлов", "desc": "Собери сложность 6x6."},
    "three_stars": {"title": "Три звезды", "desc": "Заверши пазл на оценку ★★★."},
    "rotator": {"title": "Вращатель", "desc": "Поверни любую деталь клавишей R."},
    "custom_size": {"title": "Своя сложность", "desc": "Запусти пазл с нестандартным размером."},
    "saved_game": {"title": "Продолжение следует", "desc": "Сохрани игру и загрузи её снова."},
    "hardcore_win": {"title": "Хардкор", "desc": "Собери пазл в хардкорном режиме."},
}


def load_achievements():
    if not os.path.exists(ACHIEVEMENTS_FILE):
        return {}
    try:
        with open(ACHIEVEMENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_achievements(data):
    try:
        with open(ACHIEVEMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def unlock_achievement(key):
    data = load_achievements()
    if key not in ACHIEVEMENTS or data.get(key):
        return False
    data[key] = time.strftime("%Y-%m-%d %H:%M")
    save_achievements(data)
    return True

# =========================================================
# ГЕНЕРАЦИЯ И ЗАГРУЗКА ИЗОБРАЖЕНИЙ
# =========================================================
def generate_and_save_defaults():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(CUSTOM_IMAGES_DIR, exist_ok=True)
    make_window_icon()
    w, h = 1024, 768
    paths = [os.path.join(IMAGES_DIR, x) for x in ["easy.jpg", "medium.jpg", "hard.jpg"]]
    colors = [(39, 174, 96), (44, 62, 80), (142, 68, 173)]
    for i, path in enumerate(paths):
        if not os.path.exists(path):
            surf = pygame.Surface((w, h))
            surf.fill(colors[i])
            for _ in range(18):
                pygame.draw.circle(
                    surf,
                    (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
                    (random.randint(50, w - 50), random.randint(50, h - 50)),
                    random.randint(35, 105),
                )
            for _ in range(8):
                pygame.draw.rect(
                    surf,
                    (random.randint(40, 240), random.randint(40, 240), random.randint(40, 240)),
                    (random.randint(20, w - 180), random.randint(20, h - 140), random.randint(80, 180), random.randint(40, 120)),
                    border_radius=20,
                )
            pygame.image.save(surf, path)


def get_default_image_for_level(rows):
    names = {3: "easy.jpg", 4: "medium.jpg", 6: "hard.jpg"}
    return os.path.join(IMAGES_DIR, names.get(rows, "medium.jpg"))


def load_and_scale_image(path, rows, target_w, target_h):
    if not path:
        path = get_default_image_for_level(rows)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, (target_w, target_h)), None
        except Exception as e:
            return make_error_surface(target_w, target_h), f"Не удалось загрузить картинку: {e}"
    return make_error_surface(target_w, target_h), "Картинка не найдена"


def make_error_surface(target_w, target_h):
    surf = pygame.Surface((target_w, target_h))
    surf.fill((180, 50, 50))
    return surf

# =========================================================
# ГЕОМЕТРИЯ ПАЗЛА
# =========================================================
def generate_edge_profiles(rows, cols):
    horizontal_edges = [[0] * cols for _ in range(rows + 1)]
    vertical_edges = [[0] * (cols + 1) for _ in range(rows)]

    for r in range(1, rows):
        for c in range(cols):
            horizontal_edges[r][c] = random.choice([1, -1])
    for r in range(rows):
        for c in range(1, cols):
            vertical_edges[r][c] = random.choice([1, -1])
    return horizontal_edges, vertical_edges


def create_piece_mask(w, h, top, right, bottom, left):
    margin = max(18, int(min(w, h) * 0.34))
    ox, oy = margin, margin
    surf_w, surf_h = w + margin * 2, h + margin * 2
    scale = 3
    hi_mask = pygame.Surface((surf_w * scale, surf_h * scale), pygame.SRCALPHA)
    points = []

    def cubic_bezier(p0, p1, p2, p3, steps=10):
        result = []
        for i in range(1, steps + 1):
            t = i / steps
            mt = 1 - t
            x = (mt ** 3) * p0[0] + 3 * (mt ** 2) * t * p1[0] + 3 * mt * (t ** 2) * p2[0] + (t ** 3) * p3[0]
            y = (mt ** 3) * p0[1] + 3 * (mt ** 2) * t * p1[1] + 3 * mt * (t ** 2) * p2[1] + (t ** 3) * p3[1]
            result.append((x, y))
        return result

    def add_side(p1, p2, edge_type):
        if edge_type == 0:
            points.append(p2)
            return

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return

        ux, uy = dx / length, dy / length
        nx, ny = -uy, ux
        depth = min(w, h) * 0.24 * edge_type

        def pt(t, off=0):
            return (p1[0] + ux * length * t + nx * off, p1[1] + uy * length * t + ny * off)

        a = pt(0.30, 0)
        b = pt(0.36, 0.03 * depth)
        c = pt(0.38, 0.25 * depth)
        d = pt(0.43, 0.78 * depth)
        e = pt(0.50, 1.00 * depth)
        f = pt(0.57, 0.78 * depth)
        g = pt(0.62, 0.25 * depth)
        k = pt(0.64, 0.03 * depth)
        m = pt(0.70, 0)

        points.append(a)
        points.extend(cubic_bezier(a, pt(0.33, 0), pt(0.35, 0.02 * depth), b, 5))
        points.extend(cubic_bezier(b, pt(0.36, 0.16 * depth), pt(0.38, 0.20 * depth), c, 5))
        points.extend(cubic_bezier(c, pt(0.39, 0.55 * depth), pt(0.39, 0.74 * depth), d, 8))
        points.extend(cubic_bezier(d, pt(0.46, 0.98 * depth), pt(0.48, 1.05 * depth), e, 8))
        points.extend(cubic_bezier(e, pt(0.52, 1.05 * depth), pt(0.54, 0.98 * depth), f, 8))
        points.extend(cubic_bezier(f, pt(0.61, 0.74 * depth), pt(0.61, 0.55 * depth), g, 8))
        points.extend(cubic_bezier(g, pt(0.62, 0.20 * depth), pt(0.64, 0.16 * depth), k, 5))
        points.extend(cubic_bezier(k, pt(0.65, 0.02 * depth), pt(0.67, 0), m, 5))
        points.append(p2)

    t_l = (ox, oy)
    t_r = (ox + w, oy)
    b_r = (ox + w, oy + h)
    b_l = (ox, oy + h)

    points.append(t_l)
    add_side(t_l, t_r, top)
    add_side(t_r, b_r, right)
    add_side(b_r, b_l, -bottom)
    add_side(b_l, t_l, -left)

    scaled_points = [(int(x * scale), int(y * scale)) for x, y in points]
    pygame.draw.polygon(hi_mask, (255, 255, 255, 255), scaled_points)
    mask = pygame.transform.smoothscale(hi_mask, (surf_w, surf_h))
    return mask, ox, oy


class PuzzlePiece:
    def __init__(self, texture, x, y, w, h, edges, correct_pos, index=0, row=0, col=0):
        self.w, self.h = w, h
        self.correct_pos = correct_pos
        self.is_locked = False
        self.rotation = 0
        self.index = index
        self.row = row
        self.col = col
        self.group_id = index

        mask, ox, oy = create_piece_mask(w, h, *edges)
        piece_surf = pygame.Surface(mask.get_size(), pygame.SRCALPHA)
        piece_surf.blit(texture, (ox - x, oy - y))
        piece_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        rect = piece_surf.get_bounding_rect()
        self.image = piece_surf.subsurface(rect).copy()
        self.offset_x = rect.x - ox
        self.offset_y = rect.y - oy
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.base_image = self.image.copy()

        outline = self.mask.outline()
        if len(outline) > 2:
            pygame.draw.lines(self.image, (25, 25, 25, 180), True, outline, 2)

    def rotate_clockwise(self):
        if self.is_locked:
            return
        center = self.rect.center
        self.rotation = (self.rotation + 90) % 360
        self.image = pygame.transform.rotate(self.base_image, -self.rotation)
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.image)

    def contains_point(self, pos):
        x, y = pos[0] - self.rect.x, pos[1] - self.rect.y
        if 0 <= x < self.rect.w and 0 <= y < self.rect.h:
            return self.mask.get_at((int(x), int(y)))
        return False

    def get_origin_pos(self):
        return (self.rect.x - self.offset_x, self.rect.y - self.offset_y)

    def set_origin_pos(self, pos):
        tx, ty = pos
        self.rect.x = tx + self.offset_x
        self.rect.y = ty + self.offset_y

# =========================================================
# ФАЙЛЫ И СЛОТЫ ДЕТАЛЕЙ
# =========================================================
def open_file_dialog():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        title="Картинка пазла",
        filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp")],
    )
    root.destroy()
    return path


def calculate_spawn_slots(scr_w, scr_h, count):
    slots = []
    l_zone, r_zone = board_x - 40, board_x + board_w + 40
    usable_h = max(180, scr_h - 160)

    if l_zone > 60:
        for r in range(max(1, usable_h // 110)):
            for c in range(max(1, l_zone // 130)):
                if not (c == 0 and r >= (usable_h // 110) - 2):
                    slots.append((25 + c * 130, 40 + r * 110))
    if scr_w - r_zone - 20 > 60:
        for r in range(max(1, usable_h // 110)):
            for c in range(max(1, (scr_w - r_zone - 20) // 130)):
                slots.append((r_zone + c * 130, 40 + r * 110))
    while len(slots) < count:
        x1 = max(20, min(scr_w - 140, r_zone))
        x2 = max(x1 + 1, scr_w - 140)
        slots.append((random.randint(x1, x2), random.randint(40, usable_h)))
    random.shuffle(slots)
    return slots


def create_puzzle(image_path, rows, cols, scr_w, scr_h, seed=None):
    old_random_state = random.getstate()
    if seed is not None:
        random.seed(seed)
    current_board_img, error_message = load_and_scale_image(image_path, rows, board_w, board_h)
    p_w, p_h = board_w // cols, board_h // rows
    h_edges, v_edges = generate_edge_profiles(rows, cols)
    all_pieces, active_pieces, box_pieces = [], [], []
    for r in range(rows):
        for c in range(cols):
            edges = (h_edges[r][c], v_edges[r][c + 1], h_edges[r + 1][c], v_edges[r][c])
            piece = PuzzlePiece(
                current_board_img,
                c * p_w,
                r * p_h,
                p_w,
                p_h,
                edges,
                (board_x + c * p_w, board_y + r * p_h),
                index=r * cols + c,
                row=r,
                col=c,
            )
            box_pieces.append(piece)
            all_pieces.append(piece)
    random.shuffle(box_pieces)
    slots = calculate_spawn_slots(scr_w, scr_h, rows * cols)
    if seed is not None:
        random.setstate(old_random_state)
    return all_pieces, active_pieces, box_pieces, current_board_img, slots, error_message

# =========================================================
# ИГРА
# =========================================================
class Game:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.current_w = WINDOW_W
        self.current_h = WINDOW_H
        self.is_fullscreen = False
        self.state = "MENU"
        self.popup = None  # difficulty, records, settings, gallery
        self.settings = load_settings()
        self.nickname = str(self.settings.get("nickname", "Игрок"))
        self.input_active = False
        self.rows = 4
        self.cols = 4
        self.custom_size = 5
        self.mode = "normal"
        self.puzzle_seed = random.randint(1, 999999999)
        self.loaded_elapsed = 0
        self.time_limit = None
        self.lost_by_time = False
        self.current_image_path = None
        self.all_pieces = []
        self.active_pieces = []
        self.box_pieces = []
        self.current_board_img = None
        self.spawn_slots = []
        self.slot_index = 0
        self.selected_piece = None
        self.offset_x = 0
        self.offset_y = 0
        self.is_victory = False
        self.victory_saved = False
        self.start_ticks = pygame.time.get_ticks()
        self.end_seconds = 0
        self.moves = 0
        self.hints_used = 0
        self.hint_penalty_seconds = 0
        self.achievement_toast = ""
        self.achievement_toast_until = 0
        self.confetti = []
        self.stars = 0
        self.hint_piece = None
        self.hint_until_ticks = 0
        self.hint_message = ""
        self.hint_level = 0
        self.last_hint_index = None
        self.selected_group = []
        self.group_offsets = []
        self.dragging_volume = False
        self.error_message = ""
        self.theme_key = self.settings.get("theme", "dark") if self.settings.get("theme", "dark") in THEMES else "dark"
        self.sound = SoundManager()
        self.sound.set_volume(float(self.settings.get("volume", 0.75)))
        self.rotate_key = str(self.settings.get("rotate_key", "R"))
        self.hint_key = str(self.settings.get("hint_key", "SPACE"))
        self.right_click_rotate = bool(self.settings.get("right_click_rotate", True))
        self.bg_pieces = self.make_bg_pieces()

        self.font_btn = pygame.font.SysFont("Arial", 15, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 13, bold=True)
        self.font_box = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_win = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 46, bold=True)

        generate_and_save_defaults()
        if self.settings.get("music"):
            self.sound.toggle_music()
        update_layout_sizes(self.current_w, self.current_h)
        self.new_puzzle(reset_image=False)

    @property
    def theme(self):
        return THEMES[self.theme_key]

    def make_bg_pieces(self):
        pieces = []
        for _ in range(24):
            pieces.append({
                "x": random.randint(0, WINDOW_W),
                "y": random.randint(0, WINDOW_H),
                "speed": random.uniform(0.15, 0.55),
                "size": random.randint(12, 32),
                "phase": random.random() * math.tau,
            })
        return pieces

    def new_puzzle(self, rows=None, cols=None, image_path_marker="keep", reset_image=False, keep_seed=False):
        if rows:
            self.rows = rows
            self.cols = cols or rows
        if self.mode == "kids":
            self.rows = max(2, min(self.rows, 4))
            self.cols = max(2, min(self.cols, 4))
        if reset_image:
            self.current_image_path = None
        elif image_path_marker != "keep":
            self.current_image_path = image_path_marker
        if not keep_seed:
            self.puzzle_seed = random.randint(1, 999999999)

        (
            self.all_pieces,
            self.active_pieces,
            self.box_pieces,
            self.current_board_img,
            self.spawn_slots,
            error_message,
        ) = create_puzzle(self.current_image_path, self.rows, self.cols, self.current_w, self.current_h, self.puzzle_seed)
        self.slot_index = 0
        self.selected_piece = None
        self.is_victory = False
        self.victory_saved = False
        self.moves = 0
        self.hints_used = 0
        self.hint_penalty_seconds = 0
        self.confetti = []
        self.stars = 0
        self.start_ticks = pygame.time.get_ticks()
        self.end_seconds = 0
        self.loaded_elapsed = 0
        self.time_limit = self.get_time_limit()
        self.lost_by_time = False
        self.hint_piece = None
        self.hint_until_ticks = 0
        self.hint_message = ""
        self.hint_level = 0
        self.last_hint_index = None
        self.selected_group = []
        self.group_offsets = []
        self.error_message = error_message or ""

    def elapsed_seconds(self):
        if self.is_victory:
            return self.end_seconds
        return self.loaded_elapsed + (pygame.time.get_ticks() - self.start_ticks) // 1000 + self.hint_penalty_seconds

    def get_time_limit(self):
        if self.mode != "timed":
            return None
        return max(45, self.rows * self.cols * 8)

    def mode_allows_hints(self):
        return self.mode not in ("no_hints", "hardcore")

    def mode_allows_rotation(self):
        return self.mode not in ("kids",)

    def mode_shows_grid(self):
        return self.mode != "hardcore"

    def save_settings(self):
        self.settings.update({
            "theme": self.theme_key,
            "volume": self.sound.volume,
            "music": self.sound.music_enabled,
            "rotate_key": self.rotate_key,
            "hint_key": self.hint_key,
            "right_click_rotate": self.right_click_rotate,
            "nickname": self.nickname or "Игрок",
        })
        save_settings_dict(self.settings)

    def save_current_game(self):
        pieces = []
        for piece in self.all_pieces:
            loc = "box"
            if piece in self.active_pieces:
                loc = "active"
            pieces.append({
                "index": piece.index,
                "x": piece.get_origin_pos()[0],
                "y": piece.get_origin_pos()[1],
                "rotation": piece.rotation,
                "locked": piece.is_locked,
                "loc": loc,
                "group": piece.group_id,
            })
        ok = save_game_data({
            "rows": self.rows, "cols": self.cols, "mode": self.mode,
            "image": self.current_image_path, "seed": self.puzzle_seed,
            "elapsed": self.elapsed_seconds(), "moves": self.moves,
            "hints": self.hints_used, "penalty": self.hint_penalty_seconds,
            "nickname": self.nickname, "pieces": pieces,
        })
        self.hint_message = "Игра сохранена" if ok else "Не удалось сохранить игру"
        self.hint_until_ticks = pygame.time.get_ticks() + 1800
        if ok:
            self.notify_achievement("saved_game")

    def load_saved_game(self):
        data = load_game_data()
        if not data:
            self.error_message = "Сохранение не найдено"
            return False
        self.rows = int(data.get("rows", 4)); self.cols = int(data.get("cols", self.rows))
        self.mode = data.get("mode", "normal")
        self.current_image_path = data.get("image")
        self.puzzle_seed = int(data.get("seed", random.randint(1, 999999999)))
        self.state = "PUZZLE"; self.popup = None
        self.new_puzzle(self.rows, self.cols, image_path_marker=self.current_image_path, keep_seed=True)
        self.loaded_elapsed = int(data.get("elapsed", 0))
        self.moves = int(data.get("moves", 0))
        self.hints_used = int(data.get("hints", 0))
        self.hint_penalty_seconds = int(data.get("penalty", 0))
        by_index = {p.index: p for p in self.all_pieces}
        self.active_pieces = []
        self.box_pieces = []
        for st in data.get("pieces", []):
            piece = by_index.get(st.get("index"))
            if not piece:
                continue
            piece.set_origin_pos((int(st.get("x", piece.correct_pos[0])), int(st.get("y", piece.correct_pos[1]))))
            piece.rotation = 0
            for _ in range((int(st.get("rotation", 0)) % 360) // 90):
                piece.rotate_clockwise()
            piece.is_locked = bool(st.get("locked", False))
            piece.group_id = int(st.get("group", piece.index))
            if st.get("loc") == "active" or piece.is_locked:
                self.active_pieces.append(piece)
            else:
                self.box_pieces.append(piece)
        missing = [p for p in self.all_pieces if p not in self.active_pieces and p not in self.box_pieces]
        self.box_pieces.extend(missing)
        self.slot_index = len(self.active_pieces)
        self.notify_achievement("saved_game")
        return True

    def cycle_mode(self):
        keys = [x[0] for x in MODES]
        self.mode = keys[(keys.index(self.mode) + 1) % len(keys)]

    def cycle_rotate_key(self):
        self.rotate_key = "T" if self.rotate_key == "R" else "R"
        self.save_settings()

    def cycle_hint_key(self):
        self.hint_key = "H" if self.hint_key == "SPACE" else "SPACE"
        self.save_settings()

    def key_matches(self, event, name):
        if name == "SPACE":
            return event.key == pygame.K_SPACE
        if name == "H":
            return event.key == pygame.K_h
        if name == "R":
            return event.key == pygame.K_r
        if name == "T":
            return event.key == pygame.K_t
        return False

    def group_for(self, piece):
        return [p for p in self.active_pieces if p.group_id == piece.group_id and not p.is_locked]

    def merge_groups_if_close(self, piece):
        if piece.rotation != 0:
            return
        px, py = piece.get_origin_pos()
        for other in self.active_pieces:
            if other is piece or other.rotation != 0:
                continue
            ox, oy = other.get_origin_pos()
            expected_dx = other.correct_pos[0] - piece.correct_pos[0]
            expected_dy = other.correct_pos[1] - piece.correct_pos[1]
            close_grid = abs((ox - px) - expected_dx) < 18 and abs((oy - py) - expected_dy) < 18
            neighbors = abs(other.row - piece.row) + abs(other.col - piece.col) == 1
            if close_grid and neighbors:
                old = other.group_id
                for p in self.active_pieces:
                    if p.group_id == old:
                        p.group_id = piece.group_id
                self.sound.play("lock")

    def auto_place_piece(self, piece):
        if not piece or piece.is_locked:
            return
        piece.rotation = 0
        piece.image = piece.base_image.copy()
        piece.rect = piece.image.get_rect()
        piece.mask = pygame.mask.from_surface(piece.image)
        piece.set_origin_pos(piece.correct_pos)
        piece.is_locked = True
        if piece not in self.active_pieces:
            self.active_pieces.append(piece)
        if piece in self.box_pieces:
            self.box_pieces.remove(piece)
        self.sound.play("lock")

    def next_theme(self):
        keys = list(THEMES.keys())
        self.theme_key = keys[(keys.index(self.theme_key) + 1) % len(keys)]
        self.save_settings()

    def next_difficulty(self):
        if self.rows == 3:
            self.new_puzzle(4, 4, reset_image=True)
        elif self.rows == 4:
            self.new_puzzle(6, 6, reset_image=True)
        else:
            self.new_puzzle(3, 3, reset_image=True)

    def place_close_button(self, rect):
        btn_close_popup.update(rect.right - 38, rect.top + 12, 26, 26)

    def set_volume_from_mouse(self, mx):
        if volume_slider_rect.width <= 0:
            return
        value = (mx - volume_slider_rect.left) / volume_slider_rect.width
        self.sound.set_volume(value)
        self.save_settings()

    def reveal_from_box(self, amount=1):
        for _ in range(amount):
            if not self.box_pieces or self.slot_index >= len(self.spawn_slots):
                break
            piece = self.box_pieces.pop()
            piece.set_origin_pos(self.spawn_slots[self.slot_index])
            if self.mode_allows_rotation():
                for _ in range(random.randint(0, 3)):
                    piece.rotate_clockwise()
            self.active_pieces.append(piece)
            self.slot_index += 1
        self.sound.play("pick")

    def notify_achievement(self, key):
        if unlock_achievement(key):
            self.achievement_toast = f"Достижение: {ACHIEVEMENTS[key]['title']}"
            self.achievement_toast_until = pygame.time.get_ticks() + 3500

    def calculate_stars(self):
        base = max(1, self.rows * self.cols)
        ideal_moves = base + max(4, base // 3)
        good_moves = base * 3
        ideal_time = {3: 45, 4: 110, 6: 260}.get(self.rows, base * 8)
        good_time = ideal_time * 2
        score = 3
        if self.end_seconds > ideal_time or self.moves > ideal_moves:
            score -= 1
        if self.end_seconds > good_time or self.moves > good_moves or self.hints_used >= 3:
            score -= 1
        if self.hints_used >= 5:
            score -= 1
        return max(1, score)

    def spawn_confetti(self):
        self.confetti = []
        colors = [self.theme["success"], self.theme["warning"], self.theme["accent"], self.theme["orange"], self.theme["danger"]]
        for _ in range(140):
            self.confetti.append({
                "x": random.randint(0, self.current_w),
                "y": random.randint(-self.current_h // 2, 0),
                "vx": random.uniform(-1.5, 1.5),
                "vy": random.uniform(2.0, 5.5),
                "size": random.randint(4, 9),
                "color": random.choice(colors),
                "rot": random.uniform(0, math.tau),
            })

    def draw_confetti(self):
        for c in self.confetti:
            rect = pygame.Rect(int(c["x"]), int(c["y"]), c["size"], c["size"] + 3)
            pygame.draw.rect(screen, c["color"], rect, border_radius=2)

    def show_piece_hint(self):
        if not self.mode_allows_hints():
            self.hint_piece = None
            self.hint_message = "В этом режиме подсказки отключены"
            self.hint_until_ticks = pygame.time.get_ticks() + 1800
            return
        target = self.selected_piece
        if not target:
            unlocked = [p for p in self.active_pieces if not p.is_locked]
            target = unlocked[-1] if unlocked else None
        if not target:
            self.hint_piece = None
            self.hint_message = "Сначала достань пазлик из коробки"
            self.hint_until_ticks = pygame.time.get_ticks() + 1800
            return
        if self.last_hint_index == target.index:
            self.hint_level = min(3, self.hint_level + 1)
        else:
            self.hint_level = 1
            self.last_hint_index = target.index
        penalty_mult = self.hint_level
        self.hints_used += 1
        self.hint_penalty_seconds += HINT_TIME_PENALTY * penalty_mult
        self.moves += HINT_MOVE_PENALTY * penalty_mult
        self.hint_piece = target
        messages = {
            1: "Подсказка 1: подсвечена зона",
            2: "Подсказка 2: показан силуэт",
            3: "Подсказка 3: пазлик поставлен автоматически",
        }
        self.hint_message = messages[self.hint_level]
        self.hint_until_ticks = pygame.time.get_ticks() + 3200
        if self.hint_level == 3:
            self.auto_place_piece(target)
            self.check_victory()

    def draw_piece_hint(self):
        if pygame.time.get_ticks() > self.hint_until_ticks:
            return
        t = self.theme
        if self.hint_piece and not self.hint_piece.is_locked:
            tx, ty = self.hint_piece.correct_pos
            target_rect = pygame.Rect(tx, ty, self.hint_piece.w, self.hint_piece.h)
            glow = pygame.Surface((target_rect.w + 28, target_rect.h + 28), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*t["success"], 70), glow.get_rect(), border_radius=12)
            pygame.draw.rect(glow, (*t["warning"], 180), glow.get_rect(), 4, border_radius=12)
            screen.blit(glow, (target_rect.x - 14, target_rect.y - 14))

            if self.hint_level >= 2:
                ghost = self.hint_piece.image.copy()
                ghost.set_alpha(105)
                screen.blit(ghost, (tx + self.hint_piece.offset_x, ty + self.hint_piece.offset_y))

            sx, sy = self.hint_piece.get_origin_pos()
            start = (sx + self.hint_piece.w // 2, sy + self.hint_piece.h // 2)
            end = (tx + self.hint_piece.w // 2, ty + self.hint_piece.h // 2)
            if self.hint_level >= 2 and abs(start[0] - end[0]) + abs(start[1] - end[1]) > 30:
                pygame.draw.line(screen, t["warning"], start, end, 4)
                angle = math.atan2(end[1] - start[1], end[0] - start[0])
                arrow_len = 14
                left = (end[0] - arrow_len * math.cos(angle - 0.55), end[1] - arrow_len * math.sin(angle - 0.55))
                right = (end[0] - arrow_len * math.cos(angle + 0.55), end[1] - arrow_len * math.sin(angle + 0.55))
                pygame.draw.polygon(screen, t["warning"], [end, left, right])

        if self.hint_message:
            label = self.font_btn.render(self.hint_message, True, t["text"])
            pad = 12
            box = label.get_rect(center=(self.current_w // 2, board_y + board_h + 24))
            bg = pygame.Rect(box.left - pad, box.top - 7, box.w + pad * 2, box.h + 14)
            pygame.draw.rect(screen, t["panel2"], bg, border_radius=8)
            pygame.draw.rect(screen, t["warning"], bg, 2, border_radius=8)
            screen.blit(label, box)

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

    def handle_events(self):
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                self.current_w, self.current_h = event.w, event.h
                update_layout_sizes(self.current_w, self.current_h)
                self.new_puzzle()

            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse_down(mx, my)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.right_click_rotate:
                self.rotate_selected_or_hovered(mx, my)

            if event.type == pygame.MOUSEMOTION and self.dragging_volume:
                self.set_volume_from_mouse(event.pos[0])

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.handle_mouse_up()

    def handle_keydown(self, event):
        if event.key == pygame.K_F11:
            self.is_fullscreen = not self.is_fullscreen
            self.current_w, self.current_h = (MONITOR_W, MONITOR_H) if self.is_fullscreen else (WINDOW_W, WINDOW_H)
            pygame.display.set_mode((self.current_w, self.current_h), pygame.FULLSCREEN if self.is_fullscreen else pygame.RESIZABLE)
            update_layout_sizes(self.current_w, self.current_h)
            self.new_puzzle()
            return

        if event.key == pygame.K_ESCAPE:
            if self.popup:
                self.popup = None
            elif self.state == "PUZZLE":
                self.state = "MENU"
            return

        if self.state == "PUZZLE" and not self.is_victory:
            if self.key_matches(event, self.hint_key):
                self.show_piece_hint()
                return
            if event.key == pygame.K_s:
                self.save_current_game(); return
            if event.key == pygame.K_l:
                self.load_saved_game(); return
            if self.key_matches(event, self.rotate_key):
                self.rotate_selected_or_hovered(*pygame.mouse.get_pos())
                return

        if self.state == "MENU" and self.input_active and not self.popup:
            if event.key == pygame.K_BACKSPACE:
                self.nickname = self.nickname[:-1]
            elif event.key == pygame.K_RETURN:
                self.input_active = False
                self.save_settings()
            elif event.unicode and len(self.nickname) < 15 and event.unicode.isprintable():
                self.nickname += event.unicode

    def rotate_selected_or_hovered(self, mx, my):
        if not self.mode_allows_rotation():
            return
        target = self.selected_piece
        if not target:
            for piece in reversed(self.active_pieces):
                if not piece.is_locked and piece.contains_point((mx, my)):
                    target = piece; break
        if target:
            target.rotate_clockwise()
            self.notify_achievement("rotator")
            self.sound.play("pick")

    def handle_mouse_down(self, mx, my):
        self.sound.play("click")
        if self.state == "MENU":
            self.handle_menu_click(mx, my)
        elif self.state == "PUZZLE":
            self.handle_puzzle_click(mx, my)

    def handle_menu_click(self, mx, my):
        if self.popup == "difficulty":
            rect = pygame.Rect(self.current_w // 2 - 150, self.current_h // 2 - 145, 300, 360)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my):
                self.popup = None
            elif btn_pop_easy.collidepoint(mx, my):
                self.start_game(3, 3)
            elif btn_pop_medium.collidepoint(mx, my):
                self.start_game(4, 4)
            elif btn_pop_hard.collidepoint(mx, my):
                self.start_game(6, 6)
            elif btn_custom_minus.collidepoint(mx, my):
                self.custom_size = max(2, self.custom_size - 1)
            elif btn_custom_plus.collidepoint(mx, my):
                self.custom_size = min(10, self.custom_size + 1)
            elif btn_custom_start.collidepoint(mx, my):
                self.notify_achievement("custom_size")
                self.start_game(self.custom_size, self.custom_size)
            elif btn_mode_toggle.collidepoint(mx, my):
                self.cycle_mode()
            elif btn_gallery_open.collidepoint(mx, my):
                self.popup = "gallery"
            elif not rect.collidepoint(mx, my):
                self.popup = None
            return

        if self.popup == "records":
            rect = pygame.Rect(self.current_w // 2 - 260, self.current_h // 2 - 190, 520, 380)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my) or not rect.collidepoint(mx, my):
                self.popup = None
            return

        if self.popup == "achievements":
            rect = pygame.Rect(self.current_w // 2 - 285, self.current_h // 2 - 205, 570, 410)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my) or not rect.collidepoint(mx, my):
                self.popup = None
            return

        if self.popup == "gallery":
            rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my):
                self.popup = "difficulty"
                return
            for r, path in gallery_rects:
                if r.collidepoint(mx, my):
                    self.current_image_path = path
                    self.start_game(self.rows, self.cols, image_path_marker=path)
                    return
            if not rect.collidepoint(mx, my):
                self.popup = "difficulty"
            return

        if self.popup == "settings":
            rect = pygame.Rect(self.current_w // 2 - 170, self.current_h // 2 - 165, 340, 360)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my):
                self.popup = None
            elif btn_music_toggle.collidepoint(mx, my):
                self.sound.toggle_music()
                self.save_settings()
            elif btn_theme_toggle.collidepoint(mx, my):
                self.next_theme()
            elif btn_controls_toggle.collidepoint(mx, my):
                self.cycle_rotate_key()
            elif btn_hint_key_toggle.collidepoint(mx, my):
                self.cycle_hint_key()
            elif btn_right_rotate_toggle.collidepoint(mx, my):
                self.right_click_rotate = not self.right_click_rotate; self.save_settings()
            elif volume_slider_rect.collidepoint(mx, my) or volume_knob_rect.collidepoint(mx, my):
                self.dragging_volume = True
                self.set_volume_from_mouse(mx)
            elif not rect.collidepoint(mx, my):
                self.popup = None
            return

        if input_nick_rect.collidepoint(mx, my):
            self.input_active = True
        elif btn_menu_play.collidepoint(mx, my):
            self.input_active = False
            self.popup = "difficulty"
        elif btn_menu_records.collidepoint(mx, my):
            self.input_active = False
            self.popup = "records"
        elif btn_menu_settings.collidepoint(mx, my):
            self.input_active = False
            self.popup = "settings"
        elif btn_menu_achievements.collidepoint(mx, my):
            self.input_active = False
            self.popup = "achievements"
        elif btn_continue.collidepoint(mx, my):
            self.input_active = False
            self.load_saved_game()
        else:
            self.input_active = False

    def start_game(self, rows, cols, image_path_marker=None):
        self.rows = rows
        self.cols = cols
        if image_path_marker is not None:
            self.current_image_path = image_path_marker
        else:
            self.current_image_path = None
        self.state = "PUZZLE"
        self.popup = None
        self.new_puzzle(rows, cols, image_path_marker=self.current_image_path, reset_image=(image_path_marker is None))

    def handle_puzzle_click(self, mx, my):
        hover_choose = btn_choose.collidepoint(mx, my)
        hover_easy = btn_easy.collidepoint(mx, my)
        hover_medium = btn_medium.collidepoint(mx, my)
        hover_hard = btn_hard.collidepoint(mx, my)
        hover_box = btn_box.collidepoint(mx, my)
        hover_box_5 = btn_box_5.collidepoint(mx, my)
        hover_preview = btn_preview.collidepoint(mx, my)
        hover_back = btn_back_to_menu.collidepoint(mx, my)
        hover_restart = btn_restart.collidepoint(mx, my)
        hover_save = btn_save_game.collidepoint(mx, my)
        hover_load = btn_load_game.collidepoint(mx, my)

        if self.is_victory or self.lost_by_time:
            if btn_victory_again.collidepoint(mx, my):
                self.new_puzzle()
            elif btn_victory_menu.collidepoint(mx, my):
                self.state = "MENU"
            elif btn_victory_next.collidepoint(mx, my):
                if self.lost_by_time:
                    self.mode = "normal"; self.new_puzzle()
                else:
                    self.next_difficulty()
            return

        if hover_preview:
            self.show_piece_hint()
            return
        if hover_back:
            self.state = "MENU"
            return
        if hover_restart:
            self.new_puzzle()
            return
        if hover_save:
            self.save_current_game()
            return
        if hover_load:
            self.load_saved_game()
            return
        if hover_choose:
            path = open_file_dialog()
            if path:
                self.new_puzzle(image_path_marker=path)
            return
        if hover_easy:
            self.new_puzzle(3, 3, reset_image=True)
            return
        if hover_medium:
            self.new_puzzle(4, 4, reset_image=True)
            return
        if hover_hard:
            self.new_puzzle(6, 6, reset_image=True)
            return
        if hover_box_5 and self.box_pieces:
            self.reveal_from_box(5)
            return
        if hover_box and self.box_pieces:
            self.reveal_from_box(1)
            return

        for piece in reversed(self.active_pieces):
            if not piece.is_locked and piece.contains_point((mx, my)):
                self.selected_piece = piece
                self.selected_group = self.group_for(piece) or [piece]
                self.group_offsets = [(gp, gp.rect.x - mx, gp.rect.y - my) for gp in self.selected_group]
                self.offset_x = piece.rect.x - mx
                self.offset_y = piece.rect.y - my
                for gp in self.selected_group:
                    if gp in self.active_pieces:
                        self.active_pieces.remove(gp); self.active_pieces.append(gp)
                self.sound.play("pick")
                break

    def handle_mouse_up(self):
        self.dragging_volume = False
        if self.state != "PUZZLE" or not self.selected_piece:
            return

        self.moves += 1
        moved_group = self.selected_group or [self.selected_piece]
        for piece in moved_group:
            cx, cy = piece.get_origin_pos()
            tx, ty = piece.correct_pos
            if piece.rotation == 0 and math.hypot(tx - cx, ty - cy) < 25:
                piece.set_origin_pos((tx, ty))
                piece.is_locked = True
                self.sound.play("lock")
            else:
                self.merge_groups_if_close(piece)
        self.selected_piece = None
        self.selected_group = []
        self.group_offsets = []
        self.check_victory()

    def check_victory(self):
        if self.all_pieces and all(piece.is_locked for piece in self.all_pieces) and not self.is_victory:
            self.end_seconds = self.elapsed_seconds()
            self.is_victory = True
            self.stars = self.calculate_stars()
            self.spawn_confetti()
            if not self.victory_saved:
                add_record(self.nickname, self.rows, self.cols, self.end_seconds, self.moves, self.stars, self.hints_used)
                self.victory_saved = True
            self.notify_achievement("first_win")
            if self.hints_used == 0:
                self.notify_achievement("no_hint")
            if self.rows == 3 and self.end_seconds <= 45:
                self.notify_achievement("speed_3x3")
            if self.rows == 6:
                self.notify_achievement("master_6x6")
            if self.stars == 3:
                self.notify_achievement("three_stars")
            if self.mode == "hardcore":
                self.notify_achievement("hardcore_win")
            self.sound.play("win")

    def update(self):
        mx, my = pygame.mouse.get_pos()
        if self.state == "PUZZLE" and self.selected_piece:
            if self.selected_group and self.group_offsets:
                for gp, ox, oy in self.group_offsets:
                    gp.rect.x = mx + ox
                    gp.rect.y = my + oy
            else:
                self.selected_piece.rect.x = mx + self.offset_x
                self.selected_piece.rect.y = my + self.offset_y
        if self.state == "PUZZLE" and self.mode == "timed" and not self.is_victory and self.time_limit is not None:
            if self.elapsed_seconds() >= self.time_limit:
                self.lost_by_time = True

        for c in self.confetti:
            c["x"] += c["vx"]
            c["y"] += c["vy"]
            c["rot"] += 0.08
            if c["y"] > self.current_h + 20:
                c["y"] = random.randint(-120, -20)
                c["x"] = random.randint(0, self.current_w)

        for p in self.bg_pieces:
            p["y"] += p["speed"]
            p["x"] += math.sin(p["phase"] + pygame.time.get_ticks() / 700) * 0.12
            if p["y"] > self.current_h + 40:
                p["y"] = -40
                p["x"] = random.randint(0, self.current_w)

    def draw(self):
        t = self.theme
        screen.fill(t["bg"])
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "PUZZLE":
            self.draw_puzzle()
        self.draw_achievement_toast()

    def draw_achievement_toast(self):
        if not self.achievement_toast or pygame.time.get_ticks() > self.achievement_toast_until:
            return
        t = self.theme
        label = self.font_btn.render(self.achievement_toast, True, t["text"])
        rect = pygame.Rect(self.current_w - label.get_width() - 42, self.current_h - 74, label.get_width() + 26, 42)
        pygame.draw.rect(screen, t["panel2"], rect, border_radius=10)
        pygame.draw.rect(screen, t["success"], rect, 2, border_radius=10)
        screen.blit(label, label.get_rect(center=rect.center))

    def draw_background_animation(self):
        t = self.theme
        for c in self.confetti:
            c["x"] += c["vx"]
            c["y"] += c["vy"]
            c["rot"] += 0.08
            if c["y"] > self.current_h + 20:
                c["y"] = random.randint(-120, -20)
                c["x"] = random.randint(0, self.current_w)

        for p in self.bg_pieces:
            size = p["size"]
            rect = pygame.Rect(int(p["x"]), int(p["y"]), size, size)
            pygame.draw.rect(screen, (*t["border"], 60), rect, border_radius=5)
            pygame.draw.circle(screen, (*t["accent"], 45), rect.center, max(4, size // 4))

    def draw_menu(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        self.draw_background_animation()

        title = self.font_big.render("ФИГУРНЫЙ ПАЗЛ ", True, t["text"])
        screen.blit(title, title.get_rect(centerx=self.current_w // 2, centery=self.current_h // 2 - 185))
        subtitle = self.font_btn.render("Собирай, ставь рекорды и загружай свои картинки", True, t["warning"])
        screen.blit(subtitle, subtitle.get_rect(centerx=self.current_w // 2, centery=self.current_h // 2 - 145))

        pygame.draw.rect(screen, t["panel"], input_nick_rect, border_radius=6)
        pygame.draw.rect(screen, t["success"] if self.input_active else t["border"], input_nick_rect, 2, border_radius=6)
        nick_text = f"Ник: {self.nickname}" if self.nickname else "Введите ваш ник..."
        draw_text_center(nick_text, self.font_btn, t["text"], screen, input_nick_rect.centerx, input_nick_rect.centery)

        draw_button(screen, btn_menu_play, "ИГРАТЬ", pygame.font.SysFont("Arial", 22, bold=True), t["accent"], t["text"], btn_menu_play.collidepoint(mx, my))
        draw_button(screen, btn_menu_records, "Рекорды", self.font_btn, t["orange"], t["text"], btn_menu_records.collidepoint(mx, my))
        draw_button(screen, btn_menu_settings, "Настройки", self.font_btn, t["border"], t["text"], btn_menu_settings.collidepoint(mx, my))
        draw_button(screen, btn_menu_achievements, "Достижения", self.font_btn, t["success"], t["text"], btn_menu_achievements.collidepoint(mx, my))
        draw_button(screen, btn_continue, "Продолжить сохранение", self.font_btn, t["warning"], t["text"], btn_continue.collidepoint(mx, my), t["border"])

        hint = self.font_small.render("F11 — полноэкранный режим | ESC — назад", True, t["border"])
        screen.blit(hint, hint.get_rect(centerx=self.current_w // 2, bottom=self.current_h - 18))

        if self.popup == "difficulty":
            self.draw_difficulty_popup()
        elif self.popup == "records":
            self.draw_records_popup()
        elif self.popup == "settings":
            self.draw_settings_popup()
        elif self.popup == "achievements":
            self.draw_achievements_popup()
        elif self.popup == "gallery":
            self.draw_gallery_popup()

    def draw_popup_base(self, rect, title):
        self.place_close_button(rect)
        t = self.theme
        overlay = pygame.Surface((self.current_w, self.current_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, t["panel2"], rect, border_radius=10)
        pygame.draw.rect(screen, t["warning"], rect, 2, border_radius=10)
        draw_text_center(title, self.font_btn, t["warning"], screen, rect.centerx, rect.top + 28)
        draw_button(screen, btn_close_popup, "×", self.font_btn, t["danger"], t["text"], btn_close_popup.collidepoint(pygame.mouse.get_pos()))

    def draw_difficulty_popup(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 150, self.current_h // 2 - 145, 300, 360)
        self.draw_popup_base(rect, "НОВАЯ ИГРА")
        info = self.font_small.render(f"Режим: {mode_title(self.mode)}", True, t["text"])
        screen.blit(info, info.get_rect(centerx=rect.centerx, top=rect.top + 48))
        draw_button(screen, btn_pop_easy, "Лёгкий (3x3)", self.font_btn, (39, 174, 96), t["text"], btn_pop_easy.collidepoint(mx, my))
        draw_button(screen, btn_pop_medium, "Средний (4x4)", self.font_btn, (52, 152, 219), t["text"], btn_pop_medium.collidepoint(mx, my))
        draw_button(screen, btn_pop_hard, "Сложный (6x6)", self.font_btn, (142, 68, 173), t["text"], btn_pop_hard.collidepoint(mx, my))
        draw_button(screen, btn_custom_minus, "−", self.font_btn, t["danger"], t["text"], btn_custom_minus.collidepoint(mx, my))
        draw_button(screen, btn_custom_start, f"Своя {self.custom_size}x{self.custom_size}", self.font_btn, t["success"], t["text"], btn_custom_start.collidepoint(mx, my))
        draw_button(screen, btn_custom_plus, "+", self.font_btn, t["accent"], t["text"], btn_custom_plus.collidepoint(mx, my))
        draw_button(screen, btn_mode_toggle, f"Сменить режим: {mode_title(self.mode)}", self.font_btn, t["orange"], t["text"], btn_mode_toggle.collidepoint(mx, my))
        draw_button(screen, btn_gallery_open, "Галерея картинок", self.font_btn, t["border"], t["text"], btn_gallery_open.collidepoint(mx, my))
        notes = {
            "normal": "Классический режим с подсказками.",
            "timed": "Собери до окончания таймера.",
            "no_hints": "Подсказки отключены.",
            "kids": "Без поворотов, проще играть.",
            "hardcore": "Нет сетки и подсказок.",
        }
        note = self.font_small.render(notes.get(self.mode, ""), True, t["border"])
        screen.blit(note, note.get_rect(centerx=rect.centerx, bottom=rect.bottom - 18))

    def draw_gallery_popup(self):
        global gallery_rects
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
        self.draw_popup_base(rect, "ГАЛЕРЕЯ КАРТИНОК")
        images = list_gallery_images()
        gallery_rects = []
        if not images:
            draw_text_center("Добавь картинки в папку images/custom", self.font_btn, t["text"], screen, rect.centerx, rect.centery)
            return
        x0, y0 = rect.left + 28, rect.top + 64
        card_w, card_h = 140, 96
        for i, path in enumerate(images[:12]):
            x = x0 + (i % 4) * 155
            y = y0 + (i // 4) * 120
            card = pygame.Rect(x, y, card_w, card_h)
            gallery_rects.append((card, path))
            pygame.draw.rect(screen, t["panel"], card, border_radius=8)
            pygame.draw.rect(screen, t["success"] if card.collidepoint(mx, my) else t["border"], card, 2, border_radius=8)
            try:
                img = pygame.image.load(path).convert_alpha()
                thumb = pygame.transform.smoothscale(img, (card_w - 12, card_h - 30))
                screen.blit(thumb, (card.left + 6, card.top + 6))
            except Exception:
                pygame.draw.rect(screen, t["danger"], (card.left + 6, card.top + 6, card_w - 12, card_h - 30), border_radius=5)
            name = os.path.basename(path)[:18]
            label = self.font_small.render(name, True, t["text"])
            screen.blit(label, label.get_rect(centerx=card.centerx, bottom=card.bottom - 5))
        text = self.font_small.render("Клик по картинке запускает игру. Свои файлы клади в images/custom", True, t["border"])
        screen.blit(text, text.get_rect(centerx=rect.centerx, bottom=rect.bottom - 18))

    def draw_records_popup(self):
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 260, self.current_h // 2 - 190, 520, 380)
        self.draw_popup_base(rect, "ЛУЧШИЕ РЕЗУЛЬТАТЫ")
        records = best_records_for(self.rows, self.cols, 8)
        diff_text = self.font_btn.render(f"Текущая сложность: {difficulty_name(self.rows, self.cols)}", True, t["text"])
        screen.blit(diff_text, (rect.left + 28, rect.top + 58))
        if not records:
            draw_text_center("Пока нет рекордов. Сыграй первую партию!", self.font_btn, t["text"], screen, rect.centerx, rect.centery)
            return
        y = rect.top + 95
        headers = ["#", "Игрок", "Время", "Ходы", "★", "Подс."]
        xs = [rect.left + 30, rect.left + 70, rect.left + 210, rect.left + 295, rect.left + 360, rect.left + 410]
        for x, h in zip(xs, headers):
            screen.blit(self.font_small.render(h, True, t["warning"]), (x, y))
        y += 28
        for i, r in enumerate(records, 1):
            values = [str(i), str(r.get("nickname", "Игрок"))[:12], format_time(r.get("time", 0)), str(r.get("moves", 0)), "★" * int(r.get("stars", 0)), str(r.get("hints", 0))]
            for x, value in zip(xs, values):
                screen.blit(self.font_small.render(value, True, t["text"]), (x, y))
            y += 28

    def draw_achievements_popup(self):
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 285, self.current_h // 2 - 205, 570, 410)
        self.draw_popup_base(rect, "ДОСТИЖЕНИЯ")
        unlocked = load_achievements()
        y = rect.top + 62
        for key, info in ACHIEVEMENTS.items():
            got = bool(unlocked.get(key))
            badge_rect = pygame.Rect(rect.left + 26, y, rect.width - 52, 48)
            pygame.draw.rect(screen, t["panel"] if got else t["bg"], badge_rect, border_radius=8)
            pygame.draw.rect(screen, t["success"] if got else t["border"], badge_rect, 2, border_radius=8)
            icon = "✓" if got else "?"
            screen.blit(self.font_win.render(icon, True, t["success"] if got else t["border"]), (badge_rect.left + 14, badge_rect.top + 9))
            screen.blit(self.font_btn.render(info["title"], True, t["text"]), (badge_rect.left + 48, badge_rect.top + 6))
            desc = info["desc"] if not got else f"{info['desc']}  Получено: {unlocked.get(key)}"
            screen.blit(self.font_small.render(desc, True, t["border"]), (badge_rect.left + 48, badge_rect.top + 28))
            y += 56

    def draw_settings_popup(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 170, self.current_h // 2 - 165, 340, 360)
        self.draw_popup_base(rect, "НАСТРОЙКИ")
        music_label = "Музыка: Вкл" if self.sound.music_enabled else "Музыка: Выкл"
        draw_button(screen, btn_music_toggle, music_label, self.font_btn, t["accent"], t["text"], btn_music_toggle.collidepoint(mx, my))
        draw_button(screen, btn_theme_toggle, f"Тема: {t['name']}", self.font_btn, t["orange"], t["text"], btn_theme_toggle.collidepoint(mx, my))
        draw_button(screen, btn_controls_toggle, f"Поворот: клавиша {self.rotate_key}", self.font_btn, t["border"], t["text"], btn_controls_toggle.collidepoint(mx, my))
        draw_button(screen, btn_hint_key_toggle, f"Подсказка: {self.hint_key}", self.font_small, t["accent"], t["text"], btn_hint_key_toggle.collidepoint(mx, my))
        right_text = "ПКМ: поворот" if self.right_click_rotate else "ПКМ: выкл"
        draw_button(screen, btn_right_rotate_toggle, right_text, self.font_small, t["success"], t["text"], btn_right_rotate_toggle.collidepoint(mx, my))

        volume_title = self.font_btn.render(f"Громкость звуков: {int(self.sound.volume * 100)}%", True, t["text"])
        screen.blit(volume_title, volume_title.get_rect(centerx=rect.centerx, top=rect.top + 152))
        pygame.draw.rect(screen, t["border"], volume_slider_rect, border_radius=4)
        filled = pygame.Rect(volume_slider_rect.left, volume_slider_rect.top, int(volume_slider_rect.width * self.sound.volume), volume_slider_rect.height)
        pygame.draw.rect(screen, t["success"], filled, border_radius=4)
        knob_x = volume_slider_rect.left + int(volume_slider_rect.width * self.sound.volume)
        volume_knob_rect.update(knob_x - 9, volume_slider_rect.centery - 9, 18, 18)
        pygame.draw.circle(screen, t["warning"], volume_knob_rect.center, 10)
        pygame.draw.circle(screen, t["text"], volume_knob_rect.center, 10, 2)

        lines = [
            "S — сохранить игру, L — загрузить",
            "Музыка: sounds/menu_music.mp3/ogg/wav",
            "Настройки сохраняются в settings.json",
        ]
        for i, text in enumerate(lines):
            label = self.font_small.render(text, True, t["border"])
            screen.blit(label, label.get_rect(centerx=rect.centerx, top=rect.top + 205 + i * 20))

    def draw_puzzle(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        pygame.draw.rect(screen, t["panel"], (board_x, board_y, board_w, board_h), border_radius=2)
        pygame.draw.rect(screen, t["border"], (board_x, board_y, board_w, board_h), 2)

        p_w, p_h = board_w // self.cols, board_h // self.rows
        if self.mode_shows_grid():
            for r in range(self.rows):
                for c in range(self.cols):
                    cell_rect = pygame.Rect(board_x + c * p_w, board_y + r * p_h, p_w, p_h)
                    pygame.draw.rect(screen, t["grid"], cell_rect, 1)

        self.draw_piece_hint()

        self.draw_hud()
        self.draw_mini_preview()
        self.draw_box()

        for piece in self.active_pieces:
            screen.blit(piece.image, piece.rect)

        self.draw_bottom_buttons()

        if self.error_message:
            msg = self.font_small.render(self.error_message[:90], True, t["danger"])
            screen.blit(msg, msg.get_rect(centerx=self.current_w // 2, top=board_y + board_h + 8))

        if self.lost_by_time:
            self.draw_time_lost_popup()
        if self.is_victory:
            self.draw_victory_popup()

    def draw_hud(self):
        t = self.theme
        panel = pygame.Rect(20, 20, 225, 154)
        pygame.draw.rect(screen, t["panel"], panel, border_radius=8)
        pygame.draw.rect(screen, t["border"], panel, 2, border_radius=8)
        items = [
            f"Игрок: {self.nickname or 'Игрок'}",
            f"Время: {format_time(self.elapsed_seconds())}",
            f"Ходы: {self.moves}",
            f"Сложность: {self.rows}x{self.cols}",
            f"Режим: {mode_title(self.mode)}",
            f"Подсказки: {self.hints_used} (+{self.hint_penalty_seconds} сек)",
            f"{self.rotate_key}/ПКМ — повернуть",
        ]
        for i, text in enumerate(items):
            screen.blit(self.font_small.render(text, True, t["text"]), (panel.left + 12, panel.top + 9 + i * 18))
        if self.time_limit is not None:
            left = max(0, self.time_limit - self.elapsed_seconds())
            screen.blit(self.font_small.render(f"Осталось: {format_time(left)}", True, t["danger"] if left <= 10 else t["warning"]), (panel.left + 12, panel.top + 9 + len(items) * 18))

    def draw_mini_preview(self):
        if not self.current_board_img or self.mode == "hardcore":
            return
        t = self.theme
        preview_w, preview_h = 160, 120
        x = self.current_w - preview_w - 20
        y = 20
        if x < board_x + board_w + 10:
            y = board_y + board_h + 14
            x = self.current_w - preview_w - 20
        if x < 20:
            return
        preview = pygame.transform.smoothscale(self.current_board_img, (preview_w, preview_h))
        screen.blit(preview, (x, y))
        pygame.draw.rect(screen, t["warning"], (x, y, preview_w, preview_h), 2)
        label = self.font_small.render("Мини-превью", True, t["text"])
        screen.blit(label, label.get_rect(centerx=x + preview_w // 2, top=y + preview_h + 4))

    def draw_box(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        hovered = btn_box.collidepoint(mx, my)
        draw_button(screen, btn_box_5, "Достать 5", self.font_btn, t["accent"], t["text"], btn_box_5.collidepoint(mx, my))

        shadow = btn_box.move(5, 6)
        pygame.draw.rect(screen, (0, 0, 0, 70), shadow, border_radius=14)

        body_color = (151, 84, 36) if not hovered else (176, 98, 42)
        lid_color = (190, 119, 55) if not hovered else (210, 135, 66)
        dark_wood = (91, 48, 18)
        pygame.draw.rect(screen, body_color, btn_box, border_radius=14)
        pygame.draw.rect(screen, dark_wood, btn_box, 3, border_radius=14)

        lid = pygame.Rect(btn_box.left - 6, btn_box.top - 9, btn_box.width + 12, 28)
        pygame.draw.rect(screen, lid_color, lid, border_radius=10)
        pygame.draw.rect(screen, dark_wood, lid, 3, border_radius=10)
        pygame.draw.line(screen, (238, 174, 94), (btn_box.left + 12, btn_box.top + 29), (btn_box.right - 12, btn_box.top + 29), 2)

        # Маленькие цветные пазлики внутри коробки.
        random.seed(len(self.box_pieces) + self.rows * 100 + self.cols)
        for i in range(min(8, max(0, len(self.box_pieces)))):
            px = btn_box.left + 15 + (i % 4) * 30 + random.randint(-3, 3)
            py = btn_box.top + 34 + (i // 4) * 23 + random.randint(-2, 2)
            color = [(52, 152, 219), (46, 204, 113), (241, 196, 15), (231, 76, 60), (155, 89, 182)][i % 5]
            piece_rect = pygame.Rect(px, py, 24, 18)
            pygame.draw.rect(screen, color, piece_rect, border_radius=5)
            pygame.draw.circle(screen, color, (piece_rect.centerx, piece_rect.top), 5)
            pygame.draw.circle(screen, dark_wood, (piece_rect.left, piece_rect.centery), 4)
            pygame.draw.rect(screen, (25, 25, 25), piece_rect, 1, border_radius=5)

        pygame.draw.rect(screen, (0, 0, 0, 50), (btn_box.left + 9, btn_box.bottom - 35, btn_box.width - 18, 28), border_radius=8)
        title = self.font_box.render("КОРОБКА", True, (255, 232, 185))
        count = self.font_small.render(f"{len(self.box_pieces)} деталей", True, t["text"])
        hint = self.font_small.render("клик — достать", True, t["warning"])
        screen.blit(title, title.get_rect(centerx=btn_box.centerx, top=btn_box.top + 6))
        screen.blit(count, count.get_rect(centerx=btn_box.centerx, bottom=btn_box.bottom - 18))
        screen.blit(hint, hint.get_rect(centerx=btn_box.centerx, bottom=btn_box.bottom - 3))

    def draw_bottom_buttons(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        buttons = [
            (btn_choose, "Открыть картинку", t["accent"], btn_choose.collidepoint(mx, my)),
            (btn_easy, "Лёгкий", t["success"] if self.rows == 3 else t["border"], btn_easy.collidepoint(mx, my)),
            (btn_medium, "Средний", t["success"] if self.rows == 4 else t["border"], btn_medium.collidepoint(mx, my)),
            (btn_hard, "Сложный", t["success"] if self.rows == 6 else t["border"], btn_hard.collidepoint(mx, my)),
            (btn_preview, "Подсказка" if self.mode_allows_hints() else "Без подсказок", t["orange"], btn_preview.collidepoint(mx, my) or pygame.time.get_ticks() <= self.hint_until_ticks),
            (btn_back_to_menu, "Меню", t["danger"], btn_back_to_menu.collidepoint(mx, my)),
            (btn_restart, "Заново", t["warning"], btn_restart.collidepoint(mx, my)),
            (btn_save_game, "Сохранить", t["success"], btn_save_game.collidepoint(mx, my)),
            (btn_load_game, "Загрузить", t["border"], btn_load_game.collidepoint(mx, my)),
        ]
        for rect, text, color, hover in buttons:
            draw_button(screen, rect, text, self.font_btn, color, t["text"], hover)

    def draw_time_lost_popup(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        overlay = pygame.Surface((self.current_w, self.current_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        screen.blit(overlay, (0, 0))
        rect = pygame.Rect(self.current_w // 2 - 210, self.current_h // 2 - 100, 420, 200)
        pygame.draw.rect(screen, t["panel2"], rect, border_radius=14)
        pygame.draw.rect(screen, t["danger"], rect, 3, border_radius=14)
        draw_text_center("ВРЕМЯ ВЫШЛО", self.font_title, t["danger"], screen, rect.centerx, rect.top + 48)
        draw_text_center("Попробуй ещё раз или смени режим", self.font_btn, t["text"], screen, rect.centerx, rect.top + 92)
        draw_button(screen, btn_victory_again, "Ещё раз", self.font_btn, t["accent"], t["text"], btn_victory_again.collidepoint(mx, my))
        draw_button(screen, btn_victory_menu, "Меню", self.font_btn, t["danger"], t["text"], btn_victory_menu.collidepoint(mx, my))
        draw_button(screen, btn_victory_next, "Обычный", self.font_btn, t["success"], t["text"], btn_victory_next.collidepoint(mx, my))

    def draw_victory_popup(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        self.draw_confetti()
        overlay = pygame.Surface((self.current_w, self.current_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        screen.blit(overlay, (0, 0))
        rect = pygame.Rect(self.current_w // 2 - 230, self.current_h // 2 - 125, 460, 250)
        pygame.draw.rect(screen, t["panel2"], rect, border_radius=14)
        pygame.draw.rect(screen, t["success"], rect, 3, border_radius=14)
        draw_text_center("ПОБЕДА!", self.font_title, t["success"], screen, rect.centerx, rect.top + 45)
        draw_text_center(f"{self.nickname or 'Игрок'}, пазл собран!", self.font_win, t["text"], screen, rect.centerx, rect.top + 88)    
        draw_text_center("Оценка: " + "★" * self.stars + "☆" * (3 - self.stars), self.font_win, t["warning"], screen, rect.centerx, rect.top + 118)
        draw_text_center(f"Время: {format_time(self.end_seconds)}   Ходы: {self.moves}   Подсказки: {self.hints_used}", self.font_btn, t["text"], screen, rect.centerx, rect.top + 148)
        draw_button(screen, btn_victory_again, "Ещё раз", self.font_btn, t["accent"], t["text"], btn_victory_again.collidepoint(mx, my))
        draw_button(screen, btn_victory_menu, "Меню", self.font_btn, t["danger"], t["text"], btn_victory_menu.collidepoint(mx, my))
        draw_button(screen, btn_victory_next, "Следующая", self.font_btn, t["success"], t["text"], btn_victory_next.collidepoint(mx, my))
        hint = self.font_small.render("Результат сохранён в records.json", True, t["border"])
        screen.blit(hint, hint.get_rect(centerx=rect.centerx, bottom=rect.bottom - 18))




# =========================================================
# ДОПОЛНЕНИЕ: CAMPAIGN EDITION
# =========================================================
# Эта секция расширяет Mega-версию, не ломая старые сохранения.
PROFILES_FILE = "profiles.json"
STATS_FILE = "stats.json"
ECONOMY_FILE = "economy.json"
CAMPAIGN_FILE = "campaign.json"
DAILY_FILE = "daily.json"

THEMES.update({
    "wood": {"name": "Деревянный стол", "bg": (96, 58, 31), "panel": (128, 82, 45), "panel2": (110, 68, 38), "grid": (153, 101, 57), "border": (77, 43, 22), "text": (255, 242, 214), "accent": (59, 130, 246), "success": (34, 197, 94), "warning": (245, 158, 11), "danger": (239, 68, 68), "orange": (217, 119, 6)},
    "space": {"name": "Космос", "bg": (5, 8, 22), "panel": (17, 24, 39), "panel2": (30, 41, 59), "grid": (51, 65, 85), "border": (99, 102, 241), "text": (226, 232, 240), "accent": (56, 189, 248), "success": (45, 212, 191), "warning": (250, 204, 21), "danger": (248, 113, 113), "orange": (251, 146, 60)},
    "winter": {"name": "Зима", "bg": (219, 234, 254), "panel": (239, 246, 255), "panel2": (224, 242, 254), "grid": (186, 230, 253), "border": (14, 165, 233), "text": (12, 74, 110), "accent": (37, 99, 235), "success": (5, 150, 105), "warning": (202, 138, 4), "danger": (220, 38, 38), "orange": (234, 88, 12)},
    "pixel": {"name": "Пиксель", "bg": (24, 24, 27), "panel": (39, 39, 42), "panel2": (63, 63, 70), "grid": (82, 82, 91), "border": (250, 204, 21), "text": (250, 250, 250), "accent": (168, 85, 247), "success": (34, 197, 94), "warning": (250, 204, 21), "danger": (239, 68, 68), "orange": (251, 146, 60)},
})
SHOP_THEMES = {"wood": 120, "space": 180, "winter": 150, "pixel": 220}
FREE_THEMES = ["dark", "light", "neon"]

EXTRA_ACHIEVEMENTS = {
    "campaign_1": {"title": "Первый уровень", "desc": "Пройди первый уровень кампании."},
    "daily_done": {"title": "Пазл дня", "desc": "Собери ежедневный пазл."},
    "rich": {"title": "Копилка", "desc": "Накопи 500 монет."},
    "buyer": {"title": "Покупатель", "desc": "Купи тему в магазине."},
    "sorter": {"title": "Сортировщик", "desc": "Используй сортировку деталей."},
    "tray_user": {"title": "Лоточник", "desc": "Используй лоток для деталей."},
    "profile_master": {"title": "Профили", "desc": "Создай или выбери профиль игрока."},
    "hard_option": {"title": "Экспериментатор", "desc": "Запусти пазл с дополнительной опцией сложности."},
}
ACHIEVEMENTS.update(EXTRA_ACHIEVEMENTS)

btn_campaign = pygame.Rect(0,0,1,1)
btn_daily = pygame.Rect(0,0,1,1)
btn_shop = pygame.Rect(0,0,1,1)
btn_profiles = pygame.Rect(0,0,1,1)
btn_stats = pygame.Rect(0,0,1,1)
btn_extra_modes = pygame.Rect(0,0,1,1)
btn_no_picture = pygame.Rect(0,0,1,1)
btn_mirror = pygame.Rect(0,0,1,1)
btn_false_pieces = pygame.Rect(0,0,1,1)
btn_silhouette = pygame.Rect(0,0,1,1)
btn_import_folder = pygame.Rect(0,0,1,1)
btn_sort_all = pygame.Rect(0,0,1,1)
btn_sort_corners = pygame.Rect(0,0,1,1)
btn_sort_edges = pygame.Rect(0,0,1,1)
btn_sort_center = pygame.Rect(0,0,1,1)
btn_arrange = pygame.Rect(0,0,1,1)
tray_rects = [pygame.Rect(0,0,1,1), pygame.Rect(0,0,1,1), pygame.Rect(0,0,1,1)]
shop_rects = []
profile_rects = []
campaign_rects = []
btn_create_profile = pygame.Rect(0,0,1,1)
btn_fps_toggle = pygame.Rect(0,0,1,1)
btn_anim_toggle = pygame.Rect(0,0,1,1)
btn_quality_toggle = pygame.Rect(0,0,1,1)
btn_self_test = pygame.Rect(0,0,1,1)

CAMPAIGN_LEVELS = [
    {"name": "Старт", "rows": 2, "cols": 2, "mode": "kids", "coins": 35},
    {"name": "Первые шаги", "rows": 3, "cols": 3, "mode": "normal", "coins": 55},
    {"name": "Повороты", "rows": 4, "cols": 4, "mode": "normal", "coins": 75},
    {"name": "Гонка", "rows": 4, "cols": 4, "mode": "timed", "coins": 95},
    {"name": "Без помощи", "rows": 5, "cols": 5, "mode": "no_hints", "coins": 120},
    {"name": "Хардкор", "rows": 6, "cols": 6, "mode": "hardcore", "coins": 160},
]

def _load_json_file(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, type(default)) else default
    except (OSError, json.JSONDecodeError):
        return default

def _save_json_file(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False

def load_profiles():
    data = _load_json_file(PROFILES_FILE, {})
    if not data:
        data = {"Игрок": {"created": time.strftime("%Y-%m-%d %H:%M")}}
        _save_json_file(PROFILES_FILE, data)
    return data

def load_stats():
    return _load_json_file(STATS_FILE, {})

def save_stats(data):
    _save_json_file(STATS_FILE, data)

def load_economy():
    data = _load_json_file(ECONOMY_FILE, {"coins": 0, "unlocked_themes": FREE_THEMES[:]})
    data.setdefault("coins", 0)
    data.setdefault("unlocked_themes", FREE_THEMES[:])
    for k in FREE_THEMES:
        if k not in data["unlocked_themes"]:
            data["unlocked_themes"].append(k)
    return data

def save_economy(data):
    _save_json_file(ECONOMY_FILE, data)

def load_campaign():
    data = _load_json_file(CAMPAIGN_FILE, {"unlocked": 1, "completed": []})
    data.setdefault("unlocked", 1)
    data.setdefault("completed", [])
    return data

def save_campaign(data):
    _save_json_file(CAMPAIGN_FILE, data)

def rank_from_stats(stats):
    wins = int(stats.get("wins", 0))
    best = int(stats.get("best_stars", 0))
    if wins >= 50 and best >= 3: return "Легенда пазлов"
    if wins >= 25: return "Эксперт"
    if wins >= 10: return "Мастер"
    if wins >= 3: return "Любитель"
    return "Новичок"

def today_key():
    return time.strftime("%Y-%m-%d")

def extended_gallery_images(extra_folders=None):
    result = list_gallery_images()
    for folder in extra_folders or []:
        try:
            for name in sorted(os.listdir(folder)):
                if name.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
                    path = os.path.join(folder, name)
                    if os.path.isfile(path):
                        result.append(path)
        except OSError:
            pass
    seen, unique = set(), []
    for path in result:
        ap = os.path.abspath(path)
        if ap not in seen:
            seen.add(ap); unique.append(path)
    return unique[:24]

def piece_kind(piece, rows, cols):
    corner = (piece.row in (0, rows-1)) and (piece.col in (0, cols-1))
    edge = piece.row in (0, rows-1) or piece.col in (0, cols-1)
    if corner: return "corners"
    if edge: return "edges"
    return "center"

def create_puzzle_ext(image_path, rows, cols, scr_w, scr_h, seed=None, mirror=False, no_picture=False, false_count=0):
    old_random_state = random.getstate()
    if seed is not None:
        random.seed(seed)
    current_board_img, error_message = load_and_scale_image(image_path, rows, board_w, board_h)
    if mirror:
        current_board_img = pygame.transform.flip(current_board_img, True, False)
    texture = current_board_img
    if no_picture:
        texture = pygame.Surface((board_w, board_h), pygame.SRCALPHA)
        texture.fill((118, 128, 145, 255))
        for r in range(rows):
            for c in range(cols):
                pygame.draw.rect(texture, (92, 100, 115), (c*(board_w//cols), r*(board_h//rows), board_w//cols, board_h//rows), 1)
    p_w, p_h = board_w // cols, board_h // rows
    h_edges, v_edges = generate_edge_profiles(rows, cols)
    all_pieces, active_pieces, box_pieces = [], [], []
    for r in range(rows):
        for c in range(cols):
            edges = (h_edges[r][c], v_edges[r][c + 1], h_edges[r + 1][c], v_edges[r][c])
            piece = PuzzlePiece(texture, c * p_w, r * p_h, p_w, p_h, edges, (board_x + c * p_w, board_y + r * p_h), index=r * cols + c, row=r, col=c)
            piece.is_false = False
            box_pieces.append(piece); all_pieces.append(piece)
    # Ложные детали: выглядят как пазлики, но не входят в победу.
    for i in range(false_count):
        surf = pygame.Surface((board_w, board_h), pygame.SRCALPHA)
        surf.fill((random.randint(40,220), random.randint(40,220), random.randint(40,220), 255))
        rr, cc = random.randrange(rows), random.randrange(cols)
        edges = (0 if rr == 0 else random.choice([1,-1]), 0 if cc == cols-1 else random.choice([1,-1]), 0 if rr == rows-1 else random.choice([1,-1]), 0 if cc == 0 else random.choice([1,-1]))
        fake = PuzzlePiece(surf, 0, 0, p_w, p_h, edges, (-9999, -9999), index=100000+i, row=rr, col=cc)
        fake.is_false = True
        box_pieces.append(fake)
    random.shuffle(box_pieces)
    slots = calculate_spawn_slots(scr_w, scr_h, rows * cols + false_count)
    if seed is not None:
        random.setstate(old_random_state)
    return all_pieces, active_pieces, box_pieces, current_board_img, slots, error_message

class EnhancedGame(Game):
    def __init__(self):
        self.extra_ready = False
        super().__init__()
        self.current_profile = self.settings.get("profile", self.nickname or "Игрок")
        self.profiles = load_profiles()
        if self.current_profile not in self.profiles:
            self.profiles[self.current_profile] = {"created": time.strftime("%Y-%m-%d %H:%M")}
            _save_json_file(PROFILES_FILE, self.profiles)
        self.economy = load_economy()
        self.campaign = load_campaign()
        self.extra_folders = self.settings.get("extra_image_folders", []) if isinstance(self.settings.get("extra_image_folders", []), list) else []
        self.no_picture_mode = bool(self.settings.get("no_picture_mode", False))
        self.mirror_mode = bool(self.settings.get("mirror_mode", False))
        self.false_pieces_mode = bool(self.settings.get("false_pieces_mode", False))
        self.silhouette_mode = bool(self.settings.get("silhouette_mode", True))
        self.sort_filter = "all"
        self.current_tray = 0
        self.active_campaign_level = None
        self.daily_active = False
        self.tutorial_step = 0 if not self.settings.get("tutorial_done") else 999
        self.graphics_fps = int(self.settings.get("graphics_fps", 60)) if int(self.settings.get("graphics_fps", 60)) in (30,60,120) else 60
        self.animations_enabled = bool(self.settings.get("animations_enabled", True))
        self.effects_enabled = bool(self.settings.get("effects_enabled", True))
        self.quality = self.settings.get("quality", "high") if self.settings.get("quality", "high") in ("low","medium","high") else "high"
        self.self_test_message = ""
        self.extra_ready = True

    def save_settings(self):
        super().save_settings()
        self.settings.update({
            "profile": getattr(self, "current_profile", self.nickname or "Игрок"),
            "extra_image_folders": getattr(self, "extra_folders", []),
            "no_picture_mode": getattr(self, "no_picture_mode", False),
            "mirror_mode": getattr(self, "mirror_mode", False),
            "false_pieces_mode": getattr(self, "false_pieces_mode", False),
            "silhouette_mode": getattr(self, "silhouette_mode", True),
            "tutorial_done": getattr(self, "tutorial_step", 0) >= 999,
            "graphics_fps": getattr(self, "graphics_fps", 60),
            "animations_enabled": getattr(self, "animations_enabled", True),
            "effects_enabled": getattr(self, "effects_enabled", True),
            "quality": getattr(self, "quality", "high"),
        })
        save_settings_dict(self.settings)

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(getattr(self, "graphics_fps", 60))

    def new_puzzle(self, rows=None, cols=None, image_path_marker="keep", reset_image=False, keep_seed=False):
        if rows:
            self.rows = rows; self.cols = cols or rows
        if getattr(self, "mode", "normal") == "kids":
            self.rows = max(2, min(self.rows, 4)); self.cols = max(2, min(self.cols, 4))
        if reset_image:
            self.current_image_path = None
        elif image_path_marker != "keep":
            self.current_image_path = image_path_marker
        if not keep_seed:
            self.puzzle_seed = random.randint(1, 999999999)
        false_count = 3 if getattr(self, "false_pieces_mode", False) else 0
        (self.all_pieces, self.active_pieces, self.box_pieces, self.current_board_img, self.spawn_slots, error_message) = create_puzzle_ext(
            self.current_image_path, self.rows, self.cols, self.current_w, self.current_h, self.puzzle_seed,
            mirror=getattr(self, "mirror_mode", False), no_picture=getattr(self, "no_picture_mode", False), false_count=false_count)
        self.slot_index = 0; self.selected_piece = None; self.is_victory = False; self.victory_saved = False
        self.moves = 0; self.hints_used = 0; self.hint_penalty_seconds = 0; self.confetti = []; self.stars = 0
        self.start_ticks = pygame.time.get_ticks(); self.end_seconds = 0; self.loaded_elapsed = 0
        self.time_limit = self.get_time_limit(); self.lost_by_time = False
        self.hint_piece = None; self.hint_until_ticks = 0; self.hint_message = ""; self.hint_level = 0; self.last_hint_index = None
        self.selected_group = []; self.group_offsets = []; self.error_message = error_message or ""

    def next_theme(self):
        unlocked = self.economy.get("unlocked_themes", FREE_THEMES[:]) if hasattr(self, "economy") else list(THEMES.keys())
        keys = [k for k in THEMES.keys() if k in unlocked]
        if not keys: keys = FREE_THEMES[:]
        self.theme_key = keys[(keys.index(self.theme_key) + 1) % len(keys)] if self.theme_key in keys else keys[0]
        self.save_settings()

    def reward_coins(self, amount):
        self.economy = load_economy()
        self.economy["coins"] = int(self.economy.get("coins",0)) + int(amount)
        save_economy(self.economy)
        if self.economy["coins"] >= 500: self.notify_achievement("rich")

    def update_stats_after_win(self):
        stats = load_stats()
        profile = self.current_profile
        s = stats.setdefault(profile, {"wins":0,"total_time":0,"total_moves":0,"hints":0,"best_time":None,"best_stars":0,"max_pieces":0,"daily":0})
        s["wins"] += 1
        s["total_time"] += int(self.end_seconds)
        s["total_moves"] += int(self.moves)
        s["hints"] += int(self.hints_used)
        s["best_stars"] = max(int(s.get("best_stars",0)), int(self.stars))
        s["max_pieces"] = max(int(s.get("max_pieces",0)), self.rows*self.cols)
        if s.get("best_time") is None or self.end_seconds < s.get("best_time", 10**9): s["best_time"] = int(self.end_seconds)
        save_stats(stats)

    def check_victory(self):
        was = self.is_victory
        super().check_victory()
        if self.is_victory and not was:
            self.update_stats_after_win()
            base_reward = 20 + self.rows*self.cols*2 + self.stars*10 - self.hints_used*2
            if self.mode == "hardcore": base_reward += 30
            if getattr(self, "daily_active", False):
                base_reward += 50
                d = _load_json_file(DAILY_FILE, {})
                d[today_key()] = {"profile": self.current_profile, "time": self.end_seconds, "moves": self.moves, "stars": self.stars}
                _save_json_file(DAILY_FILE, d)
                stats = load_stats(); stats.setdefault(self.current_profile, {}).setdefault("daily", 0)
                stats[self.current_profile]["daily"] = stats[self.current_profile].get("daily",0)+1; save_stats(stats)
                self.notify_achievement("daily_done")
            if getattr(self, "active_campaign_level", None) is not None:
                idx = self.active_campaign_level
                self.campaign = load_campaign()
                if idx not in self.campaign.get("completed", []):
                    self.campaign.setdefault("completed", []).append(idx)
                    self.campaign["unlocked"] = max(int(self.campaign.get("unlocked",1)), idx+2)
                    save_campaign(self.campaign)
                    base_reward += CAMPAIGN_LEVELS[idx].get("coins",0)
                    if idx == 0: self.notify_achievement("campaign_1")
            if getattr(self, "no_picture_mode", False) or getattr(self, "mirror_mode", False) or getattr(self, "false_pieces_mode", False):
                self.notify_achievement("hard_option")
            self.reward_coins(max(5, base_reward))

    def reveal_from_box(self, amount=1):
        for _ in range(amount):
            if not self.box_pieces or self.slot_index >= len(self.spawn_slots): break
            idx = None
            if self.sort_filter != "all":
                for i,p in enumerate(self.box_pieces):
                    if getattr(p, "is_false", False) or piece_kind(p, self.rows, self.cols) == self.sort_filter:
                        idx = i; break
            if idx is None: idx = len(self.box_pieces)-1
            piece = self.box_pieces.pop(idx)
            slot = self.spawn_slots[self.slot_index]
            if self.current_tray:
                tray = tray_rects[self.current_tray-1]
                slot = (tray.left + 10 + (self.slot_index % 3)*42, tray.top + 28 + ((self.slot_index//3)%3)*38)
            piece.set_origin_pos(slot)
            if self.mode_allows_rotation() and not getattr(piece,"is_false",False):
                for _ in range(random.randint(0, 3)): piece.rotate_clockwise()
            self.active_pieces.append(piece); self.slot_index += 1
        self.sound.play("pick")

    def show_piece_hint(self):
        if not self.mode_allows_hints():
            self.hint_piece=None; self.hint_message="В этом режиме подсказки отключены"; self.hint_until_ticks=pygame.time.get_ticks()+1800; return
        target = self.selected_piece
        if not target or getattr(target, "is_false", False):
            unlocked = [p for p in self.active_pieces if not p.is_locked and not getattr(p,"is_false",False)]
            target = unlocked[-1] if unlocked else None
        if not target:
            self.hint_piece=None; self.hint_message="Сначала достань настоящий пазлик"; self.hint_until_ticks=pygame.time.get_ticks()+1800; return
        self.selected_piece = target
        super().show_piece_hint()

    def arrange_active_pieces(self):
        slots = calculate_spawn_slots(self.current_w, self.current_h, len(self.active_pieces))
        i = 0
        for p in self.active_pieces:
            if not p.is_locked:
                p.set_origin_pos(slots[i % len(slots)]); i += 1
        self.hint_message = "Детали разложены вокруг поля"; self.hint_until_ticks = pygame.time.get_ticks()+1700

    def start_campaign_level(self, idx):
        if idx >= int(self.campaign.get("unlocked", 1)): return
        lvl = CAMPAIGN_LEVELS[idx]
        self.active_campaign_level = idx; self.daily_active = False; self.mode = lvl["mode"]
        self.start_game(lvl["rows"], lvl["cols"])

    def start_daily_puzzle(self):
        imgs = extended_gallery_images(getattr(self, "extra_folders", []))
        random.seed(today_key())
        img = random.choice(imgs) if imgs else None
        self.daily_active = True; self.active_campaign_level = None
        self.mode = random.choice(["normal", "timed", "no_hints"])
        size = random.choice([3,4,5])
        self.puzzle_seed = abs(hash(today_key())) % 999999999
        self.rows = size; self.cols = size; self.current_image_path = img
        self.state = "PUZZLE"; self.popup = None
        self.new_puzzle(size, size, image_path_marker=img, keep_seed=True)

    def start_game(self, rows, cols, image_path_marker=None):
        # Обычный запуск сбрасывает ежедневный режим. Кампания сохраняется, если уровень был выбран через start_campaign_level.
        self.daily_active = False
        super().start_game(rows, cols, image_path_marker)

    def handle_mouse_down(self, mx, my):
        if self.tutorial_step < 999:
            self.tutorial_step += 1
            if self.tutorial_step >= 4:
                self.tutorial_step = 999; self.save_settings()
            return
        super().handle_mouse_down(mx, my)

    def handle_menu_click(self, mx, my):
        if self.popup in ("campaign","daily","shop","profiles","stats","advanced_options"):
            self.handle_extra_popup_click(mx,my); return
        if self.popup == "difficulty" and btn_extra_modes.collidepoint(mx,my):
            self.popup = "advanced_options"; return
        if btn_campaign.collidepoint(mx,my): self.popup="campaign"; return
        if btn_daily.collidepoint(mx,my): self.popup="daily"; return
        if btn_shop.collidepoint(mx,my): self.popup="shop"; return
        if btn_profiles.collidepoint(mx,my): self.popup="profiles"; return
        if btn_stats.collidepoint(mx,my): self.popup="stats"; return
        super().handle_menu_click(mx,my)

    def handle_extra_popup_click(self, mx, my):
        rect = pygame.Rect(self.current_w//2-330, self.current_h//2-230, 660, 460)
        self.place_close_button(rect)
        if btn_close_popup.collidepoint(mx,my) or not rect.collidepoint(mx,my): self.popup=None; return
        if self.popup == "campaign":
            for r,idx in campaign_rects:
                if r.collidepoint(mx,my): self.start_campaign_level(idx); return
        elif self.popup == "daily":
            start = pygame.Rect(rect.centerx-120, rect.bottom-74, 240, 42)
            if start.collidepoint(mx,my): self.start_daily_puzzle(); return
        elif self.popup == "shop":
            for r,key in shop_rects:
                if r.collidepoint(mx,my):
                    self.buy_or_select_theme(key); return
        elif self.popup == "profiles":
            if btn_create_profile.collidepoint(mx,my):
                name = self.nickname.strip() or f"Игрок {len(self.profiles)+1}"
                self.profiles[name] = {"created": time.strftime("%Y-%m-%d %H:%M")}; _save_json_file(PROFILES_FILE, self.profiles)
                self.current_profile = name; self.nickname = name; self.save_settings(); self.notify_achievement("profile_master"); return
            for r,name in profile_rects:
                if r.collidepoint(mx,my):
                    self.current_profile=name; self.nickname=name; self.save_settings(); self.notify_achievement("profile_master"); return
        elif self.popup == "advanced_options":
            if btn_no_picture.collidepoint(mx,my): self.no_picture_mode = not self.no_picture_mode; self.save_settings(); return
            if btn_mirror.collidepoint(mx,my): self.mirror_mode = not self.mirror_mode; self.save_settings(); return
            if btn_false_pieces.collidepoint(mx,my): self.false_pieces_mode = not self.false_pieces_mode; self.save_settings(); return
            if btn_silhouette.collidepoint(mx,my): self.silhouette_mode = not self.silhouette_mode; self.save_settings(); return

    def buy_or_select_theme(self, key):
        self.economy = load_economy(); unlocked = self.economy.setdefault("unlocked_themes", FREE_THEMES[:])
        if key in unlocked:
            self.theme_key = key; self.save_settings(); return
        cost = SHOP_THEMES.get(key, 999)
        if int(self.economy.get("coins",0)) >= cost:
            self.economy["coins"] -= cost; unlocked.append(key); save_economy(self.economy)
            self.theme_key = key; self.save_settings(); self.notify_achievement("buyer")
        else:
            self.hint_message = "Не хватает монет"; self.hint_until_ticks = pygame.time.get_ticks()+1800

    def handle_puzzle_click(self, mx, my):
        self.update_extra_puzzle_rects()
        for rect, filt in [(btn_sort_all,"all"),(btn_sort_corners,"corners"),(btn_sort_edges,"edges"),(btn_sort_center,"center")]:
            if rect.collidepoint(mx,my):
                self.sort_filter=filt; self.notify_achievement("sorter"); return
        for i,tr in enumerate(tray_rects,1):
            if tr.collidepoint(mx,my):
                self.current_tray = 0 if self.current_tray == i else i; self.notify_achievement("tray_user"); return
        if btn_arrange.collidepoint(mx,my): self.arrange_active_pieces(); return
        super().handle_puzzle_click(mx,my)

    def handle_keydown(self, event):
        if self.state == "PUZZLE" and event.key == pygame.K_a:
            self.arrange_active_pieces(); return
        super().handle_keydown(event)

    def draw_menu(self):
        super().draw_menu()
        if self.popup in ("difficulty","records","settings","achievements","gallery"):
            return
        self.draw_extra_menu_buttons()
        if self.popup == "campaign": self.draw_campaign_popup()
        elif self.popup == "daily": self.draw_daily_popup()
        elif self.popup == "shop": self.draw_shop_popup()
        elif self.popup == "profiles": self.draw_profiles_popup()
        elif self.popup == "stats": self.draw_stats_popup()
        elif self.popup == "advanced_options": self.draw_advanced_options_popup()

    def draw_extra_menu_buttons(self):
        mx,my=pygame.mouse.get_pos(); t=self.theme; cx=self.current_w//2; y=self.current_h//2+180
        btn_campaign.update(cx-330,y,126,36); btn_daily.update(cx-198,y,126,36); btn_shop.update(cx-66,y,126,36); btn_profiles.update(cx+66,y,126,36); btn_stats.update(cx+198,y,126,36)
        draw_button(screen, btn_campaign, "Кампания", self.font_small, t["accent"], t["text"], btn_campaign.collidepoint(mx,my))
        draw_button(screen, btn_daily, "Пазл дня", self.font_small, t["success"], t["text"], btn_daily.collidepoint(mx,my))
        draw_button(screen, btn_shop, f"Магазин ({self.economy.get('coins',0)}¢)", self.font_small, t["orange"], t["text"], btn_shop.collidepoint(mx,my))
        draw_button(screen, btn_profiles, "Профили", self.font_small, t["border"], t["text"], btn_profiles.collidepoint(mx,my))
        draw_button(screen, btn_stats, "Статистика", self.font_small, t["warning"], t["text"], btn_stats.collidepoint(mx,my))

    def draw_difficulty_popup(self):
        super().draw_difficulty_popup()
        mx,my=pygame.mouse.get_pos(); t=self.theme
        btn_extra_modes.update(self.current_w//2-130, self.current_h//2+199, 260, 30)
        draw_button(screen, btn_extra_modes, "Доп. режимы и усложнения", self.font_small, t["danger"] if (self.no_picture_mode or self.mirror_mode or self.false_pieces_mode) else t["border"], t["text"], btn_extra_modes.collidepoint(mx,my))

    def draw_gallery_popup(self):
        global gallery_rects
        super().draw_gallery_popup()
        mx,my=pygame.mouse.get_pos(); t=self.theme
        rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
        btn_import_folder.update(rect.left+28, rect.bottom-44, 190, 28)
        draw_button(screen, btn_import_folder, "Добавить папку", self.font_small, t["success"], t["text"], btn_import_folder.collidepoint(mx,my))

    def handle_menu_click(self, mx, my):
        # расширенная галерея: сначала ловим кнопку импорта
        if self.popup == "gallery" and btn_import_folder.collidepoint(mx,my):
            root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
            folder = filedialog.askdirectory(title="Папка с картинками")
            root.destroy()
            if folder and folder not in self.extra_folders:
                self.extra_folders.append(folder); self.save_settings()
            return
        # галерея с дополнительными папками
        if self.popup == "gallery":
            rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx,my): self.popup="difficulty"; return
            for r,path in gallery_rects:
                if r.collidepoint(mx,my): self.current_image_path=path; self.start_game(self.rows,self.cols,image_path_marker=path); return
            if not rect.collidepoint(mx,my): self.popup="difficulty"
            return
        if self.popup in ("campaign","daily","shop","profiles","stats","advanced_options"):
            self.handle_extra_popup_click(mx,my); return
        if self.popup == "difficulty" and btn_extra_modes.collidepoint(mx,my): self.popup="advanced_options"; return
        if btn_campaign.collidepoint(mx,my): self.popup="campaign"; return
        if btn_daily.collidepoint(mx,my): self.popup="daily"; return
        if btn_shop.collidepoint(mx,my): self.popup="shop"; return
        if btn_profiles.collidepoint(mx,my): self.popup="profiles"; return
        if btn_stats.collidepoint(mx,my): self.popup="stats"; return
        super().handle_menu_click(mx,my)

    def draw_gallery_popup(self):
        global gallery_rects
        mx,my=pygame.mouse.get_pos(); t=self.theme
        rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
        self.draw_popup_base(rect, "ГАЛЕРЕЯ КАРТИНОК")
        images = extended_gallery_images(getattr(self,"extra_folders",[]))
        gallery_rects=[]
        if not images:
            draw_text_center("Добавь картинки в images/custom или нажми 'Добавить папку'", self.font_btn, t["text"], screen, rect.centerx, rect.centery)
        x0,y0=rect.left+28,rect.top+64; card_w,card_h=140,86
        for i,path in enumerate(images[:16]):
            x=x0+(i%4)*155; y=y0+(i//4)*96; card=pygame.Rect(x,y,card_w,card_h); gallery_rects.append((card,path))
            pygame.draw.rect(screen,t["panel"],card,border_radius=8); pygame.draw.rect(screen,t["success"] if card.collidepoint(mx,my) else t["border"],card,2,border_radius=8)
            try:
                img=pygame.image.load(path).convert_alpha(); thumb=pygame.transform.smoothscale(img,(card_w-12,card_h-28)); screen.blit(thumb,(card.left+6,card.top+6))
            except Exception: pygame.draw.rect(screen,t["danger"],(card.left+6,card.top+6,card_w-12,card_h-28),border_radius=5)
            label=self.font_small.render(os.path.basename(path)[:18],True,t["text"]); screen.blit(label,label.get_rect(centerx=card.centerx,bottom=card.bottom-4))
        btn_import_folder.update(rect.left+28, rect.bottom-40, 190, 28)
        draw_button(screen, btn_import_folder, "Добавить папку", self.font_small, t["success"], t["text"], btn_import_folder.collidepoint(mx,my))
        note=self.font_small.render("Можно импортировать целую папку с изображениями",True,t["border"]); screen.blit(note,note.get_rect(right=rect.right-28,centery=btn_import_folder.centery))

    def draw_campaign_popup(self):
        global campaign_rects
        mx,my=pygame.mouse.get_pos(); t=self.theme; rect=pygame.Rect(self.current_w//2-330,self.current_h//2-230,660,460); self.draw_popup_base(rect,"КАМПАНИЯ")
        self.campaign=load_campaign(); campaign_rects=[]; unlocked=int(self.campaign.get("unlocked",1)); completed=set(self.campaign.get("completed",[]))
        y=rect.top+64
        for i,lvl in enumerate(CAMPAIGN_LEVELS):
            r=pygame.Rect(rect.left+32,y,rect.width-64,48); campaign_rects.append((r,i))
            available=i<unlocked; done=i in completed
            pygame.draw.rect(screen,t["panel"] if available else t["bg"],r,border_radius=8); pygame.draw.rect(screen,t["success"] if done else (t["warning"] if available else t["border"]),r,2,border_radius=8)
            label=("✓ " if done else ("▶ " if available else "🔒 "))+f"{i+1}. {lvl['name']} — {lvl['rows']}x{lvl['cols']} — {mode_title(lvl['mode'])}"
            screen.blit(self.font_btn.render(label,True,t["text"] if available else t["border"]),(r.left+14,r.top+7))
            screen.blit(self.font_small.render(f"Награда: {lvl['coins']} монет",True,t["border"]),(r.left+14,r.top+29))
            y+=58

    def draw_daily_popup(self):
        t=self.theme; mx,my=pygame.mouse.get_pos(); rect=pygame.Rect(self.current_w//2-330,self.current_h//2-230,660,460); self.draw_popup_base(rect,"ЕЖЕДНЕВНЫЙ ПАЗЛ")
        d=_load_json_file(DAILY_FILE,{})
        done=d.get(today_key())
        lines=[f"Сегодня: {today_key()}","Каждый день выбирается новая картинка и случайный режим.","За победу дают дополнительную награду +50 монет."]
        if done: lines.append(f"Сегодня уже собрано: {done.get('profile','Игрок')} — {format_time(done.get('time',0))}, ★{done.get('stars',0)}")
        for i,line in enumerate(lines): screen.blit(self.font_btn.render(line,True,t["text"]),(rect.left+48,rect.top+82+i*34))
        start=pygame.Rect(rect.centerx-120,rect.bottom-74,240,42); draw_button(screen,start,"Начать пазл дня",self.font_btn,t["success"],t["text"],start.collidepoint(mx,my))

    def draw_shop_popup(self):
        global shop_rects
        mx,my=pygame.mouse.get_pos(); t=self.theme; rect=pygame.Rect(self.current_w//2-330,self.current_h//2-230,660,460); self.draw_popup_base(rect,"МАГАЗИН ТЕМ")
        self.economy=load_economy(); unlocked=self.economy.get("unlocked_themes",FREE_THEMES[:]); shop_rects=[]
        screen.blit(self.font_btn.render(f"Монеты: {self.economy.get('coins',0)}",True,t["warning"]),(rect.left+36,rect.top+58))
        keys=FREE_THEMES+list(SHOP_THEMES.keys())
        for i,key in enumerate(keys):
            x=rect.left+36+(i%3)*200; y=rect.top+92+(i//3)*112; r=pygame.Rect(x,y,180,86); shop_rects.append((r,key))
            th=THEMES[key]; pygame.draw.rect(screen,th["bg"],r,border_radius=10); pygame.draw.rect(screen,t["success"] if key==self.theme_key else t["border"],r,3,border_radius=10)
            screen.blit(self.font_btn.render(th["name"],True,th["text"]),(r.left+12,r.top+10))
            status="Выбрана" if key==self.theme_key else ("Выбрать" if key in unlocked else f"Купить {SHOP_THEMES.get(key,0)}¢")
            screen.blit(self.font_small.render(status,True,th["warning"]),(r.left+12,r.bottom-26))

    def draw_profiles_popup(self):
        global profile_rects
        mx,my=pygame.mouse.get_pos(); t=self.theme; rect=pygame.Rect(self.current_w//2-330,self.current_h//2-230,660,460); self.draw_popup_base(rect,"ПРОФИЛИ ИГРОКОВ")
        self.profiles=load_profiles(); profile_rects=[]; y=rect.top+70
        for name,info in list(self.profiles.items())[:7]:
            r=pygame.Rect(rect.left+48,y,rect.width-96,42); profile_rects.append((r,name)); pygame.draw.rect(screen,t["panel"],r,border_radius=8); pygame.draw.rect(screen,t["success"] if name==self.current_profile else t["border"],r,2,border_radius=8)
            screen.blit(self.font_btn.render(("★ " if name==self.current_profile else "")+name,True,t["text"]),(r.left+12,r.top+10)); y+=50
        btn_create_profile.update(rect.centerx-130,rect.bottom-62,260,34); draw_button(screen,btn_create_profile,f"Создать/выбрать: {self.nickname or 'Игрок'}",self.font_small,t["accent"],t["text"],btn_create_profile.collidepoint(mx,my))

    def draw_stats_popup(self):
        t=self.theme; rect=pygame.Rect(self.current_w//2-330,self.current_h//2-230,660,460); self.draw_popup_base(rect,"СТАТИСТИКА")
        s=load_stats().get(self.current_profile,{})
        wins=int(s.get("wins",0)); avg_time=int(s.get("total_time",0)/wins) if wins else 0; avg_moves=int(s.get("total_moves",0)/wins) if wins else 0
        lines=[f"Профиль: {self.current_profile}",f"Ранг: {rank_from_stats(s)}",f"Собрано пазлов: {wins}",f"Лучшее время: {format_time(s.get('best_time') or 0)}",f"Среднее время: {format_time(avg_time)}",f"Средние ходы: {avg_moves}",f"Подсказок использовано: {s.get('hints',0)}",f"Самый большой пазл: {s.get('max_pieces',0)} деталей",f"Ежедневных пазлов: {s.get('daily',0)}",f"Монеты: {load_economy().get('coins',0)}"]
        for i,line in enumerate(lines): screen.blit(self.font_btn.render(line,True,t["text"]),(rect.left+70,rect.top+72+i*34))

    def draw_advanced_options_popup(self):
        mx,my=pygame.mouse.get_pos(); t=self.theme; rect=pygame.Rect(self.current_w//2-330,self.current_h//2-230,660,460); self.draw_popup_base(rect,"ДОПОЛНИТЕЛЬНЫЕ РЕЖИМЫ")
        opts=[(btn_no_picture,"Без картинки: "+("Вкл" if self.no_picture_mode else "Выкл")),(btn_mirror,"Зеркальная картинка: "+("Вкл" if self.mirror_mode else "Выкл")),(btn_false_pieces,"Ложные детали: "+("Вкл" if self.false_pieces_mode else "Выкл")),(btn_silhouette,"Подложка-силуэты: "+("Вкл" if self.silhouette_mode else "Выкл"))]
        y=rect.top+82
        for b,text in opts:
            b.update(rect.centerx-180,y,360,42); draw_button(screen,b,text,self.font_btn,t["orange"],t["text"],b.collidepoint(mx,my)); y+=58
        notes=["Без картинки — на деталях только серые формы.","Зеркало — изображение переворачивается по горизонтали.","Ложные детали — в коробке появляются лишние пазлики.","Силуэты — на поле видны полупрозрачные места деталей."]
        for i,n in enumerate(notes): screen.blit(self.font_small.render(n,True,t["border"]),(rect.left+60,rect.bottom-122+i*23))

    def draw_settings_popup(self):
        super().draw_settings_popup()
        mx,my=pygame.mouse.get_pos(); t=self.theme; rect=pygame.Rect(self.current_w//2-170,self.current_h//2-165,340,360)
        btn_fps_toggle.update(rect.left+26,rect.bottom-82,92,26); btn_anim_toggle.update(rect.left+124,rect.bottom-82,92,26); btn_quality_toggle.update(rect.left+222,rect.bottom-82,92,26); btn_self_test.update(rect.left+26,rect.bottom-48,288,26)
        draw_button(screen,btn_fps_toggle,f"FPS {self.graphics_fps}",self.font_small,t["border"],t["text"],btn_fps_toggle.collidepoint(mx,my))
        draw_button(screen,btn_anim_toggle,"Аним: "+("Вкл" if self.animations_enabled else "Выкл"),self.font_small,t["border"],t["text"],btn_anim_toggle.collidepoint(mx,my))
        draw_button(screen,btn_quality_toggle,"Кач: "+{"low":"низ","medium":"ср","high":"выс"}[self.quality],self.font_small,t["border"],t["text"],btn_quality_toggle.collidepoint(mx,my))
        draw_button(screen,btn_self_test,"Самотест сохранений",self.font_small,t["success"],t["text"],btn_self_test.collidepoint(mx,my))
        if self.self_test_message:
            screen.blit(self.font_small.render(self.self_test_message,True,t["warning"]),(rect.left+30,rect.bottom-112))

    def handle_menu_click(self, mx, my):
        if self.popup == "settings":
            if btn_fps_toggle.collidepoint(mx,my):
                self.graphics_fps = {30:60,60:120,120:30}.get(self.graphics_fps,60); self.save_settings(); return
            if btn_anim_toggle.collidepoint(mx,my): self.animations_enabled=not self.animations_enabled; self.save_settings(); return
            if btn_quality_toggle.collidepoint(mx,my): self.quality={"low":"medium","medium":"high","high":"low"}.get(self.quality,"high"); self.save_settings(); return
            if btn_self_test.collidepoint(mx,my): self.self_test_message=self.run_self_tests(); return
        # остальная логика определена ниже через вспомогатель
        self._handle_menu_click_extended(mx,my)

    def _handle_menu_click_extended(self, mx, my):
        if self.popup == "gallery" and btn_import_folder.collidepoint(mx,my):
            root=tk.Tk(); root.withdraw(); root.attributes('-topmost', True); folder=filedialog.askdirectory(title="Папка с картинками"); root.destroy()
            if folder and folder not in self.extra_folders: self.extra_folders.append(folder); self.save_settings()
            return
        if self.popup == "gallery":
            rect=pygame.Rect(self.current_w//2-330,self.current_h//2-230,660,460); self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx,my): self.popup="difficulty"; return
            for r,path in gallery_rects:
                if r.collidepoint(mx,my): self.current_image_path=path; self.start_game(self.rows,self.cols,image_path_marker=path); return
            if not rect.collidepoint(mx,my): self.popup="difficulty"
            return
        if self.popup in ("campaign","daily","shop","profiles","stats","advanced_options"):
            self.handle_extra_popup_click(mx,my); return
        if self.popup == "difficulty" and btn_extra_modes.collidepoint(mx,my): self.popup="advanced_options"; return
        if btn_campaign.collidepoint(mx,my): self.popup="campaign"; return
        if btn_daily.collidepoint(mx,my): self.popup="daily"; return
        if btn_shop.collidepoint(mx,my): self.popup="shop"; return
        if btn_profiles.collidepoint(mx,my): self.popup="profiles"; return
        if btn_stats.collidepoint(mx,my): self.popup="stats"; return
        super().handle_menu_click(mx,my)

    def run_self_tests(self):
        try:
            tmp={"ok":True,"t":time.time()}; _save_json_file("selftest_tmp.json",tmp); data=_load_json_file("selftest_tmp.json",{}); os.remove("selftest_tmp.json")
            assert data.get("ok") is True
            assert isinstance(load_records(), list)
            assert isinstance(load_settings(), dict)
            return "Самотест: OK"
        except Exception as e:
            return f"Самотест: ошибка {e}"

    def update_extra_puzzle_rects(self):
        x=20; y=max(185, board_y+board_h+12)
        btn_sort_all.update(x,y,78,26); btn_sort_corners.update(x+84,y,78,26); btn_sort_edges.update(x+168,y,78,26); btn_sort_center.update(x+252,y,78,26); btn_arrange.update(x+336,y,100,26)
        tray_y=y+36
        for i,tr in enumerate(tray_rects): tr.update(x+i*145,tray_y,135,62)

    def draw_puzzle(self):
        super().draw_puzzle()
        self.draw_extra_puzzle_ui()
        self.draw_tutorial_overlay()

    def draw_extra_puzzle_ui(self):
        self.update_extra_puzzle_rects(); mx,my=pygame.mouse.get_pos(); t=self.theme
        buttons=[(btn_sort_all,"Все","all"),(btn_sort_corners,"Углы","corners"),(btn_sort_edges,"Края","edges"),(btn_sort_center,"Центр","center")]
        for rect,text,f in buttons: draw_button(screen,rect,text,self.font_small,t["success"] if self.sort_filter==f else t["border"],t["text"],rect.collidepoint(mx,my))
        draw_button(screen,btn_arrange,"Разложить",self.font_small,t["orange"],t["text"],btn_arrange.collidepoint(mx,my))
        for i,tr in enumerate(tray_rects,1):
            pygame.draw.rect(screen,t["panel"],tr,border_radius=8); pygame.draw.rect(screen,t["success"] if self.current_tray==i else t["border"],tr,2,border_radius=8)
            screen.blit(self.font_small.render(f"Лоток {i}",True,t["text"]),(tr.left+10,tr.top+7))
            screen.blit(self.font_small.render("клик — выбрать",True,t["border"]),(tr.left+10,tr.top+31))
        if self.silhouette_mode and self.mode != "hardcore": self.draw_silhouette_board()
        self.draw_neighbor_highlights()

    def draw_silhouette_board(self):
        t=self.theme
        if not self.all_pieces: return
        p_w,p_h=board_w//self.cols, board_h//self.rows
        overlay=pygame.Surface((board_w,board_h),pygame.SRCALPHA)
        for p in self.all_pieces:
            if not p.is_locked:
                x=p.col*p_w; y=p.row*p_h
                pygame.draw.rect(overlay, (*t["border"], 45), (x+4,y+4,p_w-8,p_h-8), border_radius=8)
        screen.blit(overlay,(board_x,board_y))

    def draw_neighbor_highlights(self):
        if not self.selected_piece: return
        t=self.theme; target_neighbors=[]
        for p in self.active_pieces:
            if p is self.selected_piece or p.is_locked: continue
            if abs(p.row-self.selected_piece.row)+abs(p.col-self.selected_piece.col)==1:
                target_neighbors.append(p)
        for p in target_neighbors[:4]:
            pygame.draw.rect(screen,t["warning"],p.rect.inflate(8,8),3,border_radius=8)

    def draw_background_animation(self):
        if getattr(self,"animations_enabled",True): super().draw_background_animation()

    def spawn_confetti(self):
        if getattr(self,"effects_enabled",True): super().spawn_confetti()
        else: self.confetti=[]

    def draw_tutorial_overlay(self):
        if self.tutorial_step >= 999: return
        t=self.theme; overlay=pygame.Surface((self.current_w,self.current_h),pygame.SRCALPHA); overlay.fill((0,0,0,150)); screen.blit(overlay,(0,0))
        rect=pygame.Rect(self.current_w//2-280,self.current_h//2-110,560,220); pygame.draw.rect(screen,t["panel2"],rect,border_radius=14); pygame.draw.rect(screen,t["warning"],rect,3,border_radius=14)
        steps=["Добро пожаловать! Кликни по коробке, чтобы доставать пазлики.","Перетаскивай детали мышкой. R или ПКМ поворачивает деталь.","Кнопка 'Подсказка' показывает место детали, но даёт штраф.","Используй лотки, сортировку, кампанию и магазин тем. Клик — закрыть обучение."]
        draw_text_center("ОБУЧЕНИЕ",self.font_title,t["warning"],screen,rect.centerx,rect.top+42)
        draw_text_center(steps[min(self.tutorial_step,len(steps)-1)],self.font_btn,t["text"],screen,rect.centerx,rect.centery)
        draw_text_center("Кликни, чтобы продолжить",self.font_small,t["border"],screen,rect.centerx,rect.bottom-36)



# =========================================================
# ДОПОЛНЕНИЕ: DELUXE EDITION
# =========================================================
# Новая секция добавляет удобство: пауза, слоты сохранений, Undo/Redo,
# перемещение рабочего стола, мини-карта, альбом, ежедневные задания,
# визуальные эффекты и диагностика. Старые JSON-файлы остаются совместимыми.
SAVE_SLOTS_DIR = "saves"
ALBUM_FILE = "album.json"
DAILY_QUESTS_FILE = "daily_quests.json"
DIAGNOSTICS_LOG = "diagnostics.json"
ASSETS_FILE = "assets.json"
GAME_VERSION = "Deluxe 1.0"

btn_pause_continue = pygame.Rect(0,0,1,1)
btn_pause_menu = pygame.Rect(0,0,1,1)
btn_pause_settings = pygame.Rect(0,0,1,1)
btn_pause_save = pygame.Rect(0,0,1,1)
btn_center_view = pygame.Rect(0,0,1,1)
btn_undo = pygame.Rect(0,0,1,1)
btn_redo = pygame.Rect(0,0,1,1)
btn_album = pygame.Rect(0,0,1,1)
btn_quests = pygame.Rect(0,0,1,1)
btn_diagnostics = pygame.Rect(0,0,1,1)
save_slot_rects = []

EXTRA_ACHIEVEMENTS_DELUXE = {
    "undo_user": {"title": "Время назад", "desc": "Используй отмену действия."},
    "album_first": {"title": "Фотоальбом", "desc": "Собери пазл и добавь его в альбом."},
    "daily_quest": {"title": "Задание дня", "desc": "Выполни ежедневное задание."},
    "zoom_user": {"title": "Лупа", "desc": "Используй масштабирование рабочего стола."},
    "slot_save": {"title": "Архивариус", "desc": "Сохрани игру в отдельный слот."},
}
ACHIEVEMENTS.update(EXTRA_ACHIEVEMENTS_DELUXE)


def ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass


def slot_file(slot):
    ensure_dir(SAVE_SLOTS_DIR)
    return os.path.join(SAVE_SLOTS_DIR, f"slot_{int(slot)}.json")


def load_slot_info(slot):
    data = _load_json_file(slot_file(slot), {})
    if not data:
        return None
    pieces = data.get("pieces", [])
    locked = sum(1 for p in pieces if p.get("locked"))
    total = max(1, int(data.get("rows", 1)) * int(data.get("cols", 1)))
    return {
        "rows": int(data.get("rows", 0)),
        "cols": int(data.get("cols", 0)),
        "mode": data.get("mode", "normal"),
        "elapsed": int(data.get("elapsed", 0)),
        "progress": int(locked * 100 / total),
        "nickname": data.get("nickname", "Игрок"),
        "date": data.get("saved_at", ""),
    }


def add_album_entry(profile, image, rows, cols, seconds, moves, stars):
    album = _load_json_file(ALBUM_FILE, [])
    if not isinstance(album, list):
        album = []
    album.append({
        "profile": profile or "Игрок",
        "image": image or "default",
        "rows": rows,
        "cols": cols,
        "time": int(seconds),
        "moves": int(moves),
        "stars": int(stars),
        "date": time.strftime("%Y-%m-%d %H:%M"),
    })
    _save_json_file(ALBUM_FILE, album[-80:])


def daily_quests_for_today():
    today = today_key()
    data = _load_json_file(DAILY_QUESTS_FILE, {})
    if data.get("date") == today and isinstance(data.get("quests"), list):
        return data
    seed = sum(ord(ch) for ch in today)
    rnd = random.Random(seed)
    pool = [
        {"id": "place20", "title": "Поставь 20 деталей", "target": 20, "reward": 35},
        {"id": "win_no_hint", "title": "Собери пазл без подсказок", "target": 1, "reward": 60},
        {"id": "win_5x5", "title": "Собери пазл 5x5 или больше", "target": 1, "reward": 70},
        {"id": "use_custom", "title": "Сыграй со своей картинкой", "target": 1, "reward": 40},
        {"id": "rotate10", "title": "Поверни детали 10 раз", "target": 10, "reward": 30},
        {"id": "save_slot", "title": "Сохрани игру в слот", "target": 1, "reward": 25},
    ]
    rnd.shuffle(pool)
    quests = []
    for q in pool[:3]:
        item = dict(q)
        item["progress"] = 0
        item["done"] = False
        quests.append(item)
    data = {"date": today, "quests": quests}
    _save_json_file(DAILY_QUESTS_FILE, data)
    return data


def update_daily_quest(qid, amount=1, reward_callback=None):
    data = daily_quests_for_today()
    changed = False
    completed = []
    for q in data.get("quests", []):
        if q.get("id") == qid and not q.get("done"):
            q["progress"] = min(int(q.get("target", 1)), int(q.get("progress", 0)) + int(amount))
            if q["progress"] >= int(q.get("target", 1)):
                q["done"] = True
                completed.append(q)
            changed = True
    if changed:
        _save_json_file(DAILY_QUESTS_FILE, data)
    if reward_callback:
        for q in completed:
            reward_callback(int(q.get("reward", 0)), q.get("title", "Задание"))
    return completed


def write_diagnostics(game):
    payload = {
        "version": GAME_VERSION,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "fps": round(game.clock.get_fps(), 1),
        "state": game.state,
        "popup": game.popup,
        "pieces_total": len(getattr(game, "all_pieces", [])),
        "pieces_active": len(getattr(game, "active_pieces", [])),
        "pieces_box": len(getattr(game, "box_pieces", [])),
        "rows": getattr(game, "rows", 0),
        "cols": getattr(game, "cols", 0),
        "mode": getattr(game, "mode", "normal"),
        "theme": getattr(game, "theme_key", "dark"),
        "save_dir": os.path.abspath(SAVE_SLOTS_DIR),
        "records_file": os.path.abspath(RECORDS_FILE),
        "settings_file": os.path.abspath(SETTINGS_FILE),
        "last_error": getattr(game, "error_message", ""),
    }
    _save_json_file(DIAGNOSTICS_LOG, payload)
    return payload


def create_default_assets_file():
    if os.path.exists(ASSETS_FILE):
        return
    data = {
        "version": GAME_VERSION,
        "images_dir": IMAGES_DIR,
        "sounds_dir": SOUNDS_DIR,
        "campaign_levels": CAMPAIGN_LEVELS,
        "themes": list(THEMES.keys()),
        "note": "Этот файл можно использовать как список ресурсов и уровней без изменения кода игры.",
    }
    _save_json_file(ASSETS_FILE, data)


class DeluxeGame(EnhancedGame):
    def __init__(self):
        create_default_assets_file()
        self.paused = False
        self.pause_started_ticks = 0
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 40
        self.board_pan_x = 0
        self.board_pan_y = 0
        self.view_zoom = 1.0
        self.middle_drag = False
        self.last_mouse_pos = (0, 0)
        self.box_anim_until = 0
        self.snap_effects = []
        self.warning_shake_until = 0
        self.current_save_slot = 1
        super().__init__()
        self.settings.setdefault("launcher_seen", True)
        self.save_settings()

    def save_settings(self):
        super().save_settings()
        self.settings.update({
            "board_pan_x": getattr(self, "board_pan_x", 0),
            "board_pan_y": getattr(self, "board_pan_y", 0),
            "view_zoom": getattr(self, "view_zoom", 1.0),
        })
        save_settings_dict(self.settings)

    def elapsed_seconds(self):
        if getattr(self, "paused", False):
            return int(getattr(self, "paused_elapsed", self.loaded_elapsed))
        return super().elapsed_seconds()

    def pause_game(self):
        if self.state != "PUZZLE" or self.is_victory or self.lost_by_time:
            return
        self.paused = True
        self.paused_elapsed = super().elapsed_seconds()
        self.pause_started_ticks = pygame.time.get_ticks()
        self.popup = "pause"

    def resume_game(self):
        if not self.paused:
            return
        self.loaded_elapsed = int(getattr(self, "paused_elapsed", self.loaded_elapsed))
        self.start_ticks = pygame.time.get_ticks()
        self.paused = False
        self.popup = None

    def center_view(self):
        dx, dy = -self.board_pan_x, -self.board_pan_y
        self.apply_pan(dx, dy)
        self.board_pan_x = 0
        self.board_pan_y = 0
        self.view_zoom = 1.0
        self.save_settings()

    def apply_pan(self, dx, dy):
        global board_x, board_y
        board_x += int(dx)
        board_y += int(dy)
        self.board_pan_x += int(dx)
        self.board_pan_y += int(dy)
        for p in self.all_pieces:
            if p.is_locked:
                p.correct_pos = (p.correct_pos[0] + int(dx), p.correct_pos[1] + int(dy))
                p.set_origin_pos(p.correct_pos)
            else:
                p.correct_pos = (p.correct_pos[0] + int(dx), p.correct_pos[1] + int(dy))
        self.spawn_slots = [(x + int(dx), y + int(dy)) for x, y in self.spawn_slots]

    def zoom_view(self, direction):
        old = self.view_zoom
        self.view_zoom = max(0.7, min(1.6, self.view_zoom + 0.1 * direction))
        if abs(self.view_zoom - old) > 0.01:
            self.notify_achievement("zoom_user")
            self.hint_message = f"Масштаб рабочего стола: {int(self.view_zoom*100)}%"
            self.hint_until_ticks = pygame.time.get_ticks() + 1200
            self.save_settings()

    def snapshot(self):
        return {
            "moves": self.moves,
            "hints": self.hints_used,
            "penalty": self.hint_penalty_seconds,
            "pieces": [{
                "index": p.index,
                "x": p.get_origin_pos()[0],
                "y": p.get_origin_pos()[1],
                "rotation": p.rotation,
                "locked": p.is_locked,
                "loc": "active" if p in self.active_pieces else "box",
                "group": p.group_id,
            } for p in self.all_pieces + [p for p in self.box_pieces if getattr(p, "is_false", False)]],
        }

    def push_history(self):
        if self.is_victory or self.lost_by_time:
            return
        self.undo_stack.append(self.snapshot())
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def restore_snapshot(self, snap):
        if not snap:
            return
        by_index = {p.index: p for p in self.all_pieces + self.active_pieces + self.box_pieces}
        self.active_pieces = []
        self.box_pieces = []
        self.moves = int(snap.get("moves", self.moves))
        self.hints_used = int(snap.get("hints", self.hints_used))
        self.hint_penalty_seconds = int(snap.get("penalty", self.hint_penalty_seconds))
        seen = set()
        for st in snap.get("pieces", []):
            p = by_index.get(st.get("index"))
            if not p:
                continue
            p.rotation = 0
            p.image = p.base_image.copy()
            p.rect = p.image.get_rect()
            p.mask = pygame.mask.from_surface(p.image)
            for _ in range((int(st.get("rotation", 0)) % 360) // 90):
                p.rotate_clockwise()
            p.set_origin_pos((int(st.get("x", 0)), int(st.get("y", 0))))
            p.is_locked = bool(st.get("locked", False))
            p.group_id = int(st.get("group", p.index))
            if st.get("loc") == "active" or p.is_locked:
                self.active_pieces.append(p)
            else:
                self.box_pieces.append(p)
            seen.add(p.index)
        for p in self.all_pieces:
            if p.index not in seen:
                self.box_pieces.append(p)
        self.selected_piece = None
        self.selected_group = []
        self.group_offsets = []
        self.is_victory = False
        self.victory_saved = False

    def undo(self):
        if not self.undo_stack:
            self.hint_message = "Нечего отменять"
            self.hint_until_ticks = pygame.time.get_ticks() + 1000
            return
        self.redo_stack.append(self.snapshot())
        snap = self.undo_stack.pop()
        self.restore_snapshot(snap)
        self.notify_achievement("undo_user")
        self.sound.play("click")

    def redo(self):
        if not self.redo_stack:
            self.hint_message = "Нечего повторять"
            self.hint_until_ticks = pygame.time.get_ticks() + 1000
            return
        self.undo_stack.append(self.snapshot())
        snap = self.redo_stack.pop()
        self.restore_snapshot(snap)
        self.sound.play("click")

    def save_current_game(self, slot=None):
        if slot is None:
            return super().save_current_game()
        pieces = []
        for piece in self.all_pieces:
            loc = "box"
            if piece in self.active_pieces:
                loc = "active"
            pieces.append({
                "index": piece.index,
                "x": piece.get_origin_pos()[0],
                "y": piece.get_origin_pos()[1],
                "rotation": piece.rotation,
                "locked": piece.is_locked,
                "loc": loc,
                "group": piece.group_id,
            })
        data = {
            "version": GAME_VERSION,
            "saved_at": time.strftime("%Y-%m-%d %H:%M"),
            "rows": self.rows, "cols": self.cols, "mode": self.mode,
            "image": self.current_image_path, "seed": self.puzzle_seed,
            "elapsed": self.elapsed_seconds(), "moves": self.moves,
            "hints": self.hints_used, "penalty": self.hint_penalty_seconds,
            "nickname": self.nickname, "pieces": pieces,
            "pan": [self.board_pan_x, self.board_pan_y],
            "zoom": self.view_zoom,
        }
        ok = _save_json_file(slot_file(slot), data)
        if ok:
            self.current_save_slot = int(slot)
            self.notify_achievement("slot_save")
            update_daily_quest("save_slot", 1, self.reward_for_quest)
        self.hint_message = f"Слот {slot}: сохранено" if ok else "Не удалось сохранить слот"
        self.hint_until_ticks = pygame.time.get_ticks() + 1800
        return ok

    def load_saved_game(self, slot=None):
        if slot is None:
            return super().load_saved_game()
        data = _load_json_file(slot_file(slot), {})
        if not data:
            self.error_message = f"Слот {slot} пуст"
            self.hint_message = self.error_message
            self.hint_until_ticks = pygame.time.get_ticks() + 1500
            return False
        old_pan = (self.board_pan_x, self.board_pan_y)
        self.center_view()
        self.rows = int(data.get("rows", 4)); self.cols = int(data.get("cols", self.rows))
        self.mode = data.get("mode", "normal")
        self.current_image_path = data.get("image")
        self.puzzle_seed = int(data.get("seed", random.randint(1, 999999999)))
        self.state = "PUZZLE"; self.popup = None; self.paused = False
        self.new_puzzle(self.rows, self.cols, image_path_marker=self.current_image_path, keep_seed=True)
        self.loaded_elapsed = int(data.get("elapsed", 0))
        self.moves = int(data.get("moves", 0)); self.hints_used = int(data.get("hints", 0)); self.hint_penalty_seconds = int(data.get("penalty", 0))
        by_index = {p.index: p for p in self.all_pieces}
        self.active_pieces = []; self.box_pieces = []
        for st in data.get("pieces", []):
            piece = by_index.get(st.get("index"))
            if not piece:
                continue
            piece.set_origin_pos((int(st.get("x", piece.correct_pos[0])), int(st.get("y", piece.correct_pos[1]))))
            piece.rotation = 0; piece.image = piece.base_image.copy(); piece.rect = piece.image.get_rect(); piece.mask = pygame.mask.from_surface(piece.image)
            for _ in range((int(st.get("rotation", 0)) % 360) // 90):
                piece.rotate_clockwise()
            piece.is_locked = bool(st.get("locked", False)); piece.group_id = int(st.get("group", piece.index))
            if st.get("loc") == "active" or piece.is_locked:
                self.active_pieces.append(piece)
            else:
                self.box_pieces.append(piece)
        missing = [p for p in self.all_pieces if p not in self.active_pieces and p not in self.box_pieces]
        self.box_pieces.extend(missing)
        self.slot_index = len(self.active_pieces)
        pan = data.get("pan", [0, 0])
        if isinstance(pan, list) and len(pan) == 2:
            self.apply_pan(int(pan[0]), int(pan[1]))
        self.view_zoom = float(data.get("zoom", 1.0))
        self.current_save_slot = int(slot)
        self.undo_stack.clear(); self.redo_stack.clear()
        return True

    def reward_for_quest(self, amount, title):
        self.reward_coins(amount)
        self.notify_achievement("daily_quest")
        self.achievement_toast = f"Задание выполнено: {title} (+{amount}¢)"
        self.achievement_toast_until = pygame.time.get_ticks() + 3500

    def new_puzzle(self, *args, **kwargs):
        super().new_puzzle(*args, **kwargs)
        self.undo_stack = []
        self.redo_stack = []
        self.paused = False
        self.popup = None if self.state == "PUZZLE" else self.popup
        self.snap_effects = []

    def reveal_from_box(self, amount=1):
        self.push_history()
        super().reveal_from_box(amount)
        self.box_anim_until = pygame.time.get_ticks() + 450

    def rotate_selected_or_hovered(self, mx, my):
        self.push_history()
        before = self.snapshot()
        super().rotate_selected_or_hovered(mx, my)
        update_daily_quest("rotate10", 1, self.reward_for_quest)

    def show_piece_hint(self):
        self.push_history()
        super().show_piece_hint()

    def auto_place_piece(self, piece):
        super().auto_place_piece(piece)
        if piece:
            self.snap_effects.append({"x": piece.correct_pos[0]+piece.w//2, "y": piece.correct_pos[1]+piece.h//2, "t": pygame.time.get_ticks()})

    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE and self.state == "PUZZLE":
            if self.paused:
                self.resume_game()
            else:
                self.pause_game()
            return
        if self.state == "PUZZLE" and self.paused:
            if event.key == pygame.K_s:
                self.save_current_game(self.current_save_slot)
            return
        if self.state == "PUZZLE" and not self.is_victory:
            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.undo(); return
            if event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.redo(); return
            if event.key == pygame.K_p:
                self.pause_game(); return
        super().handle_keydown(event)

    def handle_events(self):
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                self.current_w, self.current_h = event.w, event.h
                update_layout_sizes(self.current_w, self.current_h)
                self.new_puzzle()
            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
            if event.type == pygame.MOUSEWHEEL and self.state == "PUZZLE" and not self.paused:
                self.zoom_view(event.y)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2 and self.state == "PUZZLE":
                self.middle_drag = True; self.last_mouse_pos = event.pos
            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                self.middle_drag = False; self.save_settings()
            if event.type == pygame.MOUSEMOTION and self.middle_drag and self.state == "PUZZLE":
                dx = event.pos[0] - self.last_mouse_pos[0]; dy = event.pos[1] - self.last_mouse_pos[1]
                self.last_mouse_pos = event.pos
                self.apply_pan(dx, dy)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse_down(mx, my)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.right_click_rotate and not self.paused:
                self.rotate_selected_or_hovered(mx, my)
            if event.type == pygame.MOUSEMOTION and self.dragging_volume:
                self.set_volume_from_mouse(event.pos[0])
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.handle_mouse_up()

    def handle_mouse_down(self, mx, my):
        if self.popup == "pause":
            self.handle_pause_click(mx, my); return
        if self.popup in ("slots", "album", "quests", "diagnostics"):
            self.handle_deluxe_popup_click(mx, my); return
        super().handle_mouse_down(mx, my)

    def handle_puzzle_click(self, mx, my):
        if self.paused:
            return
        if btn_undo.collidepoint(mx, my): self.undo(); return
        if btn_redo.collidepoint(mx, my): self.redo(); return
        if btn_center_view.collidepoint(mx, my): self.center_view(); return
        super().handle_puzzle_click(mx, my)

    def handle_mouse_up(self):
        self.dragging_volume = False
        if self.state != "PUZZLE" or self.paused or not self.selected_piece:
            return
        self.push_history()
        before_locked = sum(1 for p in self.all_pieces if p.is_locked)
        super().handle_mouse_up()
        after_locked = sum(1 for p in self.all_pieces if p.is_locked)
        if after_locked > before_locked:
            update_daily_quest("place20", after_locked - before_locked, self.reward_for_quest)
            self.snap_effects.append({"x": pygame.mouse.get_pos()[0], "y": pygame.mouse.get_pos()[1], "t": pygame.time.get_ticks()})
        elif before_locked == after_locked:
            self.warning_shake_until = pygame.time.get_ticks() + 180

    def handle_menu_click(self, mx, my):
        if self.popup in ("slots", "album", "quests", "diagnostics"):
            self.handle_deluxe_popup_click(mx, my); return
        if btn_album.collidepoint(mx, my): self.popup = "album"; return
        if btn_quests.collidepoint(mx, my): self.popup = "quests"; return
        if btn_diagnostics.collidepoint(mx, my): self.popup = "diagnostics"; write_diagnostics(self); return
        super().handle_menu_click(mx, my)

    def handle_pause_click(self, mx, my):
        rect = pygame.Rect(self.current_w//2-250, self.current_h//2-210, 500, 420)
        self.place_close_button(rect)
        if btn_close_popup.collidepoint(mx, my) or btn_pause_continue.collidepoint(mx, my): self.resume_game(); return
        if btn_pause_menu.collidepoint(mx, my): self.paused=False; self.state="MENU"; self.popup=None; return
        if btn_pause_settings.collidepoint(mx, my): self.popup="settings"; return
        if btn_pause_save.collidepoint(mx, my): self.popup="slots"; return
        for r, slot in save_slot_rects:
            if r.collidepoint(mx, my):
                self.current_save_slot = slot
                self.save_current_game(slot)
                return
        if not rect.collidepoint(mx, my): self.resume_game()

    def handle_deluxe_popup_click(self, mx, my):
        rect = pygame.Rect(self.current_w//2-340, self.current_h//2-235, 680, 470)
        self.place_close_button(rect)
        if btn_close_popup.collidepoint(mx, my) or not rect.collidepoint(mx, my):
            self.popup = "pause" if self.paused else None
            return
        if self.popup == "slots":
            for r, slot in save_slot_rects:
                if r.collidepoint(mx, my):
                    if self.state == "PUZZLE": self.save_current_game(slot)
                    else: self.load_saved_game(slot)
                    return
        if self.popup == "diagnostics":
            write_diagnostics(self)

    def check_victory(self):
        was = self.is_victory
        super().check_victory()
        if self.is_victory and not was:
            add_album_entry(self.current_profile, self.current_image_path, self.rows, self.cols, self.end_seconds, self.moves, self.stars)
            self.notify_achievement("album_first")
            if self.hints_used == 0:
                update_daily_quest("win_no_hint", 1, self.reward_for_quest)
            if self.rows >= 5 and self.cols >= 5:
                update_daily_quest("win_5x5", 1, self.reward_for_quest)
            if self.current_image_path:
                update_daily_quest("use_custom", 1, self.reward_for_quest)

    def update(self):
        if self.paused:
            # Анимации меню паузы продолжаются, но детали и таймер не обновляются.
            for p in self.bg_pieces:
                p["y"] += p["speed"] * 0.25
                if p["y"] > self.current_h + 40:
                    p["y"] = -40; p["x"] = random.randint(0, self.current_w)
            return
        super().update()
        now = pygame.time.get_ticks()
        self.snap_effects = [e for e in self.snap_effects if now - e["t"] < 650]

    def draw_menu(self):
        super().draw_menu()
        if self.popup:
            return
        mx, my = pygame.mouse.get_pos(); t = self.theme
        w = 150; h = 34; y = self.current_h//2 + 178
        btn_album.update(self.current_w//2-235, y, w, h)
        btn_quests.update(self.current_w//2-75, y, w, h)
        btn_diagnostics.update(self.current_w//2+85, y, w, h)
        draw_button(screen, btn_album, "Фотоальбом", self.font_small, t["accent"], t["text"], btn_album.collidepoint(mx,my))
        draw_button(screen, btn_quests, "Задания дня", self.font_small, t["success"], t["text"], btn_quests.collidepoint(mx,my))
        draw_button(screen, btn_diagnostics, "Диагностика", self.font_small, t["border"], t["text"], btn_diagnostics.collidepoint(mx,my))

    def draw_puzzle(self):
        super().draw_puzzle()
        self.draw_deluxe_game_ui()
        if self.paused or self.popup == "pause":
            self.draw_pause_popup()
        elif self.popup == "slots":
            self.draw_slots_popup()
        elif self.popup == "album":
            self.draw_album_popup()
        elif self.popup == "quests":
            self.draw_quests_popup()
        elif self.popup == "diagnostics":
            self.draw_diagnostics_popup()

    def draw_deluxe_game_ui(self):
        mx, my = pygame.mouse.get_pos(); t = self.theme
        # Дополнительные кнопки удобства над нижней панелью.
        y = self.current_h - 155
        btn_undo.update(board_x + 500, y, 76, 28)
        btn_redo.update(board_x + 582, y, 76, 28)
        btn_center_view.update(board_x + 664, y, 104, 28)
        draw_button(screen, btn_undo, "Undo", self.font_small, t["border"], t["text"], btn_undo.collidepoint(mx,my))
        draw_button(screen, btn_redo, "Redo", self.font_small, t["border"], t["text"], btn_redo.collidepoint(mx,my))
        draw_button(screen, btn_center_view, "Центр", self.font_small, t["orange"], t["text"], btn_center_view.collidepoint(mx,my))
        zoom_label = self.font_small.render(f"Масштаб: {int(self.view_zoom*100)}% | колесо — масштаб, средняя кнопка — двигать стол", True, t["border"])
        screen.blit(zoom_label, (board_x, max(5, board_y - 22)))
        self.draw_minimap()
        self.draw_snap_effects()

    def draw_minimap(self):
        t = self.theme
        mini = pygame.Rect(self.current_w - 178, self.current_h - 150, 158, 118)
        pygame.draw.rect(screen, t["panel"], mini, border_radius=8)
        pygame.draw.rect(screen, t["border"], mini, 2, border_radius=8)
        pad = 10
        bx = mini.left + pad; by = mini.top + pad
        bw = mini.w - pad*2; bh = mini.h - pad*2 - 18
        pygame.draw.rect(screen, t["bg"], (bx, by, bw, bh), border_radius=5)
        for p in self.all_pieces:
            x = bx + int((p.correct_pos[0] - board_x) / max(1, board_w) * bw)
            y = by + int((p.correct_pos[1] - board_y) / max(1, board_h) * bh)
            col = t["success"] if p.is_locked else (t["warning"] if p in self.active_pieces else t["border"])
            pygame.draw.rect(screen, col, (x, y, max(2, bw//max(1,self.cols)//2), max(2, bh//max(1,self.rows)//2)))
        label = self.font_small.render("Мини-карта", True, t["text"])
        screen.blit(label, label.get_rect(centerx=mini.centerx, bottom=mini.bottom-5))

    def draw_snap_effects(self):
        now = pygame.time.get_ticks(); t = self.theme
        for e in self.snap_effects:
            age = now - e["t"]
            radius = 10 + age // 20
            alpha = max(0, 180 - age // 4)
            surf = pygame.Surface((radius*2+4, radius*2+4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*t["success"], alpha), (radius+2, radius+2), radius, 3)
            screen.blit(surf, (e["x"]-radius-2, e["y"]-radius-2))

    def draw_box(self):
        # Переопределять старую коробку сложно, поэтому добавляем поверх красивую анимацию крышки.
        pass

    def draw_pause_popup(self):
        global save_slot_rects
        mx, my = pygame.mouse.get_pos(); t = self.theme
        rect = pygame.Rect(self.current_w//2-250, self.current_h//2-210, 500, 420)
        self.draw_popup_base(rect, "ПАУЗА")
        draw_text_center("Таймер остановлен", self.font_btn, t["text"], screen, rect.centerx, rect.top+58)
        btn_pause_continue.update(rect.centerx-105, rect.top+86, 210, 36)
        btn_pause_save.update(rect.centerx-105, rect.top+130, 210, 34)
        btn_pause_settings.update(rect.centerx-105, rect.top+172, 210, 34)
        btn_pause_menu.update(rect.centerx-105, rect.top+214, 210, 34)
        draw_button(screen, btn_pause_continue, "Продолжить", self.font_btn, t["success"], t["text"], btn_pause_continue.collidepoint(mx,my))
        draw_button(screen, btn_pause_save, "Слоты сохранений", self.font_btn, t["accent"], t["text"], btn_pause_save.collidepoint(mx,my))
        draw_button(screen, btn_pause_settings, "Настройки", self.font_btn, t["border"], t["text"], btn_pause_settings.collidepoint(mx,my))
        draw_button(screen, btn_pause_menu, "В меню", self.font_btn, t["danger"], t["text"], btn_pause_menu.collidepoint(mx,my))
        save_slot_rects = []
        y = rect.top + 270
        for i in range(1, 4):
            r = pygame.Rect(rect.left+34+(i-1)*150, y, 132, 80); save_slot_rects.append((r, i))
            info = load_slot_info(i)
            pygame.draw.rect(screen, t["panel"], r, border_radius=8); pygame.draw.rect(screen, t["warning"] if i==self.current_save_slot else t["border"], r, 2, border_radius=8)
            screen.blit(self.font_btn.render(f"Слот {i}", True, t["text"]), (r.left+10, r.top+8))
            text = "пусто" if not info else f"{info['rows']}x{info['cols']} {info['progress']}%"
            screen.blit(self.font_small.render(text, True, t["border"]), (r.left+10, r.top+34))
            screen.blit(self.font_small.render("клик — сохранить", True, t["warning"]), (r.left+10, r.top+56))

    def draw_slots_popup(self):
        global save_slot_rects
        mx, my = pygame.mouse.get_pos(); t = self.theme
        rect = pygame.Rect(self.current_w//2-340, self.current_h//2-235, 680, 470)
        self.draw_popup_base(rect, "СЛОТЫ СОХРАНЕНИЯ")
        save_slot_rects = []
        for i in range(1, 6):
            x = rect.left + 42 + ((i-1) % 2) * 310
            y = rect.top + 70 + ((i-1) // 2) * 112
            r = pygame.Rect(x, y, 280, 86); save_slot_rects.append((r, i))
            info = load_slot_info(i)
            pygame.draw.rect(screen, t["panel"], r, border_radius=10); pygame.draw.rect(screen, t["success"] if info else t["border"], r, 2, border_radius=10)
            screen.blit(self.font_btn.render(f"Слот {i}", True, t["text"]), (r.left+14, r.top+10))
            if info:
                lines = [f"{info['rows']}x{info['cols']} — {mode_title(info['mode'])}", f"{format_time(info['elapsed'])}, прогресс {info['progress']}%", info.get("date", "")]
            else:
                lines = ["Пустой слот", "Клик — сохранить текущую игру" if self.state=="PUZZLE" else "", ""]
            for j, line in enumerate(lines):
                screen.blit(self.font_small.render(line, True, t["border"]), (r.left+14, r.top+34+j*16))

    def draw_album_popup(self):
        t = self.theme
        rect = pygame.Rect(self.current_w//2-340, self.current_h//2-235, 680, 470)
        self.draw_popup_base(rect, "ФОТОАЛЬБОМ СОБРАННЫХ ПАЗЛОВ")
        album = _load_json_file(ALBUM_FILE, [])
        if not album:
            draw_text_center("Пока нет собранных пазлов", self.font_btn, t["text"], screen, rect.centerx, rect.centery)
            return
        y = rect.top + 68
        for entry in list(reversed(album))[:9]:
            row = pygame.Rect(rect.left+36, y, rect.width-72, 36)
            pygame.draw.rect(screen, t["panel"], row, border_radius=6)
            title = f"{entry.get('profile','Игрок')} — {entry.get('rows')}x{entry.get('cols')} — {format_time(entry.get('time',0))} — {'★'*int(entry.get('stars',0))}"
            screen.blit(self.font_small.render(title, True, t["text"]), (row.left+12, row.top+5))
            screen.blit(self.font_small.render(str(entry.get("date", "")), True, t["border"]), (row.left+12, row.top+20))
            y += 42

    def draw_quests_popup(self):
        t = self.theme
        rect = pygame.Rect(self.current_w//2-340, self.current_h//2-235, 680, 470)
        self.draw_popup_base(rect, "ЕЖЕДНЕВНЫЕ ЗАДАНИЯ")
        data = daily_quests_for_today()
        draw_text_center(f"Дата: {data.get('date')}", self.font_btn, t["text"], screen, rect.centerx, rect.top+58)
        y = rect.top + 94
        for q in data.get("quests", []):
            r = pygame.Rect(rect.left+48, y, rect.width-96, 70)
            pygame.draw.rect(screen, t["panel"], r, border_radius=10)
            pygame.draw.rect(screen, t["success"] if q.get("done") else t["border"], r, 2, border_radius=10)
            screen.blit(self.font_btn.render(("✓ " if q.get("done") else "• ") + q.get("title", ""), True, t["text"]), (r.left+16, r.top+10))
            prog = f"Прогресс: {q.get('progress',0)}/{q.get('target',1)}   Награда: {q.get('reward',0)} монет"
            screen.blit(self.font_small.render(prog, True, t["warning"]), (r.left+16, r.top+40))
            y += 84

    def draw_diagnostics_popup(self):
        t = self.theme
        rect = pygame.Rect(self.current_w//2-340, self.current_h//2-235, 680, 470)
        self.draw_popup_base(rect, "ДИАГНОСТИКА")
        data = write_diagnostics(self)
        lines = [
            f"Версия: {data['version']}", f"FPS: {data['fps']}", f"Состояние: {data['state']} / {data['popup']}",
            f"Деталей: всего {data['pieces_total']}, активных {data['pieces_active']}, в коробке {data['pieces_box']}",
            f"Пазл: {data['rows']}x{data['cols']}, режим {data['mode']}", f"Тема: {data['theme']}",
            f"Папка сохранений: {data['save_dir']}", f"Файл настроек: {data['settings_file']}",
            f"Последняя ошибка: {data['last_error'] or 'нет'}", "Данные также записаны в diagnostics.json",
        ]
        y = rect.top + 70
        for line in lines:
            screen.blit(self.font_small.render(line, True, t["text"]), (rect.left+44, y)); y += 28

    def draw_victory_popup(self):
        super().draw_victory_popup()
        t = self.theme
        note = self.font_small.render("Картинка добавлена в фотоальбом. Награды и задания обновлены.", True, t["warning"])
        screen.blit(note, note.get_rect(centerx=self.current_w//2, centery=self.current_h//2+118))

    def draw_box_beauty_overlay(self):
        # Более красивая корзина/коробка: многослойный корпус, открывающаяся крышка,
        # ручка, внутренние тени и яркие пазлики внутри.
        t = self.theme
        now = pygame.time.get_ticks()
        mx, my = pygame.mouse.get_pos()
        hovered = btn_box.collidepoint(mx, my)
        pulse = 1 if now < self.box_anim_until else 0
        lid_lift = 16 if pulse else (4 if hovered else 0)

        x, y, w, h = btn_box.x, btn_box.y, btn_box.w, btn_box.h
        body = pygame.Rect(x + 6, y + 18, w - 12, h - 22)
        inner = pygame.Rect(body.x + 10, body.y + 12, body.w - 20, body.h - 34)
        lid = pygame.Rect(x - 2, y - 6 - lid_lift, w + 4, 28)

        # Тень под всей коробкой.
        shadow = pygame.Surface((w + 28, h + 28), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 80), (8, 12, w + 4, h + 6), border_radius=16)
        screen.blit(shadow, (x - 12, y - 2))

        # Корпус коробки.
        body_dark = (92, 48, 18)
        body_mid = (130, 72, 32)
        body_light = (162, 95, 45) if hovered else (150, 86, 40)
        pygame.draw.rect(screen, body_dark, body, border_radius=14)
        inset = body.inflate(-4, -4)
        pygame.draw.rect(screen, body_mid, inset, border_radius=12)
        main_panel = pygame.Rect(inset.x + 2, inset.y + 2, inset.w - 4, inset.h - 4)
        pygame.draw.rect(screen, body_light, main_panel, border_radius=11)

        # Блик слева и тонкая нижняя кромка.
        pygame.draw.line(screen, (210, 145, 84), (main_panel.left + 8, main_panel.top + 10), (main_panel.left + 8, main_panel.bottom - 10), 3)
        pygame.draw.line(screen, (86, 45, 20), (main_panel.left + 12, main_panel.bottom - 8), (main_panel.right - 12, main_panel.bottom - 8), 3)

        # Внутреннее углубление.
        inner_shadow = pygame.Surface((inner.w, inner.h), pygame.SRCALPHA)
        pygame.draw.rect(inner_shadow, (55, 28, 10, 160), inner_shadow.get_rect(), border_radius=10)
        screen.blit(inner_shadow, inner.topleft)
        inner_fill = inner.inflate(-4, -4)
        pygame.draw.rect(screen, (98, 54, 24), inner_fill, border_radius=8)

        # Декоративные "планки" на корпусе.
        strap_y1 = body.top + 18
        strap_y2 = body.top + 42
        for sy in (strap_y1, strap_y2):
            pygame.draw.line(screen, (110, 62, 28), (body.left + 10, sy), (body.right - 10, sy), 2)

        # Крышка.
        lid_shadow = pygame.Surface((lid.w + 8, lid.h + 8), pygame.SRCALPHA)
        pygame.draw.rect(lid_shadow, (0, 0, 0, 70), (4, 4, lid.w, lid.h), border_radius=10)
        screen.blit(lid_shadow, (lid.x - 4, lid.y - 1))
        pygame.draw.rect(screen, (98, 54, 24), lid, border_radius=10)
        lid_inner = lid.inflate(-4, -4)
        pygame.draw.rect(screen, (186, 116, 58) if hovered else (174, 106, 52), lid_inner, border_radius=9)
        pygame.draw.line(screen, (230, 170, 100), (lid_inner.left + 10, lid_inner.top + 6), (lid_inner.right - 10, lid_inner.top + 6), 2)
        pygame.draw.rect(screen, (78, 44, 18), lid, 2, border_radius=10)

        # Ручка на крышке.
        handle_outer = pygame.Rect(lid.centerx - 18, lid.centery - 4, 36, 10)
        pygame.draw.rect(screen, (84, 50, 22), handle_outer, border_radius=5)
        handle_inner = handle_outer.inflate(-6, -4)
        pygame.draw.rect(screen, (230, 186, 94), handle_inner, border_radius=4)

        # Металлические петли.
        for hx in (lid.left + 20, lid.right - 32):
            hinge = pygame.Rect(hx, lid.bottom - 4, 12, 8)
            pygame.draw.rect(screen, (213, 177, 72), hinge, border_radius=3)
            pygame.draw.rect(screen, (98, 76, 18), hinge, 1, border_radius=3)

        # Яркие пазлики внутри.
        rnd = random.Random(len(self.box_pieces) * 17 + self.rows * 31 + self.cols)
        colors = [t["accent"], t["success"], t["warning"], t["orange"], (170, 106, 220)]
        count = min(12, max(3, len(self.box_pieces)))
        for i in range(count):
            pw = rnd.randint(14, 18)
            ph = rnd.randint(10, 13)
            px = inner_fill.left + rnd.randint(4, max(5, inner_fill.w - pw - 8))
            py = inner_fill.top + rnd.randint(4, max(5, inner_fill.h - ph - 8))
            color = colors[i % len(colors)]
            piece = pygame.Rect(px, py, pw, ph)
            pygame.draw.rect(screen, color, piece, border_radius=3)
            tab_r = max(3, ph // 3)
            pygame.draw.circle(screen, color, (piece.centerx, piece.top + 1), tab_r)
            pygame.draw.circle(screen, inner_fill and (98, 54, 24), (piece.left + 1, piece.centery), max(2, tab_r - 1))
            pygame.draw.rect(screen, (35, 35, 35), piece, 1, border_radius=3)

        # Табличка внизу с количеством деталей.
        plaque = pygame.Rect(body.left + 12, body.bottom - 28, body.w - 24, 22)
        pygame.draw.rect(screen, (73, 40, 19), plaque, border_radius=7)
        pygame.draw.rect(screen, (226, 182, 74), plaque, 1, border_radius=7)
        count_text = self.font_small.render(f"{len(self.box_pieces)} деталей", True, (255, 240, 210))
        screen.blit(count_text, count_text.get_rect(center=plaque.center))

        # Эффект подсветки во время выдачи пазлика.
        if pulse:
            glow = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*t["warning"], 85), glow.get_rect(), border_radius=16)
            screen.blit(glow, (x - 12, y - 12))

    def draw_extra_puzzle_ui(self):
        super().draw_extra_puzzle_ui()
        self.draw_box_beauty_overlay()


# =========================================================
# HOTFIX: отдельные рабочие экраны для фотоальбома, заданий дня и диагностики
# =========================================================
class FixedDeluxeGame(DeluxeGame):
    """Исправляет наложение новых кнопок меню и делает три окна настоящими модальными экранами."""

    def layout_deluxe_menu_buttons(self):
        # Уносим кнопки на отдельную строку ниже кнопок кампании/магазина.
        w, h = 150, 32
        y = min(self.current_h - 82, self.current_h // 2 + 224)
        gap = 12
        total = w * 3 + gap * 2
        left = self.current_w // 2 - total // 2
        btn_album.update(left, y, w, h)
        btn_quests.update(left + w + gap, y, w, h)
        btn_diagnostics.update(left + (w + gap) * 2, y, w, h)

    def handle_mouse_down(self, mx, my):
        # Модальные окна должны получать клик первыми независимо от состояния игры.
        if self.popup in ("album", "quests", "diagnostics"):
            self.handle_deluxe_modal_click(mx, my)
            return
        super().handle_mouse_down(mx, my)

    def handle_menu_click(self, mx, my):
        if self.popup in ("album", "quests", "diagnostics"):
            self.handle_deluxe_modal_click(mx, my)
            return

        if not self.popup:
            self.layout_deluxe_menu_buttons()
            if btn_album.collidepoint(mx, my):
                self.popup = "album"
                return
            if btn_quests.collidepoint(mx, my):
                self.popup = "quests"
                return
            if btn_diagnostics.collidepoint(mx, my):
                self.popup = "diagnostics"
                write_diagnostics(self)
                return

        super().handle_menu_click(mx, my)

    def handle_deluxe_modal_click(self, mx, my):
        rect = self.deluxe_modal_rect()
        self.place_close_button(rect)
        if btn_close_popup.collidepoint(mx, my) or not rect.collidepoint(mx, my):
            self.popup = "pause" if getattr(self, "paused", False) else None
            return
        # Диагностика обновляется по клику внутри окна, чтобы было понятно, что экран живой.
        if self.popup == "diagnostics":
            write_diagnostics(self)
            self.hint_message = "Диагностика обновлена"
            self.hint_until_ticks = pygame.time.get_ticks() + 1200

    def deluxe_modal_rect(self):
        w = min(760, self.current_w - 70)
        h = min(520, self.current_h - 70)
        return pygame.Rect(self.current_w // 2 - w // 2, self.current_h // 2 - h // 2, w, h)

    def draw_menu(self):
        # Важно: не вызываем DeluxeGame.draw_menu(), потому что он уже рисует
        # старую строку кнопок "Фотоальбом / Задания дня / Диагностика"
        # поверх кнопок кампании. Рисуем базовое меню и нужные окна вручную.
        Game.draw_menu(self)

        # Базовые окна уже полностью нарисованы в Game.draw_menu().
        if self.popup in ("difficulty", "records", "settings", "achievements", "gallery"):
            return

        # Окна расширенной версии EnhancedGame.
        if self.popup == "campaign":
            self.draw_campaign_popup()
            return
        if self.popup == "daily":
            self.draw_daily_popup()
            return
        if self.popup == "shop":
            self.draw_shop_popup()
            return
        if self.popup == "profiles":
            self.draw_profiles_popup()
            return
        if self.popup == "stats":
            self.draw_stats_popup()
            return
        if self.popup == "advanced_options":
            self.draw_advanced_options_popup()
            return

        # Наши три окна рисуются как модальные экраны поверх меню.
        if self.popup == "album":
            self.draw_album_popup()
            return
        if self.popup == "quests":
            self.draw_quests_popup()
            return
        if self.popup == "diagnostics":
            self.draw_diagnostics_popup()
            return

        # Когда других окон нет: первая строка — кампания/магазин/статистика,
        # вторая строка — фотоальбом/задания/диагностика.
        if not self.popup:
            self.draw_extra_menu_buttons()
            self.draw_deluxe_menu_buttons_fixed()

    def draw_deluxe_menu_buttons_fixed(self):
        self.layout_deluxe_menu_buttons()
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        draw_button(screen, btn_album, "Фотоальбом", self.font_small, t["accent"], t["text"], btn_album.collidepoint(mx, my))
        draw_button(screen, btn_quests, "Задания дня", self.font_small, t["success"], t["text"], btn_quests.collidepoint(mx, my))
        draw_button(screen, btn_diagnostics, "Диагностика", self.font_small, t["border"], t["text"], btn_diagnostics.collidepoint(mx, my))

    def draw_album_popup(self):
        t = self.theme
        rect = self.deluxe_modal_rect()
        self.draw_popup_base(rect, "ФОТОАЛЬБОМ")

        album = _load_json_file(ALBUM_FILE, [])
        if not isinstance(album, list):
            album = []

        if not album:
            draw_text_center("Пока нет собранных пазлов", self.font_btn, t["text"], screen, rect.centerx, rect.centery - 12)
            draw_text_center("Собери любой пазл — он появится здесь автоматически.", self.font_small, t["border"], screen, rect.centerx, rect.centery + 20)
            return

        header = self.font_small.render("Последние собранные пазлы:", True, t["border"])
        screen.blit(header, (rect.left + 36, rect.top + 58))

        y = rect.top + 88
        max_rows = max(1, (rect.bottom - y - 22) // 42)
        for entry in list(reversed(album))[:max_rows]:
            row = pygame.Rect(rect.left + 32, y, rect.width - 64, 36)
            pygame.draw.rect(screen, t["panel"], row, border_radius=7)
            pygame.draw.rect(screen, t["border"], row, 1, border_radius=7)
            stars = "★" * int(entry.get("stars", 0)) or "—"
            title = f"{entry.get('profile','Игрок')}  |  {entry.get('rows','?')}x{entry.get('cols','?')}  |  {format_time(int(entry.get('time',0)))}  |  {stars}"
            screen.blit(self.font_small.render(title, True, t["text"]), (row.left + 12, row.top + 5))
            screen.blit(self.font_small.render(str(entry.get("date", "")), True, t["border"]), (row.left + 12, row.top + 20))
            y += 42

    def draw_quests_popup(self):
        t = self.theme
        rect = self.deluxe_modal_rect()
        self.draw_popup_base(rect, "ЗАДАНИЯ ДНЯ")
        data = daily_quests_for_today()

        date_text = self.font_btn.render(f"Дата: {data.get('date', '')}", True, t["text"])
        screen.blit(date_text, date_text.get_rect(centerx=rect.centerx, top=rect.top + 54))

        y = rect.top + 92
        quests = data.get("quests", []) if isinstance(data, dict) else []
        if not quests:
            draw_text_center("Задания не найдены. Файл будет создан заново при следующем запуске.", self.font_small, t["text"], screen, rect.centerx, rect.centery)
            return

        for q in quests:
            r = pygame.Rect(rect.left + 42, y, rect.width - 84, 72)
            done = bool(q.get("done"))
            pygame.draw.rect(screen, t["panel"], r, border_radius=10)
            pygame.draw.rect(screen, t["success"] if done else t["border"], r, 2, border_radius=10)
            title = ("✓ " if done else "• ") + str(q.get("title", "Задание"))
            screen.blit(self.font_btn.render(title, True, t["text"]), (r.left + 16, r.top + 10))
            target = max(1, int(q.get("target", 1)))
            progress = min(target, int(q.get("progress", 0)))
            reward = int(q.get("reward", 0))
            info = f"Прогресс: {progress}/{target}     Награда: {reward} монет"
            screen.blit(self.font_small.render(info, True, t["warning"]), (r.left + 16, r.top + 42))

            bar = pygame.Rect(r.right - 190, r.top + 43, 150, 12)
            pygame.draw.rect(screen, t["bg"], bar, border_radius=6)
            fill = pygame.Rect(bar.left, bar.top, int(bar.w * progress / target), bar.h)
            pygame.draw.rect(screen, t["success"] if done else t["accent"], fill, border_radius=6)
            y += 84
            if y + 80 > rect.bottom - 20:
                break

    def draw_diagnostics_popup(self):
        t = self.theme
        rect = self.deluxe_modal_rect()
        self.draw_popup_base(rect, "ДИАГНОСТИКА")
        data = write_diagnostics(self)

        lines = [
            f"Версия: {data.get('version', GAME_VERSION)}",
            f"FPS: {data.get('fps', 0)}",
            f"Состояние: {data.get('state', '')} / окно: {data.get('popup', '')}",
            f"Деталей: всего {data.get('pieces_total', 0)}, активных {data.get('pieces_active', 0)}, в коробке {data.get('pieces_box', 0)}",
            f"Пазл: {data.get('rows', 0)}x{data.get('cols', 0)}, режим: {data.get('mode', '')}",
            f"Тема: {data.get('theme', '')}",
            f"Папка сохранений: {data.get('save_dir', '')}",
            f"Файл настроек: {data.get('settings_file', '')}",
            f"Последняя ошибка: {data.get('last_error') or 'нет'}",
            "Клик внутри окна обновляет диагностику.",
            "Данные записываются в diagnostics.json.",
        ]
        y = rect.top + 70
        for line in lines:
            if y > rect.bottom - 30:
                break
            screen.blit(self.font_small.render(line, True, t["text"]), (rect.left + 42, y))
            y += 28


class SimpleModesGame(FixedDeluxeGame):
    """Версия без дополнительных игровых режимов: остаётся только обычный пазл."""

    def __init__(self):
        super().__init__()
        self.disable_extra_modes()

    def disable_extra_modes(self):
        self.mode = "normal"
        self.no_picture_mode = False
        self.mirror_mode = False
        self.false_pieces_mode = False
        self.silhouette_mode = True
        if hasattr(self, "settings"):
            self.settings["no_picture_mode"] = False
            self.settings["mirror_mode"] = False
            self.settings["false_pieces_mode"] = False
            self.settings["mode"] = "normal"

    def cycle_mode(self):
        self.mode = "normal"
        self.hint_message = "Дополнительные режимы убраны. Доступен обычный режим."
        self.hint_until_ticks = pygame.time.get_ticks() + 1400

    def mode_allows_hints(self):
        return True

    def mode_allows_rotation(self):
        return True

    def mode_shows_grid(self):
        return True

    def save_settings(self):
        super().save_settings()
        self.settings.update({
            "no_picture_mode": False,
            "mirror_mode": False,
            "false_pieces_mode": False,
            "mode": "normal",
        })
        save_settings_dict(self.settings)

    def new_puzzle(self, rows=None, cols=None, image_path_marker="keep", reset_image=False, keep_seed=False):
        self.disable_extra_modes()
        if rows:
            self.rows = rows
            self.cols = cols or rows
        if reset_image:
            self.current_image_path = None
        elif image_path_marker != "keep":
            self.current_image_path = image_path_marker
        if not keep_seed:
            self.puzzle_seed = random.randint(1, 999999999)
        (self.all_pieces, self.active_pieces, self.box_pieces, self.current_board_img, self.spawn_slots, error_message) = create_puzzle_ext(
            self.current_image_path, self.rows, self.cols, self.current_w, self.current_h, self.puzzle_seed,
            mirror=False, no_picture=False, false_count=0)
        self.slot_index = 0
        self.selected_piece = None
        self.is_victory = False
        self.victory_saved = False
        self.moves = 0
        self.hints_used = 0
        self.hint_penalty_seconds = 0
        self.confetti = []
        self.stars = 0
        self.start_ticks = pygame.time.get_ticks()
        self.end_seconds = 0
        self.loaded_elapsed = 0
        self.time_limit = None
        self.lost_by_time = False
        self.hint_piece = None
        self.hint_until_ticks = 0
        self.hint_message = ""
        self.hint_level = 0
        self.last_hint_index = None
        self.selected_group = []
        self.group_offsets = []
        self.error_message = error_message or ""

    def start_campaign_level(self, idx):
        lvl = CAMPAIGN_LEVELS[idx]
        self.active_campaign_level = idx
        self.daily_active = False
        self.mode = "normal"
        self.start_game(lvl["rows"], lvl["cols"])

    def start_daily_puzzle(self):
        images = extended_gallery_images(getattr(self, "extra_folders", [])) or list_gallery_images()
        img = images[abs(hash(today_key())) % len(images)] if images else None
        self.daily_active = True
        self.active_campaign_level = None
        self.mode = "normal"
        size = random.choice([3, 4, 5])
        self.puzzle_seed = abs(hash(today_key())) % 999999999
        self.rows = size
        self.cols = size
        self.current_image_path = img
        self.state = "PUZZLE"
        self.popup = None
        self.new_puzzle(size, size, image_path_marker=img, keep_seed=True)

    def draw_difficulty_popup(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 150, self.current_h // 2 - 135, 300, 320)
        self.draw_popup_base(rect, "НОВАЯ ИГРА")
        draw_text_center("Обычный режим", self.font_small, t["border"], screen, rect.centerx, rect.top + 52)
        draw_button(screen, btn_pop_easy, "Лёгкий (3x3)", self.font_btn, (39, 174, 96), t["text"], btn_pop_easy.collidepoint(mx, my))
        draw_button(screen, btn_pop_medium, "Средний (4x4)", self.font_btn, (52, 152, 219), t["text"], btn_pop_medium.collidepoint(mx, my))
        draw_button(screen, btn_pop_hard, "Сложный (6x6)", self.font_btn, (142, 68, 173), t["text"], btn_pop_hard.collidepoint(mx, my))
        draw_button(screen, btn_custom_minus, "−", self.font_btn, t["danger"], t["text"], btn_custom_minus.collidepoint(mx, my))
        draw_button(screen, btn_custom_start, f"Своя {self.custom_size}x{self.custom_size}", self.font_btn, t["success"], t["text"], btn_custom_start.collidepoint(mx, my))
        draw_button(screen, btn_custom_plus, "+", self.font_btn, t["accent"], t["text"], btn_custom_plus.collidepoint(mx, my))
        draw_button(screen, btn_gallery_open, "Галерея картинок", self.font_btn, t["border"], t["text"], btn_gallery_open.collidepoint(mx, my))
        note = self.font_small.render("Дополнительные режимы отключены.", True, t["border"])
        screen.blit(note, note.get_rect(centerx=rect.centerx, bottom=rect.bottom - 18))

    def handle_menu_click(self, mx, my):
        if self.popup in ("album", "quests", "diagnostics"):
            self.handle_deluxe_modal_click(mx, my)
            return

        if not self.popup:
            self.layout_deluxe_menu_buttons()
            if btn_album.collidepoint(mx, my):
                self.popup = "album"; return
            if btn_quests.collidepoint(mx, my):
                self.popup = "quests"; return
            if btn_diagnostics.collidepoint(mx, my):
                self.popup = "diagnostics"; write_diagnostics(self); return

        if self.popup == "gallery" and btn_import_folder.collidepoint(mx, my):
            root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
            folder = filedialog.askdirectory(title="Папка с картинками")
            root.destroy()
            if folder and folder not in self.extra_folders:
                self.extra_folders.append(folder); self.save_settings()
            return
        if self.popup == "gallery":
            rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my): self.popup = "difficulty"; return
            for r, path in gallery_rects:
                if r.collidepoint(mx, my): self.current_image_path = path; self.start_game(self.rows, self.cols, image_path_marker=path); return
            if not rect.collidepoint(mx, my): self.popup = "difficulty"
            return

        if self.popup in ("campaign", "daily", "shop", "profiles", "stats"):
            self.handle_extra_popup_click(mx, my)
            return
        if self.popup == "advanced_options":
            self.popup = None
            return
        if btn_campaign.collidepoint(mx, my): self.popup = "campaign"; return
        if btn_daily.collidepoint(mx, my): self.popup = "daily"; return
        if btn_shop.collidepoint(mx, my): self.popup = "shop"; return
        if btn_profiles.collidepoint(mx, my): self.popup = "profiles"; return
        if btn_stats.collidepoint(mx, my): self.popup = "stats"; return

        # Базовое меню, но без кнопки смены режима.
        if self.popup == "difficulty":
            rect = pygame.Rect(self.current_w // 2 - 150, self.current_h // 2 - 135, 300, 320)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my): self.popup = None
            elif btn_pop_easy.collidepoint(mx, my): self.mode = "normal"; self.start_game(3, 3)
            elif btn_pop_medium.collidepoint(mx, my): self.mode = "normal"; self.start_game(4, 4)
            elif btn_pop_hard.collidepoint(mx, my): self.mode = "normal"; self.start_game(6, 6)
            elif btn_custom_minus.collidepoint(mx, my): self.custom_size = max(2, self.custom_size - 1)
            elif btn_custom_plus.collidepoint(mx, my): self.custom_size = min(10, self.custom_size + 1)
            elif btn_custom_start.collidepoint(mx, my): self.notify_achievement("custom_size"); self.mode = "normal"; self.start_game(self.custom_size, self.custom_size)
            elif btn_gallery_open.collidepoint(mx, my): self.popup = "gallery"
            elif not rect.collidepoint(mx, my): self.popup = None
            return
        Game.handle_menu_click(self, mx, my)

    def handle_extra_popup_click(self, mx, my):
        if self.popup == "advanced_options":
            self.popup = None
            return
        return super().handle_extra_popup_click(mx, my)

    def draw_menu(self):
        Game.draw_menu(self)
        if self.popup in ("difficulty", "records", "settings", "achievements", "gallery"):
            return
        if self.popup == "campaign": self.draw_campaign_popup(); return
        if self.popup == "daily": self.draw_daily_popup(); return
        if self.popup == "shop": self.draw_shop_popup(); return
        if self.popup == "profiles": self.draw_profiles_popup(); return
        if self.popup == "stats": self.draw_stats_popup(); return
        if self.popup == "album": self.draw_album_popup(); return
        if self.popup == "quests": self.draw_quests_popup(); return
        if self.popup == "diagnostics": self.draw_diagnostics_popup(); return
        if not self.popup:
            self.draw_extra_menu_buttons()
            self.draw_deluxe_menu_buttons_fixed()

    def draw_campaign_popup(self):
        global campaign_rects
        t = self.theme; mx, my = pygame.mouse.get_pos()
        rect = pygame.Rect(self.current_w//2-330, self.current_h//2-230, 660, 460)
        self.draw_popup_base(rect, "КАМПАНИЯ")
        campaign_rects = []
        done = set(self.campaign.get("completed", []))
        y = rect.top + 70
        for i, lvl in enumerate(CAMPAIGN_LEVELS):
            available = i == 0 or (i - 1) in done
            completed = i in done
            r = pygame.Rect(rect.left + 42, y, rect.width - 84, 48)
            if available: campaign_rects.append((r, i))
            pygame.draw.rect(screen, t["panel"] if available else t["bg"], r, border_radius=8)
            pygame.draw.rect(screen, t["success"] if completed else (t["warning"] if available else t["border"]), r, 2, border_radius=8)
            label = ("✓ " if completed else ("▶ " if available else "🔒 ")) + f"{i+1}. {lvl['name']} — {lvl['rows']}x{lvl['cols']}"
            screen.blit(self.font_btn.render(label, True, t["text"] if available else t["border"]), (r.left + 14, r.top + 7))
            screen.blit(self.font_small.render(f"Обычный режим · награда: {lvl['coins']} монет", True, t["border"]), (r.left + 14, r.top + 29))
            y += 58

    def draw_daily_popup(self):
        t = self.theme; mx, my = pygame.mouse.get_pos()
        rect = pygame.Rect(self.current_w//2-330, self.current_h//2-230, 660, 460)
        self.draw_popup_base(rect, "ЕЖЕДНЕВНЫЙ ПАЗЛ")
        d = _load_json_file(DAILY_FILE, {})
        done = d.get(today_key())
        lines = [f"Сегодня: {today_key()}", "Каждый день выбирается новая картинка.", "Режим: обычный.", "За победу дают дополнительную награду +50 монет."]
        if done:
            lines.append(f"Сегодня уже собрано: {done.get('profile','Игрок')} — {format_time(done.get('time',0))}, ★{done.get('stars',0)}")
        for i, line in enumerate(lines):
            screen.blit(self.font_btn.render(line, True, t["text"]), (rect.left + 48, rect.top + 82 + i * 34))
        start = pygame.Rect(rect.centerx - 120, rect.bottom - 74, 240, 42)
        draw_button(screen, start, "Начать пазл дня", self.font_btn, t["success"], t["text"], start.collidepoint(mx, my))


# =========================================================
# CLEAN VERSION: убраны сортировка, лотки и кнопка "Разложить"
# =========================================================
for _removed_achievement in ("sorter", "tray_user"):
    ACHIEVEMENTS.pop(_removed_achievement, None)

class CleanGame(SimpleModesGame):
    """Версия без функций из нижнего блока: Все/Углы/Края/Центр, Разложить и Лотки."""

    def update_extra_puzzle_rects(self):
        # Уводим старые невидимые кнопки за экран, чтобы они не ловили клики.
        for rect in (btn_sort_all, btn_sort_corners, btn_sort_edges, btn_sort_center, btn_arrange):
            rect.update(-10000, -10000, 1, 1)
        for rect in tray_rects:
            rect.update(-10000, -10000, 1, 1)

    def arrange_active_pieces(self):
        # Функция полностью отключена по просьбе пользователя.
        return

    def reveal_from_box(self, amount=1):
        # Обычное доставание деталей из коробки без сортировки и без лотков.
        self.push_history()
        for _ in range(amount):
            if not self.box_pieces or self.slot_index >= len(self.spawn_slots):
                break
            piece = self.box_pieces.pop()
            piece.set_origin_pos(self.spawn_slots[self.slot_index])
            if self.mode_allows_rotation() and not getattr(piece, "is_false", False):
                for _rot in range(random.randint(0, 3)):
                    piece.rotate_clockwise()
            self.active_pieces.append(piece)
            self.slot_index += 1
        self.sound.play("pick")
        self.box_anim_until = pygame.time.get_ticks() + 450

    def handle_puzzle_click(self, mx, my):
        if self.paused:
            return
        if btn_undo.collidepoint(mx, my):
            self.undo(); return
        if btn_redo.collidepoint(mx, my):
            self.redo(); return
        if btn_center_view.collidepoint(mx, my):
            self.center_view(); return
        # Важно: вызываем базовый обработчик игры, минуя EnhancedGame,
        # где были сортировка, лотки и кнопка "Разложить".
        Game.handle_puzzle_click(self, mx, my)

    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE and self.state == "PUZZLE":
            if self.paused:
                self.resume_game()
            else:
                self.pause_game()
            return
        if self.state == "PUZZLE" and self.paused:
            if event.key == pygame.K_s:
                self.save_current_game(self.current_save_slot)
            return
        if self.state == "PUZZLE" and not self.is_victory:
            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.undo(); return
            if event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.redo(); return
            if event.key == pygame.K_p:
                self.pause_game(); return
        # Минует EnhancedGame.handle_keydown, где клавиша A запускала "Разложить".
        Game.handle_keydown(self, event)

    def draw_extra_puzzle_ui(self):
        # Не рисуем старый нижний блок сортировки/лотков/разложить.
        # Оставляем только невидимые вспомогательные эффекты и красивую коробку.
        if getattr(self, "silhouette_mode", True) and self.mode != "hardcore":
            self.draw_silhouette_board()
        self.draw_neighbor_highlights()
        self.draw_box_beauty_overlay()




# =========================================================
# MINIMAL UI VERSION: убраны Undo/Redo/Центр и мини-карта
# =========================================================
class MinimalUIGame(CleanGame):
    """Версия без дополнительных игровых блоков Undo/Redo/Центр и мини-карты."""

    def update_extra_puzzle_rects(self):
        super().update_extra_puzzle_rects()
        # Уводим также кнопки Undo/Redo/Центр за экран.
        for rect in (btn_undo, btn_redo, btn_center_view):
            rect.update(-10000, -10000, 1, 1)

    def handle_puzzle_click(self, mx, my):
        if self.paused:
            return
        # Больше не обрабатываем клики по Undo/Redo/Центр.
        Game.handle_puzzle_click(self, mx, my)

    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE and self.state == "PUZZLE":
            if self.paused:
                self.resume_game()
            else:
                self.pause_game()
            return
        if self.state == "PUZZLE" and self.paused:
            if event.key == pygame.K_s:
                self.save_current_game(self.current_save_slot)
            return
        if self.state == "PUZZLE" and not self.is_victory:
            if event.key == pygame.K_p:
                self.pause_game(); return
            # Ctrl+Z/Ctrl+Y отключены вместе с блоком Undo/Redo.
            if event.key in (pygame.K_z, pygame.K_y) and pygame.key.get_mods() & pygame.KMOD_CTRL:
                return
        Game.handle_keydown(self, event)

    def draw_deluxe_game_ui(self):
        # Не рисуем блок Undo/Redo/Центр, подпись масштаба и мини-карту.
        # Оставляем только эффект правильной установки деталей.
        self.draw_snap_effects()


# =========================================================
# ACTION WINDOW VERSION: нижние игровые кнопки перенесены в отдельное окно
# =========================================================
btn_game_actions = pygame.Rect(0, 0, 1, 1)

class ActionWindowGame(MinimalUIGame):
    """Версия, где игровые кнопки открываются отдельным окном, а не лежат на поле."""

    def hide_action_rects(self):
        for rect in (
            btn_choose, btn_easy, btn_medium, btn_hard, btn_preview,
            btn_back_to_menu, btn_restart, btn_save_game, btn_load_game
        ):
            rect.update(-10000, -10000, 1, 1)

    def layout_action_popup_buttons(self):
        cx, cy = self.current_w // 2, self.current_h // 2
        rect = pygame.Rect(cx - 170, cy - 135, 340, 270)
        self.place_close_button(rect)
        x = rect.left + 50
        y = rect.top + 70
        w1, h1 = 240, 38
        gap = 14

        # Порядок кнопок: Сохранить, Заново, Главное меню.
        btn_save_game.update(x, y, w1, h1)
        btn_restart.update(x, y + (h1 + gap) * 1, w1, h1)
        btn_back_to_menu.update(x, y + (h1 + gap) * 2, w1, h1)

        # Убраны из окна: Открыть картинку, Загрузить, Подсказка и выбор сложности.
        for r in (btn_choose, btn_load_game, btn_preview, btn_easy, btn_medium, btn_hard):
            r.update(-10000, -10000, 1, 1)
        return rect

    def draw_bottom_buttons(self):
        # На игровом экране оставляем две отдельные кнопки: Меню и Подсказка.
        self.hide_action_rects()
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        w, h, gap = 210, 38, 14
        total = w * 2 + gap
        y = self.current_h - 62
        btn_game_actions.update(self.current_w // 2 - total // 2, y, w, h)
        btn_preview.update(btn_game_actions.right + gap, y, w, h)

        draw_button(
            screen, btn_game_actions, "Меню", self.font_btn, t["accent"], t["text"],
            btn_game_actions.collidepoint(mx, my), t["border"]
        )
        draw_button(
            screen, btn_preview, "Подсказка" if self.mode_allows_hints() else "Без подсказок",
            self.font_btn, t["orange"], t["text"],
            btn_preview.collidepoint(mx, my) or pygame.time.get_ticks() <= self.hint_until_ticks
        )

    def draw_action_popup(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        overlay = pygame.Surface((self.current_w, self.current_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 135))
        screen.blit(overlay, (0, 0))
        rect = self.layout_action_popup_buttons()
        pygame.draw.rect(screen, t["panel2"], rect, border_radius=16)
        pygame.draw.rect(screen, t["warning"], rect, 3, border_radius=16)
        draw_text_center("ИГРОВЫЕ ДЕЙСТВИЯ", self.font_win, t["warning"], screen, rect.centerx, rect.top + 34)
        draw_button(screen, btn_close_popup, "×", self.font_btn, t["danger"], t["text"], btn_close_popup.collidepoint(mx, my))

        buttons = [
            (btn_save_game, "Сохранить", t["success"]),
            (btn_restart, "Заново", t["warning"]),
            (btn_back_to_menu, "Главное меню", t["danger"]),
        ]
        for r, label, color in buttons:
            draw_button(screen, r, label, self.font_btn, color, t["text"], r.collidepoint(mx, my))

        note = self.font_small.render("Нажми Esc или кликни вне окна, чтобы закрыть", True, t["border"])
        screen.blit(note, note.get_rect(centerx=rect.centerx, bottom=rect.bottom - 18))

    def draw_deluxe_game_ui(self):
        # Сохраняем эффект установки деталей из MinimalUIGame.
        MinimalUIGame.draw_deluxe_game_ui(self)
        if self.popup == "game_actions":
            self.draw_action_popup()

    def handle_puzzle_click(self, mx, my):
        if self.paused:
            return

        if self.popup == "game_actions":
            rect = self.layout_action_popup_buttons()
            if btn_close_popup.collidepoint(mx, my) or not rect.collidepoint(mx, my):
                self.popup = None
                self.hide_action_rects()
                return
            if btn_save_game.collidepoint(mx, my):
                self.save_current_game()
                self.popup = None
            elif btn_restart.collidepoint(mx, my):
                self.popup = None
                self.new_puzzle()
            elif btn_back_to_menu.collidepoint(mx, my):
                self.state = "MENU"
                self.popup = None
            return

        # Подсказка вынесена обратно на игровой экран отдельной кнопкой.
        if btn_preview.collidepoint(mx, my):
            self.show_piece_hint()
            return

        # Открытие отдельного окна действий.
        if btn_game_actions.collidepoint(mx, my):
            self.popup = "game_actions"
            self.layout_action_popup_buttons()
            return

        # Старые нижние кнопки скрыты и не должны ловить клики.
        self.hide_action_rects()
        Game.handle_puzzle_click(self, mx, my)

    def handle_keydown(self, event):
        if self.state == "PUZZLE" and self.popup == "game_actions" and event.key == pygame.K_ESCAPE:
            self.popup = None
            self.hide_action_rects()
            return
        super().handle_keydown(event)



# =========================================================
# QUICK MENU VERSION: отдельное окно быстрой игры, кампания перенесена в окно 'Новая игра'
# =========================================================
btn_quick_game = pygame.Rect(0, 0, 1, 1)

class QuickMenuGame(ActionWindowGame):
    """Новая структура окна 'Новая игра':
    сначала кнопки 'Быстрая игра', 'Кампания' и 'Галерея картинок'.
    """

    def draw_extra_menu_buttons(self):
        """Главное меню без кнопки 'Кампания'. Кампания теперь в окне 'Новая игра'."""
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        cx = self.current_w // 2
        y = self.current_h // 2 + 180
        w, h, gap = 150, 36, 12
        total = w * 4 + gap * 3
        left = cx - total // 2

        # Уводим кнопку кампании за экран, чтобы она не ловила клики в главном меню.
        btn_campaign.update(-10000, -10000, 1, 1)
        btn_daily.update(left, y, w, h)
        btn_shop.update(left + (w + gap), y, w, h)
        btn_profiles.update(left + (w + gap) * 2, y, w, h)
        btn_stats.update(left + (w + gap) * 3, y, w, h)

        draw_button(screen, btn_daily, "Пазл дня", self.font_small, t["success"], t["text"], btn_daily.collidepoint(mx, my))
        draw_button(screen, btn_shop, f"Магазин ({self.economy.get('coins',0)}¢)", self.font_small, t["orange"], t["text"], btn_shop.collidepoint(mx, my))
        draw_button(screen, btn_profiles, "Профили", self.font_small, t["border"], t["text"], btn_profiles.collidepoint(mx, my))
        draw_button(screen, btn_stats, "Статистика", self.font_small, t["warning"], t["text"], btn_stats.collidepoint(mx, my))

    def quick_menu_rect(self):
        w = min(380, self.current_w - 50)
        h = min(390, self.current_h - 50)
        return pygame.Rect(self.current_w // 2 - w // 2, self.current_h // 2 - h // 2, w, h)

    def layout_quick_menu_buttons(self):
        rect = self.quick_menu_rect()
        self.place_close_button(rect)
        x = rect.left + 50
        y = rect.top + 70
        w, h, gap = rect.width - 100, 38, 12
        btn_pop_easy.update(x, y, w, h)
        btn_pop_medium.update(x, y + (h + gap), w, h)
        btn_pop_hard.update(x, y + (h + gap) * 2, w, h)

        custom_y = y + (h + gap) * 3 + 8
        btn_custom_minus.update(x, custom_y, 54, h)
        btn_custom_start.update(x + 66, custom_y, w - 132, h)
        btn_custom_plus.update(x + w - 54, custom_y, 54, h)

        # В этом окне кампании больше нет: она находится в первом окне 'Новая игра'.
        btn_campaign.update(-10000, -10000, 1, 1)
        return rect

    def draw_difficulty_popup(self):
        """Первое окно новой игры: быстрая игра, кампания и галерея."""
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 170, self.current_h // 2 - 140, 340, 280)
        self.draw_popup_base(rect, "НОВАЯ ИГРА")

        btn_quick_game.update(rect.left + 40, rect.top + 72, rect.width - 80, 42)
        btn_campaign.update(rect.left + 40, rect.top + 126, rect.width - 80, 42)
        btn_gallery_open.update(rect.left + 40, rect.top + 180, rect.width - 80, 42)

        # Уводим старые кнопки сложности из этого окна.
        for r in (btn_pop_easy, btn_pop_medium, btn_pop_hard, btn_custom_minus, btn_custom_start, btn_custom_plus):
            r.update(-10000, -10000, 1, 1)

        draw_button(screen, btn_quick_game, "Быстрая игра", self.font_btn, t["success"], t["text"], btn_quick_game.collidepoint(mx, my))
        draw_button(screen, btn_campaign, "Кампания", self.font_btn, t["accent"], t["text"], btn_campaign.collidepoint(mx, my))
        draw_button(screen, btn_gallery_open, "Галерея картинок", self.font_btn, t["border"], t["text"], btn_gallery_open.collidepoint(mx, my))

    def draw_quick_game_popup(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = self.layout_quick_menu_buttons()
        overlay = pygame.Surface((self.current_w, self.current_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, t["panel2"], rect, border_radius=16)
        pygame.draw.rect(screen, t["warning"], rect, 3, border_radius=16)
        draw_text_center("БЫСТРАЯ ИГРА", self.font_win, t["warning"], screen, rect.centerx, rect.top + 34)
        draw_button(screen, btn_close_popup, "×", self.font_btn, t["danger"], t["text"], btn_close_popup.collidepoint(mx, my))

        draw_button(screen, btn_pop_easy, "Лёгкий (3x3)", self.font_btn, (39, 174, 96), t["text"], btn_pop_easy.collidepoint(mx, my))
        draw_button(screen, btn_pop_medium, "Средний (4x4)", self.font_btn, (52, 152, 219), t["text"], btn_pop_medium.collidepoint(mx, my))
        draw_button(screen, btn_pop_hard, "Сложный (6x6)", self.font_btn, (142, 68, 173), t["text"], btn_pop_hard.collidepoint(mx, my))
        draw_button(screen, btn_custom_minus, "−", self.font_btn, t["danger"], t["text"], btn_custom_minus.collidepoint(mx, my))
        draw_button(screen, btn_custom_start, f"Своя {self.custom_size}x{self.custom_size}", self.font_btn, t["success"], t["text"], btn_custom_start.collidepoint(mx, my))
        draw_button(screen, btn_custom_plus, "+", self.font_btn, t["accent"], t["text"], btn_custom_plus.collidepoint(mx, my))

        note = self.font_small.render("Esc или × — назад", True, t["border"])
        screen.blit(note, note.get_rect(centerx=rect.centerx, bottom=rect.bottom - 14))

    def draw_menu(self):
        # Берём исправленную схему FixedDeluxeGame, но добавляем окно quick_game.
        Game.draw_menu(self)

        if self.popup in ("difficulty", "records", "settings", "achievements", "gallery"):
            return
        if self.popup == "quick_game":
            self.draw_quick_game_popup()
            return
        if self.popup == "campaign":
            self.draw_campaign_popup(); return
        if self.popup == "daily":
            self.draw_daily_popup(); return
        if self.popup == "shop":
            self.draw_shop_popup(); return
        if self.popup == "profiles":
            self.draw_profiles_popup(); return
        if self.popup == "stats":
            self.draw_stats_popup(); return
        if self.popup == "advanced_options":
            self.draw_advanced_options_popup(); return
        if self.popup == "album":
            self.draw_album_popup(); return
        if self.popup == "quests":
            self.draw_quests_popup(); return
        if self.popup == "diagnostics":
            self.draw_diagnostics_popup(); return

        if not self.popup:
            self.draw_extra_menu_buttons()
            self.draw_deluxe_menu_buttons_fixed()

    def handle_menu_click(self, mx, my):
        if self.popup in ("album", "quests", "diagnostics"):
            self.handle_deluxe_modal_click(mx, my)
            return

        if not self.popup:
            self.layout_deluxe_menu_buttons()
            if btn_album.collidepoint(mx, my):
                self.popup = "album"; return
            if btn_quests.collidepoint(mx, my):
                self.popup = "quests"; return
            if btn_diagnostics.collidepoint(mx, my):
                self.popup = "diagnostics"; write_diagnostics(self); return

            # Кнопки главного меню без кампании.
            if btn_daily.collidepoint(mx, my): self.popup = "daily"; return
            if btn_shop.collidepoint(mx, my): self.popup = "shop"; return
            if btn_profiles.collidepoint(mx, my): self.popup = "profiles"; return
            if btn_stats.collidepoint(mx, my): self.popup = "stats"; return

        if self.popup == "gallery" and btn_import_folder.collidepoint(mx, my):
            root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
            folder = filedialog.askdirectory(title="Папка с картинками")
            root.destroy()
            if folder and folder not in self.extra_folders:
                self.extra_folders.append(folder); self.save_settings()
            return

        if self.popup == "gallery":
            rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my):
                self.popup = "difficulty"; return
            for r, path in gallery_rects:
                if r.collidepoint(mx, my):
                    self.current_image_path = path
                    self.start_game(self.rows, self.cols, image_path_marker=path)
                    return
            if not rect.collidepoint(mx, my):
                self.popup = "difficulty"
            return

        if self.popup in ("campaign", "daily", "shop", "profiles", "stats"):
            self.handle_extra_popup_click(mx, my)
            return

        if self.popup == "quick_game":
            rect = self.layout_quick_menu_buttons()
            if btn_close_popup.collidepoint(mx, my) or not rect.collidepoint(mx, my):
                self.popup = "difficulty"
                return
            if btn_pop_easy.collidepoint(mx, my):
                self.mode = "normal"; self.start_game(3, 3); return
            if btn_pop_medium.collidepoint(mx, my):
                self.mode = "normal"; self.start_game(4, 4); return
            if btn_pop_hard.collidepoint(mx, my):
                self.mode = "normal"; self.start_game(6, 6); return
            if btn_custom_minus.collidepoint(mx, my):
                self.custom_size = max(2, self.custom_size - 1); return
            if btn_custom_plus.collidepoint(mx, my):
                self.custom_size = min(10, self.custom_size + 1); return
            if btn_custom_start.collidepoint(mx, my):
                self.notify_achievement("custom_size")
                self.mode = "normal"
                self.start_game(self.custom_size, self.custom_size)
                return
            return

        if self.popup == "difficulty":
            rect = pygame.Rect(self.current_w // 2 - 170, self.current_h // 2 - 140, 340, 280)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my):
                self.popup = None
            elif btn_quick_game.collidepoint(mx, my):
                self.popup = "quick_game"
            elif btn_campaign.collidepoint(mx, my):
                self.popup = "campaign"
            elif btn_gallery_open.collidepoint(mx, my):
                self.popup = "gallery"
            elif not rect.collidepoint(mx, my):
                self.popup = None
            return

        if self.popup == "advanced_options":
            self.popup = None
            return

        # Остальные базовые кнопки меню: Играть, Рекорды, Настройки, Достижения и т.п.
        Game.handle_menu_click(self, mx, my)

    def clear_piece_drag(self):
        """Останавливает перетаскивание, чтобы кнопка подсказки не уводила пазлик под курсор."""
        self.selected_piece = None
        self.selected_group = []
        self.group_offsets = []

    def show_piece_hint(self):
        """Исправленная подсказка: показывает место детали, но не тащит её на кнопку.

        В старых версиях несколько надстроек оставляли target в self.selected_piece.
        После нажатия кнопки "Подсказка" основной update() считал, что игрок всё ещё
        перетаскивает деталь, и переносил её к курсору — прямо на кнопку подсказки.
        """
        super().show_piece_hint()
        self.clear_piece_drag()

    def auto_place_piece(self, piece):
        super().auto_place_piece(piece)
        self.clear_piece_drag()
        if piece:
            piece.set_origin_pos(piece.correct_pos)
            piece.is_locked = True

    def update(self):
        # Защита на случай, если locked-пазлик остался выбранным после автоподсказки.
        if getattr(self, "selected_piece", None) is not None and getattr(self.selected_piece, "is_locked", False):
            self.clear_piece_drag()
        super().update()

    def handle_keydown(self, event):
        if self.state == "MENU" and self.popup == "quick_game" and event.key == pygame.K_ESCAPE:
            self.popup = "difficulty"
            return
        super().handle_keydown(event)




# =========================================================
# NEW GAME MENU UPDATE: пазл дня и продолжение сохранения перенесены в окно "Новая игра"
# =========================================================
class NewGameMenuGame(QuickMenuGame):
    def draw_base_menu_without_continue(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        self.draw_background_animation()

        title = self.font_big.render("ФИГУРНЫЙ ХТТБПТ ", True, t["text"])
        screen.blit(title, title.get_rect(centerx=self.current_w // 2, centery=self.current_h // 2 - 185))
        subtitle = self.font_btn.render("Собирай, ставь рекорды и загружай свои картинки", True, t["warning"])
        screen.blit(subtitle, subtitle.get_rect(centerx=self.current_w // 2, centery=self.current_h // 2 - 145))

        pygame.draw.rect(screen, t["panel"], input_nick_rect, border_radius=6)
        pygame.draw.rect(screen, t["success"] if self.input_active else t["border"], input_nick_rect, 2, border_radius=6)
        nick_text = f"Ник: {self.nickname}" if self.nickname else "Введите ваш ник..."
        draw_text_center(nick_text, self.font_btn, t["text"], screen, input_nick_rect.centerx, input_nick_rect.centery)

        draw_button(screen, btn_menu_play, "ИГРАТЬ", pygame.font.SysFont("Arial", 22, bold=True), t["accent"], t["text"], btn_menu_play.collidepoint(mx, my))
        draw_button(screen, btn_menu_records, "Рекорды", self.font_btn, t["orange"], t["text"], btn_menu_records.collidepoint(mx, my))
        draw_button(screen, btn_menu_settings, "Настройки", self.font_btn, t["border"], t["text"], btn_menu_settings.collidepoint(mx, my))
        draw_button(screen, btn_menu_achievements, "Достижения", self.font_btn, t["success"], t["text"], btn_menu_achievements.collidepoint(mx, my))

        # Кнопка "Продолжить сохранение" больше не рисуется в главном меню.
        btn_continue.update(-10000, -10000, 1, 1)

        hint = self.font_small.render("F11 — полноэкранный режим | ESC — назад", True, t["border"])
        screen.blit(hint, hint.get_rect(centerx=self.current_w // 2, bottom=self.current_h - 18))

    def draw_extra_menu_buttons(self):
        """В главном меню больше нет кнопок 'Кампания' и 'Пазл дня'."""
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        cx = self.current_w // 2
        y = self.current_h // 2 + 180
        btn_campaign.update(-10000, -10000, 1, 1)
        btn_daily.update(-10000, -10000, 1, 1)
        btn_shop.update(cx - 198, y, 126, 36)
        btn_profiles.update(cx - 66, y, 126, 36)
        btn_stats.update(cx + 66, y, 126, 36)
        draw_button(screen, btn_shop, f"Магазин ({self.economy.get('coins',0)}¢)", self.font_small, t["orange"], t["text"], btn_shop.collidepoint(mx, my))
        draw_button(screen, btn_profiles, "Профили", self.font_small, t["border"], t["text"], btn_profiles.collidepoint(mx, my))
        draw_button(screen, btn_stats, "Статистика", self.font_small, t["warning"], t["text"], btn_stats.collidepoint(mx, my))

    def draw_difficulty_popup(self):
        """Окно 'Новая игра': продолжить сохранение, быстрая игра, пазл дня, кампания, галерея."""
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 185, self.current_h // 2 - 190, 370, 380)
        self.draw_popup_base(rect, "НОВАЯ ИГРА")

        x = rect.left + 42
        y = rect.top + 64
        w = rect.width - 84
        h = 42
        gap = 12

        # Новый порядок кнопок:
        # 1) Кампания  2) Быстрая игра  3) Пазл дня  4) Продолжить игру
        btn_campaign.update(x, y, w, h)
        btn_quick_game.update(x, y + (h + gap), w, h)
        btn_daily.update(x, y + (h + gap) * 2, w, h)
        btn_continue.update(x, y + (h + gap) * 3, w, h)
        btn_gallery_open.update(x, y + (h + gap) * 4, w, h)

        # Старые кнопки сложности уводим за экран — они находятся в окне "Быстрая игра".
        for r in (btn_pop_easy, btn_pop_medium, btn_pop_hard, btn_custom_minus, btn_custom_start, btn_custom_plus):
            r.update(-10000, -10000, 1, 1)

        draw_button(screen, btn_campaign, "Кампания", self.font_btn, t["accent"], t["text"], btn_campaign.collidepoint(mx, my))
        draw_button(screen, btn_quick_game, "Быстрая игра", self.font_btn, t["success"], t["text"], btn_quick_game.collidepoint(mx, my))
        draw_button(screen, btn_daily, "Пазл дня", self.font_btn, t["success"], t["text"], btn_daily.collidepoint(mx, my))
        draw_button(screen, btn_continue, "Продолжить игру", self.font_btn, t["warning"], t["text"], btn_continue.collidepoint(mx, my), t["border"])
        draw_button(screen, btn_gallery_open, "Галерея картинок", self.font_btn, t["border"], t["text"], btn_gallery_open.collidepoint(mx, my))

    def draw_menu(self):
        self.draw_base_menu_without_continue()

        if self.popup == "difficulty":
            self.draw_difficulty_popup(); return
        if self.popup == "records":
            self.draw_records_popup(); return
        if self.popup == "settings":
            self.draw_settings_popup(); return
        if self.popup == "achievements":
            self.draw_achievements_popup(); return
        if self.popup == "gallery":
            self.draw_gallery_popup(); return
        if self.popup == "quick_game":
            self.draw_quick_game_popup(); return
        if self.popup == "campaign":
            self.draw_campaign_popup(); return
        if self.popup == "daily":
            self.draw_daily_popup(); return
        if self.popup == "shop":
            self.draw_shop_popup(); return
        if self.popup == "profiles":
            self.draw_profiles_popup(); return
        if self.popup == "stats":
            self.draw_stats_popup(); return
        if self.popup == "advanced_options":
            self.draw_advanced_options_popup(); return
        if self.popup == "album":
            self.draw_album_popup(); return
        if self.popup == "quests":
            self.draw_quests_popup(); return
        if self.popup == "diagnostics":
            self.draw_diagnostics_popup(); return

        if not self.popup:
            self.draw_extra_menu_buttons()
            self.draw_deluxe_menu_buttons_fixed()

    def handle_menu_click(self, mx, my):
        if self.popup in ("album", "quests", "diagnostics"):
            self.handle_deluxe_modal_click(mx, my)
            return

        if not self.popup:
            self.layout_deluxe_menu_buttons()
            if btn_album.collidepoint(mx, my):
                self.popup = "album"; return
            if btn_quests.collidepoint(mx, my):
                self.popup = "quests"; return
            if btn_diagnostics.collidepoint(mx, my):
                self.popup = "diagnostics"; write_diagnostics(self); return

            if btn_shop.collidepoint(mx, my): self.popup = "shop"; return
            if btn_profiles.collidepoint(mx, my): self.popup = "profiles"; return
            if btn_stats.collidepoint(mx, my): self.popup = "stats"; return

            if input_nick_rect.collidepoint(mx, my):
                self.input_active = True; return
            if btn_menu_play.collidepoint(mx, my):
                self.input_active = False; self.popup = "difficulty"; return
            if btn_menu_records.collidepoint(mx, my):
                self.input_active = False; self.popup = "records"; return
            if btn_menu_settings.collidepoint(mx, my):
                self.input_active = False; self.popup = "settings"; return
            if btn_menu_achievements.collidepoint(mx, my):
                self.input_active = False; self.popup = "achievements"; return
            self.input_active = False
            return

        if self.popup == "difficulty":
            rect = pygame.Rect(self.current_w // 2 - 185, self.current_h // 2 - 190, 370, 380)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my):
                self.popup = None; return
            if btn_continue.collidepoint(mx, my):
                self.load_saved_game(); return
            if btn_quick_game.collidepoint(mx, my):
                self.popup = "quick_game"; return
            if btn_daily.collidepoint(mx, my):
                self.popup = "daily"; return
            if btn_campaign.collidepoint(mx, my):
                self.popup = "campaign"; return
            if btn_gallery_open.collidepoint(mx, my):
                self.popup = "gallery"; return
            if not rect.collidepoint(mx, my):
                self.popup = None
            return

        # Для остальных окон используем уже исправленную логику QuickMenuGame.
        super().handle_menu_click(mx, my)

    def handle_keydown(self, event):
        if self.state == "MENU" and self.popup == "difficulty" and event.key == pygame.K_ESCAPE:
            self.popup = None
            return
        super().handle_keydown(event)




# =========================================================
# FINAL UI CLEANUP: убран фотоальбом, диагностика переименована в состояние
# =========================================================
class StateMenuGame(NewGameMenuGame):
    def layout_deluxe_menu_buttons(self):
        """В нижней строке главного меню остаются только 'Задания дня' и 'Состояние'."""
        w, h = 150, 32
        y = min(self.current_h - 82, self.current_h // 2 + 224)
        gap = 12
        total = w * 2 + gap
        left = self.current_w // 2 - total // 2
        btn_album.update(-10000, -10000, 1, 1)
        btn_quests.update(left, y, w, h)
        btn_diagnostics.update(left + w + gap, y, w, h)

    def draw_deluxe_menu_buttons_fixed(self):
        self.layout_deluxe_menu_buttons()
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        draw_button(screen, btn_quests, "Задания дня", self.font_small, t["success"], t["text"], btn_quests.collidepoint(mx, my))
        draw_button(screen, btn_diagnostics, "Состояние", self.font_small, t["border"], t["text"], btn_diagnostics.collidepoint(mx, my))

    def handle_menu_click(self, mx, my):
        if self.popup in ("quests", "diagnostics"):
            self.handle_deluxe_modal_click(mx, my)
            return
        if self.popup == "album":
            self.popup = None
            return

        if not self.popup:
            self.layout_deluxe_menu_buttons()
            if btn_quests.collidepoint(mx, my):
                self.popup = "quests"
                return
            if btn_diagnostics.collidepoint(mx, my):
                self.popup = "diagnostics"
                write_diagnostics(self)
                return

        super().handle_menu_click(mx, my)

    def draw_menu(self):
        self.draw_base_menu_without_continue()

        if self.popup == "difficulty":
            self.draw_difficulty_popup(); return
        if self.popup == "records":
            self.draw_records_popup(); return
        if self.popup == "settings":
            self.draw_settings_popup(); return
        if self.popup == "achievements":
            self.draw_achievements_popup(); return
        if self.popup == "gallery":
            self.draw_gallery_popup(); return
        if self.popup == "quick_game":
            self.draw_quick_game_popup(); return
        if self.popup == "campaign":
            self.draw_campaign_popup(); return
        if self.popup == "daily":
            self.draw_daily_popup(); return
        if self.popup == "shop":
            self.draw_shop_popup(); return
        if self.popup == "profiles":
            self.draw_profiles_popup(); return
        if self.popup == "stats":
            self.draw_stats_popup(); return
        if self.popup == "advanced_options":
            self.draw_advanced_options_popup(); return
        if self.popup == "quests":
            self.draw_quests_popup(); return
        if self.popup == "diagnostics":
            self.draw_diagnostics_popup(); return

        if not self.popup:
            self.draw_extra_menu_buttons()
            self.draw_deluxe_menu_buttons_fixed()

    def draw_diagnostics_popup(self):
        t = self.theme
        rect = self.deluxe_modal_rect()
        self.draw_popup_base(rect, "СОСТОЯНИЕ")
        data = write_diagnostics(self)

        lines = [
            f"Версия: {data.get('version', GAME_VERSION)}",
            f"FPS: {data.get('fps', 0)}",
            f"Состояние: {data.get('state', '')} / окно: {data.get('popup', '')}",
            f"Деталей: всего {data.get('pieces_total', 0)}, активных {data.get('pieces_active', 0)}, в коробке {data.get('pieces_box', 0)}",
            f"Пазл: {data.get('rows', 0)}x{data.get('cols', 0)}, режим: {data.get('mode', '')}",
            f"Тема: {data.get('theme', '')}",
            f"Папка сохранений: {data.get('save_dir', '')}",
            f"Файл настроек: {data.get('settings_file', '')}",
            f"Последняя ошибка: {data.get('last_error') or 'нет'}",
            "Клик внутри окна обновляет состояние.",
            "Данные записываются в diagnostics.json.",
        ]
        y = rect.top + 70
        for line in lines:
            if y > rect.bottom - 30:
                break
            screen.blit(self.font_small.render(line, True, t["text"]), (rect.left + 42, y))
            y += 28


# =========================================================
# PROFILE PROGRESS PATCH: монеты и достижения отдельно для каждого профиля
# =========================================================
PROFILE_PROGRESS_FILE = "profile_progress.json"


def _profile_progress_default():
    return {"profiles": {}}


def load_profile_progress():
    data = _load_json_file(PROFILE_PROGRESS_FILE, _profile_progress_default())
    if not isinstance(data, dict):
        data = _profile_progress_default()
    data.setdefault("profiles", {})
    return data


def save_profile_progress(data):
    if not isinstance(data, dict):
        data = _profile_progress_default()
    data.setdefault("profiles", {})
    _save_json_file(PROFILE_PROGRESS_FILE, data)


class ProfileProgressGame(StateMenuGame):
    """Финальная версия: деньги, купленные темы и достижения хранятся по профилям."""

    def __init__(self):
        super().__init__()
        self.profile_progress = load_profile_progress()
        self.ensure_profile_progress(self.current_profile)
        self.sync_profile_progress_to_game()

    def ensure_profile_progress(self, profile_name):
        profile_name = profile_name or "Игрок"
        self.profile_progress = load_profile_progress()
        profiles = self.profile_progress.setdefault("profiles", {})
        if profile_name not in profiles:
            # Если это самый первый профиль, аккуратно переносим старые общие монеты/достижения.
            old_economy = load_economy()
            old_achievements = load_achievements()
            profiles[profile_name] = {
                "coins": int(old_economy.get("coins", 0)) if len(profiles) == 0 else 0,
                "unlocked_themes": list(old_economy.get("unlocked_themes", FREE_THEMES[:])) if len(profiles) == 0 else FREE_THEMES[:],
                "achievements": dict(old_achievements) if len(profiles) == 0 else {},
            }
        entry = profiles[profile_name]
        entry.setdefault("coins", 0)
        entry.setdefault("unlocked_themes", FREE_THEMES[:])
        entry.setdefault("achievements", {})
        for theme_key in FREE_THEMES:
            if theme_key not in entry["unlocked_themes"]:
                entry["unlocked_themes"].append(theme_key)
        save_profile_progress(self.profile_progress)
        return entry

    def get_profile_entry(self, profile_name=None):
        return self.ensure_profile_progress(profile_name or self.current_profile)

    def sync_profile_progress_to_game(self):
        entry = self.get_profile_entry(self.current_profile)
        self.economy = {
            "coins": int(entry.get("coins", 0)),
            "unlocked_themes": list(entry.get("unlocked_themes", FREE_THEMES[:])),
        }
        if self.theme_key not in self.economy["unlocked_themes"]:
            self.theme_key = self.economy["unlocked_themes"][0] if self.economy["unlocked_themes"] else "dark"
            self.save_settings()

    def save_current_profile_economy(self):
        entry = self.get_profile_entry(self.current_profile)
        entry["coins"] = int(self.economy.get("coins", 0))
        entry["unlocked_themes"] = list(self.economy.get("unlocked_themes", FREE_THEMES[:]))
        for theme_key in FREE_THEMES:
            if theme_key not in entry["unlocked_themes"]:
                entry["unlocked_themes"].append(theme_key)
        save_profile_progress(self.profile_progress)

    def switch_profile(self, profile_name):
        profile_name = (profile_name or "Игрок").strip() or "Игрок"
        self.profiles = load_profiles()
        if profile_name not in self.profiles:
            self.profiles[profile_name] = {"created": time.strftime("%Y-%m-%d %H:%M")}
            _save_json_file(PROFILES_FILE, self.profiles)
        self.current_profile = profile_name
        self.nickname = profile_name
        self.ensure_profile_progress(profile_name)
        self.sync_profile_progress_to_game()
        self.save_settings()
        self.notify_achievement("profile_master")

    def notify_achievement(self, key):
        if key not in ACHIEVEMENTS:
            return
        entry = self.get_profile_entry(self.current_profile)
        achievements = entry.setdefault("achievements", {})
        if achievements.get(key):
            return
        achievements[key] = time.strftime("%Y-%m-%d %H:%M")
        save_profile_progress(self.profile_progress)
        self.achievement_toast = f"Достижение: {ACHIEVEMENTS[key]['title']}"
        self.achievement_toast_until = pygame.time.get_ticks() + 3500

    def reward_coins(self, amount):
        self.sync_profile_progress_to_game()
        self.economy["coins"] = int(self.economy.get("coins", 0)) + int(amount)
        self.save_current_profile_economy()
        if self.economy["coins"] >= 500:
            self.notify_achievement("rich")

    def buy_or_select_theme(self, key):
        self.sync_profile_progress_to_game()
        unlocked = self.economy.setdefault("unlocked_themes", FREE_THEMES[:])
        if key in unlocked:
            self.theme_key = key
            self.save_settings()
            return
        cost = SHOP_THEMES.get(key, 999)
        if int(self.economy.get("coins", 0)) >= cost:
            self.economy["coins"] = int(self.economy.get("coins", 0)) - cost
            unlocked.append(key)
            self.save_current_profile_economy()
            self.theme_key = key
            self.save_settings()
            self.notify_achievement("buyer")
        else:
            self.hint_message = "Не хватает монет у этого профиля"
            self.hint_until_ticks = pygame.time.get_ticks() + 1800

    def next_theme(self):
        self.sync_profile_progress_to_game()
        unlocked = self.economy.get("unlocked_themes", FREE_THEMES[:])
        keys = [k for k in THEMES.keys() if k in unlocked]
        if not keys:
            keys = FREE_THEMES[:]
        self.theme_key = keys[(keys.index(self.theme_key) + 1) % len(keys)] if self.theme_key in keys else keys[0]
        self.save_settings()

    def draw_shop_popup(self):
        global shop_rects
        self.sync_profile_progress_to_game()
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
        self.draw_popup_base(rect, "МАГАЗИН ТЕМ")
        unlocked = self.economy.get("unlocked_themes", FREE_THEMES[:])
        shop_rects = []
        screen.blit(self.font_btn.render(f"Профиль: {self.current_profile}", True, t["text"]), (rect.left + 36, rect.top + 54))
        screen.blit(self.font_btn.render(f"Монеты: {self.economy.get('coins', 0)}", True, t["warning"]), (rect.left + 360, rect.top + 54))
        keys = FREE_THEMES + list(SHOP_THEMES.keys())
        for i, key in enumerate(keys):
            x = rect.left + 36 + (i % 3) * 200
            y = rect.top + 92 + (i // 3) * 112
            r = pygame.Rect(x, y, 180, 86)
            shop_rects.append((r, key))
            th = THEMES[key]
            pygame.draw.rect(screen, th["bg"], r, border_radius=10)
            pygame.draw.rect(screen, t["success"] if key == self.theme_key else t["border"], r, 3, border_radius=10)
            screen.blit(self.font_btn.render(th["name"], True, th["text"]), (r.left + 12, r.top + 10))
            status = "Выбрана" if key == self.theme_key else ("Выбрать" if key in unlocked else f"Купить {SHOP_THEMES.get(key, 0)}¢")
            screen.blit(self.font_small.render(status, True, th["warning"]), (r.left + 12, r.bottom - 26))

    def draw_achievements_popup(self):
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 285, self.current_h // 2 - 205, 570, 410)
        self.draw_popup_base(rect, "ДОСТИЖЕНИЯ")
        entry = self.get_profile_entry(self.current_profile)
        unlocked = entry.setdefault("achievements", {})
        screen.blit(self.font_small.render(f"Профиль: {self.current_profile} · Получено: {sum(1 for k in ACHIEVEMENTS if unlocked.get(k))}/{len(ACHIEVEMENTS)}", True, t["warning"]), (rect.left + 26, rect.top + 48))
        y = rect.top + 76
        for key, info in ACHIEVEMENTS.items():
            if y > rect.bottom - 58:
                break
            got = bool(unlocked.get(key))
            badge_rect = pygame.Rect(rect.left + 26, y, rect.width - 52, 48)
            pygame.draw.rect(screen, t["panel"] if got else t["bg"], badge_rect, border_radius=8)
            pygame.draw.rect(screen, t["success"] if got else t["border"], badge_rect, 2, border_radius=8)
            icon = "✓" if got else "?"
            screen.blit(self.font_win.render(icon, True, t["success"] if got else t["border"]), (badge_rect.left + 14, badge_rect.top + 9))
            screen.blit(self.font_btn.render(info["title"], True, t["text"]), (badge_rect.left + 48, badge_rect.top + 6))
            desc = info["desc"] if not got else f"{info['desc']}  Получено: {unlocked.get(key)}"
            screen.blit(self.font_small.render(desc, True, t["border"]), (badge_rect.left + 48, badge_rect.top + 28))
            y += 56

    def draw_profiles_popup(self):
        global profile_rects
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
        self.draw_popup_base(rect, "ПРОФИЛИ ИГРОКОВ")
        self.profiles = load_profiles()
        profile_rects = []
        y = rect.top + 70
        for name, info in list(self.profiles.items())[:7]:
            entry = self.get_profile_entry(name)
            ach_count = sum(1 for k in ACHIEVEMENTS if entry.get("achievements", {}).get(k))
            r = pygame.Rect(rect.left + 48, y, rect.width - 96, 46)
            profile_rects.append((r, name))
            pygame.draw.rect(screen, t["panel"], r, border_radius=8)
            pygame.draw.rect(screen, t["success"] if name == self.current_profile else t["border"], r, 2, border_radius=8)
            title = ("★ " if name == self.current_profile else "") + name
            screen.blit(self.font_btn.render(title, True, t["text"]), (r.left + 12, r.top + 7))
            meta = f"Монеты: {entry.get('coins', 0)} · Достижения: {ach_count}/{len(ACHIEVEMENTS)}"
            screen.blit(self.font_small.render(meta, True, t["warning"]), (r.left + 300, r.top + 14))
            y += 54
        btn_create_profile.update(rect.centerx - 130, rect.bottom - 62, 260, 34)
        draw_button(screen, btn_create_profile, f"Создать/выбрать: {self.nickname or 'Игрок'}", self.font_small, t["accent"], t["text"], btn_create_profile.collidepoint(mx, my))

    def draw_stats_popup(self):
        self.sync_profile_progress_to_game()
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
        self.draw_popup_base(rect, "СТАТИСТИКА")
        s = load_stats().get(self.current_profile, {})
        entry = self.get_profile_entry(self.current_profile)
        wins = int(s.get("wins", 0))
        avg_time = int(s.get("total_time", 0) / wins) if wins else 0
        avg_moves = int(s.get("total_moves", 0) / wins) if wins else 0
        ach_count = sum(1 for k in ACHIEVEMENTS if entry.get("achievements", {}).get(k))
        lines = [
            f"Профиль: {self.current_profile}",
            f"Ранг: {rank_from_stats(s)}",
            f"Монеты профиля: {entry.get('coins', 0)}",
            f"Достижения профиля: {ach_count}/{len(ACHIEVEMENTS)}",
            f"Собрано пазлов: {wins}",
            f"Лучшее время: {format_time(s.get('best_time') or 0)}",
            f"Среднее время: {format_time(avg_time)}",
            f"Средние ходы: {avg_moves}",
            f"Подсказок использовано: {s.get('hints', 0)}",
            f"Самый большой пазл: {s.get('max_pieces', 0)} деталей",
            f"Ежедневных пазлов: {s.get('daily', 0)}",
        ]
        for i, line in enumerate(lines):
            screen.blit(self.font_btn.render(line, True, t["text"]), (rect.left + 70, rect.top + 72 + i * 32))

    def handle_menu_click(self, mx, my):
        if self.popup == "profiles":
            if btn_create_profile.collidepoint(mx, my):
                name = (self.nickname.strip() or f"Игрок {len(self.profiles) + 1}")
                self.switch_profile(name)
                return
            for r, name in profile_rects:
                if r.collidepoint(mx, my):
                    self.switch_profile(name)
                    return
        super().handle_menu_click(mx, my)

    def save_settings(self):
        super().save_settings()
        # Дополнительно сохраняем активный профиль даже после переключения.
        self.settings["profile"] = getattr(self, "current_profile", self.nickname or "Игрок")
        save_settings_dict(self.settings)


class SettingsNoOverlapGame(ProfileProgressGame):
    """Версия с исправленной раскладкой меню настроек: кнопки не наслаиваются."""

    def settings_rect(self):
        return pygame.Rect(self.current_w // 2 - 210, self.current_h // 2 - 270, 420, 540)

    def layout_settings_controls(self, rect):
        # Все элементы раскладываются заново при каждом кадре и клике,
        # поэтому они не зависят от старых координат update_layout_sizes().
        x = rect.left + 40
        w = rect.width - 80
        y = rect.top + 64
        btn_music_toggle.update(x, y, w, 36)
        btn_theme_toggle.update(x, y + 46, w, 36)
        btn_controls_toggle.update(x, y + 92, w, 34)

        volume_slider_rect.update(x + 18, y + 172, w - 36, 10)

        btn_hint_key_toggle.update(x, y + 202, (w - 10) // 2, 32)
        btn_right_rotate_toggle.update(x + (w + 10) // 2, y + 202, (w - 10) // 2, 32)

        btn_fps_toggle.update(x, y + 248, (w - 16) // 3, 32)
        btn_anim_toggle.update(x + (w - 16) // 3 + 8, y + 248, (w - 16) // 3, 32)
        btn_quality_toggle.update(x + 2 * ((w - 16) // 3 + 8), y + 248, (w - 16) // 3, 32)

        btn_self_test.update(x, y + 294, w, 34)
        return x, y, w

    def draw_settings_popup(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = self.settings_rect()
        self.draw_popup_base(rect, "НАСТРОЙКИ")
        x, y, w = self.layout_settings_controls(rect)

        music_label = "Музыка: Вкл" if self.sound.music_enabled else "Музыка: Выкл"
        draw_button(screen, btn_music_toggle, music_label, self.font_btn, t["accent"], t["text"], btn_music_toggle.collidepoint(mx, my))
        draw_button(screen, btn_theme_toggle, f"Тема: {t['name']}", self.font_btn, t["orange"], t["text"], btn_theme_toggle.collidepoint(mx, my))
        draw_button(screen, btn_controls_toggle, f"Поворот: клавиша {self.rotate_key}", self.font_btn, t["border"], t["text"], btn_controls_toggle.collidepoint(mx, my))

        volume_title = self.font_btn.render(f"Громкость звуков: {int(self.sound.volume * 100)}%", True, t["text"])
        screen.blit(volume_title, volume_title.get_rect(centerx=rect.centerx, top=y + 138))
        pygame.draw.rect(screen, t["border"], volume_slider_rect, border_radius=5)
        filled = pygame.Rect(volume_slider_rect.left, volume_slider_rect.top, int(volume_slider_rect.width * self.sound.volume), volume_slider_rect.height)
        pygame.draw.rect(screen, t["success"], filled, border_radius=5)
        knob_x = volume_slider_rect.left + int(volume_slider_rect.width * self.sound.volume)
        volume_knob_rect.update(knob_x - 10, volume_slider_rect.centery - 10, 20, 20)
        pygame.draw.circle(screen, t["warning"], volume_knob_rect.center, 11)
        pygame.draw.circle(screen, t["text"], volume_knob_rect.center, 11, 2)

        draw_button(screen, btn_hint_key_toggle, f"Подсказка: {self.hint_key}", self.font_small, t["accent"], t["text"], btn_hint_key_toggle.collidepoint(mx, my))
        right_text = "ПКМ: поворот" if self.right_click_rotate else "ПКМ: выкл"
        draw_button(screen, btn_right_rotate_toggle, right_text, self.font_small, t["success"], t["text"], btn_right_rotate_toggle.collidepoint(mx, my))

        draw_button(screen, btn_fps_toggle, f"FPS {self.graphics_fps}", self.font_small, t["border"], t["text"], btn_fps_toggle.collidepoint(mx, my))
        draw_button(screen, btn_anim_toggle, "Анимация: " + ("Вкл" if self.animations_enabled else "Выкл"), self.font_small, t["border"], t["text"], btn_anim_toggle.collidepoint(mx, my))
        draw_button(screen, btn_quality_toggle, "Качество: " + {"low": "низ", "medium": "ср", "high": "выс"}[self.quality], self.font_small, t["border"], t["text"], btn_quality_toggle.collidepoint(mx, my))
        draw_button(screen, btn_self_test, "Самотест сохранений", self.font_small, t["success"], t["text"], btn_self_test.collidepoint(mx, my))

        if self.self_test_message:
            msg = self.font_small.render(self.self_test_message, True, t["warning"])
            screen.blit(msg, msg.get_rect(centerx=rect.centerx, top=y + 336))

        lines = [
            "S — сохранить игру, L — загрузить",
            "Музыка: sounds/menu_music.mp3 / .ogg / .wav",
            "Настройки сохраняются в settings.json",
        ]
        for i, text in enumerate(lines):
            label = self.font_small.render(text, True, t["border"])
            screen.blit(label, label.get_rect(centerx=rect.centerx, top=y + 370 + i * 24))

    def handle_menu_click(self, mx, my):
        if self.popup == "settings":
            rect = self.settings_rect()
            self.place_close_button(rect)
            self.layout_settings_controls(rect)
            if btn_close_popup.collidepoint(mx, my):
                self.popup = None
                return
            if btn_music_toggle.collidepoint(mx, my):
                self.sound.toggle_music(); self.save_settings(); return
            if btn_theme_toggle.collidepoint(mx, my):
                self.next_theme(); return
            if btn_controls_toggle.collidepoint(mx, my):
                self.cycle_rotate_key(); return
            if btn_hint_key_toggle.collidepoint(mx, my):
                self.cycle_hint_key(); return
            if btn_right_rotate_toggle.collidepoint(mx, my):
                self.right_click_rotate = not self.right_click_rotate; self.save_settings(); return
            if volume_slider_rect.collidepoint(mx, my) or volume_knob_rect.collidepoint(mx, my):
                self.dragging_volume = True
                self.set_volume_from_mouse(mx)
                return
            if btn_fps_toggle.collidepoint(mx, my):
                self.graphics_fps = {30: 60, 60: 120, 120: 30}.get(self.graphics_fps, 60); self.save_settings(); return
            if btn_anim_toggle.collidepoint(mx, my):
                self.animations_enabled = not self.animations_enabled; self.save_settings(); return
            if btn_quality_toggle.collidepoint(mx, my):
                self.quality = {"low": "medium", "medium": "high", "high": "low"}.get(self.quality, "high"); self.save_settings(); return
            if btn_self_test.collidepoint(mx, my):
                self.self_test_message = self.run_self_tests(); return
            if not rect.collidepoint(mx, my):
                self.popup = None
                return
            return
        super().handle_menu_click(mx, my)




# =========================================================
# STATE BUTTON IN SETTINGS: перенос кнопки "Состояние" из главного меню в настройки
# =========================================================
class StateInSettingsGame(SettingsNoOverlapGame):
    """Кнопка 'Состояние' теперь находится внутри окна настроек, а не в главном меню."""

    def settings_rect(self):
        return pygame.Rect(self.current_w // 2 - 210, self.current_h // 2 - 300, 420, 600)

    def layout_settings_controls(self, rect):
        x = rect.left + 40
        w = rect.width - 80
        y = rect.top + 64
        btn_music_toggle.update(x, y, w, 36)
        btn_theme_toggle.update(x, y + 46, w, 36)
        btn_controls_toggle.update(x, y + 92, w, 34)

        volume_slider_rect.update(x + 18, y + 172, w - 36, 10)

        btn_hint_key_toggle.update(x, y + 202, (w - 10) // 2, 32)
        btn_right_rotate_toggle.update(x + (w + 10) // 2, y + 202, (w - 10) // 2, 32)

        btn_fps_toggle.update(x, y + 248, (w - 16) // 3, 32)
        btn_anim_toggle.update(x + (w - 16) // 3 + 8, y + 248, (w - 16) // 3, 32)
        btn_quality_toggle.update(x + 2 * ((w - 16) // 3 + 8), y + 248, (w - 16) // 3, 32)

        # Кнопка самотеста сохранений убрана из меню настроек.
        btn_self_test.update(-10000, -10000, 1, 1)
        btn_diagnostics.update(x, y + 294, w, 34)
        return x, y, w

    def layout_deluxe_menu_buttons(self):
        """На главном экране оставляем только 'Задания дня'; 'Состояние' перенесено в настройки."""
        w, h = 150, 32
        y = min(self.current_h - 82, self.current_h // 2 + 224)
        btn_album.update(-10000, -10000, 1, 1)
        btn_diagnostics.update(-10000, -10000, 1, 1)
        btn_quests.update(self.current_w // 2 - w // 2, y, w, h)

    def draw_deluxe_menu_buttons_fixed(self):
        self.layout_deluxe_menu_buttons()
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        draw_button(screen, btn_quests, "Задания дня", self.font_small, t["success"], t["text"], btn_quests.collidepoint(mx, my))

    def draw_settings_popup(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = self.settings_rect()
        self.draw_popup_base(rect, "НАСТРОЙКИ")
        x, y, w = self.layout_settings_controls(rect)

        music_label = "Музыка: Вкл" if self.sound.music_enabled else "Музыка: Выкл"
        draw_button(screen, btn_music_toggle, music_label, self.font_btn, t["accent"], t["text"], btn_music_toggle.collidepoint(mx, my))
        draw_button(screen, btn_theme_toggle, f"Тема: {t['name']}", self.font_btn, t["orange"], t["text"], btn_theme_toggle.collidepoint(mx, my))
        draw_button(screen, btn_controls_toggle, f"Поворот: клавиша {self.rotate_key}", self.font_btn, t["border"], t["text"], btn_controls_toggle.collidepoint(mx, my))

        volume_title = self.font_btn.render(f"Громкость звуков: {int(self.sound.volume * 100)}%", True, t["text"])
        screen.blit(volume_title, volume_title.get_rect(centerx=rect.centerx, top=y + 138))
        pygame.draw.rect(screen, t["border"], volume_slider_rect, border_radius=5)
        filled = pygame.Rect(volume_slider_rect.left, volume_slider_rect.top, int(volume_slider_rect.width * self.sound.volume), volume_slider_rect.height)
        pygame.draw.rect(screen, t["success"], filled, border_radius=5)
        knob_x = volume_slider_rect.left + int(volume_slider_rect.width * self.sound.volume)
        volume_knob_rect.update(knob_x - 10, volume_slider_rect.centery - 10, 20, 20)
        pygame.draw.circle(screen, t["warning"], volume_knob_rect.center, 11)
        pygame.draw.circle(screen, t["text"], volume_knob_rect.center, 11, 2)

        draw_button(screen, btn_hint_key_toggle, f"Подсказка: {self.hint_key}", self.font_small, t["accent"], t["text"], btn_hint_key_toggle.collidepoint(mx, my))
        right_text = "ПКМ: поворот" if self.right_click_rotate else "ПКМ: выкл"
        draw_button(screen, btn_right_rotate_toggle, right_text, self.font_small, t["success"], t["text"], btn_right_rotate_toggle.collidepoint(mx, my))

        draw_button(screen, btn_fps_toggle, f"FPS {self.graphics_fps}", self.font_small, t["border"], t["text"], btn_fps_toggle.collidepoint(mx, my))
        draw_button(screen, btn_anim_toggle, "Анимация: " + ("Вкл" if self.animations_enabled else "Выкл"), self.font_small, t["border"], t["text"], btn_anim_toggle.collidepoint(mx, my))
        draw_button(screen, btn_quality_toggle, "Качество: " + {"low": "низ", "medium": "ср", "high": "выс"}[self.quality], self.font_small, t["border"], t["text"], btn_quality_toggle.collidepoint(mx, my))
        draw_button(screen, btn_diagnostics, "Состояние", self.font_small, t["border"], t["text"], btn_diagnostics.collidepoint(mx, my))

        lines = [
            "S — сохранить игру, L — загрузить",
            "Музыка: sounds/menu_music.mp3 / .ogg / .wav",
            "Настройки сохраняются в settings.json",
        ]
        for i, text in enumerate(lines):
            label = self.font_small.render(text, True, t["border"])
            screen.blit(label, label.get_rect(centerx=rect.centerx, top=y + 360 + i * 24))

    def handle_menu_click(self, mx, my):
        if self.popup == "settings":
            rect = self.settings_rect()
            self.place_close_button(rect)
            self.layout_settings_controls(rect)
            if btn_close_popup.collidepoint(mx, my):
                self.popup = None
                return
            if btn_music_toggle.collidepoint(mx, my):
                self.sound.toggle_music(); self.save_settings(); return
            if btn_theme_toggle.collidepoint(mx, my):
                self.next_theme(); return
            if btn_controls_toggle.collidepoint(mx, my):
                self.cycle_rotate_key(); return
            if btn_hint_key_toggle.collidepoint(mx, my):
                self.cycle_hint_key(); return
            if btn_right_rotate_toggle.collidepoint(mx, my):
                self.right_click_rotate = not self.right_click_rotate; self.save_settings(); return
            if volume_slider_rect.collidepoint(mx, my) or volume_knob_rect.collidepoint(mx, my):
                self.dragging_volume = True
                self.set_volume_from_mouse(mx)
                return
            if btn_fps_toggle.collidepoint(mx, my):
                self.graphics_fps = {30: 60, 60: 120, 120: 30}.get(self.graphics_fps, 60); self.save_settings(); return
            if btn_anim_toggle.collidepoint(mx, my):
                self.animations_enabled = not self.animations_enabled; self.save_settings(); return
            if btn_quality_toggle.collidepoint(mx, my):
                self.quality = {"low": "medium", "medium": "high", "high": "low"}.get(self.quality, "high"); self.save_settings(); return
            if btn_diagnostics.collidepoint(mx, my):
                self.popup = "diagnostics"
                write_diagnostics(self)
                return
            if not rect.collidepoint(mx, my):
                self.popup = None
                return
            return
        super().handle_menu_click(mx, my)


# =========================================================
# PROFILE MENU PATCH: кнопка статистики перенесена в окно профилей
# =========================================================
class ProfileStatsInProfilesGame(StateInSettingsGame):
    """В главном меню нет кнопки 'Статистика'; она находится внутри окна 'Профили'."""

    def draw_extra_menu_buttons(self):
        # В главном меню оставляем только магазин и профили.
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        cx = self.current_w // 2
        y = self.current_h // 2 + 180
        w, h, gap = 150, 34, 12
        total = w * 2 + gap
        left = cx - total // 2

        btn_campaign.update(-10000, -10000, 1, 1)
        btn_daily.update(-10000, -10000, 1, 1)
        btn_stats.update(-10000, -10000, 1, 1)
        btn_shop.update(left, y, w, h)
        btn_profiles.update(left + w + gap, y, w, h)

        draw_button(screen, btn_shop, f"Магазин ({self.economy.get('coins', 0)}¢)", self.font_small, t["orange"], t["text"], btn_shop.collidepoint(mx, my))
        draw_button(screen, btn_profiles, "Профили", self.font_small, t["border"], t["text"], btn_profiles.collidepoint(mx, my))

    def draw_profiles_popup(self):
        global profile_rects
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
        self.draw_popup_base(rect, "ПРОФИЛИ ИГРОКОВ")
        self.profiles = load_profiles()
        profile_rects = []
        y = rect.top + 70

        for name, info in list(self.profiles.items())[:7]:
            entry = self.get_profile_entry(name)
            ach_count = sum(1 for k in ACHIEVEMENTS if entry.get("achievements", {}).get(k))
            r = pygame.Rect(rect.left + 48, y, rect.width - 96, 46)
            profile_rects.append((r, name))
            pygame.draw.rect(screen, t["panel"], r, border_radius=8)
            pygame.draw.rect(screen, t["success"] if name == self.current_profile else t["border"], r, 2, border_radius=8)
            title = ("★ " if name == self.current_profile else "") + name
            screen.blit(self.font_btn.render(title, True, t["text"]), (r.left + 12, r.top + 7))
            meta = f"Монеты: {entry.get('coins', 0)} · Достижения: {ach_count}/{len(ACHIEVEMENTS)}"
            screen.blit(self.font_small.render(meta, True, t["warning"]), (r.left + 300, r.top + 14))
            y += 54

        # Две кнопки внизу окна профилей: статистика текущего профиля и создание/выбор.
        btn_stats.update(rect.left + 70, rect.bottom - 62, 230, 34)
        btn_create_profile.update(rect.right - 300, rect.bottom - 62, 230, 34)
        draw_button(screen, btn_stats, "Статистика", self.font_small, t["warning"], t["text"], btn_stats.collidepoint(mx, my))
        draw_button(screen, btn_create_profile, f"Создать/выбрать: {self.nickname or 'Игрок'}", self.font_small, t["accent"], t["text"], btn_create_profile.collidepoint(mx, my))

    def handle_menu_click(self, mx, my):
        # Обрабатываем профили раньше родительских классов, чтобы кнопка статистики работала внутри окна.
        if self.popup == "profiles":
            rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 230, 660, 460)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my) or not rect.collidepoint(mx, my):
                self.popup = None
                return
            if btn_stats.collidepoint(mx, my):
                self.popup = "stats"
                return
            if btn_create_profile.collidepoint(mx, my):
                name = (self.nickname.strip() or f"Игрок {len(self.profiles) + 1}")
                self.switch_profile(name)
                return
            for r, name in profile_rects:
                if r.collidepoint(mx, my):
                    self.switch_profile(name)
                    return
            return

        # На главном экране кнопки статистики больше нет.
        if not self.popup:
            btn_stats.update(-10000, -10000, 1, 1)

        super().handle_menu_click(mx, my)


# =========================================================
# PROFILE DAILY QUESTS PATCH: задания дня отдельно для каждого профиля
# =========================================================
ACTIVE_QUEST_PROFILE = "Игрок"


def _quest_profile_name(profile=None):
    name = str(profile or ACTIVE_QUEST_PROFILE or "Игрок").strip()
    return name or "Игрок"


def _make_daily_quests_for_date(day_key):
    seed = sum(ord(ch) for ch in str(day_key))
    rnd = random.Random(seed)
    pool = [
        {"id": "place20", "title": "Поставь 20 деталей", "target": 20, "reward": 35},
        {"id": "win_no_hint", "title": "Собери пазл без подсказок", "target": 1, "reward": 60},
        {"id": "win_5x5", "title": "Собери пазл 5x5 или больше", "target": 1, "reward": 70},
        {"id": "use_custom", "title": "Сыграй со своей картинкой", "target": 1, "reward": 40},
        {"id": "rotate10", "title": "Поверни детали 10 раз", "target": 10, "reward": 30},
        {"id": "save_slot", "title": "Сохрани игру в слот", "target": 1, "reward": 25},
    ]
    rnd.shuffle(pool)
    quests = []
    for q in pool[:3]:
        item = dict(q)
        item["progress"] = 0
        item["done"] = False
        quests.append(item)
    return quests


def daily_quests_for_today(profile=None):
    """Возвращает задания текущего дня именно для выбранного профиля.

    Новый формат daily_quests.json:
    {
        "date": "YYYY-MM-DD",
        "profiles": {
            "Игрок": [{...}],
            "Вася": [{...}]
        }
    }

    Старый формат {"date": ..., "quests": [...]} автоматически переносится
    в текущий профиль, чтобы прогресс не потерялся.
    """
    day = today_key()
    profile_name = _quest_profile_name(profile)
    raw = _load_json_file(DAILY_QUESTS_FILE, {})
    if not isinstance(raw, dict):
        raw = {}

    # Новый день — начинаем чистую структуру по профилям.
    if raw.get("date") != day:
        data = {"date": day, "profiles": {}}
    else:
        data = dict(raw)
        if not isinstance(data.get("profiles"), dict):
            data["profiles"] = {}
        # Миграция старого общего списка заданий в активный профиль.
        if isinstance(data.get("quests"), list) and profile_name not in data["profiles"]:
            data["profiles"][profile_name] = data.get("quests", [])
        data.pop("quests", None)

    profiles = data.setdefault("profiles", {})
    if profile_name not in profiles or not isinstance(profiles.get(profile_name), list):
        profiles[profile_name] = _make_daily_quests_for_date(day)
        _save_json_file(DAILY_QUESTS_FILE, data)
    else:
        _save_json_file(DAILY_QUESTS_FILE, data)

    return {"date": day, "profile": profile_name, "quests": profiles[profile_name], "profiles": profiles}


def update_daily_quest(qid, amount=1, reward_callback=None, profile=None):
    profile_name = _quest_profile_name(profile)
    data = daily_quests_for_today(profile_name)
    changed = False
    completed = []
    quests = data.get("quests", [])

    for q in quests:
        if q.get("id") == qid and not q.get("done"):
            q["progress"] = min(int(q.get("target", 1)), int(q.get("progress", 0)) + int(amount))
            if q["progress"] >= int(q.get("target", 1)):
                q["done"] = True
                completed.append(q)
            changed = True

    if changed:
        save_data = {"date": data.get("date", today_key()), "profiles": data.get("profiles", {})}
        save_data["profiles"][profile_name] = quests
        _save_json_file(DAILY_QUESTS_FILE, save_data)

    if reward_callback:
        for q in completed:
            reward_callback(int(q.get("reward", 0)), q.get("title", "Задание"))
    return completed


class ProfileQuestsGame(ProfileStatsInProfilesGame):
    """Задания дня теперь хранятся отдельно для каждого профиля игрока."""

    def __init__(self):
        super().__init__()
        self.activate_quest_profile()

    def activate_quest_profile(self):
        global ACTIVE_QUEST_PROFILE
        ACTIVE_QUEST_PROFILE = _quest_profile_name(getattr(self, "current_profile", getattr(self, "nickname", "Игрок")))
        # Создаём задания для профиля заранее, чтобы окно сразу показывало его данные.
        daily_quests_for_today(ACTIVE_QUEST_PROFILE)

    def switch_profile(self, profile_name):
        super().switch_profile(profile_name)
        self.activate_quest_profile()

    def handle_menu_click(self, mx, my):
        # Перед открытием заданий обновляем активный профиль.
        self.activate_quest_profile()
        super().handle_menu_click(mx, my)

    def handle_mouse_down(self, mx, my):
        self.activate_quest_profile()
        super().handle_mouse_down(mx, my)

    def draw_quests_popup(self):
        self.activate_quest_profile()
        t = self.theme
        rect = self.deluxe_modal_rect()
        self.draw_popup_base(rect, "ЗАДАНИЯ ДНЯ")
        data = daily_quests_for_today(getattr(self, "current_profile", "Игрок"))

        date_text = self.font_btn.render(f"Профиль: {data.get('profile', 'Игрок')}   |   Дата: {data.get('date', '')}", True, t["text"])
        screen.blit(date_text, date_text.get_rect(centerx=rect.centerx, top=rect.top + 54))

        y = rect.top + 92
        quests = data.get("quests", []) if isinstance(data, dict) else []
        if not quests:
            draw_text_center("Задания не найдены. Они будут созданы заново.", self.font_small, t["text"], screen, rect.centerx, rect.centery)
            return

        for q in quests:
            r = pygame.Rect(rect.left + 42, y, rect.width - 84, 72)
            done = bool(q.get("done"))
            pygame.draw.rect(screen, t["panel"], r, border_radius=10)
            pygame.draw.rect(screen, t["success"] if done else t["border"], r, 2, border_radius=10)
            title = ("✓ " if done else "• ") + str(q.get("title", "Задание"))
            screen.blit(self.font_btn.render(title, True, t["text"]), (r.left + 16, r.top + 10))
            target = max(1, int(q.get("target", 1)))
            progress = min(target, int(q.get("progress", 0)))
            reward = int(q.get("reward", 0))
            info = f"Прогресс: {progress}/{target}     Награда: {reward} монет"
            screen.blit(self.font_small.render(info, True, t["warning"]), (r.left + 16, r.top + 42))

            bar = pygame.Rect(r.right - 190, r.top + 43, 150, 12)
            pygame.draw.rect(screen, t["bg"], bar, border_radius=6)
            fill = pygame.Rect(bar.left, bar.top, int(bar.w * progress / target), bar.h)
            pygame.draw.rect(screen, t["success"] if done else t["accent"], fill, border_radius=6)
            y += 84
            if y + 80 > rect.bottom - 20:
                break

    def reward_for_quest(self, amount, title):
        # Награда начисляется текущему профилю, потому что монеты уже привязаны к профилям.
        self.activate_quest_profile()
        super().reward_for_quest(amount, title)




# =========================================================
# SETTINGS GEAR PATCH: кнопка "Настройки" в виде шестерёнки справа сверху
# =========================================================
class GearSettingsGame(ProfileQuestsGame):
    """В главном меню кнопка настроек перенесена вправо вверх и показана как шестерёнка."""

    def layout_settings_gear(self):
        size = 46
        margin = 22
        btn_menu_settings.update(self.current_w - size - margin, margin, size, size)
        return btn_menu_settings

    def draw_settings_gear_button(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = self.layout_settings_gear()
        hovered = rect.collidepoint(mx, my)

        base = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        bg_color = t["accent"] if hovered else t["panel"]
        border_color = t["warning"] if hovered else t["border"]
        pygame.draw.rect(base, (*bg_color, 255), base.get_rect(), border_radius=12)
        pygame.draw.rect(base, (*border_color, 255), base.get_rect(), 2, border_radius=12)

        cx, cy = rect.w // 2, rect.h // 2
        gear_color = t["text"]
        tooth_color = t["warning"] if hovered else t["accent"]
        # Зубцы шестерёнки.
        for i in range(8):
            ang = math.radians(i * 45)
            dx = math.cos(ang)
            dy = math.sin(ang)
            tw, th = 6, 12
            tooth = pygame.Surface((tw, th), pygame.SRCALPHA)
            pygame.draw.rect(tooth, tooth_color, (0, 0, tw, th), border_radius=3)
            rotated = pygame.transform.rotate(tooth, -i * 45)
            rx = cx + int(dx * 12) - rotated.get_width() // 2
            ry = cy + int(dy * 12) - rotated.get_height() // 2
            base.blit(rotated, (rx, ry))

        pygame.draw.circle(base, gear_color, (cx, cy), 12)
        pygame.draw.circle(base, bg_color, (cx, cy), 6)
        pygame.draw.circle(base, gear_color, (cx, cy), 12, 2)

        screen.blit(base, rect.topleft)

    def draw_base_menu_without_continue(self):
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        self.draw_background_animation()

        title = self.font_big.render("ФИГУРНЫЙ ПАЗЛ", True, t["text"])
        screen.blit(title, title.get_rect(centerx=self.current_w // 2, centery=self.current_h // 2 - 185))
        subtitle = self.font_btn.render("Собирай, ставь рекорды и загружай свои картинки", True, t["warning"])
        screen.blit(subtitle, subtitle.get_rect(centerx=self.current_w // 2, centery=self.current_h // 2 - 145))

        pygame.draw.rect(screen, t["panel"], input_nick_rect, border_radius=6)
        pygame.draw.rect(screen, t["success"] if self.input_active else t["border"], input_nick_rect, 2, border_radius=6)
        nick_text = f"Ник: {self.nickname}" if self.nickname else "Введите ваш ник..."
        draw_text_center(nick_text, self.font_btn, t["text"], screen, input_nick_rect.centerx, input_nick_rect.centery)

        draw_button(screen, btn_menu_play, "ИГРАТЬ", pygame.font.SysFont("Arial", 22, bold=True), t["accent"], t["text"], btn_menu_play.collidepoint(mx, my))
        draw_button(screen, btn_menu_records, "Рекорды", self.font_btn, t["orange"], t["text"], btn_menu_records.collidepoint(mx, my))
        # Кнопка настроек в виде шестерёнки справа сверху.
        self.draw_settings_gear_button()
        draw_button(screen, btn_menu_achievements, "Достижения", self.font_btn, t["success"], t["text"], btn_menu_achievements.collidepoint(mx, my))

        # Кнопка "Продолжить сохранение" больше не рисуется в главном меню.
        btn_continue.update(-10000, -10000, 1, 1)

        hint = self.font_small.render("F11 — полноэкранный режим | ESC — назад", True, t["border"])
        screen.blit(hint, hint.get_rect(centerx=self.current_w // 2, bottom=self.current_h - 18))




# =========================================================
# TWO STEP HINT PATCH: подсказка теперь работает в 2 этапа
# =========================================================
class TwoStepHintGame(GearSettingsGame):
    """Подсказка без второго этапа 'Показан силуэт'.

    Этап 1: подсветить место, куда нужно поставить выбранный/последний пазлик.
    Этап 2: автоматически поставить этот пазлик на правильное место.
    """

    def show_piece_hint(self):
        if not self.mode_allows_hints():
            self.hint_piece = None
            self.hint_message = "В этом режиме подсказки отключены"
            self.hint_until_ticks = pygame.time.get_ticks() + 1800
            if hasattr(self, "clear_piece_drag"):
                self.clear_piece_drag()
            return

        target = getattr(self, "selected_piece", None)
        if not target or getattr(target, "is_false", False) or getattr(target, "is_locked", False):
            unlocked = [
                p for p in self.active_pieces
                if not getattr(p, "is_locked", False) and not getattr(p, "is_false", False)
            ]
            target = unlocked[-1] if unlocked else None

        if not target:
            self.hint_piece = None
            self.hint_message = "Сначала достань настоящий пазлик"
            self.hint_until_ticks = pygame.time.get_ticks() + 1800
            if hasattr(self, "clear_piece_drag"):
                self.clear_piece_drag()
            return

        if self.last_hint_index == target.index:
            self.hint_level = min(2, self.hint_level + 1)
        else:
            self.hint_level = 1
            self.last_hint_index = target.index

        penalty_mult = self.hint_level
        self.hints_used += 1
        self.hint_penalty_seconds += HINT_TIME_PENALTY * penalty_mult
        self.moves += HINT_MOVE_PENALTY * penalty_mult
        self.hint_piece = target

        if self.hint_level == 1:
            self.hint_message = "Подсказка 1: подсвечена зона"
            self.hint_until_ticks = pygame.time.get_ticks() + 3200
        else:
            self.hint_message = "Подсказка 2: пазлик поставлен автоматически"
            self.hint_until_ticks = pygame.time.get_ticks() + 2200
            self.auto_place_piece(target)
            if hasattr(self, "clear_piece_drag"):
                self.clear_piece_drag()
            self.check_victory()




# =========================================================
# QUESTS BUTTON PATCH: "Задания дня" на месте старой кнопки настроек
# =========================================================
class QuestsInOldSettingsPlaceGame(TwoStepHintGame):
    """Кнопка 'Задания дня' перенесена на место старой кнопки 'Настройки'.

    Настройки остаются шестерёнкой справа сверху.
    """

    def layout_main_quests_button(self):
        # Старое место кнопки "Настройки": справа от "Рекорды".
        btn_quests.update(self.current_w // 2 + 5, self.current_h // 2 + 25, 145, 42)
        return btn_quests

    def draw_base_menu_without_continue(self):
        super().draw_base_menu_without_continue()
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = self.layout_main_quests_button()
        draw_button(
            screen,
            rect,
            "Задания дня",
            self.font_btn,
            t["orange"],
            t["text"],
            rect.collidepoint(mx, my),
        )

    def draw_deluxe_menu_buttons_fixed(self):
        # Нижнюю отдельную кнопку "Задания дня" больше не рисуем,
        # потому что она перенесена наверх на место старых настроек.
        btn_album.update(-10000, -10000, 1, 1)
        btn_diagnostics.update(-10000, -10000, 1, 1)

    def layout_deluxe_menu_buttons(self):
        # Не даём старой логике перенести кнопку "Задания дня" обратно вниз.
        self.layout_main_quests_button()
        btn_album.update(-10000, -10000, 1, 1)
        btn_diagnostics.update(-10000, -10000, 1, 1)

    def handle_menu_click(self, mx, my):
        if not self.popup:
            self.layout_main_quests_button()
            if btn_quests.collidepoint(mx, my):
                self.popup = "quests"
                return
        super().handle_menu_click(mx, my)




# =========================================================
# TOP ICONS PATCH: магазин и профили рядом с шестерёнкой
# =========================================================
class TopIconMenuGame(QuestsInOldSettingsPlaceGame):
    """Магазин и профили вынесены в правый верхний угол рядом с настройками."""

    def layout_top_menu_icons(self):
        size = 46
        gap = 12
        margin = 22
        # Справа налево: настройки, профили, магазин.
        btn_menu_settings.update(self.current_w - size - margin, margin, size, size)
        btn_profiles.update(btn_menu_settings.left - gap - size, margin, size, size)
        btn_shop.update(btn_profiles.left - gap - size, margin, size, size)
        return btn_shop, btn_profiles, btn_menu_settings

    def layout_settings_gear(self):
        self.layout_top_menu_icons()
        return btn_menu_settings

    def draw_round_icon_button(self, rect, kind, bg_color, hovered=False, label_text=None):
        t = self.theme
        surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        color = bg_color if not hovered else tuple(min(255, c + 24) for c in bg_color)
        pygame.draw.rect(surf, (*color, 255), surf.get_rect(), border_radius=13)
        pygame.draw.rect(surf, (*t["warning"], 255) if hovered else (*t["border"], 255), surf.get_rect(), 2, border_radius=13)
        cx, cy = rect.w // 2, rect.h // 2

        if kind == "coin":
            pygame.draw.circle(surf, t["warning"], (cx, cy), 14)
            pygame.draw.circle(surf, (190, 120, 20), (cx, cy), 14, 2)
            pygame.draw.circle(surf, (255, 234, 130), (cx - 4, cy - 5), 4)
            sym = self.font_btn.render("¢", True, (120, 75, 10))
            surf.blit(sym, sym.get_rect(center=(cx + 2, cy + 1)))
        elif kind == "profile":
            pygame.draw.circle(surf, t["text"], (cx, cy - 8), 8)
            pygame.draw.ellipse(surf, t["text"], (cx - 15, cy + 2, 30, 20))
            pygame.draw.circle(surf, color, (cx, cy - 8), 3)
        elif kind == "gear":
            gear_color = t["text"]
            tooth_color = t["warning"] if hovered else t["accent"]
            for i in range(8):
                ang = math.radians(i * 45)
                dx = math.cos(ang)
                dy = math.sin(ang)
                tooth = pygame.Surface((6, 12), pygame.SRCALPHA)
                pygame.draw.rect(tooth, tooth_color, (0, 0, 6, 12), border_radius=3)
                rotated = pygame.transform.rotate(tooth, -i * 45)
                rx = cx + int(dx * 12) - rotated.get_width() // 2
                ry = cy + int(dy * 12) - rotated.get_height() // 2
                surf.blit(rotated, (rx, ry))
            pygame.draw.circle(surf, gear_color, (cx, cy), 12)
            pygame.draw.circle(surf, color, (cx, cy), 6)
            pygame.draw.circle(surf, gear_color, (cx, cy), 12, 2)

        screen.blit(surf, rect.topleft)

        # Маленькая подсказка при наведении.
        if hovered and label_text:
            label = self.font_small.render(label_text, True, t["text"])
            pad = 8
            tip = pygame.Rect(0, 0, label.get_width() + pad * 2, label.get_height() + 8)
            tip.midtop = (rect.centerx, rect.bottom + 8)
            pygame.draw.rect(screen, t["panel"], tip, border_radius=6)
            pygame.draw.rect(screen, t["border"], tip, 1, border_radius=6)
            screen.blit(label, label.get_rect(center=tip.center))

    def draw_settings_gear_button(self):
        # Рисуем все три иконки одной группой.
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        shop_rect, profile_rect, settings_rect = self.layout_top_menu_icons()
        self.draw_round_icon_button(shop_rect, "coin", t["orange"], shop_rect.collidepoint(mx, my), "Магазин")
        self.draw_round_icon_button(profile_rect, "profile", t["border"], profile_rect.collidepoint(mx, my), "Профили")
        self.draw_round_icon_button(settings_rect, "gear", t["panel"], settings_rect.collidepoint(mx, my), "Настройки")

    def draw_extra_menu_buttons(self):
        # Старые текстовые кнопки "Магазин" и "Профили" больше не рисуем внизу.
        # Иконки рисуются в draw_settings_gear_button(), который вызывается из главного меню.
        btn_stats.update(-10000, -10000, 1, 1)
        self.layout_top_menu_icons()

    def handle_menu_click(self, mx, my):
        if not self.popup:
            self.layout_top_menu_icons()
            if btn_shop.collidepoint(mx, my):
                self.popup = "shop"
                return
            if btn_profiles.collidepoint(mx, my):
                self.popup = "profiles"
                return
            if btn_menu_settings.collidepoint(mx, my):
                self.input_active = False
                self.popup = "settings"
                return
        super().handle_menu_click(mx, my)




# =========================================================
# FULL ACHIEVEMENTS PATCH: полный список достижений с прокруткой
# =========================================================
class FullAchievementsGame(TopIconMenuGame):
    """Окно достижений теперь показывает все достижения, список прокручивается."""

    def __init__(self):
        super().__init__()
        self.achievements_scroll = 0

    def max_achievements_scroll(self, rect):
        row_h = 56
        header_h = 78
        bottom_pad = 26
        content_h = len(ACHIEVEMENTS) * row_h
        view_h = rect.height - header_h - bottom_pad
        return max(0, content_h - view_h)

    def scroll_achievements(self, delta):
        rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 245, 660, 490)
        self.achievements_scroll = max(0, min(self.achievements_scroll + delta, self.max_achievements_scroll(rect)))

    def handle_keydown(self, event):
        if self.state == "MENU" and self.popup == "achievements":
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.scroll_achievements(56)
                return
            if event.key in (pygame.K_UP, pygame.K_w):
                self.scroll_achievements(-56)
                return
            if event.key == pygame.K_PAGEDOWN:
                self.scroll_achievements(260)
                return
            if event.key == pygame.K_PAGEUP:
                self.scroll_achievements(-260)
                return
            if event.key == pygame.K_HOME:
                self.achievements_scroll = 0
                return
            if event.key == pygame.K_END:
                rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 245, 660, 490)
                self.achievements_scroll = self.max_achievements_scroll(rect)
                return
        super().handle_keydown(event)

    def handle_events(self):
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                self.current_w, self.current_h = event.w, event.h
                update_layout_sizes(self.current_w, self.current_h)
                self.new_puzzle()
            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
            if event.type == pygame.MOUSEWHEEL:
                if self.state == "MENU" and self.popup == "achievements":
                    self.scroll_achievements(-event.y * 56)
                elif self.state == "PUZZLE" and not getattr(self, "paused", False):
                    self.zoom_view(event.y)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2 and self.state == "PUZZLE":
                self.middle_drag = True; self.last_mouse_pos = event.pos
            if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
                self.middle_drag = False; self.save_settings()
            if event.type == pygame.MOUSEMOTION and self.middle_drag and self.state == "PUZZLE":
                dx = event.pos[0] - self.last_mouse_pos[0]; dy = event.pos[1] - self.last_mouse_pos[1]
                self.last_mouse_pos = event.pos
                self.apply_pan(dx, dy)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse_down(mx, my)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.right_click_rotate and not getattr(self, "paused", False):
                self.rotate_selected_or_hovered(mx, my)
            if event.type == pygame.MOUSEMOTION and self.dragging_volume:
                self.set_volume_from_mouse(event.pos[0])
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.handle_mouse_up()

    def draw_achievements_popup(self):
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 330, self.current_h // 2 - 245, 660, 490)
        self.draw_popup_base(rect, "ДОСТИЖЕНИЯ")
        entry = self.get_profile_entry(self.current_profile)
        unlocked = entry.setdefault("achievements", {})
        got_count = sum(1 for k in ACHIEVEMENTS if unlocked.get(k))
        total = len(ACHIEVEMENTS)

        header = self.font_small.render(
            f"Профиль: {self.current_profile} · Получено: {got_count}/{total} · Колесо мыши — прокрутка",
            True,
            t["warning"],
        )
        screen.blit(header, (rect.left + 26, rect.top + 48))

        view = pygame.Rect(rect.left + 22, rect.top + 76, rect.width - 44, rect.height - 104)
        self.achievements_scroll = max(0, min(self.achievements_scroll, self.max_achievements_scroll(rect)))

        old_clip = screen.get_clip()
        screen.set_clip(view)
        y = view.top - self.achievements_scroll
        for key, info in ACHIEVEMENTS.items():
            badge_rect = pygame.Rect(view.left + 4, y, view.width - 8, 48)
            if badge_rect.bottom >= view.top and badge_rect.top <= view.bottom:
                got = bool(unlocked.get(key))
                pygame.draw.rect(screen, t["panel"] if got else t["bg"], badge_rect, border_radius=8)
                pygame.draw.rect(screen, t["success"] if got else t["border"], badge_rect, 2, border_radius=8)
                icon = "✓" if got else "?"
                screen.blit(self.font_win.render(icon, True, t["success"] if got else t["border"]), (badge_rect.left + 14, badge_rect.top + 9))
                screen.blit(self.font_btn.render(info["title"], True, t["text"]), (badge_rect.left + 48, badge_rect.top + 6))
                desc = info["desc"] if not got else f"{info['desc']}  Получено: {unlocked.get(key)}"
                screen.blit(self.font_small.render(desc, True, t["border"]), (badge_rect.left + 48, badge_rect.top + 28))
            y += 56
        screen.set_clip(old_clip)

        # Рамка области списка и полоса прокрутки.
        pygame.draw.rect(screen, t["border"], view, 1, border_radius=8)
        max_scroll = self.max_achievements_scroll(rect)
        if max_scroll > 0:
            track = pygame.Rect(view.right - 10, view.top + 6, 5, view.height - 12)
            pygame.draw.rect(screen, t["bg"], track, border_radius=3)
            knob_h = max(28, int(track.h * (track.h / (track.h + max_scroll))))
            knob_y = track.top + int((track.h - knob_h) * self.achievements_scroll / max_scroll)
            pygame.draw.rect(screen, t["warning"], (track.left, knob_y, track.w, knob_h), border_radius=3)


# =========================================================
# ACHIEVEMENTS CLEANUP: убраны достижения за хардкор и дополнительные сложности
# =========================================================
for _achievement_to_remove in (
    "hardcore_win",   # Хардкорный режим
    "hard_option",    # Дополнительные опции сложности
    "custom_size",    # Нестандартная/своя сложность
):
    ACHIEVEMENTS.pop(_achievement_to_remove, None)





# =========================================================
# MENU BACKGROUND UPGRADE: более интересный фон главного меню
# =========================================================
class InterestingMenuBackgroundGame(FullAchievementsGame):
    """Главное меню с более живым и красивым фоном."""

    def _draw_soft_glow(self, x, y, radius, color, alpha):
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -max(2, radius // 10)):
            a = int(alpha * (r / radius) ** 2)
            pygame.draw.circle(surf, (*color, a), (radius, radius), r)
        screen.blit(surf, (x - radius, y - radius))

    def _draw_bg_piece(self, x, y, size, border, accent, alpha=90):
        surf = pygame.Surface((size + 18, size + 18), pygame.SRCALPHA)
        body = pygame.Rect(9, 9, size, size)
        pygame.draw.rect(surf, (*border, alpha), body, border_radius=max(4, size // 5))
        nub_r = max(4, size // 5)
        pygame.draw.circle(surf, (*accent, max(60, alpha + 20)), (body.centerx, body.centery), nub_r)
        pygame.draw.rect(surf, (*accent, 40), body.inflate(2, 2), 1, border_radius=max(4, size // 5))
        screen.blit(surf, (int(x - 9), int(y - 9)))

    def draw_background_animation(self):
        t = self.theme
        now = pygame.time.get_ticks() / 1000.0

        # Градиентный фон.
        top = (12, 16, 30)
        mid = (18, 23, 40)
        bottom = (12, 17, 32)
        for y in range(self.current_h):
            r = y / max(1, self.current_h - 1)
            if r < 0.55:
                k = r / 0.55
                color = (
                    int(top[0] * (1 - k) + mid[0] * k),
                    int(top[1] * (1 - k) + mid[1] * k),
                    int(top[2] * (1 - k) + mid[2] * k),
                )
            else:
                k = (r - 0.55) / 0.45
                color = (
                    int(mid[0] * (1 - k) + bottom[0] * k),
                    int(mid[1] * (1 - k) + bottom[1] * k),
                    int(mid[2] * (1 - k) + bottom[2] * k),
                )
            pygame.draw.line(screen, color, (0, y), (self.current_w, y))

        # Мягкие цветные свечения.
        self._draw_soft_glow(int(self.current_w * 0.18), int(self.current_h * 0.22), 180, t["accent"], 26)
        self._draw_soft_glow(int(self.current_w * 0.82), int(self.current_h * 0.20), 150, t["success"], 18)
        self._draw_soft_glow(int(self.current_w * 0.70), int(self.current_h * 0.74), 210, t["warning"], 12)
        self._draw_soft_glow(int(self.current_w * 0.26), int(self.current_h * 0.78), 170, t["border"], 14)

        # Едва заметная подложка-пазл за центральным блоком.
        base_w = min(620, int(self.current_w * 0.45))
        base_h = min(350, int(self.current_h * 0.40))
        base = pygame.Rect(self.current_w // 2 - base_w // 2, self.current_h // 2 - base_h // 2 + 8, base_w, base_h)
        plate = pygame.Surface((base.w, base.h), pygame.SRCALPHA)
        pygame.draw.rect(plate, (*t["panel"], 34), plate.get_rect(), border_radius=26)
        pygame.draw.rect(plate, (*t["border"], 22), plate.get_rect(), 1, border_radius=26)
        # сетка пазла
        cols, rows = 4, 3
        for i in range(1, cols):
            x = int(base.w * i / cols)
            pygame.draw.line(plate, (*t["border"], 20), (x, 18), (x, base.h - 18), 1)
        for j in range(1, rows):
            y = int(base.h * j / rows)
            pygame.draw.line(plate, (*t["border"], 20), (18, y), (base.w - 18, y), 1)
        screen.blit(plate, base.topleft)

        # Маленькие мерцающие точки.
        star_color = t["warning"]
        for i in range(22):
            sx = int((i * 97 + 53) % max(1, self.current_w))
            sy = int((i * 149 + 91) % max(1, self.current_h))
            pulse = 90 + int(60 * (0.5 + 0.5 * math.sin(now * 1.7 + i)))
            star = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(star, (*star_color, pulse), (4, 4), 2)
            screen.blit(star, (sx, sy))

        # Плавающие фоновые пазлики.
        visible_positions = []
        for idx, p in enumerate(self.bg_pieces):
            p.setdefault("phase", idx * 0.55)
            p.setdefault("vx", 0.0)
            p.setdefault("vy", 0.0)
            p["y"] += p["vy"] * 0.45
            p["x"] += p["vx"] * 0.18 + math.sin(now * 0.35 + p["phase"]) * 0.10
            if p["y"] > self.current_h + 30:
                p["y"] = random.randint(-120, -20)
                p["x"] = random.randint(0, self.current_w)
            if p["x"] < -40:
                p["x"] = self.current_w + 20
            elif p["x"] > self.current_w + 40:
                p["x"] = -20
            bob_x = p["x"] + math.sin(now * 0.9 + p["phase"]) * 10
            bob_y = p["y"] + math.cos(now * 0.7 + p["phase"] * 1.3) * 6
            size = max(10, int(p["size"]))
            self._draw_bg_piece(bob_x, bob_y, size, t["border"], t["accent"], 88 if size > 12 else 70)
            visible_positions.append((bob_x + size/2, bob_y + size/2))

        # Несколько тонких соединительных линий между близкими пазликами.
        line_surf = pygame.Surface((self.current_w, self.current_h), pygame.SRCALPHA)
        limit = min(10, len(visible_positions))
        for i in range(limit):
            x1, y1 = visible_positions[i]
            best_j = None
            best_d = 999999
            for j in range(i + 1, limit):
                x2, y2 = visible_positions[j]
                d = (x2 - x1) ** 2 + (y2 - y1) ** 2
                if d < best_d:
                    best_d = d
                    best_j = j
            if best_j is not None and best_d < 120000:
                x2, y2 = visible_positions[best_j]
                pygame.draw.line(line_surf, (*t["border"], 28), (x1, y1), (x2, y2), 1)
        screen.blit(line_surf, (0, 0))





# =========================================================
# SIMPLE PAUSE SAVE PATCH: без слотов, одна кнопка "Сохранить"
# =========================================================
class SimplePauseSaveGame(InterestingMenuBackgroundGame):
    """Пауза без слотов сохранения и без настроек.
    Сохраняет в обычный savegame.json, а пункт "Продолжить" в меню
    загружает именно это сохранение.
    """

    def draw_pause_popup(self):
        mx, my = pygame.mouse.get_pos(); t = self.theme
        rect = pygame.Rect(self.current_w//2-250, self.current_h//2-170, 500, 300)
        self.draw_popup_base(rect, "ПАУЗА")
        draw_text_center("Таймер остановлен", self.font_btn, t["text"], screen, rect.centerx, rect.top+58)
        btn_pause_continue.update(rect.centerx-105, rect.top+86, 210, 36)
        btn_pause_save.update(rect.centerx-105, rect.top+132, 210, 34)
        btn_pause_settings.update(-10000, -10000, 1, 1)
        btn_pause_menu.update(rect.centerx-105, rect.top+178, 210, 34)
        draw_button(screen, btn_pause_continue, "Продолжить", self.font_btn, t["success"], t["text"], btn_pause_continue.collidepoint(mx,my))
        draw_button(screen, btn_pause_save, "Сохранить", self.font_btn, t["accent"], t["text"], btn_pause_save.collidepoint(mx,my))
        draw_button(screen, btn_pause_menu, "В меню", self.font_btn, t["danger"], t["text"], btn_pause_menu.collidepoint(mx,my))

        note1 = self.font_small.render("Сохранение записывается в savegame.json", True, t["border"])
        note2 = self.font_small.render("В главном меню нажми 'Продолжить игру', чтобы вернуться к этому пазлу", True, t["border"])
        screen.blit(note1, note1.get_rect(centerx=rect.centerx, top=rect.top + 232))
        screen.blit(note2, note2.get_rect(centerx=rect.centerx, top=rect.top + 254))

    def handle_pause_click(self, mx, my):
        rect = pygame.Rect(self.current_w//2-250, self.current_h//2-170, 500, 300)
        self.place_close_button(rect)
        if btn_close_popup.collidepoint(mx, my) or btn_pause_continue.collidepoint(mx, my):
            self.resume_game(); return
        if btn_pause_menu.collidepoint(mx, my):
            self.paused = False; self.state = "MENU"; self.popup = None; return
        if btn_pause_save.collidepoint(mx, my):
            self.save_current_game()
            return
        if not rect.collidepoint(mx, my):
            self.resume_game()

    def draw_puzzle(self):
        super().draw_puzzle()
        # Перерисовываем поверх нужные модальные окна, исключая старые слоты.
        if self.paused or self.popup == "pause":
            self.draw_pause_popup()
        elif self.popup == "album":
            self.draw_album_popup()
        elif self.popup == "quests":
            self.draw_quests_popup()
        elif self.popup == "diagnostics":
            self.draw_diagnostics_popup()
        elif self.popup == "settings":
            self.draw_settings_popup()

    def handle_mouse_down(self, mx, my):
        # Если вдруг где-то осталось старое состояние popup='slots', закрываем его.
        if getattr(self, 'popup', None) == 'slots':
            self.popup = 'pause' if getattr(self, 'paused', False) else None
            return
        super().handle_mouse_down(mx, my)

    def draw_difficulty_popup(self):
        """Та же раскладка окна новой игры, но с текстом 'Продолжить игру'."""
        mx, my = pygame.mouse.get_pos()
        t = self.theme
        rect = pygame.Rect(self.current_w // 2 - 185, self.current_h // 2 - 190, 370, 380)
        self.draw_popup_base(rect, "НОВАЯ ИГРА")

        x = rect.left + 42
        y = rect.top + 64
        w = rect.width - 84
        h = 42
        gap = 12

        btn_campaign.update(x, y, w, h)
        btn_quick_game.update(x, y + (h + gap), w, h)
        btn_daily.update(x, y + (h + gap) * 2, w, h)
        btn_continue.update(x, y + (h + gap) * 3, w, h)
        btn_gallery_open.update(x, y + (h + gap) * 4, w, h)

        for r in (btn_pop_easy, btn_pop_medium, btn_pop_hard, btn_custom_minus, btn_custom_start, btn_custom_plus):
            r.update(-10000, -10000, 1, 1)

        draw_button(screen, btn_campaign, "Кампания", self.font_btn, t["accent"], t["text"], btn_campaign.collidepoint(mx, my))
        draw_button(screen, btn_quick_game, "Быстрая игра", self.font_btn, t["success"], t["text"], btn_quick_game.collidepoint(mx, my))
        draw_button(screen, btn_daily, "Пазл дня", self.font_btn, t["success"], t["text"], btn_daily.collidepoint(mx, my))
        draw_button(screen, btn_continue, "Продолжить игру", self.font_btn, t["warning"], t["text"], btn_continue.collidepoint(mx, my), t["border"])
        draw_button(screen, btn_gallery_open, "Галерея картинок", self.font_btn, t["border"], t["text"], btn_gallery_open.collidepoint(mx, my))

    def handle_menu_click(self, mx, my):
        # Переиспользуем прежнюю логику, но окно "Новая игра" имеет другой порядок кнопок.
        if self.popup == "difficulty":
            rect = pygame.Rect(self.current_w // 2 - 185, self.current_h // 2 - 190, 370, 380)
            self.place_close_button(rect)
            if btn_close_popup.collidepoint(mx, my):
                self.popup = None; return
            if btn_campaign.collidepoint(mx, my):
                self.popup = "campaign"; return
            if btn_quick_game.collidepoint(mx, my):
                self.popup = "quick_game"; return
            if btn_daily.collidepoint(mx, my):
                self.popup = "daily"; return
            if btn_continue.collidepoint(mx, my):
                self.load_saved_game(); return
            if btn_gallery_open.collidepoint(mx, my):
                self.popup = "gallery"; return
            if not rect.collidepoint(mx, my):
                self.popup = None
            return
        super().handle_menu_click(mx, my)


if __name__ == "__main__":
    SimplePauseSaveGame().run()
