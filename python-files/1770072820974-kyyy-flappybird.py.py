import pygame, sys, random, json, os

pygame.init()

# --- Genel ayarlar ---
WIDTH, HEIGHT = 480, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy — Store/Inventory Fix + LevelComplete SPACE Fix")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)
big_font = pygame.font.SysFont(None, 34)
title_font = pygame.font.SysFont(None, 40)

# --- Renkler ---
WHITE = (250,250,250); BLACK = (20,20,20); DARK = (40,40,40)
PANEL_BG = (235,235,235); ACCENT_DARK = (30,90,60); GOLD = (220,180,40)
LOCK_GRAY = (140,140,140); RED = (200,50,50)

# --- Kaydetme ---
SAVE_FILE = "save.json"
def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {"highscore":0,"coins":0,"inventory":[],"selected_pattern":"None","unlocked_level":1,"stars":{}}
def save_data(d):
    with open(SAVE_FILE, "w") as f:
        json.dump(d, f)

data = load_data()

# --- Fizik / kuş ---
gravity = 0.4
jump = -9
BIRD_W, BIRD_H = 34, 24
def make_bird_rect():
    return pygame.Rect(60, HEIGHT//2 - BIRD_H//2, BIRD_W, BIRD_H)

bird = make_bird_rect()
velocity = 0

# --- Borular ---
pipe_width = 60
pipe_gap = 150
BASE_PIPE_SPEED = 3
pipe_speed = BASE_PIPE_SPEED

def create_pipe():
    h = random.randint(60, HEIGHT - pipe_gap - 80)
    top = pygame.Rect(WIDTH, 0, pipe_width, h)
    bottom = pygame.Rect(WIDTH, h + pipe_gap, pipe_width, HEIGHT - (h + pipe_gap))
    return {"top": top, "bottom": bottom, "passed": False}

pipes = [create_pipe()]

# --- Levels / store / patterns ---
levels = {i: {"requirement": 10 if i==1 else 10 + (i-1)*5, "reward": 50 if i==1 else 50 + (i-1)*30} for i in range(1,16)}
unlocked_level = data.get("unlocked_level", 1)
level_stars = data.get("stars", {})

pattern_items = {
    "None": {"price":0, "desc":"No pattern"},
    "Skyline": {"price":100, "desc":"Thin horizontal lines."},
    "Nebula": {"price":150, "desc":"Soft blotches."},
    "Aurora": {"price":200, "desc":"Vertical gradient bands."},
    "Comet": {"price":250, "desc":"Comet tail effect."},
    "Circuit": {"price":300, "desc":"Geometric circuit lines."}
}

# --- Oyun durumları ---
inventory = data.get("inventory", [])
coins = data.get("coins", 0)
score = 0
selected_pattern = data.get("selected_pattern", "None")
menu_state = "menu"   # menu, playing, level_complete, game_over
current_level = None
level_progress = 0
game_over = False
store_open = False
inv_open = False

# --- PowerUp sınıf (basit) ---
class PowerUp:
    def __init__(self, kind, x, y, duration_ms):
        self.kind = kind
        self.rect = pygame.Rect(x, y, 22, 22)
        self.collected = False
        self.active = False
        self.start_time = 0
        self.duration = duration_ms
    def spawn_move(self, speed):
        self.rect.x -= speed
    def try_collect(self, player_rect, now_ms):
        if not self.collected and player_rect.colliderect(self.rect):
            self.collected = True
            self.activate(now_ms)
            return True
        return False
    def activate(self, now_ms):
        self.active = True
        self.start_time = now_ms
    def update_active(self, now_ms):
        if self.active and (now_ms - self.start_time) >= self.duration:
            self.active = False
            return True
        return False

powerups = []
def spawn_powerup_near_pipe(pipes):
    if not pipes:
        y = random.randint(120, HEIGHT-120)
    else:
        last = pipes[-1]
        gap_top = last["top"].height
        gap_bottom = last["bottom"].y
        if gap_bottom - gap_top > 80:
            y = random.randint(gap_top + 20, gap_bottom - 40)
        else:
            y = random.randint(120, HEIGHT-120)
    kind = random.choice(["shield","double","speed"])
    duration = 7000 if kind != "speed" else 6000
    return PowerUp(kind, WIDTH, y, duration)

# --- Pattern surfaces (basit) ---
pattern_surfaces = {}
BIRD_SURF_SIZE = (40, 30)
def generate_pattern_surface(name, size):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    w, h = size
    if name == "None":
        pygame.draw.circle(surf, (120,120,120), (6, h-6), 3)
    elif name == "Skyline":
        for i in range(0, h, 4):
            color = (120 + (i % 40), 140 + (i % 60), 160)
            pygame.draw.rect(surf, color, (0, i, w, 2))
    elif name == "Nebula":
        seeds = [(w//4, h//3, 6), (w//2, h//2, 8), (3*w//4, h//3, 5)]
        for (rx, ry, r) in seeds:
            pygame.draw.circle(surf, (160,120,200,200), (rx, ry), r)
    elif name == "Aurora":
        for i in range(0, w, max(1, w//6)):
            col = (80 + (i//max(1,w//6))*20, 160 - (i//max(1,w//6))*10, 180 + (i//max(1,w//6))*5)
            pygame.draw.rect(surf, col, (i, 0, max(1,w//6), h))
    elif name == "Comet":
        pygame.draw.polygon(surf, (220,180,100), [(w-2, h//2), (w+18, h//2-6), (w+18, h//2+6)])
    elif name == "Circuit":
        step = 6
        for x in range(4, w-4, step):
            pygame.draw.line(surf, (80,200,160), (x, 4), (x, h-4), 1)
    return surf

for pname in pattern_items.keys():
    pattern_surfaces[pname] = generate_pattern_surface(pname, BIRD_SURF_SIZE)

def draw_bird(surface, rect, pattern_name):
    body = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.ellipse(body, (210,210,210), (0,0,rect.w,rect.h))
    pygame.draw.circle(body, WHITE, (rect.w-10, 6), 3)
    pygame.draw.circle(body, BLACK, (rect.w-10, 6), 2)
    pat = pattern_surfaces.get(pattern_name)
    if pat:
        pat_scaled = pygame.transform.smoothscale(pat, (rect.w, rect.h))
        body.blit(pat_scaled, (0,0), special_flags=pygame.BLEND_RGBA_ADD)
    surface.blit(body, (rect.x, rect.y))

# --- Reset / complete helpers ---
def reset_game_for_level():
    global bird, velocity, pipes, score, game_over, level_progress, pipe_speed, powerups
    bird = make_bird_rect()
    velocity = 0
    pipes = [create_pipe()]
    score = 0
    game_over = False
    level_progress = 0
    pipe_speed = BASE_PIPE_SPEED
    powerups = []

def complete_level(level_num):
    global coins, unlocked_level, data, level_stars
    reward = levels[level_num]["reward"]
    coins += reward
    if level_num >= unlocked_level and level_num < max(levels.keys()):
        unlocked_level = level_num + 1
    level_stars[str(level_num)] = 3
    data["coins"] = coins
    data["unlocked_level"] = unlocked_level
    data["stars"] = level_stars
    save_data(data)

# --- Admin / menu variables ---
ADMIN_PASSWORD = "1547"
awaiting_admin_password = False
admin_password_input = ""
admin_panel_open = False
admin_state = {"invincible": False}

# --- Level select drawing (oklar kaldırıldı) ---
LEVELS_PER_ROW = 5; LEVEL_ROWS = 3
LEVEL_BUTTON_SIZE = 64; LEVEL_BUTTON_PADDING = 18
LEVEL_PANEL_W = WIDTH - 40; LEVEL_PANEL_H = 360

def draw_level_button(surface, x, y, level_num, unlocked, stars_count):
    rect = pygame.Rect(x, y, LEVEL_BUTTON_SIZE, LEVEL_BUTTON_SIZE)
    bg = PANEL_BG if unlocked else (230,230,230)
    pygame.draw.rect(surface, bg, rect, border_radius=8)
    border_col = ACCENT_DARK if unlocked else LOCK_GRAY
    pygame.draw.rect(surface, border_col, rect, 2, border_radius=8)
    txt = font.render(str(level_num), True, BLACK if unlocked else LOCK_GRAY)
    surface.blit(txt, (x + (LEVEL_BUTTON_SIZE - txt.get_width())//2, y + 10))
    star_y = y - 14
    for i in range(3):
        sx = x + i*14 + 6
        color = GOLD if i < stars_count else (210,210,210)
        pygame.draw.polygon(surface, color, [(sx+6, star_y), (sx+8, star_y+6), (sx+14, star_y+6), (sx+9, star_y+10), (sx+11, star_y+16), (sx+6, star_y+12), (sx+1, star_y+16), (sx+3, star_y+10), (sx-2, star_y+6), (sx+4, star_y+6)])
    if not unlocked:
        lock_rect = pygame.Rect(x + LEVEL_BUTTON_SIZE - 22, y + LEVEL_BUTTON_SIZE - 22, 18, 18)
        pygame.draw.rect(surface, LOCK_GRAY, lock_rect, border_radius=4)
        pygame.draw.rect(surface, (200,200,200), (lock_rect.x+3, lock_rect.y+6, lock_rect.w-6, lock_rect.h-6), border_radius=2)

def draw_level_select(surface):
    panel_x = 20; panel_y = 120
    pygame.draw.rect(surface, PANEL_BG, (panel_x, panel_y, LEVEL_PANEL_W, LEVEL_PANEL_H), border_radius=12)
    pygame.draw.rect(surface, DARK, (panel_x, panel_y, LEVEL_PANEL_W, 44), border_radius=12)
    screen.blit(title_font.render("SELECT LEVEL", True, WHITE), (panel_x + 16, panel_y + 6))
    start_x = panel_x + 18; start_y = panel_y + 64
    idx0 = 0
    for row in range(LEVEL_ROWS):
        for col in range(LEVELS_PER_ROW):
            idx = idx0 + row*LEVELS_PER_ROW + col
            level_num = idx + 1
            bx = start_x + col*(LEVEL_BUTTON_SIZE + LEVEL_BUTTON_PADDING)
            by = start_y + row*(LEVEL_BUTTON_SIZE + 36)
            unlocked = level_num <= unlocked_level
            stars_count = int(level_stars.get(str(level_num), 0))
            draw_level_button(surface, bx, by, level_num, unlocked, stars_count)

# --- Store / Inventory drawing and interaction helpers ---
def draw_store_box(x, y, w, h):
    pygame.draw.rect(screen, PANEL_BG, (x, y, w, h), border_radius=8)
    pygame.draw.rect(screen, DARK, (x, y, w, 30), border_radius=8)
    screen.blit(big_font.render("STORE (Patterns)", True, BLACK), (x+12, y+2))
    return pygame.Rect(x+12, y+36, w-24, h-44)

def draw_inventory_box(x, y, w, h):
    pygame.draw.rect(screen, PANEL_BG, (x, y, w, h), border_radius=8)
    pygame.draw.rect(screen, DARK, (x, y, w, 30), border_radius=8)
    screen.blit(big_font.render("INVENTORY", True, BLACK), (x+12, y+2))
    return pygame.Rect(x+12, y+36, w-24, h-44)

def handle_store_purchase_by_index(idx):
    global coins, inventory, selected_pattern, data
    names = list(pattern_items.keys())
    if 0 <= idx < len(names):
        item = names[idx]
        price = pattern_items[item]["price"]
        if item in inventory:
            return "owned"
        if coins >= price:
            coins -= price
            inventory.append(item)
            selected_pattern = item
            data["inventory"] = inventory
            data["coins"] = coins
            data["selected_pattern"] = selected_pattern
            save_data(data)
            return "bought"
        else:
            return "notenough"
    return "invalid"

def handle_inventory_select_by_index(idx):
    global selected_pattern, data
    if 0 <= idx < len(inventory):
        chosen = inventory[idx]
        selected_pattern = chosen
        data["selected_pattern"] = selected_pattern
        save_data(data)
        return "selected"
    return "invalid"

def draw_store_list(rect):
    sf = pygame.font.SysFont(None, 18)
    y0 = rect.y
    names = list(pattern_items.keys())
    for i, name in enumerate(names, start=1):
        title = f"{i}: {name} ({pattern_items[name]['price']})"
        screen.blit(sf.render(title, True, BLACK), (rect.x, y0))
        y0 += sf.get_height() + 6
        if y0 > rect.y + rect.h - 20:
            break

def draw_inventory_list(rect):
    sf = pygame.font.SysFont(None, 18)
    y0 = rect.y
    for i, name in enumerate(inventory, start=1):
        screen.blit(sf.render(f"{i}: {name}", True, BLACK), (rect.x, y0))
        y0 += sf.get_height() + 6
        if y0 > rect.y + rect.h - 20:
            break

def draw_main_menu(surface):
    surface.fill(WHITE)
    screen.blit(big_font.render("GAME MENU", True, DARK), (24, 18))
    screen.blit(font.render(f"Coins: {coins}", True, BLACK), (24, 64))
    draw_level_select(surface)
    screen.blit(font.render("M: Store   I: Inventory   F1: Admin", True, DARK), (24, LEVEL_PANEL_H + 140))

# --- Admin (parola modal) ---
def draw_admin_panel(px, py, w, h):
    pygame.draw.rect(screen, PANEL_BG, (px, py, w, h), border_radius=8)
    pygame.draw.rect(screen, DARK, (px, py, w, 34), border_radius=8)
    screen.blit(big_font.render("ADMIN PANEL", True, BLACK), (px+12, py+4))
    content_rect = pygame.Rect(px+12, py+44, w-24, h-56)
    items = [
        ("1: +1000 Coins", "Hesabına 1000 coin ekler."),
        ("2: Unlock All Patterns", "Mağazadaki tüm desenleri envanterine ekler."),
        ("3: Toggle Invincibility", "Ölümsüzlük modunu açıp kapatır."),
        ("4: Save Highscore", "Mevcut skoru highscore olarak kaydeder."),
        ("5: Reset All Params", "Tüm oyun parametrelerini sıfırlar."),
        ("6: Reset Coins", "Sadece coin miktarını sıfırlar."),
        ("ESC: Close Admin Panel", "Paneli kapatır.")
    ]
    small_font = pygame.font.SysFont(None, 18)
    y = content_rect.y
    for title, desc in items:
        screen.blit(small_font.render(title, True, BLACK), (content_rect.x, y))
        y += small_font.get_height() + 2
        screen.blit(small_font.render(desc, True, DARK), (content_rect.x, y))
        y += small_font.get_height() + 8

# --- Main loop ---
running = True
mouse_down = False

# helper: map mouse click to store/inv index
def index_from_click_in_list(rect, click_pos, list_len):
    x, y = click_pos
    if not rect.collidepoint(x,y):
        return None
    line_h = font.get_height() + 6
    rel_y = y - rect.y
    idx = rel_y // line_h
    if 0 <= idx < list_len:
        return int(idx)
    return None

while running:
    now_ms = pygame.time.get_ticks()
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            data["coins"] = coins
            data["unlocked_level"] = unlocked_level
            data["stars"] = level_stars
            data["inventory"] = inventory
            data["selected_pattern"] = selected_pattern
            save_data(data)
            pygame.quit()
            sys.exit()

        if e.type == pygame.MOUSEBUTTONDOWN:
            mx, my = e.pos
            mouse_down = True
            # Level select clicks (menu)
            if menu_state == "menu":
                panel_x = 20; panel_y = 120
                start_x = panel_x + 18; start_y = panel_y + 64
                for row in range(LEVEL_ROWS):
                    for col in range(LEVELS_PER_ROW):
                        idx = row*LEVELS_PER_ROW + col
                        level_num = idx + 1
                        bx = start_x + col*(LEVEL_BUTTON_SIZE + LEVEL_BUTTON_PADDING)
                        by = start_y + row*(LEVEL_BUTTON_SIZE + 36)
                        btn_rect = pygame.Rect(bx, by, LEVEL_BUTTON_SIZE, LEVEL_BUTTON_SIZE)
                        if btn_rect.collidepoint(mx,my) and level_num <= unlocked_level:
                            current_level = level_num
                            reset_game_for_level()
                            menu_state = "playing"
            # If store open, handle mouse purchases
            if store_open:
                box_w, box_h = 360, 320 if menu_state=="menu" else 220
                bx = (WIDTH - box_w)//2; by = 120 + LEVEL_PANEL_H + 8 if menu_state=="menu" else (HEIGHT//2 + 70)
                store_rect = pygame.Rect(bx+12, by+36, box_w-24, box_h-44)
                idx = index_from_click_in_list(store_rect, (mx,my), len(pattern_items))
                if idx is not None:
                    handle_store_purchase_by_index(idx)
            # If inventory open, handle mouse selection
            if inv_open:
                box_w, box_h = 360, 220
                bx = (WIDTH - box_w)//2; by = 120 + LEVEL_PANEL_H + 8 if menu_state=="menu" else (HEIGHT//2 + 70)
                inv_rect = pygame.Rect(bx+12, by+36, box_w-24, box_h-44)
                idx = index_from_click_in_list(inv_rect, (mx,my), len(inventory))
                if idx is not None:
                    handle_inventory_select_by_index(idx)

        if e.type == pygame.MOUSEBUTTONUP:
            mouse_down = False

        if e.type == pygame.KEYDOWN:
            # F1: admin password modal open
            if e.key == pygame.K_F1:
                if admin_panel_open:
                    admin_panel_open = False
                else:
                    awaiting_admin_password = True
                    admin_password_input = ""

            # password modal handling
            if awaiting_admin_password:
                if e.key == pygame.K_RETURN:
                    if admin_password_input == ADMIN_PASSWORD:
                        admin_panel_open = True
                    awaiting_admin_password = False
                    admin_password_input = ""
                elif e.key == pygame.K_BACKSPACE:
                    admin_password_input = admin_password_input[:-1]
                elif e.key == pygame.K_ESCAPE:
                    awaiting_admin_password = False
                    admin_password_input = ""
                else:
                    ch = e.unicode
                    if ch and len(ch) == 1 and ord(ch) >= 32:
                        if len(admin_password_input) < 32:
                            admin_password_input += ch

            # admin panel commands
            if admin_panel_open:
                if e.key == pygame.K_1:
                    coins += 1000
                if e.key == pygame.K_2:
                    for name in pattern_items.keys():
                        if name not in inventory:
                            inventory.append(name)
                if e.key == pygame.K_3:
                    admin_state["invincible"] = not admin_state["invincible"]
                if e.key == pygame.K_4:
                    data["highscore"] = max(data.get("highscore",0), score)
                    save_data(data)
                if e.key == pygame.K_5:
                    data = {"highscore":0,"coins":0,"inventory":[],"selected_pattern":"None","unlocked_level":1,"stars":{}}
                    save_data(data)
                    inventory.clear(); coins = 0; score = 0; selected_pattern = "None"; unlocked_level = 1; level_stars.clear()
                if e.key == pygame.K_6:
                    coins = 0
                    data["coins"] = coins
                    save_data(data)
                if e.key == pygame.K_ESCAPE:
                    admin_panel_open = False

            # Menu / global keys (M/I) — works in menu and game_over and level_complete
            if e.key == pygame.K_m:
                store_open = not store_open
                inv_open = False
            if e.key == pygame.K_i:
                inv_open = not inv_open
                store_open = False

            # If store open and user presses number key, attempt purchase
            if store_open:
                if e.unicode.isdigit():
                    try:
                        idx = int(e.unicode) - 1
                        handle_store_purchase_by_index(idx)
                    except:
                        pass

            # If inventory open and user presses number key, select
            if inv_open:
                if e.unicode.isdigit():
                    try:
                        idx = int(e.unicode) - 1
                        handle_inventory_select_by_index(idx)
                    except:
                        pass

            # Playing keys
            if menu_state == "playing":
                if e.key == pygame.K_SPACE:
                    if not game_over and not admin_panel_open and not awaiting_admin_password:
                        velocity = jump
                if e.key == pygame.K_ESCAPE:
                    menu_state = "menu"
                    current_level = None
                    reset_game_for_level()

            # Level complete: SPACE should return to menu (DÜZELTME)
            if menu_state == "level_complete":
                if e.key == pygame.K_SPACE:
                    menu_state = "menu"
                    current_level = None
                    reset_game_for_level()
                    store_open = False
                    inv_open = False
                    game_over = False

            # Game over -> SPACE to menu
            if menu_state == "game_over":
                if e.key == pygame.K_SPACE:
                    menu_state = "menu"
                    current_level = None
                    reset_game_for_level()
                    store_open = False; inv_open = False; game_over = False

    # --- Oyun mantığı (oynuyorsak) ---
    if menu_state == "playing" and not game_over and not admin_panel_open:
        velocity += gravity
        bird.y += velocity

        for pipe in pipes:
            pipe["top"].x -= pipe_speed
            pipe["bottom"].x -= pipe_speed

        if pipes and pipes[-1]["top"].x < WIDTH - 220:
            pipes.append(create_pipe())

        pipes = [p for p in pipes if p["top"].right > -50]

        for pu in powerups:
            pu.spawn_move(pipe_speed)
        powerups = [pu for pu in powerups if pu.rect.right > -40 or pu.active]

        if random.randint(0, 180) == 1:
            powerups.append(spawn_powerup_near_pipe(pipes))

        for pu in powerups:
            if pu.try_collect(bird, now_ms):
                if pu.kind == "speed":
                    pipe_speed = BASE_PIPE_SPEED + 2

        for pu in powerups:
            if pu.active:
                expired = pu.update_active(now_ms)
                if expired and pu.kind == "speed":
                    pipe_speed = BASE_PIPE_SPEED

        collided = False
        for pipe in pipes:
            if bird.colliderect(pipe["top"]) or bird.colliderect(pipe["bottom"]):
                shield_active = any(p.kind == "shield" and p.active for p in powerups)
                if not (admin_state.get("invincible", False) or shield_active):
                    collided = True
                    break
        if collided:
            game_over = True
            menu_state = "game_over"

        if bird.top < 0 or bird.bottom > HEIGHT - 1:
            shield_active = any(p.kind == "shield" and p.active for p in powerups)
            if not (admin_state.get("invincible", False) or shield_active):
                game_over = True
                menu_state = "game_over"

        for pipe in pipes:
            if not pipe["passed"] and pipe["top"].x + pipe_width < bird.x:
                pipe["passed"] = True
                score += 1
                gain = 10
                if any(p.kind == "double" and p.active for p in powerups):
                    gain *= 2
                coins += gain
                level_progress += 1
                if current_level is not None:
                    req = levels[current_level]["requirement"]
                    if level_progress >= req:
                        complete_level(current_level)
                        menu_state = "level_complete"
                        game_over = True

    # --- Çizimler ---
    screen.fill(WHITE)

    if menu_state == "menu":
        draw_main_menu(screen)
        # draw store/inv if open
        if store_open:
            box_w, box_h = 360, 320
            bx = (WIDTH - box_w)//2; by = 120 + LEVEL_PANEL_H + 8
            store_rect = draw_store_box(bx, by, box_w, box_h)
            draw_store_list(store_rect)
        if inv_open:
            box_w, box_h = 360, 220
            bx = (WIDTH - box_w)//2; by = 120 + LEVEL_PANEL_H + 8
            inv_rect = draw_inventory_box(bx, by, box_w, box_h)
            draw_inventory_list(inv_rect)
        if awaiting_admin_password:
            modal_w, modal_h = 320, 140
            mx = (WIDTH - modal_w)//2; my = (HEIGHT - modal_h)//2
            pygame.draw.rect(screen, PANEL_BG, (mx, my, modal_w, modal_h), border_radius=8)
            pygame.draw.rect(screen, DARK, (mx, my, modal_w, 28), border_radius=8)
            screen.blit(big_font.render("ADMIN LOGIN", True, BLACK), (mx+12, my+2))
            screen.blit(font.render("Enter password (Esc to cancel)", True, BLACK), (mx+12, my+36))
            input_box = pygame.Rect(mx+12, my+64, modal_w-24, 36)
            pygame.draw.rect(screen, WHITE, input_box, border_radius=6)
            masked = "*" * len(admin_password_input)
            screen.blit(font.render(masked, True, BLACK), (input_box.x+8, input_box.y+8))
        if admin_panel_open:
            draw_admin_panel((WIDTH-360)//2, (HEIGHT-260)//2, 360, 260)

    elif menu_state == "playing":
        pygame.draw.rect(screen, (220,240,220), (0,0,WIDTH,HEIGHT))
        draw_bird(screen, bird, selected_pattern)
        for pipe in pipes:
            pygame.draw.rect(screen, ACCENT_DARK, pipe["top"])
            pygame.draw.rect(screen, ACCENT_DARK, pipe["bottom"])
        for pu in powerups:
            if not pu.collected:
                color = {"shield":(100,180,240),"double":(240,220,100),"speed":(240,100,100)}.get(pu.kind, (120,120,120))
                pygame.draw.ellipse(screen, color, pu.rect)
                label = font.render(pu.kind[0].upper(), True, BLACK)
                screen.blit(label, (pu.rect.x + (pu.rect.w - label.get_width())//2, pu.rect.y + (pu.rect.h - label.get_height())//2))
        screen.blit(font.render(f"Level: {current_level}", True, BLACK), (16, 12))
        screen.blit(font.render(f"Score: {score}", True, BLACK), (16, 36))
        if current_level:
            screen.blit(font.render(f"Progress: {level_progress}/{levels[current_level]['requirement']}", True, BLACK), (16, 60))
        screen.blit(font.render(f"Coins: {coins}", True, BLACK), (WIDTH-140, 12))
        hud_y = 36
        for pu in powerups:
            if pu.active:
                remaining = max(0, (pu.duration - (now_ms - pu.start_time)) // 1000)
                screen.blit(font.render(f"{pu.kind.capitalize()}: {remaining}s", True, BLACK), (WIDTH-140, hud_y))
                hud_y += 18

    elif menu_state == "level_complete":
        screen.fill(WHITE)
        screen.blit(big_font.render("LEVEL COMPLETE", True, ACCENT_DARK), (WIDTH//2 - 140, HEIGHT//2 - 80))
        screen.blit(font.render(f"You earned {levels[current_level]['reward']} coins!", True, BLACK), (WIDTH//2 - 120, HEIGHT//2 - 30))
        screen.blit(font.render("Press SPACE to return to menu", True, DARK), (WIDTH//2 - 140, HEIGHT//2 + 10))

    elif menu_state == "game_over":
        screen.fill(WHITE)
        screen.blit(big_font.render("GAME OVER", True, RED), (WIDTH//2 - 110, HEIGHT//2 - 80))
        screen.blit(font.render("Press SPACE to return to menu", True, DARK), (WIDTH//2 - 120, HEIGHT//2 - 30))
        screen.blit(font.render(f"Score: {score}  Coins: {coins}", True, BLACK), (WIDTH//2 - 120, HEIGHT//2 + 10))
        screen.blit(font.render("M: Store | I: Inventory | SPACE: Menu", True, DARK), (WIDTH//2 - 160, HEIGHT//2 + 40))
        if store_open:
            box_w, box_h = 360, 220
            bx = (WIDTH - box_w)//2; by = HEIGHT//2 + 70
            store_rect = draw_store_box(bx, by, box_w, box_h)
            draw_store_list(store_rect)
        if inv_open:
            box_w, box_h = 360, 220
            bx = (WIDTH - box_w)//2; by = HEIGHT//2 + 70
            inv_rect = draw_inventory_box(bx, by, box_w, box_h)
            draw_inventory_list(inv_rect)

    # alt bilgi
    screen.blit(font.render("Tip: Press M/I to open Store/Inventory. Click or press number to buy/select.", True, DARK), (16, HEIGHT-28))

    pygame.display.update()
    clock.tick(60)
import pyinstaller
pyinstaller --onefile --windowed main.py
