import tkinter as tk
import random
import sys
import json
import os

# Costanti di Gioco
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
FRAME_DELAY = int(1000 / FPS)  # circa 16ms per frame

# Palette colori d'ispirazione retro/arcade
COLOR_BG = "#0d0e15"          # Sfondo scuro moderno
COLOR_WALL = "#3a3f58"        # Muri dei dungeon
COLOR_PLAYER = "#2ecc71"      # Eroe (Verde)
COLOR_ENEMY = "#e74c3c"       # Mostri (Rosso)
COLOR_SWORD = "#f1c40f"       # Spada (Giallo)
COLOR_UI_TEXT = "#ecf0f1"     # Testi generali
COLOR_UI_PORTAL = "#3498db"   # Portale matematico (Azzurro)
COLOR_HEART = "#ff4757"       # Cuori (Rosso acceso)

class LegendOfNullGame:
    def __init__(self, root):
        self.root = root
        self.root.title("The Legend of Null - Math Quest")
        self.root.resizable(False, False)
        
        # Centra la finestra sullo schermo
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - SCREEN_WIDTH) // 2
        y = (screen_h - SCREEN_HEIGHT) // 2
        self.root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}+{x}+{y}")

        # Area di disegno Canvas
        self.canvas = tk.Canvas(root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack()

        # Stati del Gioco: "MENU", "TUTORIAL", "GAME", "GAMEOVER"
        self.state = "MENU"
        
        # Inizializzazione controlli tastiera
        self.keys = {}
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        # Cursore mouse per feedback pulsanti
        self.mouse_x = 0
        self.mouse_y = 0

        # Avvia il loop di gioco
        self.reset_complete_game()
        self.game_loop()

    def reset_complete_game(self):
        """Resetta l'intero stato per una nuova partita."""
        self.hearts = 4
        self.current_room = 1
        self.total_rooms = 5
        self.victory = False
        self.game_over_flag = False
        self.math_phase = False
        self.math_question = ""
        self.math_answer = ""
        self.user_input = ""
        self.door_open = False
        self.mode = getattr(self, 'mode', 'NORMAL')  # 'NORMAL' or 'ENDLESS'
        self.endless_rooms_completed = 0
        self.best_saved = False
        self.best_score = self.load_best_score()
        
        # Giocatore
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT // 2 + 100
        self.player_size = 32
        self.player_speed = 4
        self.player_direction = "UP"
        self.player_attacking = False
        self.player_attack_timer = 0
        self.sword_rect = None  # (x1, y1, x2, y2)

        # Genera ostacoli, nemici e primo indovinello
        self.generate_obstacles()
        self.spawn_enemies()
        self.generate_riddle()

    def rects_intersect(self, rect1, rect2):
        x1, y1, x2, y2 = rect1
        a1, b1, a2, b2 = rect2
        return not (x2 < a1 or x1 > a2 or y2 < b1 or y1 > b2)

    def best_score_path(self):
        return os.path.join(os.path.dirname(__file__), 'endless_best.json')

    def load_best_score(self):
        path = self.best_score_path()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return int(data.get('best', 0))
        except Exception:
            return 0

    def save_best_score(self):
        path = self.best_score_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'best': int(self.best_score)}, f)
        except Exception:
            pass

    def start_music(self):
        """Avvia la musica di sottofondo se disponibile."""
        if getattr(self, 'music_on', False):
            return
        try:
            import winsound
            base_dir = os.path.dirname(__file__)
            candidates = [
                os.path.join(base_dir, 'bg_music.wav'),
                os.path.join(base_dir, 'bg_music.wav.wav'),
            ]
            path = next((p for p in candidates if os.path.exists(p)), None)
            if path is None:
                # Cerca qualunque file WAV con prefisso "bg_music"
                for entry in os.listdir(base_dir):
                    if entry.lower().startswith('bg_music') and entry.lower().endswith('.wav'):
                        path = os.path.join(base_dir, entry)
                        break
            if path and os.path.exists(path):
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
                self.music_on = True
            else:
                self.music_on = False
        except Exception:
            self.music_on = False

    def stop_music(self):
        """Ferma la musica di sottofondo."""
        try:
            import winsound
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                try:
                    winsound.PlaySound(None, 0)
                except Exception:
                    pass
        except Exception:
            pass
        self.music_on = False

    def get_door_rect(self):
        width = 80
        height = 48
        x1 = SCREEN_WIDTH // 2 - width // 2
        y1 = 90
        return (x1, y1, x1 + width, y1 + height)

    def enter_door(self):
        if not self.door_open:
            return
        # Endless mode: increment completed counter and generate new room
        if getattr(self, 'mode', 'NORMAL') == 'ENDLESS':
            self.endless_rooms_completed = getattr(self, 'endless_rooms_completed', 0) + 1
            self.door_open = False
            self.math_phase = False
            self.user_input = ""
            self.player_x = SCREEN_WIDTH // 2
            self.player_y = SCREEN_HEIGHT // 2 + 100
            self.player_direction = "UP"
            self.generate_obstacles()
            self.spawn_enemies()
            self.generate_riddle()
            return

        # Normal mode: check final room
        if self.current_room == self.total_rooms:
            self.victory = True
            self.game_over_flag = True
            self.door_open = False
            return

        self.current_room += 1
        self.door_open = False
        self.math_phase = False
        self.user_input = ""
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT // 2 + 100
        self.player_direction = "UP"
        self.generate_obstacles()
        self.spawn_enemies()
        self.generate_riddle()

    def generate_obstacles(self):
        """Genera ostacoli statici casuali e non sovrapposti nel dungeon."""
        self.obstacles = []
        num_obstacles = random.randint(4, 6)
        room_bounds = (45, 105, SCREEN_WIDTH - 45, SCREEN_HEIGHT - 45)
        for _ in range(num_obstacles):
            placed = False
            for _attempt in range(100):
                w = random.randint(40, 80)
                h = random.randint(20, 50)
                x = random.randint(room_bounds[0] + 10, room_bounds[2] - w - 10)
                y = random.randint(room_bounds[1] + 10, room_bounds[3] - h - 10)
                new_rect = (x, y, x + w, y + h)
                if any(self.rects_intersect(new_rect, (obs["x"], obs["y"], obs["x"] + obs["w"], obs["y"] + obs["h"])) for obs in self.obstacles):
                    continue
                self.obstacles.append({"x": x, "y": y, "w": w, "h": h})
                placed = True
                break
            if not placed:
                # Se non si trova posto dopo molti tentativi, riduci il numero di ostacoli e continua
                continue

    def spawn_enemies(self):
        """Genera un numero randomico di nemici in posizioni casuali."""
        self.enemies = []
        num_enemies = random.randint(3, 6)
        for _ in range(num_enemies):
            # Posiziona i nemici evitando gli ostacoli
            while True:
                x = random.randint(100, SCREEN_WIDTH - 100)
                y = random.randint(150, SCREEN_HEIGHT // 2)
                enemy_rect = (x - 15, y - 15, x + 15, y + 15)
                if not any(self.rects_intersect(enemy_rect, (obs["x"], obs["y"], obs["x"] + obs["w"], obs["y"] + obs["h"])) for obs in self.obstacles):
                    break

            direction = random.choice(["LEFT", "RIGHT", "UP", "DOWN"])
            dir_x = -1 if direction == "LEFT" else 1 if direction == "RIGHT" else 0
            dir_y = -1 if direction == "UP" else 1 if direction == "DOWN" else 0

            self.enemies.append({
                "x": x,
                "y": y,
                "size": 30,
                "speed": random.choice([1, 2, 3]),
                "dir_x": dir_x,
                "dir_y": dir_y,
                "timer": random.randint(30, 90)
            })

    def generate_riddle(self):
        """Crea un enigma matematico randomico."""
        op = random.choice(['+', '-', '*'])
        if op == '+':
            n1, n2 = random.randint(10, 89), random.randint(10, 89)
            self.math_answer = str(n1 + n2)
        elif op == '-':
            n1 = random.randint(50, 99)
            n2 = random.randint(10, 49)
            self.math_answer = str(n1 - n2)
        else:
            n1, n2 = random.randint(2, 12), random.randint(2, 12)
            self.math_answer = str(n1 * n2)
        
        self.math_question = f"{n1} {op} {n2} = ?"

    def on_key_press(self, event):
        key = event.keysym.lower()
        self.keys[key] = True

        # Gestione attacco
        if event.keysym == "space" and self.state == "GAME" and not self.game_over_flag:
            if not self.math_phase:
                self.trigger_attack()

        # Gestione input tastiera fase matematica
        if self.state == "GAME" and self.math_phase and not self.game_over_flag:
            if event.keysym == "Return":
                self.check_math_answer()
            elif event.keysym == "BackSpace":
                self.user_input = self.user_input[:-1]
            elif event.char.isdigit() or (event.char == '-' and len(self.user_input) == 0):
                self.user_input += event.char

        # Tasti di riavvio / menu a fine gioco
        if self.game_over_flag or (self.state == "GAME" and self.victory):
            if key == 'r':
                self.reset_complete_game()
                self.state = "GAME"
                try:
                    self.start_music()
                except Exception:
                    pass
            elif key == 'm':
                self.state = "MENU"
                try:
                    self.stop_music()
                except Exception:
                    pass

    def on_key_release(self, event):
        key = event.keysym.lower()
        self.keys[key] = False

    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def on_canvas_click(self, event):
        mx, my = event.x, event.y
        if self.state == "MENU":
            # Bottone GIOCA (275, 280, 525, 340)
            if 275 <= mx <= 525 and 280 <= my <= 340:
                self.mode = 'NORMAL'
                self.reset_complete_game()
                self.state = "GAME"
                try:
                    self.start_music()
                except Exception:
                    pass
            # Bottone ENDLESS (275, 350, 525, 410)
            elif 275 <= mx <= 525 and 350 <= my <= 410:
                self.mode = 'ENDLESS'
                self.reset_complete_game()
                self.state = 'GAME'
                try:
                    self.start_music()
                except Exception:
                    pass
            # Bottone TUTORIAL (275, 370, 525, 430)
            elif 275 <= mx <= 525 and 430 <= my <= 490:
                self.state = "TUTORIAL"
        elif self.state == "TUTORIAL":
            # Bottone INDIETRO (275, 480, 525, 540)
            if 275 <= mx <= 525 and 480 <= my <= 540:
                self.state = "MENU"
                try:
                    self.stop_music()
                except Exception:
                    pass

    def trigger_attack(self):
        if not self.player_attacking:
            self.player_attacking = True
            self.player_attack_timer = 12  # Durata dell'attacco in frame
            
            # Calcolo area della spada
            range_spada = 26
            px, py = self.player_x, self.player_y
            half = self.player_size // 2
            
            if self.player_direction == "UP":
                self.sword_rect = (px - 4, py - half - range_spada, px + 4, py - half)
            elif self.player_direction == "DOWN":
                self.sword_rect = (px - 4, py + half, px + 4, py + half + range_spada)
            elif self.player_direction == "LEFT":
                self.sword_rect = (px - half - range_spada, py - 4, px - half, py + 4)
            elif self.player_direction == "RIGHT":
                self.sword_rect = (px + half, py - 4, px + half + range_spada, py + 4)

    def check_math_answer(self):
        """Verifica se la risposta matematica inserita è corretta."""
        if self.user_input == self.math_answer:
            self.door_open = True
            self.math_phase = False
            self.user_input = ""
        else:
            # Risposta Sbagliata: Togli un cuore e cambia calcolo
            self.hearts -= 1
            self.user_input = ""
            if self.hearts <= 0:
                self.game_over_flag = True
                self.victory = False
            else:
                self.generate_riddle()

    def update_physics(self):
        """Aggiorna le posizioni, gestisce collisioni e IA dei mostri."""
        if self.state != "GAME" or self.game_over_flag:
            return

        # Movimento Giocatore (solo se non sta attaccando ed è nella fase d'azione)
        if not self.player_attacking and not self.math_phase:
            dx, dy = 0, 0
            if self.keys.get('a') or self.keys.get('left'):
                dx = -self.player_speed
                self.player_direction = "LEFT"
            elif self.keys.get('d') or self.keys.get('right'):
                dx = self.player_speed
                self.player_direction = "RIGHT"
            elif self.keys.get('w') or self.keys.get('up'):
                dy = -self.player_speed
                self.player_direction = "UP"
            elif self.keys.get('s') or self.keys.get('down'):
                dy = self.player_speed
                self.player_direction = "DOWN"

            old_x, old_y = self.player_x, self.player_y
            self.player_x += dx
            self.player_y += dy

            # Limiti dei muri della stanza
            margin = 40 + self.player_size // 2
            if self.player_x < margin: self.player_x = margin
            if self.player_x > SCREEN_WIDTH - margin: self.player_x = SCREEN_WIDTH - margin
            if self.player_y < 100 + self.player_size // 2: self.player_y = 100 + self.player_size // 2
            if self.player_y > SCREEN_HEIGHT - 40 - self.player_size // 2: self.player_y = SCREEN_HEIGHT - 40 - self.player_size // 2

            # Collisione con ostacoli
            player_rect = (self.player_x - self.player_size // 2, self.player_y - self.player_size // 2,
                           self.player_x + self.player_size // 2, self.player_y + self.player_size // 2)
            if any(self.rects_intersect(player_rect, (obs["x"], obs["y"], obs["x"] + obs["w"], obs["y"] + obs["h"])) for obs in self.obstacles):
                self.player_x, self.player_y = old_x, old_y

        # Timer Attacco
        if self.player_attacking:
            self.player_attack_timer -= 1
            if self.player_attack_timer <= 0:
                self.player_attacking = False
                self.sword_rect = None

        # IA e movimento dei nemici
        if not self.math_phase:
            # Rettangolo di contenimento dungeon
            dungeon_rect = (45, 105, SCREEN_WIDTH - 45, SCREEN_HEIGHT - 45)
            
            for enemy in self.enemies[:]:
                enemy["timer"] -= 1
                if enemy["timer"] <= 0:
                    enemy["dir_x"], enemy["dir_y"] = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)])
                    enemy["timer"] = random.randint(30, 90)

                old_ex, old_ey = enemy["x"], enemy["y"]
                enemy["x"] += enemy["dir_x"] * enemy["speed"]
                enemy["y"] += enemy["dir_y"] * enemy["speed"]

                # Collisione nemici con ostacoli
                eh = enemy["size"] // 2
                enemy_rect = (enemy["x"] - eh, enemy["y"] - eh, enemy["x"] + eh, enemy["y"] + eh)
                for obs in self.obstacles:
                    if self.rects_intersect(enemy_rect, (obs["x"], obs["y"], obs["x"] + obs["w"], obs["y"] + obs["h"])):
                        enemy["x"], enemy["y"] = old_ex, old_ey
                        enemy["dir_x"] *= -1
                        enemy["dir_y"] *= -1
                        break

                # Limiti nemici nei muri
                if enemy["x"] - eh < dungeon_rect[0] or enemy["x"] + eh > dungeon_rect[2]:
                    enemy["dir_x"] *= -1
                    enemy["x"] = max(dungeon_rect[0] + eh, min(enemy["x"], dungeon_rect[2] - eh))
                if enemy["y"] - eh < dungeon_rect[1] or enemy["y"] + eh > dungeon_rect[3]:
                    enemy["dir_y"] *= -1
                    enemy["y"] = max(dungeon_rect[1] + eh, min(enemy["y"], dungeon_rect[3] - eh))

                # Collisione Spada -> Nemico
                if self.player_attacking and self.sword_rect:
                    sx1, sy1, sx2, sy2 = self.sword_rect
                    ex1, ey1 = enemy["x"] - eh, enemy["y"] - eh
                    ex2, ey2 = enemy["x"] + eh, enemy["y"] + eh
                    # Sovrapposizione rettangoli
                    if not (sx2 < ex1 or sx1 > ex2 or sy2 < ey1 or sy1 > ey2):
                        self.enemies.remove(enemy)
                        continue

                # Collisione Nemico -> Giocatore (Danno)
                px1, py1 = self.player_x - self.player_size//2, self.player_y - self.player_size//2
                px2, py2 = self.player_x + self.player_size//2, self.player_y + self.player_size//2
                ex1, ey1 = enemy["x"] - eh, enemy["y"] - eh
                ex2, ey2 = enemy["x"] + eh, enemy["y"] + eh
                if not (px2 < ex1 or px1 > ex2 or py2 < ey1 or py1 > ey2):
                    self.hearts -= 1
                    if self.hearts <= 0:
                        self.game_over_flag = True
                        self.victory = False
                    else:
                        # Resetta giocatore al sicuro in basso
                        self.player_x = SCREEN_WIDTH // 2
                        self.player_y = SCREEN_HEIGHT // 2 + 100
                        self.player_direction = "UP"
                        self.player_attacking = False
                        self.sword_rect = None

            if self.door_open and not self.math_phase:
                player_rect = (self.player_x - self.player_size // 2, self.player_y - self.player_size // 2,
                               self.player_x + self.player_size // 2, self.player_y + self.player_size // 2)
                if self.rects_intersect(player_rect, self.get_door_rect()):
                    self.enter_door()

            # Attiva la fase matematica se i mostri sono finiti e la porta non è già aperta
            if len(self.enemies) == 0 and not self.door_open:
                self.math_phase = True

    def draw_button(self, x1, y1, x2, y2, text, active_color, normal_color):
        """Disegna un fantastico bottone interattivo sul Canvas."""
        is_hover = (x1 <= self.mouse_x <= x2) and (y1 <= self.mouse_y <= y2)
        color = active_color if is_hover else normal_color
        
        # Bordo e riempimento
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=COLOR_UI_TEXT, width=3)
        self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=text, fill=COLOR_UI_TEXT, font=("Courier New", 20, "bold"))

    def draw_hearts(self, x_start, y_center):
        """Renderizza cuori vettoriali stile NES sul canvas."""
        for i in range(self.hearts):
            cx = x_start + (i * 35)
            cy = y_center
            # Disegna un cuore tramite un poligono morbido a forma di cuore retro
            coords = [
                cx, cy + 8,
                cx - 10, cy - 4,
                cx - 10, cy - 12,
                cx - 5, cy - 15,
                cx, cy - 10,
                cx + 5, cy - 15,
                cx + 10, cy - 12,
                cx + 10, cy - 4
            ]
            self.canvas.create_polygon(coords, fill=COLOR_HEART, outline="#ffffff", width=1.5)

    def draw_scene(self):
        """Pulisce e ridisegna l'intera interfaccia di gioco."""
        self.canvas.delete("all")

        # 1. MENU PRINCIPALE
        if self.state == "MENU":
            # Titolo retro pixelato
            self.canvas.create_text(SCREEN_WIDTH // 2, 120, text="THE LEGEND OF NULL", fill=COLOR_PLAYER, font=("Courier New", 42, "bold"))
            self.canvas.create_text(SCREEN_WIDTH // 2, 180, text="Un'avventura aritmetica procedurale", fill=COLOR_UI_TEXT, font=("Courier New", 18, "italic"))
            
            # Bottoni
            self.draw_button(275, 280, 525, 340, "GIOCA", "#1abc9c", "#16a085")
            self.draw_button(275, 350, 525, 410, "ENDLESS", "#9b59b6", "#71368a")
            self.draw_button(275, 430, 525, 490, "TUTORIAL", "#2980b9", "#1f3a60")
            
            # Firma piè di pagina
            self.canvas.create_text(SCREEN_WIDTH // 2, 530, text="Supera le stanze con calcoli fulminei!", fill="#7f8c8d", font=("Courier New", 14))
            # Best score Endless
            if getattr(self, 'best_score', 0) > 0:
                self.canvas.create_text(SCREEN_WIDTH // 2, 555, text=f"Endless Best: {self.best_score}", fill="#bdc3c7", font=("Courier New", 12, "bold"))

        # 2. MENU TUTORIAL
        elif self.state == "TUTORIAL":
            self.canvas.create_text(SCREEN_WIDTH // 2, 60, text="ISTRUZIONI DI GIOCO", fill=COLOR_SWORD, font=("Courier New", 32, "bold"))

            istruzioni = [
                "- Muoviti usando le FRECCE DIREZIONALI o i tasti W, A, S, D.",
                "- Attacca i mostri premendo la BARRA SPAZIATRICE.",
                "- Elimina tutti i nemici rossi per sbloccare l'enigma matematico.",
                "- Digita la risposta corretta e premi INVIO per aprire la porta.",
                "- Dirigiti verso la porta aperta per passare alla stanza successiva.",
                "- Hai 4 cuori in totale.",
                "- Attenzione: perdi 1 cuore se vieni toccato o se sbagli un calcolo!",
                "- Supera tutte e 5 le stanze generate casualmente per vincere."
            ]

            y_pos = 140
            for riga in istruzioni:
                self.canvas.create_text(60, y_pos, text=riga, fill=COLOR_UI_TEXT, font=("Courier New", 14, "bold"), anchor="w")
                y_pos += 40

            self.draw_button(275, 480, 525, 540, "INDIETRO", "#e74c3c", "#c0392b")

        # 3. INTERFACCIA DI GIOCO (GAME)
        elif self.state == "GAME":
            # Disegna i muri perimetrali della stanza (Dungeon)
            self.canvas.create_rectangle(20, 80, SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20, outline=COLOR_WALL, width=8)

            # Barra Superiore (UI)
            if getattr(self, 'mode', 'NORMAL') == 'ENDLESS':
                self.canvas.create_text(110, 40, text=f"COMPLETATE: {self.endless_rooms_completed}", fill=COLOR_UI_TEXT, font=("Courier New", 18, "bold"))
            else:
                self.canvas.create_text(110, 40, text=f"STANZA: {self.current_room}/{self.total_rooms}", fill=COLOR_UI_TEXT, font=("Courier New", 18, "bold"))
            
            if not self.math_phase and not self.game_over_flag:
                self.canvas.create_text(350, 40, text=f"MOSTRICIATTOLI: {len(self.enemies)}", fill=COLOR_ENEMY, font=("Courier New", 18, "bold"))

            # Disegna Porta di fine stanza
            door_x1, door_y1, door_x2, door_y2 = self.get_door_rect()
            door_color = "#2ecc71" if self.door_open else "#7f8c8d"
            self.canvas.create_rectangle(door_x1, door_y1, door_x2, door_y2, fill=door_color, outline=COLOR_UI_TEXT, width=3)
            door_label = "APERTA" if self.door_open else "CHIUSA"
            self.canvas.create_text((door_x1 + door_x2) // 2, door_y1 + 14, text=door_label, fill=COLOR_UI_TEXT, font=("Courier New", 10, "bold"))
            if not self.door_open:
                self.canvas.create_text((door_x1 + door_x2) // 2, door_y2 + 14, text="Rispondi per aprirla", fill="#bdc3c7", font=("Courier New", 10, "bold"))
            
            # Mostra i Cuori
            self.canvas.create_text(520, 40, text="VITE: ", fill=COLOR_UI_TEXT, font=("Courier New", 18, "bold"))
            self.draw_hearts(580, 40)

            # Elementi attivi (Giocatore, Spada e Mostri)
            # Disegna Ostacoli della stanza
            for obs in self.obstacles:
                self.canvas.create_rectangle(obs["x"], obs["y"], obs["x"] + obs["w"], obs["y"] + obs["h"], fill=COLOR_WALL, outline="#7f8c8d", width=2)

            if not self.math_phase and not self.game_over_flag:
                # Disegna Eroe
                px, py, ps = self.player_x, self.player_y, self.player_size
                self.canvas.create_rectangle(px - ps//2, py - ps//2, px + ps//2, py + ps//2, fill=COLOR_PLAYER, outline="#ffffff", width=2)
                
                # Disegna Spada se attiva
                if self.player_attacking and self.sword_rect:
                    self.canvas.create_rectangle(self.sword_rect, fill=COLOR_SWORD, outline="#ffffff")

                # Disegna Nemici
                for enemy in self.enemies:
                    ex, ey, es = enemy["x"], enemy["y"], enemy["size"]
                    self.canvas.create_rectangle(ex - es//2, ey - es//2, ex + es//2, ey + es//2, fill=COLOR_ENEMY, outline="#ffffff", width=2)

            # Popup Portale Matematico
            if self.math_phase and not self.game_over_flag:
                bx1, by1, bx2, by2 = SCREEN_WIDTH // 4, SCREEN_HEIGHT // 3, (SCREEN_WIDTH // 4) * 3, SCREEN_HEIGHT // 3 + 220
                self.canvas.create_rectangle(bx1, by1, bx2, by2, fill="#111827", outline=COLOR_UI_PORTAL, width=4)
                
                self.canvas.create_text((bx1+bx2)//2, by1 + 30, text="PORTALE CHIUSO! RISOLVI:", fill=COLOR_UI_PORTAL, font=("Courier New", 18, "bold"))
                self.canvas.create_text((bx1+bx2)//2, by1 + 80, text=self.math_question, fill=COLOR_UI_TEXT, font=("Courier New", 26, "bold"))
                self.canvas.create_text((bx1+bx2)//2, by1 + 130, text=f"Risposta: {self.user_input}_", fill=COLOR_SWORD, font=("Courier New", 22, "bold"))
                self.canvas.create_text((bx1+bx2)//2, by1 + 180, text="SE SBAGLI PERDI 1 VITA!", fill=COLOR_ENEMY, font=("Courier New", 13, "bold"))

            # Schermata Finale (Game Over / Vittoria)
            if self.game_over_flag:
                if self.victory:
                    self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30, text="COMPLIMENTI! HAI SALVATO IL REGNO!", fill=COLOR_PLAYER, font=("Courier New", 24, "bold"))
                else:
                    if getattr(self, 'mode', 'NORMAL') == 'ENDLESS':
                        if not getattr(self, 'best_saved', False):
                            if self.endless_rooms_completed > getattr(self, 'best_score', 0):
                                self.best_score = self.endless_rooms_completed
                                self.save_best_score()
                            self.best_saved = True
                        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60, text=f"VITE TERMINATE! GAME OVER", fill=COLOR_ENEMY, font=("Courier New", 22, "bold"))
                        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20, text=f"Risultato: {self.endless_rooms_completed}", fill=COLOR_UI_TEXT, font=("Courier New", 18, "bold"))
                        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10, text=f"Best: {self.best_score}", fill=COLOR_PLAYER, font=("Courier New", 16, "bold"))
                    else:
                        self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30, text="VITE TERMINATE! GAME OVER", fill=COLOR_ENEMY, font=("Courier New", 26, "bold"))
                
                self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40, text="Premi 'R' per rigiocare", fill=COLOR_UI_TEXT, font=("Courier New", 16, "bold"))
                self.canvas.create_text(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80, text="Premi 'M' per tornare alla Home", fill=COLOR_SWORD, font=("Courier New", 16, "bold"))

    def game_loop(self):
        """Ciclo d'esecuzione principale a 60 FPS."""
        self.update_physics()
        self.draw_scene()
        self.root.after(FRAME_DELAY, self.game_loop)

if __name__ == "__main__":
    root = tk.Tk()
    game = LegendOfNullGame(root)
    root.mainloop()