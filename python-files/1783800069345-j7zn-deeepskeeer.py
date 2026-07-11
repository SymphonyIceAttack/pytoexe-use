import tkinter as tk
from tkinter import ttk, messagebox
import random
import sys
import math
import json
import os

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("AIM Wailtrum")
        
        # --- Default settings ---
        self.settings = {
            "color": "red",
            "difficulty": "medium",
            "theme": "dark",  # "dark" or "light"
            "shape": "square"  # "square", "circle", "triangle"
        }
        
        # --- Game variables ---
        self.score = 0
        self.record = 0
        self.nickname = "Guest"
        self.avatar = "👤"  # аватар по умолчанию
        self.game_running = False
        self.num_targets = 1
        self.targets = []
        self.in_settings = False
        self.in_about = False
        self.in_achievements = False
        self.in_mode_choice = False
        
        # --- Combo system ---
        self.combo = 0
        self.combo_multiplier = 1
        self.combo_timer_id = None
        self.bonus_chance = 0.15
        
        # --- Achievements ---
        self.unlocked_achievements = set()
        self.total_hits = 0
        self.gold_hits = 0
        self.record_breaks = 0
        self.achievement_notifications = []
        
        # --- All achievements ---
        self.all_achievements = {
            "first_hit": "First hit",
            "combo_10": "Combo 10!",
            "combo_20": "Combo 20!",
            "combo_50": "Combo 50!",
            "score_50": "50 points",
            "score_100": "100 points",
            "score_250": "250 points",
            "score_500": "500 points",
            "score_1000": "1000 points",
            "score_2500": "2500 points",
            "score_5000": "5000 points",
            "score_10000": "10000 points",
            "score_25000": "25000 points",
            "score_50000": "50000 points",
            "score_100000": "100000 points",
            "gold_10": "Gold: 10!",
            "gold_25": "Gold: 25!",
            "gold_50": "Gold: 50!",
            "gold_100": "Gold: 100!",
            "gold_250": "Gold: 250!",
            "gold_500": "Gold: 500!",
            "gold_1000": "Gold: 1000!",
            "mode4": "Multitasking (4 blocks)!",
            "record5": "Record broken 5 times!",
        }
        for i in range(100, 40001, 100):
            self.all_achievements[f"hits_{i}"] = f"{i} clicks!"
        
        # --- Color themes ---
        self.themes = {
            "dark": {
                "bg": "#0a0a2a",
                "bg2": "#1a1a3a",
                "bg3": "#15153a",
                "fg": "#f0f0f0",
                "fg2": "#cccccc",
                "fg3": "#8888bb",
                "line": "#444477",
                "button": "#2a2a5a",
                "button_hover": "#3a3a6a",
                "button_text": "#e0e0e0",
                "glow": "#ffd700",
                "star_brightness": (80, 255),
                "game_bg": "#1a1a3a",
                "game_outline": "#333366"
            },
            "light": {
                "bg": "#e8e8f0",
                "bg2": "#d0d0e0",
                "bg3": "#c0c0d0",
                "fg": "#1a1a3a",
                "fg2": "#333355",
                "fg3": "#555577",
                "line": "#9999bb",
                "button": "#b0b0cc",
                "button_hover": "#c0c0dd",
                "button_text": "#1a1a3a",
                "glow": "#cc8800",
                "star_brightness": (180, 255),
                "game_bg": "#d0d0e0",
                "game_outline": "#8888aa"
            }
        }
        
        # --- Variables for stars ---
        self.stars = []
        self.star_animation_id = None
        
        # --- Visual effects ---
        self.particles = []
        self.sparks = []
        self.floating_texts = []
        self.glow_effects = []
        
        # --- Load record and profile ---
        self.load_record()
        self.load_profile()
        
        # --- Fullscreen mode ---
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", self.handle_escape)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # --- Create main frame ---
        self.main_frame = tk.Frame(self.root, bg="#0a0a2a")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create Canvas for stars
        self.canvas = tk.Canvas(self.main_frame, bg="#0a0a2a", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Show main menu
        self.show_main_menu()

    # ---------- FULL CANVAS CLEAR ----------
    def reset_canvas(self):
        for widget in self.canvas.winfo_children():
            widget.destroy()
        self.canvas.delete("all")
        self.particles.clear()
        self.sparks.clear()
        self.floating_texts.clear()
        self.glow_effects.clear()
        self.targets.clear()
        self.achievement_notifications.clear()
        for star in self.stars:
            self.canvas.delete(star['id'])
        self.stars = []

    # ---------- STOP ALL ANIMATIONS ----------
    def stop_all_animations(self):
        if self.star_animation_id:
            self.canvas.after_cancel(self.star_animation_id)
            self.star_animation_id = None
        if self.combo_timer_id:
            self.canvas.after_cancel(self.combo_timer_id)
            self.combo_timer_id = None
        self.game_running = False
        for target in self.targets:
            if target and target['timer_id']:
                self.canvas.after_cancel(target['timer_id'])
        self.targets.clear()

    # ---------- CLOSE WINDOW ----------
    def on_closing(self):
        self.stop_all_animations()
        self.save_record()
        self.save_profile()
        self.root.destroy()
        sys.exit()

    # ---------- ESC HANDLER ----------
    def handle_escape(self, event=None):
        if self.in_settings or self.in_about or self.in_achievements or self.in_mode_choice:
            self.show_main_menu()
        else:
            self.toggle_fullscreen()

    # ---------- RECORD ----------
    def load_record(self):
        try:
            if os.path.exists("record.json"):
                with open("record.json", "r") as f:
                    data = json.load(f)
                    self.record = data.get("record", 0)
            else:
                self.record = 0
        except:
            self.record = 0
    
    def save_record(self):
        try:
            with open("record.json", "w") as f:
                json.dump({"record": self.record}, f)
        except:
            pass

    # ---------- PROFILE (NICKNAME + AVATAR) ----------
    def load_profile(self):
        try:
            if os.path.exists("profile.json"):
                with open("profile.json", "r") as f:
                    data = json.load(f)
                    self.nickname = data.get("nickname", "Guest")
                    self.avatar = data.get("avatar", "👤")
            else:
                self.nickname = "Guest"
                self.avatar = "👤"
        except:
            self.nickname = "Guest"
            self.avatar = "👤"
    
    def save_profile(self):
        try:
            with open("profile.json", "w") as f:
                json.dump({"nickname": self.nickname, "avatar": self.avatar}, f)
        except:
            pass

    def toggle_fullscreen(self, event=None):
        is_fullscreen = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not is_fullscreen)
        self.root.focus_set()

    # ---------- STARS (with theme) ----------
    def create_stars(self, count=100, y_start=-200, y_end=None):
        for star in self.stars:
            self.canvas.delete(star['id'])
        self.stars = []
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 10 or canvas_height < 10:
            self.canvas.after(100, lambda: self.create_stars(count, y_start, y_end))
            return
        if y_end is None:
            y_end = canvas_height
        theme = self.themes[self.settings["theme"]]
        min_b, max_b = theme["star_brightness"]
        for _ in range(count):
            x = random.randint(0, canvas_width)
            y = random.randint(y_start, y_end)
            size = random.randint(1, 3)
            speed = random.uniform(0.3, 1.5)
            brightness = random.randint(min_b, max_b)
            star = self.canvas.create_oval(x - size, y - size, x + size, y + size,
                fill=f"#{brightness:02x}{brightness:02x}ff", outline="", tags=("star",))
            self.stars.append({'id': star, 'x': x, 'y': y, 'size': size,
                'speed': speed, 'brightness': brightness, 'phase': random.uniform(0, 6.28)})
        if self.star_animation_id:
            self.canvas.after_cancel(self.star_animation_id)
        self.animate_stars()

    def animate_stars(self):
        if not self.stars:
            return
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 10 or canvas_height < 10:
            self.star_animation_id = self.canvas.after(50, self.animate_stars)
            return
        theme = self.themes[self.settings["theme"]]
        min_b, max_b = theme["star_brightness"]
        for star_data in self.stars:
            star_data['y'] += star_data['speed']
            if star_data['y'] > canvas_height + 20:
                star_data['y'] = random.randint(-50, -10)
                star_data['x'] = random.randint(0, canvas_width)
                star_data['speed'] = random.uniform(0.3, 1.5)
            star_data['phase'] += 0.03
            if star_data['phase'] > 6.28:
                star_data['phase'] -= 6.28
            brightness = int((min_b + max_b)/2 + (max_b - min_b)/2 * math.sin(star_data['phase']))
            color = f"#{brightness:02x}{brightness:02x}ff"
            x, y, size = star_data['x'], star_data['y'], star_data['size']
            self.canvas.coords(star_data['id'], x - size, y - size, x + size, y + size)
            self.canvas.itemconfig(star_data['id'], fill=color)
        self.star_animation_id = self.canvas.after(33, self.animate_stars)

    # ---------- ROUNDED BUTTON ----------
    def create_rounded_button(self, canvas, x, y, width, height, text, command, 
                              radius=15, color=None, hover_color=None,
                              text_color=None, font_size=18):
        theme = self.themes[self.settings["theme"]]
        if color is None:
            color = theme["button"]
        if hover_color is None:
            hover_color = theme["button_hover"]
        if text_color is None:
            text_color = theme["button_text"]
        
        def draw_rounded_rect(x1, y1, x2, y2, radius, fill_color):
            points = []
            points.append((x1 + radius, y1))
            points.append((x2 - radius, y1))
            for angle in range(0, 91, 10):
                rad = math.radians(angle)
                points.append((x2 - radius + radius * math.cos(rad), 
                               y1 + radius - radius * math.sin(rad)))
            points.append((x2, y1 + radius))
            points.append((x2, y2 - radius))
            for angle in range(0, 91, 10):
                rad = math.radians(angle)
                points.append((x2 - radius + radius * math.sin(rad), 
                               y2 - radius + radius * math.cos(rad)))
            points.append((x2 - radius, y2))
            points.append((x1 + radius, y2))
            for angle in range(0, 91, 10):
                rad = math.radians(angle)
                points.append((x1 + radius - radius * math.cos(rad), 
                               y2 - radius + radius * math.sin(rad)))
            points.append((x1, y2 - radius))
            points.append((x1, y1 + radius))
            for angle in range(0, 91, 10):
                rad = math.radians(angle)
                points.append((x1 + radius - radius * math.sin(rad), 
                               y1 + radius - radius * math.cos(rad)))
            rect = canvas.create_polygon(points, fill=fill_color, outline=fill_color, width=0)
            return rect
        
        rect_id = draw_rounded_rect(x, y, x + width, y + height, radius, color)
        text_id = canvas.create_text(x + width//2, y + height//2, 
                                     text=text, font=("Arial", font_size, "bold"),
                                     fill=text_color)
        click_rect = canvas.create_rectangle(x - 5, y - 5, x + width + 5, y + height + 5,
                                            fill="", outline="", tags="button")
        def on_enter(e):
            canvas.itemconfig(rect_id, fill=hover_color, outline=hover_color)
        def on_leave(e):
            canvas.itemconfig(rect_id, fill=color, outline=color)
        def on_click(e):
            command()
        canvas.tag_bind(click_rect, "<Enter>", on_enter)
        canvas.tag_bind(click_rect, "<Leave>", on_leave)
        canvas.tag_bind(click_rect, "<Button-1>", on_click)
        canvas.tag_bind(text_id, "<Enter>", on_enter)
        canvas.tag_bind(text_id, "<Leave>", on_leave)
        canvas.tag_bind(text_id, "<Button-1>", on_click)
        return (rect_id, text_id, click_rect)

    # ---------- MAIN MENU ----------
    def show_main_menu(self):
        self.reset_canvas()
        self.stop_all_animations()
        self.in_settings = False
        self.in_about = False
        self.in_achievements = False
        self.in_mode_choice = False
        self.game_running = False
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 100 or canvas_height < 100:
            self.canvas.after(100, self.show_main_menu)
            return
        
        theme = self.themes[self.settings["theme"]]
        self.canvas.config(bg=theme["bg"])
        self.create_stars(count=100, y_start=-200, y_end=canvas_height)
        
        # Отображаем ник с аватаром
        display_name = f"{self.avatar} {self.nickname}" if self.nickname else f"{self.avatar} Guest"
        
        self.canvas.create_text(canvas_width//2, canvas_height//2 - 220,
                               text="🌟 AIM WAILTRUM 🌟",
                               font=("Arial", 52, "bold"), fill=theme["fg"])
        self.canvas.create_text(canvas_width//2, canvas_height//2 - 160,
                               text=f"Welcome, {display_name}!",
                               font=("Arial", 20), fill=theme["fg2"])
        self.canvas.create_text(canvas_width//2, canvas_height//2 - 120,
                               text=f"🏆 Record: {self.record} points",
                               font=("Arial", 18), fill=theme["glow"])
        
        button_width = 250
        button_height = 60
        start_y = canvas_height//2 - 30
        
        self.create_rounded_button(self.canvas, canvas_width//2 - button_width//2, start_y,
                                   button_width, button_height, "▶  Play", self.choose_mode,
                                   radius=20)
        self.create_rounded_button(self.canvas, canvas_width//2 - button_width//2, start_y + button_height + 15,
                                   button_width, button_height, "⚙  Settings", self.show_settings_screen,
                                   radius=20)
        self.create_rounded_button(self.canvas, canvas_width//2 - button_width//2, start_y + (button_height + 15)*2,
                                   button_width, button_height, "🏆  Achievements", self.show_achievements_screen,
                                   radius=20)
        self.create_rounded_button(self.canvas, canvas_width//2 - button_width//2, start_y + (button_height + 15)*3,
                                   button_width, button_height, "ℹ  About", self.show_about_screen,
                                   radius=20)
        self.create_rounded_button(self.canvas, canvas_width//2 - button_width//2, start_y + (button_height + 15)*4,
                                   button_width, button_height, "✖  Exit", self.exit_game,
                                   radius=20)

    # ---------- MODE CHOICE SCREEN (BUILT-IN) ----------
    def show_mode_choice_screen(self):
        self.reset_canvas()
        self.stop_all_animations()
        self.in_mode_choice = True
        self.in_settings = False
        self.in_about = False
        self.in_achievements = False
        self.game_running = False
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 100 or canvas_height < 100:
            self.canvas.after(100, self.show_mode_choice_screen)
            return
        
        theme = self.themes[self.settings["theme"]]
        self.canvas.config(bg=theme["bg"])
        for i in range(0, int(canvas_height), 2):
            alpha = 0.3 + 0.7 * (i / canvas_height)
            color = f"#{int(10 + 10 * alpha):02x}{int(10 + 20 * alpha):02x}{int(42 + 30 * alpha):02x}"
            self.canvas.create_line(0, i, canvas_width, i, fill=color, tags="mode_bg")
        for _ in range(40):
            xs = random.randint(0, canvas_width)
            ys = random.randint(0, canvas_height)
            sz = random.randint(1, 2)
            br = random.randint(100, 200)
            self.canvas.create_oval(xs-sz, ys-sz, xs+sz, ys+sz,
                                    fill=f"#{br:02x}{br:02x}ff", outline="", tags="mode_bg")
        
        self.canvas.create_text(canvas_width//2, 120,
                               text="Choose number of blocks",
                               font=("Arial", 36, "bold"),
                               fill=theme["fg"], tags="mode_text")
        self.canvas.create_line(canvas_width//2 - 150, 155, canvas_width//2 + 150, 155,
                               fill=theme["line"], width=1, tags="mode_text")
        
        btn_width = 80
        btn_height = 80
        spacing = 30
        total_width = 4 * btn_width + 3 * spacing
        start_x = (canvas_width - total_width) // 2
        y_btns = canvas_height//2 - btn_height//2
        
        for i in range(1, 5):
            x = start_x + (i-1) * (btn_width + spacing)
            rect = self.canvas.create_rectangle(x, y_btns, x+btn_width, y_btns+btn_height,
                                                fill=theme["button"], outline=theme["line"], width=2,
                                                tags="mode_button")
            text_id = self.canvas.create_text(x + btn_width//2, y_btns + btn_height//2,
                                              text=str(i), font=("Arial", 28, "bold"),
                                              fill=theme["button_text"], tags="mode_button")
            sub = self.canvas.create_text(x + btn_width//2, y_btns + btn_height + 20,
                                          text="blocks", font=("Arial", 12),
                                          fill=theme["fg2"], tags="mode_button")
            def make_click(num=i):
                def click(e):
                    self.start_game(num)
                return click
            self.canvas.tag_bind(rect, "<Button-1>", make_click())
            self.canvas.tag_bind(text_id, "<Button-1>", make_click())
            self.canvas.tag_bind(sub, "<Button-1>", make_click())
            def make_enter(rect=rect):
                def enter(e):
                    self.canvas.itemconfig(rect, fill=theme["button_hover"])
                return enter
            def make_leave(rect=rect):
                def leave(e):
                    self.canvas.itemconfig(rect, fill=theme["button"])
                return leave
            self.canvas.tag_bind(rect, "<Enter>", make_enter())
            self.canvas.tag_bind(rect, "<Leave>", make_leave())
            self.canvas.tag_bind(text_id, "<Enter>", make_enter())
            self.canvas.tag_bind(text_id, "<Leave>", make_leave())
            self.canvas.tag_bind(sub, "<Enter>", make_enter())
            self.canvas.tag_bind(sub, "<Leave>", make_leave())
        
        # Back button
        self.create_rounded_button(self.canvas, canvas_width//2 - 80, canvas_height - 80,
                                   160, 40, "← Back", self.show_main_menu,
                                   radius=10)

    def choose_mode(self):
        self.show_mode_choice_screen()

    # ---------- ACHIEVEMENTS SCREEN ----------
    def show_achievements_screen(self):
        self.reset_canvas()
        self.stop_all_animations()
        self.in_achievements = True
        self.in_settings = False
        self.in_about = False
        self.in_mode_choice = False
        self.game_running = False
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 100 or canvas_height < 100:
            self.canvas.after(100, self.show_achievements_screen)
            return

        theme = self.themes[self.settings["theme"]]
        self.canvas.config(bg=theme["bg"])
        for i in range(0, int(canvas_height), 2):
            alpha = 0.3 + 0.7 * (i / canvas_height)
            color = f"#{int(10 + 10 * alpha):02x}{int(10 + 20 * alpha):02x}{int(42 + 30 * alpha):02x}"
            self.canvas.create_line(0, i, canvas_width, i, fill=color, tags="ach_bg")
        for _ in range(40):
            xs = random.randint(0, canvas_width)
            ys = random.randint(0, canvas_height)
            sz = random.randint(1, 2)
            br = random.randint(100, 200)
            self.canvas.create_oval(xs-sz, ys-sz, xs+sz, ys+sz,
                                    fill=f"#{br:02x}{br:02x}ff", outline="", tags="ach_bg")

        self.canvas.create_text(canvas_width//2, 70,
                               text="🏆 ACHIEVEMENTS", font=("Arial", 36, "bold"),
                               fill=theme["glow"], tags="ach_text")
        self.canvas.create_line(canvas_width//2 - 150, 95, canvas_width//2 + 150, 95,
                               fill=theme["line"], width=1, tags="ach_text")

        list_frame = tk.Frame(self.canvas, bg=theme["bg3"], bd=0)
        list_frame.place(x=30, y=120, width=canvas_width-60, height=canvas_height-190)

        inner_frame = tk.Frame(list_frame, bg=theme["bg3"], bd=2, relief="solid")
        inner_frame.pack(expand=True, fill="both", padx=2, pady=2)
        inner_frame.configure(bg=theme["bg3"])

        canvas_list = tk.Canvas(inner_frame, bg=theme["bg2"], highlightthickness=0)
        scrollbar = tk.Scrollbar(inner_frame, orient="vertical", command=canvas_list.yview)
        scrollable_frame = tk.Frame(canvas_list, bg=theme["bg2"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_list.configure(scrollregion=canvas_list.bbox("all"))
        )
        canvas_list.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_list.configure(yscrollcommand=scrollbar.set)

        canvas_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        basic_keys = ["first_hit", "combo_10", "combo_20", "combo_50", "mode4", "record5"]
        hit_keys = [f"hits_{i}" for i in range(100, 40001, 100)]
        gold_keys = ["gold_10", "gold_25", "gold_50", "gold_100", "gold_250", "gold_500", "gold_1000"]
        score_keys = ["score_50", "score_100", "score_250", "score_500", "score_1000",
                      "score_2500", "score_5000", "score_10000", "score_25000", "score_50000", "score_100000"]
        all_keys = basic_keys + hit_keys + gold_keys + score_keys

        cols = 4
        rows = (len(all_keys) + cols - 1) // cols

        for row in range(rows):
            for col in range(cols):
                idx = row * cols + col
                if idx >= len(all_keys):
                    break
                key = all_keys[idx]
                text = self.all_achievements.get(key, key)
                unlocked = key in self.unlocked_achievements
                status_icon = "✅" if unlocked else "🔒"
                color = "#66ff66" if unlocked else "#666666"

                cell = tk.Frame(scrollable_frame, bg=theme["bg2"], bd=1, relief="solid")
                cell.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
                cell.columnconfigure(0, weight=1)
                icon_label = tk.Label(cell, text=status_icon, font=("Segoe UI", 12),
                                      bg=theme["bg2"], fg=color)
                icon_label.grid(row=0, column=0, padx=2, pady=2, sticky="w")
                name_label = tk.Label(cell, text=text, font=("Segoe UI", 11),
                                      bg=theme["bg2"], fg=theme["fg"], anchor="w")
                name_label.grid(row=0, column=1, padx=2, pady=2, sticky="w")
                if unlocked:
                    check_label = tk.Label(cell, text="✔", font=("Segoe UI", 10),
                                           bg=theme["bg2"], fg="#66ff66")
                    check_label.grid(row=0, column=2, padx=2, pady=2, sticky="e")
                else:
                    check_label = tk.Label(cell, text="—", font=("Segoe UI", 10),
                                           bg=theme["bg2"], fg="#444444")
                    check_label.grid(row=0, column=2, padx=2, pady=2, sticky="e")

        for col in range(cols):
            scrollable_frame.columnconfigure(col, weight=1)

        self.create_rounded_button(self.canvas, canvas_width//2 - 80, canvas_height - 70,
                                   160, 40, "← Back", self.show_main_menu,
                                   radius=10)

    # ---------- ABOUT SCREEN ----------
    def show_about_screen(self):
        self.reset_canvas()
        self.stop_all_animations()
        self.in_about = True
        self.in_settings = False
        self.in_achievements = False
        self.in_mode_choice = False
        self.game_running = False
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 100 or canvas_height < 100:
            self.canvas.after(100, self.show_about_screen)
            return

        theme = self.themes[self.settings["theme"]]
        self.canvas.config(bg=theme["bg"])
        for i in range(0, int(canvas_height), 2):
            alpha = 0.3 + 0.7 * (i / canvas_height)
            color = f"#{int(10 + 10 * alpha):02x}{int(10 + 20 * alpha):02x}{int(42 + 30 * alpha):02x}"
            self.canvas.create_line(0, i, canvas_width, i, fill=color, tags="about_bg")
        for _ in range(60):
            xs = random.randint(0, canvas_width)
            ys = random.randint(0, canvas_height)
            sz = random.randint(1, 2)
            br = random.randint(100, 255)
            self.canvas.create_oval(xs-sz, ys-sz, xs+sz, ys+sz,
                                    fill=f"#{br:02x}{br:02x}ff", outline="", tags="about_bg")

        self.canvas.create_text(canvas_width//2, 80,
                               text="🌟 ABOUT", font=("Arial", 40, "bold"),
                               fill=theme["glow"], tags="about_text")
        self.canvas.create_text(canvas_width//2, 130,
                               text="─  •  ─  •  ─  •  ─", font=("Arial", 18),
                               fill=theme["fg3"], tags="about_text")
        self.canvas.create_text(canvas_width//2, 165,
                               text="AIM Wailtrum v1.0", font=("Arial", 16),
                               fill=theme["fg3"], tags="about_text")

        text_frame = tk.Frame(self.canvas, bg=theme["bg3"], bd=0)
        text_frame.place(x=50, y=200, width=canvas_width-100, height=canvas_height-300)
        inner_frame = tk.Frame(text_frame, bg=theme["bg3"], bd=2, relief="solid")
        inner_frame.pack(expand=True, fill="both", padx=3, pady=3)
        inner_frame.configure(bg=theme["bg3"])

        scrollbar = tk.Scrollbar(inner_frame)
        scrollbar.pack(side="right", fill="y")

        about_text = tk.Text(inner_frame, 
                             font=("Segoe UI", 12), 
                             fg=theme["fg"], 
                             bg=theme["bg2"],
                             wrap="word",
                             yscrollcommand=scrollbar.set,
                             relief="flat",
                             padx=20,
                             pady=20,
                             spacing1=4,
                             spacing2=2,
                             spacing3=6)
        about_text.pack(expand=True, fill="both")
        scrollbar.config(command=about_text.yview)

        about_text.tag_config("header", font=("Segoe UI", 18, "bold"), foreground=theme["glow"], spacing3=10)
        about_text.tag_config("subheader", font=("Segoe UI", 14, "bold"), foreground="#88bbff", spacing3=8)
        about_text.tag_config("highlight", font=("Segoe UI", 13, "bold"), foreground="#ffaa66")
        about_text.tag_config("accent", font=("Segoe UI", 13, "bold"), foreground="#66ff66")
        about_text.tag_config("em", font=("Segoe UI", 13, "italic"), foreground=theme["fg2"])
        about_text.tag_config("divider", font=("Segoe UI", 10), foreground=theme["line"])
        about_text.tag_config("list", lmargin1=20, lmargin2=30, spacing3=4)

        about_text.insert("end", "\n✨ WELCOME TO AIM WAILTRUM ✨\n\n", "header")
        about_text.insert("end", "━"*40 + "\n\n", "divider")
        
        about_text.insert("end", "🎯 MAIN IDEA\n", "subheader")
        about_text.insert("end", "This is a reaction and speed game!\n", "em")
        about_text.insert("end", "Your task is to click on appearing blocks faster than they can move.\n\n", "")
        
        about_text.insert("end", "━"*40 + "\n\n", "divider")
        
        about_text.insert("end", "🏆 GAME GOAL\n", "subheader")
        about_text.insert("end", "Score as many points as possible!\n", "em")
        about_text.insert("end", "Each hit on a block gives you ", "")
        about_text.insert("end", "+1 point", "highlight")
        about_text.insert("end", " (or +5 for golden block).\nThe faster you click — the higher your score!\n\n", "")
        
        about_text.insert("end", "━"*40 + "\n\n", "divider")
        
        about_text.insert("end", "⚙️ MODES\n", "subheader")
        about_text.insert("end", "You can choose the number of blocks:\n", "")
        about_text.insert("end", "• 1 block – classic mode\n", "list")
        about_text.insert("end", "• 2, 3 or 4 blocks – multiple targets at once\n\n", "list")
        
        about_text.insert("end", "━"*40 + "\n\n", "divider")
        
        about_text.insert("end", "⚙️ SETTINGS\n", "subheader")
        about_text.insert("end", "• 🎨 Block color\n", "list")
        about_text.insert("end", "• 📊 Difficulty (speed and size)\n", "list")
        about_text.insert("end", "• 👤 Profile (nickname & avatar)\n\n", "list")
        
        about_text.insert("end", "━"*40 + "\n\n", "divider")
        
        about_text.insert("end", "🖥️ CONTROLS\n", "subheader")
        about_text.insert("end", "• 🖱️ Click on a block — +1 point\n", "list")
        about_text.insert("end", "• ⌨️ ESC — exit fullscreen\n", "list")
        about_text.insert("end", "• 🔙 Menu button — return to main menu\n\n", "list")
        
        about_text.insert("end", "━"*40 + "\n\n", "divider")
        
        about_text.insert("end", "💡 TIPS\n", "subheader")
        about_text.insert("end", "• Keep an eye on all blocks\n", "list")
        about_text.insert("end", "• In 4-block mode, train your peripheral vision\n\n", "list")
        
        about_text.insert("end", "━"*40 + "\n\n", "divider")
        
        about_text.insert("end", "\nGame creator: Winsyiwosh\n", "accent")
        
        about_text.config(state="disabled")

        self.create_rounded_button(self.canvas, canvas_width//2 - 100, canvas_height - 70,
                                   200, 45, "← Back", self.show_main_menu,
                                   radius=20)

    # ---------- AVATAR SELECTOR ----------
    def show_avatar_selector(self):
        avatar_window = tk.Toplevel(self.root)
        avatar_window.title("Choose Avatar")
        avatar_window.geometry("500x350")
        avatar_window.resizable(False, False)
        theme = self.themes[self.settings["theme"]]
        avatar_window.configure(bg=theme["bg"])
        avatar_window.transient(self.root)
        avatar_window.grab_set()
        
        # Центрируем окно
        avatar_window.update_idletasks()
        x = (self.root.winfo_width() - 500) // 2
        y = (self.root.winfo_height() - 350) // 2
        avatar_window.geometry(f"+{x}+{y}")
        avatar_window.bind("<Escape>", lambda e: avatar_window.destroy())
        
        # Заголовок
        tk.Label(avatar_window, text="Choose your avatar", 
                font=("Arial", 20, "bold"), fg=theme["fg"], bg=theme["bg"]).pack(pady=15)
        
        # Список аватарок (эмодзи)
        avatars = ["👤", "😊", "😎", "🤩", "🔥", "⭐", "🌟", "💪", "🎯", "🚀", "💎", "👑", "🦊", "🐺", "🦅", "🐉"]
        
        # Frame для сетки
        grid_frame = tk.Frame(avatar_window, bg=theme["bg"])
        grid_frame.pack(pady=10, padx=20, expand=True, fill="both")
        
        # Создаём кнопки для каждой аватарки
        selected_avatar = tk.StringVar(value=self.avatar)
        
        for i, av in enumerate(avatars):
            row = i // 4
            col = i % 4
            btn = tk.Button(grid_frame, text=av, font=("Arial", 28),
                           width=4, height=1,
                           bg=theme["button"], fg=theme["fg"],
                           activebackground=theme["button_hover"],
                           relief="flat", bd=1,
                           cursor="hand2")
            btn.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            # Подсветка выбранной аватарки
            if av == self.avatar:
                btn.config(bg=theme["glow"], fg="white")
            
            def make_select(a=av, b=btn):
                def select():
                    # Снимаем выделение со всех
                    for child in grid_frame.winfo_children():
                        child.config(bg=theme["button"], fg=theme["fg"])
                    b.config(bg=theme["glow"], fg="white")
                    selected_avatar.set(a)
                    self.avatar = a
                    self.save_profile()
                    avatar_window.destroy()
                    self.show_settings_screen()  # обновляем настройки
                return select
            btn.config(command=make_select())
        
        # Кнопка Cancel
        cancel_btn = tk.Button(avatar_window, text="Cancel", font=("Arial", 14),
                              bg=theme["button"], fg=theme["fg"],
                              activebackground=theme["button_hover"],
                              relief="flat", bd=0,
                              padx=20, pady=5,
                              cursor="hand2",
                              command=avatar_window.destroy)
        cancel_btn.pack(pady=15)

    # ---------- SETTINGS SCREEN (with Nickname & Avatar) ----------
    def show_settings_screen(self):
        self.reset_canvas()
        self.stop_all_animations()
        self.in_settings = True
        self.in_about = False
        self.in_achievements = False
        self.in_mode_choice = False
        self.game_running = False
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 100 or canvas_height < 100:
            self.canvas.after(100, self.show_settings_screen)
            return

        theme = self.themes[self.settings["theme"]]
        self.canvas.config(bg=theme["bg"])
        for i in range(0, int(canvas_height), 2):
            alpha = 0.3 + 0.7 * (i / canvas_height)
            color = f"#{int(10 + 10 * alpha):02x}{int(10 + 20 * alpha):02x}{int(42 + 30 * alpha):02x}"
            self.canvas.create_line(0, i, canvas_width, i, fill=color, tags="settings_bg")
        for _ in range(30):
            xs = random.randint(0, canvas_width)
            ys = random.randint(0, canvas_height)
            sz = random.randint(1, 2)
            br = random.randint(60, 120)
            self.canvas.create_oval(xs-sz, ys-sz, xs+sz, ys+sz,
                                    fill=f"#{br:02x}{br:02x}ff", outline="", tags="settings_bg")

        self.canvas.create_text(canvas_width//2, 80,
                               text="Settings", font=("Segoe UI", 32, "bold"),
                               fill=theme["fg"], tags="settings_text")
        self.canvas.create_line(canvas_width//2 - 100, 105, canvas_width//2 + 100, 105,
                               fill=theme["line"], width=1, tags="settings_text")

        left_margin = 160
        y_color_label = 115
        self.canvas.create_text(left_margin, y_color_label,
                               text="Color", font=("Segoe UI", 14, "bold"),
                               fill=theme["fg2"], anchor="w", tags="settings_text")

        colors = [
            ("#ff4444", "red"),
            ("#4488ff", "blue"),
            ("#44cc44", "green"),
            ("#ffcc00", "yellow"),
            ("#aa44ff", "purple"),
            ("#ff8800", "orange"),
            ("#ff6b6b", "coral"),
            ("#ff9ff3", "pink"),
            ("#54a0ff", "lightblue"),
            ("#1dd1a1", "teal"),
            ("#feca57", "gold"),
            ("#a29bfe", "lavender")
        ]
        self.color_var = tk.StringVar(value=self.settings["color"])
        y_color = 150
        size = 14
        spacing_x = 55
        spacing_y = 35
        cols = 4
        rows = 3
        start_x = left_margin + 30

        color_items = []
        for row in range(rows):
            for col in range(cols):
                idx = row * cols + col
                if idx >= len(colors):
                    break
                hex_col, name = colors[idx]
                x = start_x + col * spacing_x
                y = y_color + row * (size*2 + spacing_y)
                shadow = self.canvas.create_oval(x - size + 2, y - size + 2,
                                                 x + size + 2, y + size + 2,
                                                 fill="#000000", outline="", tags="color_shadow")
                circle = self.canvas.create_oval(x - size, y - size, x + size, y + size,
                                                 fill=hex_col, outline=theme["fg3"], width=2,
                                                 tags="color_circle")
                select_ring = self.canvas.create_oval(x - size - 4, y - size - 4,
                                                      x + size + 4, y + size + 4,
                                                      outline="#ffffff", width=2, state="hidden",
                                                      tags="color_select")
                label = self.canvas.create_text(x, y + size + 14,
                                                text=name.capitalize(), font=("Segoe UI", 8),
                                                fill=theme["fg3"], state="hidden", tags="color_label")
                color_items.append((circle, select_ring, label, name))
                if self.color_var.get() == name:
                    self.canvas.itemconfig(select_ring, state="normal")
                    self.canvas.itemconfig(label, state="normal")

        for circle, select_ring, label, name in color_items:
            def make_click(c=name, ring=select_ring):
                def click(e):
                    for item in self.canvas.find_withtag("color_select"):
                        self.canvas.itemconfig(item, state="hidden")
                    for item in self.canvas.find_withtag("color_label"):
                        self.canvas.itemconfig(item, state="hidden")
                    self.canvas.itemconfig(ring, state="normal")
                    self.canvas.itemconfig(label, state="normal")
                    self.color_var.set(c)
                    self.settings["color"] = c
                return click
            self.canvas.tag_bind(circle, "<Button-1>", make_click())
            self.canvas.tag_bind(label, "<Button-1>", make_click())
            def make_enter(circ=circle, lab=label):
                def enter(e):
                    self.canvas.itemconfig(circ, outline="#ffffff", width=3)
                    self.canvas.itemconfig(lab, state="normal")
                return enter
            def make_leave(circ=circle, lab=label):
                def leave(e):
                    self.canvas.itemconfig(circ, outline=theme["fg3"], width=2)
                    if self.color_var.get() != name:
                        self.canvas.itemconfig(lab, state="hidden")
                return leave
            self.canvas.tag_bind(circle, "<Enter>", make_enter())
            self.canvas.tag_bind(circle, "<Leave>", make_leave())
            self.canvas.tag_bind(label, "<Enter>", make_enter())
            self.canvas.tag_bind(label, "<Leave>", make_leave())

        y_diff_label = 370
        self.canvas.create_text(left_margin, y_diff_label,
                               text="Difficulty", font=("Segoe UI", 14, "bold"),
                               fill=theme["fg2"], anchor="w", tags="settings_text")

        diff_var = tk.StringVar(value=self.settings["difficulty"])
        diff_options = [("easy","Easy","#2e7d32"),("medium","Medium","#f57c00"),("hard","Hard","#c62828")]
        y_diff = 395
        btn_width = 100
        btn_height = 40
        spacing_diff = 15
        start_x_diff = left_margin

        def draw_round_rect(x1, y1, x2, y2, radius, fill_color, outline_color):
            points = []
            points.append((x1 + radius, y1))
            points.append((x2 - radius, y1))
            for angle in range(0, 91, 10):
                rad = math.radians(angle)
                points.append((x2 - radius + radius * math.cos(rad), 
                               y1 + radius - radius * math.sin(rad)))
            points.append((x2, y1 + radius))
            points.append((x2, y2 - radius))
            for angle in range(0, 91, 10):
                rad = math.radians(angle)
                points.append((x2 - radius + radius * math.sin(rad), 
                               y2 - radius + radius * math.cos(rad)))
            points.append((x2 - radius, y2))
            points.append((x1 + radius, y2))
            for angle in range(0, 91, 10):
                rad = math.radians(angle)
                points.append((x1 + radius - radius * math.cos(rad), 
                               y2 - radius + radius * math.sin(rad)))
            points.append((x1, y2 - radius))
            points.append((x1, y1 + radius))
            for angle in range(0, 91, 10):
                rad = math.radians(angle)
                points.append((x1 + radius - radius * math.sin(rad), 
                               y1 + radius - radius * math.cos(rad)))
            return self.canvas.create_polygon(points, fill=fill_color, outline=outline_color, width=2)

        for i, (value, label, color) in enumerate(diff_options):
            x = start_x_diff + i * (btn_width + spacing_diff)
            is_active = (diff_var.get() == value)
            bg_color = color if is_active else theme["button"]
            border_color = color if is_active else theme["line"]
            shadow_rect = draw_round_rect(x+3, y_diff+3, x+btn_width+3, y_diff+btn_height+3,
                                          radius=12, fill_color="#000000", outline_color="#000000")
            rect = draw_round_rect(x, y_diff, x+btn_width, y_diff+btn_height,
                                   radius=12, fill_color=bg_color, outline_color=border_color)
            text_id = self.canvas.create_text(x + btn_width//2, y_diff + btn_height//2,
                                              text=label, font=("Segoe UI", 12, "bold"),
                                              fill="white", tags="diff_button")

            def make_diff_click(val=value, rect=rect, text_id=text_id):
                def click(e):
                    diff_var.set(val)
                    self.settings["difficulty"] = val
                    self.show_settings_screen()
                return click
            self.canvas.tag_bind(rect, "<Button-1>", make_diff_click())
            self.canvas.tag_bind(text_id, "<Button-1>", make_diff_click())
            def make_enter_diff(rect=rect):
                def enter(e):
                    if diff_var.get() != value:
                        self.canvas.itemconfig(rect, fill=theme["button_hover"])
                return enter
            def make_leave_diff(rect=rect):
                def leave(e):
                    if diff_var.get() != value:
                        self.canvas.itemconfig(rect, fill=theme["button"])
                return leave
            self.canvas.tag_bind(rect, "<Enter>", make_enter_diff())
            self.canvas.tag_bind(rect, "<Leave>", make_leave_diff())
            self.canvas.tag_bind(text_id, "<Enter>", make_enter_diff())
            self.canvas.tag_bind(text_id, "<Leave>", make_leave_diff())

        y_shape_label = 490
        self.canvas.create_text(left_margin, y_shape_label,
                               text="Shape", font=("Segoe UI", 14, "bold"),
                               fill=theme["fg2"], anchor="w", tags="settings_text")
        
        shape_var = tk.StringVar(value=self.settings["shape"])
        shape_options = [("square", "■ Square"), ("circle", "● Circle"), ("triangle", "▲ Triangle")]
        y_shape = 515
        shape_btn_width = 110
        shape_btn_height = 40
        spacing_shape = 15
        start_x_shape = left_margin

        for i, (value, label) in enumerate(shape_options):
            x = start_x_shape + i * (shape_btn_width + spacing_shape)
            is_active = (shape_var.get() == value)
            bg_color = theme["button"] if not is_active else theme["glow"]
            border_color = theme["glow"] if is_active else theme["line"]
            rect = draw_round_rect(x, y_shape, x+shape_btn_width, y_shape+shape_btn_height,
                                   radius=12, fill_color=bg_color, outline_color=border_color)
            text_id = self.canvas.create_text(x + shape_btn_width//2, y_shape + shape_btn_height//2,
                                              text=label, font=("Segoe UI", 11, "bold"),
                                              fill="white" if is_active else theme["fg"], tags="shape_button")
            def make_shape_click(val=value, rect=rect, text_id=text_id):
                def click(e):
                    if val != self.settings["shape"]:
                        self.settings["shape"] = val
                        shape_var.set(val)
                        self.show_settings_screen()
                return click
            self.canvas.tag_bind(rect, "<Button-1>", make_shape_click())
            self.canvas.tag_bind(text_id, "<Button-1>", make_shape_click())
            def make_enter_shape(rect=rect):
                def enter(e):
                    if shape_var.get() != value:
                        self.canvas.itemconfig(rect, fill=theme["button_hover"])
                return enter
            def make_leave_shape(rect=rect):
                def leave(e):
                    if shape_var.get() != value:
                        self.canvas.itemconfig(rect, fill=theme["button"])
                return leave
            self.canvas.tag_bind(rect, "<Enter>", make_enter_shape())
            self.canvas.tag_bind(rect, "<Leave>", make_leave_shape())
            self.canvas.tag_bind(text_id, "<Enter>", make_enter_shape())
            self.canvas.tag_bind(text_id, "<Leave>", make_leave_shape())

        y_theme_label = 620
        self.canvas.create_text(left_margin, y_theme_label,
                               text="Theme", font=("Segoe UI", 14, "bold"),
                               fill=theme["fg2"], anchor="w", tags="settings_text")
        y_theme = 645
        theme_btn_width = 100
        theme_btn_height = 40
        spacing_theme = 15
        theme_var = tk.StringVar(value=self.settings["theme"])
        theme_options = [("dark","Dark"), ("light","Light")]
        start_x_theme = left_margin

        for i, (value, label) in enumerate(theme_options):
            x = start_x_theme + i * (theme_btn_width + spacing_theme)
            is_active = (theme_var.get() == value)
            bg_color = theme["button"] if not is_active else theme["glow"]
            border_color = theme["glow"] if is_active else theme["line"]
            rect = draw_round_rect(x, y_theme, x+theme_btn_width, y_theme+theme_btn_height,
                                   radius=12, fill_color=bg_color, outline_color=border_color)
            text_id = self.canvas.create_text(x + theme_btn_width//2, y_theme + theme_btn_height//2,
                                              text=label, font=("Segoe UI", 12, "bold"),
                                              fill="white" if is_active else theme["fg"], tags="theme_button")
            def make_theme_click(val=value, rect=rect, text_id=text_id):
                def click(e):
                    if val != self.settings["theme"]:
                        self.settings["theme"] = val
                        theme_var.set(val)
                        self.show_settings_screen()
                return click
            self.canvas.tag_bind(rect, "<Button-1>", make_theme_click())
            self.canvas.tag_bind(text_id, "<Button-1>", make_theme_click())
            def make_enter_theme(rect=rect):
                def enter(e):
                    if theme_var.get() != value:
                        self.canvas.itemconfig(rect, fill=theme["button_hover"])
                return enter
            def make_leave_theme(rect=rect):
                def leave(e):
                    if theme_var.get() != value:
                        self.canvas.itemconfig(rect, fill=theme["button"])
                return leave
            self.canvas.tag_bind(rect, "<Enter>", make_enter_theme())
            self.canvas.tag_bind(rect, "<Leave>", make_leave_theme())
            self.canvas.tag_bind(text_id, "<Enter>", make_enter_theme())
            self.canvas.tag_bind(text_id, "<Leave>", make_leave_theme())

        # ---------- NICKNAME & AVATAR ----------
        y_profile_label = 730
        self.canvas.create_text(left_margin, y_profile_label,
                               text="Profile", font=("Segoe UI", 14, "bold"),
                               fill=theme["fg2"], anchor="w", tags="settings_text")
        y_profile = 755
        
        # Текущий аватар
        avatar_display = self.canvas.create_text(left_margin + 20, y_profile + 20,
                                                  text=self.avatar, font=("Arial", 28),
                                                  fill=theme["fg"], tags="settings_text")
        
        # Кнопка "Change Avatar"
        def change_avatar():
            self.show_avatar_selector()
        
        self.create_rounded_button(self.canvas, left_margin + 70, y_profile,
                                   160, 40, "Change Avatar", change_avatar,
                                   radius=10, color="#6a1b9a", hover_color="#7b1fa2",
                                   text_color="white", font_size=12)
        
        # Поле ввода ника
        nick_label = self.canvas.create_text(left_margin, y_profile + 60,
                                             text="Nickname:", font=("Segoe UI", 12),
                                             fill=theme["fg2"], anchor="w", tags="settings_text")
        nick_var = tk.StringVar(value=self.nickname)
        nick_entry = tk.Entry(self.canvas, textvariable=nick_var,
                              font=("Segoe UI", 14),
                              bg=theme["bg2"], fg=theme["fg"],
                              insertbackground=theme["fg"],
                              relief="flat", bd=2,
                              width=20)
        nick_entry.place(x=left_margin + 100, y=y_profile + 50, width=200, height=35)
        # Рамка
        self.canvas.create_rectangle(left_margin + 98, y_profile + 48,
                                     left_margin + 302, y_profile + 87,
                                     outline=theme["line"], width=1,
                                     tags="settings_text")
        
        # Кнопка сохранить ник
        def save_nick():
            new_nick = nick_var.get().strip()
            if new_nick:
                self.nickname = new_nick
                self.save_profile()
                self.canvas.create_text(left_margin + 330, y_profile + 67,
                                        text="✅ Saved!", font=("Segoe UI", 12),
                                        fill="#66ff66", tags="settings_text")
                self.canvas.after(2000, lambda: self.canvas.delete("settings_text_saved"))
            else:
                self.canvas.create_text(left_margin + 330, y_profile + 67,
                                        text="❌ Enter a name!", font=("Segoe UI", 12),
                                        fill="#ff6666", tags="settings_text")
                self.canvas.after(2000, lambda: self.canvas.delete("settings_text_saved"))
        
        self.create_rounded_button(self.canvas, left_margin + 310, y_profile + 50,
                                   100, 35, "Save", save_nick,
                                   radius=10, color="#2e7d32", hover_color="#388e3c",
                                   text_color="white", font_size=11)

        # Кнопка "Back"
        self.create_rounded_button(self.canvas, left_margin, canvas_height - 70,
                                   160, 40, "← Back", self.show_main_menu,
                                   radius=10)

    # ---------- GAME ----------
    def start_game(self, num_targets=1):
        self.reset_canvas()
        self.stop_all_animations()
        self.game_running = True
        self.score = 0
        self.num_targets = num_targets
        self.targets = []
        self.in_about = False
        self.in_settings = False
        self.in_achievements = False
        self.in_mode_choice = False
        
        self.unlocked_achievements.clear()
        self.total_hits = 0
        self.gold_hits = 0
        self.record_breaks = 0
        self.achievement_notifications.clear()
        
        self.combo = 0
        self.combo_multiplier = 1
        if self.combo_timer_id:
            self.canvas.after_cancel(self.combo_timer_id)
            self.combo_timer_id = None
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 100 or canvas_height < 100:
            self.canvas.after(100, lambda: self.start_game(num_targets))
            return
        
        theme = self.themes[self.settings["theme"]]
        self.canvas.config(bg=theme["bg"])
        for i in range(0, int(canvas_height), 2):
            alpha = 0.3 + 0.7 * (i / canvas_height)
            color = f"#{int(10 + 20 * alpha):02x}{int(10 + 30 * alpha):02x}{int(40 + 60 * alpha):02x}"
            self.canvas.create_line(0, i, canvas_width, i, fill=color, tags="game_bg")
        
        self.create_stars(count=120, y_start=-200, y_end=canvas_height)
        
        # Отображаем ник с аватаром в игре
        display_name = f"{self.avatar} {self.nickname}" if self.nickname else f"{self.avatar} Guest"
        self.score_label = self.canvas.create_text(canvas_width//2, 40,
                                                   text=f"Score: 0",
                                                   font=("Arial", 28, "bold"),
                                                   fill=theme["fg"])
        self.record_label = self.canvas.create_text(canvas_width//2, 75,
                                                    text=f"🏆 Record: {self.record}",
                                                    font=("Arial", 16),
                                                    fill=theme["glow"])
        self.nick_label = self.canvas.create_text(canvas_width//2, 100,
                                                   text=f"{display_name}",
                                                   font=("Arial", 14),
                                                   fill=theme["fg2"])
        self.combo_display = self.canvas.create_text(canvas_width//2, 130,
                                                     text="",
                                                     font=("Arial", 20, "bold"),
                                                     fill="#ffaa00")
        
        self.game_area = self.canvas.create_rectangle(20, 150, canvas_width-20, canvas_height-100,
                                                      fill=theme["game_bg"], outline=theme["game_outline"], width=2,
                                                      stipple="gray50")
        self.canvas.tag_bind("game_area", "<Button-1>", self.on_miss_click)
        
        for i in range(self.num_targets):
            self.create_single_target(i)
        
        self.create_rounded_button(self.canvas, canvas_width//2 - 100, canvas_height - 80,
                                   200, 45, "☰ Menu", self.stop_game_and_menu,
                                   radius=15)
        
        self.animate_effects()
        self.animate_achievements()

    def on_miss_click(self, event):
        if not self.game_running:
            return
        self.reset_combo()

    def update_combo(self):
        if not self.game_running:
            return
        self.combo += 1
        if self.combo < 3:
            self.combo_multiplier = 1
        elif self.combo < 6:
            self.combo_multiplier = 2
        elif self.combo < 9:
            self.combo_multiplier = 3
        elif self.combo < 12:
            self.combo_multiplier = 4
        else:
            self.combo_multiplier = 5
        
        if self.combo < 3:
            self.canvas.itemconfig(self.combo_display, text="")
        else:
            self.canvas.itemconfig(self.combo_display, text=f"🔥 x{self.combo_multiplier}")
        
        if self.combo_timer_id:
            self.canvas.after_cancel(self.combo_timer_id)
        self.combo_timer_id = self.canvas.after(2000, self.reset_combo)
        
        self.check_achievements()

    def reset_combo(self):
        if not self.game_running:
            return
        self.combo = 0
        self.combo_multiplier = 1
        self.canvas.itemconfig(self.combo_display, text="")
        if self.combo_timer_id:
            self.canvas.after_cancel(self.combo_timer_id)
            self.combo_timer_id = None

    # ---------- ANIMATION SHRINK ----------
    def animate_shrink(self, item_id, callback=None):
        coords = self.canvas.coords(item_id)
        if not coords:
            if callback:
                callback()
            return
        xs = coords[0::2]
        ys = coords[1::2]
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        orig_w = x2 - x1
        orig_h = y2 - y1
        steps = 25
        step_time = 15
        current_step = 0
        
        def shrink_step():
            nonlocal current_step
            if not self.game_running:
                if callback:
                    callback()
                return
            current_step += 1
            progress = current_step / steps
            ease = 1 - (1 - progress) ** 2
            current_scale = 1 - ease
            new_w = orig_w * current_scale
            new_h = orig_h * current_scale
            if new_w < 1 and new_h < 1:
                self.canvas.delete(item_id)
                if callback:
                    callback()
                return
            shape = self.settings["shape"]
            if shape == "triangle":
                r = orig_w / 2
                points = [
                    cx, cy - r * current_scale,
                    cx - r * math.sin(math.radians(60)) * current_scale, cy + r * math.cos(math.radians(60)) * current_scale,
                    cx + r * math.sin(math.radians(60)) * current_scale, cy + r * math.cos(math.radians(60)) * current_scale
                ]
                self.canvas.coords(item_id, *points)
            else:
                self.canvas.coords(item_id, cx - new_w/2, cy - new_h/2, cx + new_w/2, cy + new_h/2)
            if current_step < steps:
                self.canvas.after(step_time, shrink_step)
            else:
                self.canvas.delete(item_id)
                if callback:
                    callback()
        shrink_step()

    def animate_score(self, new_score):
        current_display = int(self.canvas.itemcget(self.score_label, "text").split(": ")[1])
        if current_display == new_score:
            return
        diff = new_score - current_display
        steps = 20
        step_time = 30
        current_step = 0
        
        def score_step():
            nonlocal current_step
            if not self.game_running:
                return
            current_step += 1
            progress = current_step / steps
            ease = 1 - (1 - progress) ** 2
            display_val = int(current_display + diff * ease)
            self.canvas.itemconfig(self.score_label, text=f"Score: {display_val}")
            if current_step < steps:
                self.canvas.after(step_time, score_step)
            else:
                self.canvas.itemconfig(self.score_label, text=f"Score: {new_score}")
        score_step()

    def draw_target(self, x, y, size, color, outline, tags, shape):
        if shape == "circle":
            return self.canvas.create_oval(x, y, x + size, y + size,
                                           fill=color, outline=outline, width=2,
                                           tags=tags)
        elif shape == "triangle":
            cx = x + size / 2
            cy = y + size / 2
            r = size / 2
            points = [
                cx, cy - r,
                cx - r * math.sin(math.radians(60)), cy + r * math.cos(math.radians(60)),
                cx + r * math.sin(math.radians(60)), cy + r * math.cos(math.radians(60))
            ]
            return self.canvas.create_polygon(points,
                                              fill=color, outline=outline, width=2,
                                              tags=tags)
        else:
            return self.canvas.create_rectangle(x, y, x + size, y + size,
                                                fill=color, outline=outline, width=2,
                                                tags=tags)

    def create_single_target(self, index):
        if not self.game_running:
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 100 or canvas_height < 100:
            self.canvas.after(100, lambda: self.create_single_target(index))
            return
        
        difficulty_params = {
            "easy": {"size": 70, "move_interval": 700},
            "medium": {"size": 55, "move_interval": 500},
            "hard": {"size": 45, "move_interval": 350}
        }
        params = difficulty_params.get(self.settings["difficulty"], difficulty_params["medium"])
        size = params["size"]
        move_interval = params["move_interval"]
        
        min_distance = 150
        attempts = 30
        x, y = 0, 0
        found = False
        for _ in range(attempts):
            x = random.randint(30, canvas_width - size - 30)
            y = random.randint(140, canvas_height - size - 110)
            too_close = False
            for t in self.targets:
                if t is None:
                    continue
                cx_prev, cy_prev = t['center']
                dist = math.hypot(x - cx_prev, y - cy_prev)
                if dist < min_distance:
                    too_close = True
                    break
            if not too_close:
                found = True
                break
        if not found:
            x = random.randint(30, canvas_width - size - 30)
            y = random.randint(140, canvas_height - size - 110)
        
        center = (x + size/2, y + size/2)
        
        is_bonus = random.random() < self.bonus_chance
        if is_bonus:
            color = "#ffd700"
            outline = "#ffaa00"
            tags = (f"target_{index}", "bonus")
        else:
            color = self.settings["color"]
            outline = "white"
            tags = (f"target_{index}",)
        
        shape = self.settings["shape"]
        target_id = self.draw_target(x, y, size, color, outline, tags, shape)
        self.canvas.tag_raise(f"target_{index}")
        
        self.canvas.tag_bind(f"target_{index}", "<Button-1>", 
                             lambda e, idx=index: self.on_target_click(e, idx))
        
        target_data = {
            'id': target_id,
            'x': x,
            'y': y,
            'size': size,
            'center': center,
            'move_interval': move_interval,
            'timer_id': None,
            'is_bonus': is_bonus
        }
        if index < len(self.targets):
            self.targets[index] = target_data
        else:
            self.targets.append(target_data)
        
        self.start_target_movement(index)

    def start_target_movement(self, index):
        if not self.game_running or index >= len(self.targets):
            return
        target = self.targets[index]
        if target is None:
            return
        if target['timer_id']:
            self.canvas.after_cancel(target['timer_id'])
        self.move_target(index)

    def move_target(self, index):
        if not self.game_running or index >= len(self.targets):
            return
        target = self.targets[index]
        if target is None:
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 100 or canvas_height < 100:
            target['timer_id'] = self.canvas.after(100, lambda: self.move_target(index))
            return
        
        coords = self.canvas.coords(target['id'])
        if not coords:
            target['timer_id'] = self.canvas.after(100, lambda: self.move_target(index))
            return
        
        xs = coords[0::2]
        ys = coords[1::2]
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        size = x2 - x1
        
        difficulty_params = {
            "easy": {"step": 40, "move_interval": 700},
            "medium": {"step": 60, "move_interval": 500},
            "hard": {"step": 80, "move_interval": 350}
        }
        params = difficulty_params.get(self.settings["difficulty"], difficulty_params["medium"])
        step = params["step"]
        move_interval = params["move_interval"]
        
        new_x = x1 + random.randint(-step, step)
        new_y = y1 + random.randint(-step, step)
        margin = 30
        new_x = max(margin, min(new_x, canvas_width - size - margin))
        new_y = max(140, min(new_y, canvas_height - size - 110))
        
        color = self.settings["color"]
        outline = "white"
        is_bonus = target.get('is_bonus', False)
        if is_bonus:
            outline = "#ffaa00"
        tags = self.canvas.gettags(target['id'])
        self.canvas.delete(target['id'])
        shape = self.settings["shape"]
        new_id = self.draw_target(new_x, new_y, size, color, outline, tags, shape)
        self.canvas.tag_raise(new_id)
        self.canvas.tag_bind(new_id, "<Button-1>", 
                             lambda e, idx=index: self.on_target_click(e, idx))
        target['id'] = new_id
        target['x'] = new_x
        target['y'] = new_y
        target['center'] = (new_x + size/2, new_y + size/2)
        
        target['timer_id'] = self.canvas.after(move_interval, lambda: self.move_target(index))

    def on_target_click(self, event, index):
        if not self.game_running or index >= len(self.targets):
            return
        
        target = self.targets[index]
        if target is None:
            return
        
        coords = self.canvas.coords(target['id'])
        if not coords:
            return
        
        xs = coords[0::2]
        ys = coords[1::2]
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        size = x2 - x1
        
        is_bonus = target.get('is_bonus', False)
        if is_bonus:
            points = 5 * self.combo_multiplier
            color_palette = ["#ffd700", "#ffcc00", "#ffaa00", "#ffffff"]
            glow_color = "#ffdd44"
            self.gold_hits += 1
        else:
            points = 1 * self.combo_multiplier
            color_palette = ["#ff4444", "#ff8800", "#ffcc00", "#44ff44", "#44ccff", "#aa44ff", "#ff44ff", "#ffffff"]
            glow_color = "#ffff88"
        
        self.total_hits += 1
        new_score = self.score + points
        self.animate_score(new_score)
        self.score = new_score
        
        if self.score > self.record:
            self.record = self.score
            self.save_record()
            self.record_breaks += 1
            self.canvas.itemconfig(self.record_label, text=f"🏆 Record: {self.record} (NEW!)")
        else:
            self.canvas.itemconfig(self.record_label, text=f"🏆 Record: {self.record}")
        
        self.check_achievements()
        
        glow_size = size * 0.7
        glow = self.canvas.create_oval(cx - glow_size, cy - glow_size,
                                       cx + glow_size, cy + glow_size,
                                       outline=glow_color, width=3, tags="glow")
        self.glow_effects.append({
            'id': glow,
            'x': cx,
            'y': cy,
            'size': glow_size,
            'max_size': size * 1.8,
            'life': 25,
            'max_life': 25
        })
        self.canvas.after(80, lambda: self.canvas.itemconfig(target['id'],
                             fill="#ffd700" if is_bonus else self.settings["color"],
                             outline="gold" if is_bonus else "white"))
        
        for _ in range(random.randint(10, 16)):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            p_size = random.randint(5, 12)
            color = random.choice(color_palette)
            p = {
                'x': cx,
                'y': cy,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed - 1.5,
                'size': p_size,
                'color': color,
                'life': random.randint(20, 35),
                'max_life': 35,
                'id': None
            }
            p['id'] = self.canvas.create_oval(cx - p_size, cy - p_size,
                                               cx + p_size, cy + p_size,
                                               fill=color, outline="")
            self.particles.append(p)
        
        for _ in range(random.randint(20, 30)):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3.5)
            s_size = random.randint(2, 4)
            brightness = random.randint(150, 255)
            s = {
                'x': cx,
                'y': cy,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed - 0.5,
                'size': s_size,
                'life': random.randint(10, 20),
                'max_life': 20,
                'id': None
            }
            s['id'] = self.canvas.create_oval(cx - s_size, cy - s_size,
                                               cx + s_size, cy + s_size,
                                               fill=f"#{brightness:02x}{brightness:02x}ff", outline="")
            self.sparks.append(s)
        
        text_str = f"+{points}" + (" ✨" if is_bonus else "")
        text = self.canvas.create_text(cx, cy - 10,
                                       text=text_str, font=("Arial", 28, "bold"),
                                       fill="#ffd700" if is_bonus else "#66ff66")
        self.floating_texts.append({
            'id': text,
            'x': cx,
            'y': cy - 10,
            'alpha': 1.0
        })
        
        self.update_combo()
        
        tid = target['id']
        if target['timer_id']:
            self.canvas.after_cancel(target['timer_id'])
            target['timer_id'] = None
        self.targets[index] = None
        self.animate_shrink(tid, callback=lambda: self.create_single_target(index))

    def animate_effects(self):
        if not self.game_running:
            return
        to_remove = []
        for i, p in enumerate(self.particles):
            p['x'] += p['dx']
            p['y'] += p['dy']
            p['dy'] += 0.15
            p['life'] -= 1
            p['size'] *= 0.97
            if p['life'] <= 0 or p['size'] < 1:
                to_remove.append(i)
                continue
            self.canvas.coords(p['id'], p['x']-p['size'], p['y']-p['size'],
                               p['x']+p['size'], p['y']+p['size'])
            self.canvas.itemconfig(p['id'], fill=p['color'])
        for i in reversed(to_remove):
            self.canvas.delete(self.particles[i]['id'])
            del self.particles[i]
        
        to_remove_s = []
        for i, s in enumerate(self.sparks):
            s['x'] += s['dx']
            s['y'] += s['dy']
            s['dy'] += 0.2
            s['life'] -= 1
            if s['life'] <= 0:
                to_remove_s.append(i)
                continue
            self.canvas.coords(s['id'], s['x']-s['size'], s['y']-s['size'],
                               s['x']+s['size'], s['y']+s['size'])
            alpha = int(255 * (s['life'] / s['max_life']))
            self.canvas.itemconfig(s['id'], fill=f"#{alpha:02x}{alpha:02x}ff")
        for i in reversed(to_remove_s):
            self.canvas.delete(self.sparks[i]['id'])
            del self.sparks[i]
        
        to_remove_t = []
        for i, t in enumerate(self.floating_texts):
            t['y'] -= 1.8
            t['alpha'] -= 0.015
            if t['alpha'] <= 0:
                to_remove_t.append(i)
                continue
            self.canvas.coords(t['id'], t['x'], t['y'])
            alpha = int(255 * t['alpha'])
            self.canvas.itemconfig(t['id'], fill=f"#{alpha:02x}{alpha:02x}00")
        for i in reversed(to_remove_t):
            self.canvas.delete(self.floating_texts[i]['id'])
            del self.floating_texts[i]
        
        to_remove_g = []
        for i, g in enumerate(self.glow_effects):
            g['life'] -= 1
            if g['life'] <= 0:
                to_remove_g.append(i)
                continue
            size = g['size'] + (g['max_size'] - g['size']) * (1 - g['life']/g['max_life'])
            alpha = int(255 * (g['life'] / g['max_life']))
            self.canvas.coords(g['id'], g['x']-size, g['y']-size, g['x']+size, g['y']+size)
            self.canvas.itemconfig(g['id'], outline=f"#{alpha:02x}{alpha:02x}ff")
        for i in reversed(to_remove_g):
            self.canvas.delete(self.glow_effects[i]['id'])
            del self.glow_effects[i]
        
        if self.game_running:
            self.canvas.after(30, self.animate_effects)

    def stop_game_and_menu(self):
        self.game_running = False
        self.reset_canvas()
        self.stop_all_animations()
        self.save_record()
        self.save_profile()
        self.show_main_menu()

    def exit_game(self):
        if messagebox.askyesno("Exit", "Are you sure you want to quit?", parent=self.root):
            self.save_record()
            self.save_profile()
            self.root.destroy()
            sys.exit()

    # ---------- ACHIEVEMENT NOTIFICATIONS ----------
    def show_achievement(self, text):
        if not self.game_running:
            return
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x = 30
        y = canvas_height - 40
        shadow = self.canvas.create_text(x+2, y+2, text=f"🏆 {text}", anchor="w",
                                         font=("Segoe UI", 14, "bold"),
                                         fill="#000000", tags="achievement_shadow")
        ach_id = self.canvas.create_text(x, y, text=f"🏆 {text}", anchor="w",
                                         font=("Segoe UI", 14, "bold"),
                                         fill="#ffd700", tags="achievement")
        self.achievement_notifications.append({
            'id': ach_id,
            'shadow': shadow,
            'life': 40,
            'max_life': 40,
            'scale': 0.0,
            'target_scale': 1.0
        })

    def animate_achievements(self):
        if not self.game_running:
            return
        to_remove = []
        for i, notif in enumerate(self.achievement_notifications):
            notif['life'] -= 1
            if notif['life'] <= 0:
                to_remove.append(i)
                continue
            progress = 1 - (notif['life'] / notif['max_life'])
            if progress < 0.3:
                scale = progress / 0.3
            elif progress > 0.8:
                scale = 1 - (progress - 0.8) / 0.2
            else:
                scale = 1.0
            font_size = int(14 * scale)
            if font_size < 1:
                font_size = 1
            self.canvas.itemconfig(notif['id'], font=("Segoe UI", font_size, "bold"))
            self.canvas.itemconfig(notif['shadow'], font=("Segoe UI", font_size, "bold"))
        for i in reversed(to_remove):
            self.canvas.delete(self.achievement_notifications[i]['id'])
            self.canvas.delete(self.achievement_notifications[i]['shadow'])
            del self.achievement_notifications[i]
        if self.game_running:
            self.canvas.after(50, self.animate_achievements)

    def check_achievements(self):
        if not self.game_running:
            return
        
        hit_thresholds = list(range(100, 40001, 100))
        for threshold in hit_thresholds:
            key = f"hits_{threshold}"
            if key not in self.unlocked_achievements and self.total_hits >= threshold:
                self.unlocked_achievements.add(key)
                self.show_achievement(f"{threshold} clicks!")
        
        gold_thresholds = [10, 25, 50, 100, 250, 500, 1000]
        for threshold in gold_thresholds:
            key = f"gold_{threshold}"
            if key not in self.unlocked_achievements and self.gold_hits >= threshold:
                self.unlocked_achievements.add(key)
                self.show_achievement(f"Gold: {threshold}!")
        
        score_thresholds = [50, 100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]
        for threshold in score_thresholds:
            key = f"score_{threshold}"
            if key not in self.unlocked_achievements and self.score >= threshold:
                self.unlocked_achievements.add(key)
                self.show_achievement(f"{threshold} points!")
        
        if "record5" not in self.unlocked_achievements and self.record_breaks >= 5:
            self.unlocked_achievements.add("record5")
            self.show_achievement("Record broken 5 times!")
        
        if "first_hit" not in self.unlocked_achievements and self.total_hits >= 1:
            self.unlocked_achievements.add("first_hit")
            self.show_achievement("First hit!")
        
        combo_thresholds = [10, 20, 50]
        for threshold in combo_thresholds:
            key = f"combo_{threshold}"
            if key not in self.unlocked_achievements and self.combo >= threshold:
                self.unlocked_achievements.add(key)
                self.show_achievement(f"Combo {threshold}!")
        
        if "mode4" not in self.unlocked_achievements and self.num_targets == 4:
            self.unlocked_achievements.add("mode4")
            self.show_achievement("Multitasking (4 blocks)!")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = MainApplication(root)
    root.mainloop()