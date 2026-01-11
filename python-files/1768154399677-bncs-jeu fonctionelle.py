import pygame
import sys
import random
import os
import time

pygame.init()
pygame.mixer.init()

# ---------- FENETRE ----------
WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RPG Jour/Nuit avec Arbres et Donjons")

# ---------- POLICES ----------
FONT = pygame.font.SysFont("arial", 22)
BIGFONT = pygame.font.SysFont("arial", 28)

# ---------- COULEURS V2 ----------
GREEN = (70, 180, 110)
DARK_GREEN = (40, 120, 80)

BROWN = (150, 90, 50)
DARK_BROWN = (90, 60, 40)

BLUE = (70, 120, 255)
LIGHT_BLUE = (120, 180, 255)

WHITE = (245, 245, 245)
BLACK = (20, 20, 20)

YELLOW = (255, 220, 100)
ORANGE = (255, 160, 60)
RED = (230, 60, 60)
CYAN = (90, 220, 255)

GRAY = (170, 170, 170)
DARK_GRAY = (90, 90, 90)

LEVELUP_COLOR = (120, 255, 120)
DOOR_COLOR = (230, 200, 90)


# ---------- SKIN MENU COLORS ----------
SKIN_BG = (30, 30, 40)
SKIN_SLOT = (70, 120, 160)
SKIN_SLOT_HOVER = (100, 160, 210)
SKIN_SLOT_ACTIVE = (120, 220, 120)
SKIN_SLOT_LOCKED = (90, 60, 60)

SKIN_TEXT = (245, 245, 245)
SKIN_TEXT_LOCKED = (180, 120, 120)
SKIN_TEXT_ACTIVE = (20, 80, 20)




# ---------- TILE SYSTEM ----------
TILE = 40
MAP_W = 40
MAP_H = 30

# ---------- ASSETS FOLDER ----------
ASSETS_DIR = os.path.join("assets", "inventory")
# filenames
NAME_BACKGROUND_FILE = "rpg.png"
NIGHT_MUSIC_FILE = "nuit.mp3"
POP_SOUND_FILE = "pop.wav"
CUT_SOUND_FILE = "cut.wav"
DONJON_IMG_FILE = "donjon.png"
TREE_IMG_FILE = "woodrpg.png"

# ---------- DONJONS (top-left positions) ----------
# Each dungeon will be drawn as a 2x2 (so covers (x,y),(x+1,y),(x,y+1),(x+1,y+1))
dungeons = {
    (5, 4): "Donjon de la Forêt",
    (14, 9): "Donjon Souterrain"
}

# ---------- JOUEUR ----------
player_x = 2
player_y = 2
player_hp = 30
player_max_hp = 30
player_base_atk = 15
player_atk = player_base_atk
player_level = 1
player_exp = 0
exp_to_next = 30
move_cooldown = False
player_name = "???"
bouclier_rage_active = False
soutien_skin_unlocked = False
soutien_skin_active = False


# ---------- CLASSE ----------
player_class = None
# ---------- PASSIF SOUTIEN ----------
SOUTIEN_POTION_INTERVAL = 30000  # 30 secondes en ms
last_soutien_potion_time = 0

# ---------- EQUIPEMENT ----------
equipped = {"arme": None, "armure": None}

# ---------- INVENTAIRE EMPILABLE ----------
inventory = {}  # ex: {"Potion":2, "Bois":5}
ITEMS = ["Potion", "Épée en fer", "Armure légère", "Potion ++", "Bois"]
ITEMS.append("Pièce")      # Ajouter "Pièce" à la liste des items lootables
inventory["Pièce"] = 0     # Initialise le nombre de pièces à 0

def add_to_inventory(item, qty=1):
    if item in inventory:
        inventory[item] += qty
    else:
        inventory[item] = qty

# ---------- CHARGEMENT ICÔNES / IMAGES / SONS ----------
def load_image(filename, size=None):
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.isfile(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.scale(img, size)
            return img
        except Exception as e:
            print(f"Erreur chargement image {path}: {e}")
            return None
    else:
        # print info but don't crash
        print(f"[Info] image non trouvée : {path}")
        return None

def load_sound(filename):
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.isfile(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Erreur chargement son {path}: {e}")
            return None
    else:
        print(f"[Info] son non trouvé : {path}")
        return None

# item icons (32x32)
item_icons = {
    "Potion": load_image("potion.png", (32,32)),
    "Épée en fer": load_image("sword.png", (32,32)),
    "Armure légère": load_image("armor.png", (32,32)),
    "Potion ++": load_image("potion_plus.png", (32,32)),
    "Bois": load_image("wood.png", (32,32))
}

# background for name entry
name_background = load_image(NAME_BACKGROUND_FILE, (WIDTH, HEIGHT))

# donjon image scaled to 2x2 tiles (TILE*2)
donjon_icon = load_image(DONJON_IMG_FILE, (TILE*2, TILE*2))

# tree image (tile-sized)
tree_icon = load_image(TREE_IMG_FILE, (TILE, TILE))

ROCHER_IMG_FILE = "rocher.png"
rocher_icon = load_image(ROCHER_IMG_FILE, (TILE, TILE))

# night music path (we'll load via mixer if present)
night_music_path = os.path.join(ASSETS_DIR, NIGHT_MUSIC_FILE)
night_music = night_music_path if os.path.isfile(night_music_path) else None

# sounds
pop_sound = load_sound(POP_SOUND_FILE)
cut_sound = load_sound(CUT_SOUND_FILE)
# joueur
ASSASSIN_IMG_FILE = "guerrier.png"   # ancien guerrier
MAGE_IMG_FILE = "sorcier.png"        # ancien sorcier
TANK_IMG_FILE = "tank.png"
SOUTIEN_IMG_FILE = "soutien.png"
BOUCLIER_IMG_FILE = "bouclier.png"

assassin_img = load_image(ASSASSIN_IMG_FILE, (TILE, TILE))
mage_img = load_image(MAGE_IMG_FILE, (TILE, TILE))
tank_img = load_image(TANK_IMG_FILE, (TILE, TILE))
soutien_img = load_image(SOUTIEN_IMG_FILE, (TILE, TILE))
bouclier_img = load_image(BOUCLIER_IMG_FILE, (TILE, TILE))

item_icons["Pièce"] = load_image("piece.png", (32, 32))

shop_icon = load_image("shop.png", (TILE, TILE))

#skin
SOUTIEN_SKIN_IMG_FILE = "soutien_skin.png"
soutien_skin_img = load_image(SOUTIEN_SKIN_IMG_FILE, (TILE, TILE))

SOUTIEN_SKIN2_IMG_FILE = "soutien_skin2.png"
soutien_skin2_img = load_image(SOUTIEN_SKIN2_IMG_FILE, (TILE, TILE))

# --- SKINS BUCHERON ---
ASSASSIN_SKIN_BUCHERON_FILE = "assassin_skinbucheron.png"
TANK_SKIN_BUCHERON_FILE = "tank_skinbucheron.png"
MAGE_SKIN_BUCHERON_FILE = "mage_skinbucheron.png"
BOUCLIER_SKIN_BUCHERON_FILE = "bouclier_sbucheron.png"

assassin_skin_bucheron_img = load_image(ASSASSIN_SKIN_BUCHERON_FILE, (TILE, TILE))
tank_skin_bucheron_img = load_image(TANK_SKIN_BUCHERON_FILE, (TILE, TILE))
mage_skin_bucheron_img = load_image(MAGE_SKIN_BUCHERON_FILE, (TILE, TILE))
bouclier_skin_bucheron_img = load_image(BOUCLIER_SKIN_BUCHERON_FILE, (TILE, TILE))


SKINS = {
    "Soutien": {
        "Base": {
            "img": soutien_img,
            "unlocked": True
        },
        "Pass": {
            "img": soutien_skin_img,
            "unlocked": False
        },
        "Roi Mage": {   # ← nouveau skin
            "img": soutien_skin2_img,
            "unlocked": False
        }
    },
    "Assassin": {
    "Base": {
        "img": assassin_img,
        "unlocked": True
    },
    "bucheron": {   # ← nouveau skin
        "img": assassin_skin_bucheron_img,
        "unlocked": False
    } # <- ici la virgule est OK si tu ajoutes d'autres skins après

    },
    "Tank": {
        "Base": {
            "img": tank_img,
            "unlocked": True
        },
        "bucheron": {   # ← nouveau skin
        "img": tank_skin_bucheron_img,
        "unlocked": False
    } # <- ici la virgule est OK si tu ajoutes d'autres skins après
    },
    "Mage": {
        "Base": {
            "img": mage_img,
            "unlocked": True
        },
        "bucheron": {   # ← nouveau skin
        "img": mage_skin_bucheron_img,
        "unlocked": False
    } # <- ici la virgule est OK si tu ajoutes d'autres skins après
    },
    "Bouclier": {
        "Base": {
            "img": bouclier_img,
            "unlocked": True
        },
        "bucheron": {   # ← nouveau skin
        "img": bouclier_skin_bucheron_img,
        "unlocked": False
    } # <- ici la virgule est OK si tu ajoutes d'autres skins après
    }
}


# Déclare ces variables en haut de ton fichier, avec les autres globals
CLASS_COOLDOWN = 120000  # 2 minutes en millisecondes
last_class_change = -CLASS_COOLDOWN  # permet un premier changement immédiat

def open_class_menu():
    global player_class, player_hp, player_max_hp, player_base_atk, player_atk, player_img, current_skin
    global last_class_change

    now = pygame.time.get_ticks()
    if now - last_class_change < CLASS_COOLDOWN:
        remaining = (CLASS_COOLDOWN - (now - last_class_change)) // 1000
        add_floating_message(f"Classe indisponible, attendre {remaining}s", (255, 0, 0))
        return

    buttons = {}
    x_start = 150
    y_start = 150
    gap = 130

    for i, class_name in enumerate(CLASSES.keys()):
        buttons[class_name] = pygame.Rect(x_start + i * gap, y_start, 120, 60)

    running = True
    while running:
        win.fill(BLACK)
        win.blit(BIGFONT.render("Changer de classe", True, WHITE), (250, 50))

        mx, my = pygame.mouse.get_pos()

        for class_name, rect in buttons.items():
            pygame.draw.rect(win, CYAN, rect)
            win.blit(FONT.render(class_name, True, BLACK), (rect.x + 10, rect.y + 18))
            if rect.collidepoint(mx, my):
                pygame.draw.rect(win, YELLOW, rect, 3)

        win.blit(FONT.render("ESC pour annuler", True, WHITE), (300, 500))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for class_name, rect in buttons.items():
                    if rect.collidepoint((mx, my)):
                        data = CLASSES[class_name]
                        player_class = class_name
                        player_max_hp = data["hp"]
                        player_hp = data["hp"]
                        player_base_atk = data["atk"]
                        player_atk = data["atk"]

                        # remettre skin de base
                        current_skin = "Base"
                        player_img = SKINS[player_class]["Base"]["img"]

                        if class_name == "Soutien":
                            global last_soutien_potion_time
                            last_soutien_potion_time = pygame.time.get_ticks()

                        add_floating_message(f"Classe changée : {class_name}", (0, 255, 255))
                        last_class_change = pygame.time.get_ticks()  # <-- MAJ cooldown
                        return


# ---------- ENNEMIS MAP / SPAWN ----------
class Enemy:
    def __init__(self, name="Monstre", hp=20, atk=5, exp=10):
        self.name = name
        self.hp = hp
        self.atk = atk
        self.exp_reward = exp

class MapEnemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 15
        self.atk = 5

map_enemies = []
num_enemies = 5

def spawn_night_enemies():
    global map_enemies
    map_enemies = []
    tries_limit = 200
    for _ in range(num_enemies):
        tries = 0
        while True:
            x = random.randint(0, MAP_W-1)
            y = random.randint(0, MAP_H-1)
            tries += 1
            # avoid colliding with player start and dungeon top-left cluster
            collision_with_dungeon = False
            for (dx,dy) in dungeons.keys():
                if (x,y) in {(dx,dy),(dx+1,dy),(dx,dy+1),(dx+1,dy+1)}:
                    collision_with_dungeon = True
                    break
            if (x,y) != (player_x, player_y) and not collision_with_dungeon:
                map_enemies.append(MapEnemy(x,y))
                break
            if tries > tries_limit:
                break

# ---------- ARBRES ----------
trees = []
num_trees = 150  # plus d'arbres pour remplir la map

for _ in range(num_trees):
    tries = 0
    while True:
        tx = random.randint(0, MAP_W-1)
        ty = random.randint(0, MAP_H-1)
        tries += 1
        # Evite player start, donjons et arbres déjà placés
        collision = (tx, ty) == (player_x, player_y)
        for (dx, dy) in dungeons.keys():
            if (tx, ty) in {(dx,dy),(dx+1,dy),(dx,dy+1),(dx+1,dy+1)}:
                collision = True
                break
        if (tx, ty) in trees:
            collision = True
        if not collision:
            trees.append((tx, ty))
            break
        if tries > 500:  # plus de tentatives si la map est grande
            break


cutting_tree = None
cut_start_time = None
CUT_DURATION = 2000  # ms pour couper un arbre


rocks = []
num_rocks = 50  # nombre de rochers à placer

for _ in range(num_rocks):
    tries = 0
    while True:
        rx = random.randint(0, MAP_W-1)
        ry = random.randint(0, MAP_H-1)
        tries += 1

        # Evite player start, donjons, arbres et rochers déjà placés
        collision = (rx, ry) == (player_x, player_y)
        for (dx, dy) in dungeons.keys():
            if (rx, ry) in {(dx,dy),(dx+1,dy),(dx,dy+1),(dx+1,dy+1)}:
                collision = True
                break
        if (rx, ry) in trees or (rx, ry) in rocks:
            collision = True

        if not collision:
            rocks.append((rx, ry))
            break
        if tries > 500:
            break


# ---------- MESSAGES FLOTTANTS ----------
floating_messages = []  # dicts with keys: text, color, start_time
def add_floating_message(text, color=YELLOW):
    floating_messages.append({"text": text, "color": color, "start_time": pygame.time.get_ticks()})

# ---------- LEVEL UP ----------
def add_exp(amount):
    global player_exp, player_level, exp_to_next
    global player_hp, player_max_hp, player_base_atk, player_atk

    player_exp += amount

    if pop_sound:
        try:
            pop_sound.play()
        except:
            pass

    add_floating_message(f"+{amount} EXP", YELLOW)

    while player_exp >= exp_to_next:
        player_exp -= exp_to_next
        player_level += 1
        exp_to_next = int(exp_to_next * 1.4)

        # ----- STATS -----
        player_max_hp += 5
        player_hp = player_max_hp
        player_base_atk += 1
        player_atk = player_base_atk

        if equipped["arme"] == "Épée en fer":
            player_atk += 5

        add_floating_message(f"Niveau {player_level} !", LEVELUP_COLOR)

        # 🎁 RÉCOMPENSE DE NIVEAU (1 → 6)
        reward = LEVEL_REWARDS.get(player_level)
        if reward:
            item, qty = reward
            add_to_inventory(item, qty)
            add_floating_message(f"Récompense : {item}", CYAN)
#passe de combat
def add_pass_exp(amount):
    global pass_exp, pass_level, pass_exp_to_next

    if pass_level >= PASS_MAX_LEVEL:
        return

    pass_exp += amount

    while pass_exp >= pass_exp_to_next and pass_level < PASS_MAX_LEVEL:
        pass_exp -= pass_exp_to_next
        pass_level += 1

        add_floating_message(f"PASS +1 (Palier {pass_level})", CYAN)

        # 🎁 RÉCOMPENSE DU PASS
        if pass_level == 1:
            add_to_inventory("Potion", 1)
            add_floating_message("Récompense : Potion", CYAN)
            pass
        elif pass_level == 2:
            add_to_inventory("Potion", 1)
            add_floating_message("Récompense : Potion", CYAN)
            pass
        elif pass_level == 3:
            add_to_inventory("Potion", 1)
            add_floating_message("Récompense : Potion", CYAN)
            pass
        elif pass_level == 4:
            add_to_inventory("Potion", 1)
            add_floating_message("Récompense : Potion", CYAN)
            pass
        elif pass_level == 5:
            add_to_inventory("Potion", 1)
            add_floating_message("Récompense : Potion", CYAN)
            pass
        elif pass_level == 6:
            add_to_inventory("Potion", 1)
            add_floating_message("Récompense : Potion", CYAN)
            pass
        elif pass_level == 7:
            add_to_inventory("Potion", 1)
            add_floating_message("Récompense : Potion", CYAN)
            pass
        elif pass_level == 8:
            add_to_inventory("Potion", 1)
            add_floating_message("Récompense : Potion", CYAN)
            pass
        elif pass_level == 9:
            add_to_inventory("Potion", 1)
            add_floating_message("Récompense : Potion", CYAN)
            pass
        elif pass_level == 10:
            add_to_inventory("Potion", 3)
            SKINS["Soutien"]["Pass"]["unlocked"] = True
            add_floating_message("Skin Soutien débloqué !", LEVELUP_COLOR)


def open_pass_menu():
    running = True
    slot_w, slot_h = 200, 50
    x_start, y_start = 150, 100
    gap = 10
    scroll_y = 0  # <-- offset vertical
    scroll_speed = 30  # pixels par "crantage" de molette

    while running:
        win.fill(GRAY)

        # Titre
        win.blit(BIGFONT.render("PASS MENU", True, BLACK), (300, 30))

        # ---------- Barre Pass en haut ----------
        BAR_W, BAR_H = 300, 20
        bar_x, bar_y = WIDTH//2 - BAR_W//2, 70
        pygame.draw.rect(win, BLACK, (bar_x, bar_y, BAR_W, BAR_H))
        fill = int((pass_exp / pass_exp_to_next) * BAR_W)
        pygame.draw.rect(win, CYAN, (bar_x, bar_y, fill, BAR_H))
        txt = FONT.render(f"PASS {pass_level}/{PASS_MAX_LEVEL}  ({pass_exp}/{pass_exp_to_next} EXP)", True, WHITE)
        win.blit(txt, (bar_x, bar_y - 25))

        # Afficher les paliers
        for i in range(1, PASS_MAX_LEVEL + 1):
            y = y_start + (i - 1) * (slot_h + gap) + scroll_y
            rect = pygame.Rect(x_start, y, slot_w, slot_h)
            pygame.draw.rect(win, CYAN if pass_level >= i else BLACK, rect)
            pygame.draw.rect(win, WHITE, rect, 2)

            status = "✅" if pass_level >= i else f"{pass_exp}/{pass_exp_to_next} EXP" if pass_level == i else ""
            win.blit(FONT.render(f"Palier {i} {status}", True, WHITE), (rect.x + 10, rect.y + 15))

        win.blit(FONT.render("ESC pour fermer", True, BLACK), (300, 580))
        pygame.display.update()

        # Événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Fermer menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            # ----- SCROLL MOLETTE -----
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # molette HAUT
                    scroll_y += scroll_speed
                elif event.button == 5:  # molette BAS
                    scroll_y -= scroll_speed

                # Limiter le scroll pour ne pas dépasser le haut ou le bas
                max_scroll = 0
                min_scroll = -((slot_h + gap) * PASS_MAX_LEVEL - (HEIGHT - y_start - 50))
                if scroll_y > max_scroll:
                    scroll_y = max_scroll
                elif scroll_y < min_scroll:
                    scroll_y = min_scroll

# ---------- MENU DE SKINS ----------
def open_skin_menu():
    global player_img, current_skin

    skins = SKINS.get(player_class, {})
    if not skins:
        add_floating_message("Aucun skin pour cette classe", RED)
        return

    running = True
    slot_w, slot_h = 260, 70
    x, y = WIDTH // 2 - slot_w // 2, 180
    gap = 18
    scroll_y = 0

    while running:
        win.fill(SKIN_BG)

        # Titre
        title = BIGFONT.render("Choix du Skin", True, SKIN_TEXT)
        win.blit(title, (WIDTH // 2 - title.get_width() // 2, 110))

        buttons = {}
        mx, my = pygame.mouse.get_pos()

        for i, (skin_name, data) in enumerate(skins.items()):
            rect = pygame.Rect(x, y + i * (slot_h + gap) + scroll_y, slot_w, slot_h)

            # ----- COULEUR DU SLOT ----- #
            color = SKIN_SLOT
            if not data.get("unlocked", False):
                color = SKIN_SLOT_LOCKED
            elif skin_name == current_skin:
                color = SKIN_SLOT_ACTIVE
            elif rect.collidepoint(mx, my):
                color = SKIN_SLOT_HOVER

            pygame.draw.rect(win, color, rect)          # rectangle plein
            pygame.draw.rect(win, BLACK, rect, 2)      # contour noir

            # ----- TEXTE ----- #
            if not data.get("unlocked", False):
                label = f"{skin_name} [lock]"
                text_color = SKIN_TEXT_LOCKED
            elif skin_name == current_skin:
                label = f"{skin_name} ✓ ACTIF"
                text_color = SKIN_TEXT_ACTIVE
            else:
                label = skin_name
                text_color = SKIN_TEXT

            win.blit(FONT.render(label, True, text_color), (rect.x + 20, rect.y + 24))

            # Mini aperçu du skin
            if data.get("img"):
                win.blit(data["img"], (rect.right - TILE - 15, rect.y + (slot_h - TILE) // 2))

            buttons[skin_name] = rect

        # Footer
        win.blit(FONT.render("Clique pour sélectionner • ESC pour fermer", True, SKIN_TEXT),
                 (WIDTH // 2 - 190, 540))

        pygame.display.update()

        # ----- EVENTS ----- #
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for skin_name, rect in buttons.items():
                    if rect.collidepoint(mx, my):
                        if skins[skin_name].get("unlocked", False):
                            current_skin = skin_name
                            player_img = skins[skin_name]["img"]
                            add_floating_message(f"Skin {skin_name} activé", CYAN)
                        else:
                            add_floating_message("Skin verrouillé", RED)



LEVEL_REWARDS = {
    1: ("Potion", 1),
    2: ("Potion ++", 1),
    3: ("Épée en fer", 1),
    4: ("Potion", 2),
    5: ("Potion ++", 1),
    6: ("Armure légère", 1)
}



# ---------- PASS DE PROGRESSION ----------
PASS_MAX_LEVEL = 10
pass_level = 1
pass_exp = 0
pass_exp_to_next = 15  # EXP nécessaire par palier (modifiable)
# ---------- UTILISATION / EQUIPEMENT ----------
def use_item(item):
    global player_hp, player_atk, player_max_hp
    if item not in inventory:
        return
    if equipped["arme"] == item:
        equipped["arme"] = None
        player_atk = player_base_atk
    elif equipped["armure"] == item:
        equipped["armure"] = None
        player_max_hp -= 10
        if player_hp > player_max_hp:
            player_hp = player_max_hp

    if item == "Potion":
        player_hp = min(player_max_hp, player_hp + 15)
    elif item == "Potion ++":
        player_hp = min(player_max_hp, player_hp + 30)
    elif item == "Épée en fer":
        equipped["arme"] = item
        player_atk = player_base_atk + 5
    elif item == "Armure légère":
        equipped["armure"] = item
        player_max_hp += 10
        player_hp += 10

    inventory[item] -= 1
    if inventory[item] <= 0:
        del inventory[item]


game_state = "world"

# ---------- DESSINS UI / PLAYER ----------
def draw_player():
    if player_img:
        win.blit(
            player_img,
            (player_x * TILE - camera_x, player_y * TILE - camera_y)
        )
    else:
        pygame.draw.rect(
            win,
            BLUE,
            (player_x * TILE - camera_x, player_y * TILE - camera_y, TILE, TILE)
        )

def draw_hp_bar():
    BAR_W, BAR_H = 200, 20
    x, y = 10, 20  # au lieu de 10, descend de 5 px
    pygame.draw.rect(win, BLACK, (x, y, BAR_W, BAR_H))

    fill = int((player_hp / player_max_hp) * BAR_W)
    fill = max(fill, 0)
    pygame.draw.rect(win, RED, (x, y, fill, BAR_H))

    txt = FONT.render(f"PV : {player_hp}/{player_max_hp}", True, WHITE)
    win.blit(txt, (x, y - 25))

def draw_exp_bar():
    BAR_W, BAR_H = 300, 25
    x, y = 480, 550
    pygame.draw.rect(win, BLACK, (x, y, BAR_W, BAR_H))
    fill = 0
    if exp_to_next > 0:
        fill = int((player_exp / exp_to_next) * BAR_W)
    pygame.draw.rect(win, YELLOW, (x, y, fill, BAR_H))
    txt = FONT.render(f"LV {player_level}  EXP {player_exp}/{exp_to_next}", True, WHITE)
    win.blit(txt, (x, y - 28))

def draw_inventory_bar():
    slot_w, slot_h = 50, 50
    x_start, y_start = 10, 500
    gap = 10
    win.blit(FONT.render("Inventaire :", True, WHITE), (10, 460))
    i = 0
    for item, qty in inventory.items():
        if i >= 8:
            break
        x = x_start + i * (slot_w + gap)
        slot_rect = pygame.Rect(x, y_start, slot_w, slot_h)
        pygame.draw.rect(win, BLACK, slot_rect, 2)
        icon = item_icons.get(item)
        if icon:
            win.blit(icon, (x + 9, y_start + 9))
        if qty > 1:
            win.blit(FONT.render(str(qty), True, WHITE), (x + slot_w - 18, y_start + slot_h - 20))
        i += 1
#pass
def draw_pass_bar():
    BAR_W, BAR_H = 200, 16
    x, y = 10, 80

    pygame.draw.rect(win, BLACK, (x, y, BAR_W, BAR_H))
    fill = int((pass_exp / pass_exp_to_next) * BAR_W)
    pygame.draw.rect(win, CYAN, (x, y, fill, BAR_H))

    txt = FONT.render(
        f"PASS {pass_level}/{PASS_MAX_LEVEL}",
        True,
        WHITE
    )
    win.blit(txt, (x, y - 18))

def draw_house():   # 👈 ICI (partie 2)
    win.fill((60, 50, 40))

    for y in range(HOUSE_H):
        for x in range(HOUSE_W):
            tile = house_map[y][x]
            px = x * TILE
            py = y * TILE

            if tile == 1:
                pygame.draw.rect(win, DARK_BROWN, (px, py, TILE, TILE))
            else:
                pygame.draw.rect(win, BROWN, (px, py, TILE, TILE))

    win.blit(FONT.render("ESC pour sortir", True, WHITE), (10, HEIGHT - 30))

# ---------- ENTRY NAME SCREEN ----------
def ask_player_name():
    global player_name
    name = ""
    running = True
    while running:
        win.fill(BLACK)
        if name_background:
            win.blit(name_background, (0, 0))
        txt = BIGFONT.render("Entrez votre nom :", True, WHITE)
        win.blit(txt, (250, 200))
        name_txt = BIGFONT.render(name + "|", True, WHITE)
        win.blit(name_txt, (250, 250))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip() != "":
                    player_name = name.strip()
                    return
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    # limit name length so it doesn't overflow UI
                    if len(name) < 20:
                        name += event.unicode

CLASSES = {
    "Assassin": {
        "hp": 28,
        "atk": 20,
        "img": assassin_img
    },
    "Mage": {
        "hp": 20,
        "atk": 25,
        "img": mage_img
    },
    "Tank": {
        "hp": 55,
        "atk": 10,
        "img": tank_img
    },
    "Soutien": {
        "hp": 18,
        "atk": 15,
        "img": soutien_img
    },
    "Bouclier": {
        "hp": 45,
        "atk": 8,
        "img": bouclier_img
    }
}
# ---------- CHOIX DE CLASSE ----------

def choose_player_class():
    global player_class, player_hp, player_max_hp, player_base_atk, player_atk, player_img

    buttons = {}
    x_start = 100
    y = 350
    gap = 130

    for i, class_name in enumerate(CLASSES.keys()):
        buttons[class_name] = pygame.Rect(x_start + i * gap, y, 120, 60)

    running = True
    while running:
        win.fill(BLACK)

        win.blit(BIGFONT.render("Choisis ta classe", True, WHITE), (260, 150))

        for class_name, rect in buttons.items():
            pygame.draw.rect(win, CYAN, rect)
            win.blit(
                FONT.render(class_name, True, BLACK),
                (rect.x + 10, rect.y + 18)
            )

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for class_name, rect in buttons.items():
                    if rect.collidepoint((mx, my)):
                        data = CLASSES[class_name]
                        player_class = class_name
                        player_max_hp = data["hp"]
                        player_hp = data["hp"]
                        player_base_atk = data["atk"]
                        player_atk = data["atk"]

                        player_img = SKINS[player_class]["Base"]["img"]

                        if class_name == "Soutien":
                            global last_soutien_potion_time
                            last_soutien_potion_time = pygame.time.get_ticks()

                        return

current_skin = "Base"  # reset skin pour nouvelle classe
# ---------- ECRAN DE CHARGEMENT ANIME ----------
def loading_screen():
    duration = 2000  # 2 secondes
    start_time = pygame.time.get_ticks()
    dot_count = 0

    # Texte plus gros et gras
    big_font = pygame.font.SysFont("arial", 48, bold=True)

    while True:
        now = pygame.time.get_ticks()
        elapsed = now - start_time

        win.fill(BLACK)

        # Animation des points
        dot_count = (elapsed // 500) % 4  # change tous les 0,5s
        dots = "." * dot_count
        txt = big_font.render(f"Chargement{dots}", True, WHITE)
        rect = txt.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        win.blit(txt, rect)

        # Barre de progression
        bar_w, bar_h = 400, 30
        bar_x = WIDTH//2 - bar_w//2
        bar_y = HEIGHT//2 + 30
        pygame.draw.rect(win, WHITE, (bar_x, bar_y, bar_w, bar_h), 3)  # contour
        fill = min(int((elapsed / duration) * bar_w), bar_w)
        pygame.draw.rect(win, (0, 200, 0), (bar_x + 3, bar_y + 3, fill - 6, bar_h - 6))  # remplissage vert

        pygame.display.update()

        # Quitter après 2,5 sec
        if elapsed >= duration:
            break

        # Quitter proprement
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

# call it at start
loading_screen()  #  écran de chargement
ask_player_name()  # ensuite le joueur entre son nom
choose_player_class()  #  ROOM choix de la classe


# ---------- COMBAT ----------
def combat(enemy=None):
    global player_hp
    if enemy is None:
        enemy = Enemy()
    message = f"Un {enemy.name} attaque !"
    while True:
        win.fill(WHITE)
        win.blit(BIGFONT.render(message, True, BLACK), (50, 30))
        win.blit(FONT.render(f"PV joueur : {player_hp}", True, BLACK), (50, 120))
        win.blit(FONT.render(f"PV ennemi : {enemy.hp}", True, BLACK), (50, 160))

        atk_btn = pygame.Rect(50, 260, 200, 50)
        flee_btn = pygame.Rect(50, 330, 200, 50)
        pygame.draw.rect(win, GRAY, atk_btn)
        pygame.draw.rect(win, GRAY, flee_btn)
        win.blit(FONT.render("Attaquer", True, BLACK), (80, 275))
        win.blit(FONT.render("Fuir", True, BLACK), (80, 345))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if atk_btn.collidepoint(pos):
                    dmg = random.randint(player_atk - 2, player_atk + 2)
                    enemy.hp -= dmg
                    message = f"Tu frappes (-{dmg}) !"
                    if enemy.hp <= 0:
                        add_exp(enemy.exp_reward)
                        pygame.time.wait(500)
                        return True
                    edmg = random.randint(enemy.atk - 1, enemy.atk + 1)
                    player_hp -= edmg
                    message += f" Il riposte (-{edmg})"
                    if player_hp <= 0:
                        # game over simple
                        win.fill(BLACK)
                        txt = BIGFONT.render("TU ES MORT !", True, RED)
                        rect = txt.get_rect(center=(WIDTH//2, HEIGHT//2))
                        win.blit(txt, rect)
                        pygame.display.update()
                        pygame.time.wait(2000)
                        pygame.quit()
                        sys.exit()
                if flee_btn.collidepoint(pos):
                    return False

# ---------- DONJON (entrée) ----------
def enter_dungeon(name):
    # Charger les frames de chaque salle
    dungeon_frames = {1: load_dungeon_frames(1),
                      2: load_dungeon_frames(2),
                      3: load_dungeon_frames(3)}

    current_room = 1
    frame_index = 0
    frame_delay = 100  # ms entre chaque frame
    last_frame_time = pygame.time.get_ticks()
    frame_cycles = 0  # Compte le nombre de fois que l'animation a tourné

    chest_found = False  # Pour l'objet de la dernière salle

    # Boucle donjon
    while current_room <= 3:
        now = pygame.time.get_ticks()
        # Avancer l'animation
        if now - last_frame_time >= frame_delay:
            frame_index += 1
            last_frame_time = now
            if frame_index >= len(dungeon_frames[current_room]):
                frame_index = 0
                frame_cycles += 1  # une boucle complète de l'animation

        # Afficher frame actuelle
        if dungeon_frames[current_room]:
            win.blit(dungeon_frames[current_room][frame_index], (0, 0))

        # Affichage texte
        win.blit(BIGFONT.render(f"{name}", True, WHITE), (40, 30))
        win.blit(FONT.render(f"Salle {current_room}/3", True, WHITE), (40, 80))
        win.blit(FONT.render("ESC pour sortir", True, WHITE), (40, 120))

        pygame.display.update()

        # Événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        # Quand l'animation a tourné 2 fois, on passe à la salle suivante
        if frame_cycles >= 2:
            # Vérifier objet dans la salle (ici on met salle 3 comme coffre)
            if current_room == 3 and not chest_found:
                loot = random.choice(ITEMS)
                add_to_inventory(loot)
                add_floating_message(f"Trouvé : {loot}", CYAN)
                chest_found = True

            # Ici tu peux ajouter monstres si nécessaire
            # ex: if current_room == 2: combat(Enemy(...))

            current_room += 1
            frame_cycles = 0
            frame_index = 0

# ---------- BOUTIQUE ----------
shop_location = (10, 5)  # position sur la map
shop_items = {
    "Potion": 5,       # item: prix en pièces
    "Potion ++": 12,
    "Épée en fer": 20,
    "Armure légère": 15,
    "Bois": 2,
}
SKIN_SHOP_ITEMS = {
    "Skin Roi Mage": {
        "price": 50,
        "class": "Soutien",
        "skin": "Roi Mage"
    },

    # -------- SKINS BUCHERON --------
    "Skin Bucheron Assassin": {
        "price": 30,
        "class": "Assassin",
        "skin": "bucheron"
    },
    "Skin Bucheron Tank": {
        "price": 30,
        "class": "Tank",
        "skin": "bucheron"
    },
    "Skin Bucheron Mage": {
        "price": 30,
        "class": "Mage",
        "skin": "bucheron"
    },
    "Skin Bucheron Bouclier": {
        "price": 30,
        "class": "Bouclier",
        "skin": "bucheron"
    }
}


def open_shop():
    slot_w, slot_h = 180, 50
    x_start, y_start = 200, 200
    gap = 10
    button_spacing = 25
    scroll_y = 0
    scroll_speed = 30

    running = True
    while running:
        win.fill(GRAY)

        # ---------- TITRE + PIECES ----------
        win.blit(BIGFONT.render("Boutique", True, BLACK), (300, 20))
        win.blit(FONT.render(f"Pièces : {inventory.get('Pièce', 0)}", True, BLACK), (600, 20))

        buttons_buy = {}
        buttons_sell = {}
        skin_buttons = {}

        # ---------- ITEMS ----------
        for i, (item, price) in enumerate(shop_items.items()):
            x = x_start
            y = y_start + i * (slot_h + gap) + scroll_y

            rect_buy = pygame.Rect(x, y, slot_w, slot_h)
            rect_sell = pygame.Rect(x + slot_w + button_spacing, y, slot_w, slot_h)

            pygame.draw.rect(win, CYAN, rect_buy)
            pygame.draw.rect(win, (200, 100, 100), rect_sell)

            buttons_buy[item] = rect_buy
            buttons_sell[item] = rect_sell

            win.blit(FONT.render(f"Acheter {item} - {price} pièces", True, BLACK), (rect_buy.x + 10, rect_buy.y + 15))
            win.blit(FONT.render(f"Vendre {item} - {price} pièces", True, BLACK), (rect_sell.x + 10, rect_sell.y + 15))

        # ---------- SKINS ----------
        y_offset = y_start + len(shop_items) * (slot_h + gap) + 40
        win.blit(BIGFONT.render("Skins", True, BLACK), (x_start, y_offset - 35))

        for i, (skin_name, data) in enumerate(SKIN_SHOP_ITEMS.items()):
            y = y_offset + i * (slot_h + gap) + scroll_y
            rect = pygame.Rect(x_start, y, slot_w * 2 + button_spacing, slot_h)

            skin_data = SKINS[data["class"]][data["skin"]]
            unlocked = skin_data["unlocked"]

            color = DARK_GRAY if unlocked else ORANGE
            pygame.draw.rect(win, color, rect)
            pygame.draw.rect(win, BLACK, rect, 2)

            label = f"{skin_name} - {data['price']} pièces"
            if unlocked:
                label += " (Acheté)"

            win.blit(FONT.render(label, True, BLACK), (rect.x + 10, rect.y + 15))
            skin_buttons[skin_name] = rect

        pygame.display.update()

        # ---------- EVENTS ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                # Scroll avec molette
                if event.button == 4:  # molette vers le haut
                    scroll_y += scroll_speed
                elif event.button == 5:  # molette vers le bas
                    scroll_y -= scroll_speed

                # Achat item
                for item, rect in buttons_buy.items():
                    if rect.collidepoint(mx, my):
                        price = shop_items[item]
                        if inventory.get("Pièce", 0) >= price:
                            inventory["Pièce"] -= price
                            add_to_inventory(item)
                            add_floating_message(f"Acheté : {item}", CYAN)
                        else:
                            add_floating_message("Pas assez de pièces", RED)

                # Vente item
                for item, rect in buttons_sell.items():
                    if rect.collidepoint(mx, my) and inventory.get(item, 0) > 0:
                        price = shop_items[item]
                        inventory[item] -= 1
                        if inventory[item] <= 0:
                            del inventory[item]
                        add_to_inventory("Pièce", price)
                        add_floating_message(f"Vendu : {item} (+{price} pièces)", CYAN)

                # Achat skin
                for skin_name, rect in skin_buttons.items():
                    if rect.collidepoint(mx, my):
                        data = SKIN_SHOP_ITEMS[skin_name]
                        skin_data = SKINS[data["class"]][data["skin"]]

                        if skin_data["unlocked"]:
                            add_floating_message("Skin déjà débloqué", RED)
                        elif inventory.get("Pièce", 0) >= data["price"]:
                            inventory["Pièce"] -= data["price"]
                            skin_data["unlocked"] = True
                            add_floating_message(f"{skin_name} acheté !", LEVELUP_COLOR)
                        else:
                            add_floating_message("Pas assez de pièces", RED)

        # ---------- LIMIT SCROLL ----------
# Calculer la hauteur totale des items + skins
        content_height = (len(shop_items) + len(SKIN_SHOP_ITEMS)) * (slot_h + gap) + 300 # +50 pour le titre et espace
        scroll_y = min(scroll_y, 0)  # pas au-dessus du contenu
        scroll_y = max(scroll_y, HEIGHT - content_height)  # pas en-dessous du contenu



# ---------- OPEN INVENTAIRE ----------
def open_inventory():
    running = True
    slot_w, slot_h = 60, 60
    x_start, y_start = 100, 100
    gap = 10
    while running:
        win.fill(GRAY)
        win.blit(BIGFONT.render("Inventaire", True, BLACK), (300, 20))

        keys_list = list(inventory.keys())
        for i, item in enumerate(keys_list):
            qty = inventory[item]
            x = x_start + (i % 8) * (slot_w + gap)
            y = y_start + (i // 8) * (slot_h + gap)
            slot_rect = pygame.Rect(x, y, slot_w, slot_h)
            pygame.draw.rect(win, BLACK, slot_rect, 2)
            icon = item_icons.get(item)
            if icon:
                win.blit(icon, (x + 14, y + 14))
            if qty > 1:
                win.blit(FONT.render(str(qty), True, WHITE), (x + slot_w - 18, y + slot_h - 20))
            mx, my = pygame.mouse.get_pos()
            if slot_rect.collidepoint((mx, my)):
                pygame.draw.rect(win, YELLOW, slot_rect, 2)
                status = ""
                if equipped["arme"] == item or equipped["armure"] == item:
                    status = " (Équipé)"
                win.blit(FONT.render(item + status, True, WHITE), (x, y - 20))

        win.blit(FONT.render("Clic gauche pour utiliser/équiper/déséquiper", True, BLACK), (150, 550))
        win.blit(FONT.render("ESC pour fermer", True, BLACK), (300, 580))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                for idx, item in enumerate(list(inventory.keys())):
                    x = x_start + (idx % 8) * (slot_w + gap)
                    y = y_start + (idx // 8) * (slot_h + gap)
                    slot_rect = pygame.Rect(x, y, slot_w, slot_h)
                    if slot_rect.collidepoint((mx, my)):
                        use_item(item)
                        break
camera_x = 0
camera_y = 0

print(type(dungeons), dungeons)

def load_dungeon_frames(room_number):
    frames = []
    folder = os.path.join("assets", "dungeon_frames", f"room{room_number}")
    i = 0
    while True:
        path = os.path.join(folder, f"frame_{i}.png")
        if not os.path.isfile(path):
            break
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (WIDTH, HEIGHT))
        frames.append(img)
        i += 1
    return frames

# ---------- BOUCLE PRINCIPALE ----------

camera_x = 0
camera_y = 0
move_cooldown = False

night_cycle = 100000  # ms
night_start = pygame.time.get_ticks()
is_night = False

running = True
while running:
    win.fill(GREEN)


    # ---------- CAMERA ----------
    camera_x = player_x * TILE - WIDTH // 2 + TILE // 2
    camera_y = player_y * TILE - HEIGHT // 2 + TILE // 2
    camera_x = max(0, min(camera_x, MAP_W * TILE - WIDTH))
    camera_y = max(0, min(camera_y, MAP_H * TILE - HEIGHT))

    # ---------- DONJONS ----------
    for (dx, dy), name in dungeons.items():
        if donjon_icon:
            win.blit(donjon_icon, (dx * TILE - camera_x, dy * TILE - camera_y))
        else:
            pygame.draw.rect(win, DOOR_COLOR, (dx * TILE - camera_x, dy * TILE - camera_y, TILE * 2, TILE * 2))

    # ---------- BOUTIQUE SUR LA MAP ----------
    shop_rect = pygame.Rect(
    shop_location[0]*TILE - camera_x,
    shop_location[1]*TILE - camera_y,
    TILE,  # largeur 1 tile
    TILE   # hauteur 1 tile
    )
    shop_color = ORANGE  # couleur par défaut si icône manquante

    # Affichage de la boutique
    if shop_icon:
        win.blit(shop_icon, (shop_location[0]*TILE - camera_x, shop_location[1]*TILE - camera_y))
    else:
        pygame.draw.rect(win, shop_color, shop_rect)
        pygame.draw.rect(win, BLACK, shop_rect, 3)

# Définir les tiles occupées par la boutique (ici 1x1)
    shop_tiles = {(shop_location[0], shop_location[1])}

# Message interaction boutique
    if (player_x, player_y) in shop_tiles:
        win.blit(
            FONT.render("Appuie sur E pour ouvrir la boutique", True, WHITE),
            (WIDTH//2 - 150, HEIGHT - 40)
        )


    # ---------- ARBRES ----------
    for (tx, ty) in trees:
        if tree_icon:
            win.blit(tree_icon, (tx * TILE - camera_x, ty * TILE - camera_y))
        else:
            pygame.draw.rect(win, DARK_BROWN, (tx * TILE - camera_x, ty * TILE - camera_y, TILE, TILE))

    # ---------- MONSTRES LA NUIT ----------
    if is_night:
        for m in map_enemies:
            pygame.draw.rect(win, RED, (m.x * TILE - camera_x, m.y * TILE - camera_y, TILE, TILE))

    # ---------- JOUEUR ----------
    draw_player()

    # ---------- UI ----------
    draw_hp_bar()
    draw_inventory_bar()
    draw_exp_bar()

    # Bouton Pass
    pass_button_rect = pygame.Rect(220, 20, 80, 16)  # aligné avec la barre
    pygame.draw.rect(win, CYAN, pass_button_rect)      # remplissage bleu
    pygame.draw.rect(win, WHITE, pass_button_rect, 1)  # contour blanc
    win.blit(FONT.render("Pass", True, WHITE), (pass_button_rect.x + 5, pass_button_rect.y - 18))

    # Bouton Changer de classe
    class_button_rect = pygame.Rect(310, 20, 120, 16)  # à droite du bouton Pass
    pygame.draw.rect(win, ORANGE, class_button_rect)    # couleur orange
    pygame.draw.rect(win, WHITE, class_button_rect, 1)
    win.blit(FONT.render("Changer Classe", True, WHITE), (class_button_rect.x + 5, class_button_rect.y - 18))

    win.blit(
        FONT.render(f"[I] Inventaire  |  {player_name} ({player_class})", True, WHITE),
        (10, 560)
    )

    # ---------- MESSAGES FLOTTANTS ----------
    current_time = pygame.time.get_ticks()
    for msg in floating_messages[:]:
        elapsed = current_time - msg["start_time"]
        if elapsed > 2000:
            floating_messages.remove(msg)
        else:
            y_offset = int((elapsed / 2000) * 30)
            alpha = 255 - int((elapsed / 2000) * 255)
            surf = FONT.render(msg["text"], True, msg.get("color", WHITE))
            tmp = surf.copy()
            tmp.set_alpha(alpha)
            win.blit(tmp, (WIDTH // 2 - surf.get_width() // 2, HEIGHT - 50 - y_offset))

    # ---------- GESTION NUIT/JOUR ----------
    now = pygame.time.get_ticks()
    if now - night_start >= night_cycle:
        is_night = not is_night
        night_start = now
        if is_night:
            spawn_night_enemies()
            if night_music:
                try: pygame.mixer.music.play(-1)
                except: pass
        else:
            map_enemies = []
            try: pygame.mixer.music.stop()
            except: pass

    # ---------- LUMIERE LA NUIT ----------
    if is_night:
    # Overlay semi-transparent pour assombrir l'écran
        night_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        night_overlay.fill((0, 0, 0, 180))  # alpha 180 pour obscurcir

    # Lumière autour du joueur (halo radial)
        light_radius = 120
        light = pygame.Surface((light_radius*2, light_radius*2), pygame.SRCALPHA)

    # Remplir le halo avec un dégradé alpha pour faire un cercle "doux"
        for r in range(light_radius, 0, -1):
            alpha = int(255 * (r / light_radius))  # plus on est proche du centre, plus transparent
            pygame.draw.circle(light, (0, 0, 0, alpha), (light_radius, light_radius), r)

    # Appliquer le halo sur l'overlay
        night_overlay.blit(
            light,
            (player_x * TILE - light_radius + TILE // 2, player_y * TILE - light_radius + TILE // 2),
            special_flags=pygame.BLEND_RGBA_SUB
        )

    # Afficher l'overlay sur la fenêtre
        win.blit(night_overlay, (0, 0))


    # ---------- COUPER ARBRE ----------
    if (player_x, player_y) in trees:
        if cutting_tree != (player_x, player_y):
            cutting_tree = (player_x, player_y)
            cut_start_time = pygame.time.get_ticks()

    # Temps de base
        effective_cut_duration = CUT_DURATION

    # BONUS BUCHERON
        if current_skin.lower() == "bucheron":
            effective_cut_duration = CUT_DURATION // 2

    # ⏱️ elapsed TOUJOURS calculé
        elapsed = pygame.time.get_ticks() - cut_start_time

        bar_x = player_x * TILE - camera_x
        bar_y = player_y * TILE - camera_y - 12

        pygame.draw.rect(win, BLACK, (bar_x, bar_y, TILE, 8))
        progress = min(int((elapsed / effective_cut_duration) * TILE), TILE)
        pygame.draw.rect(win, YELLOW, (bar_x, bar_y, progress, 8))

        if elapsed >= effective_cut_duration:
            try:
                trees.remove(cutting_tree)
            except ValueError:
                pass

            add_to_inventory("Bois", 1)
            add_pass_exp(2)

            if random.random() < 0.3:
                add_to_inventory("Pièce", 1)

            add_exp(random.randint(4, 8))

            if cut_sound:
                try:
                    cut_sound.play()
        # Définir un timer pour arrêter le son après 2000 ms (2 secondes)
                    pygame.time.set_timer(pygame.USEREVENT + 1, 2000)
                except:
                    pass

            cutting_tree = None
    else:
        cutting_tree = None


    pygame.display.update()

    # ---------- EVENEMENTS ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # ----- TOUCHES -----
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:  # Inventaire
                open_inventory()
            elif event.key == pygame.K_e and (player_x, player_y) in shop_tiles:  # Boutique
                open_shop()
            elif event.key == pygame.K_k:  # Skin menu
                if player_class in SKINS:
                    open_skin_menu()
                else:
                    add_floating_message("Aucun skin pour cette classe", RED)
            elif event.key == pygame.K_ESCAPE:
                pass  # Placeholder si besoin

        if event.type == pygame.KEYUP:  # Reset cooldown déplacement
            move_cooldown = False

    # ----- SOURIS -----
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()  # Récupérer position souris au moment du clic

        # Bouton Pass
            if pass_button_rect.collidepoint(mx, my):
                open_pass_menu()

            # Bouton Changer Classe
            if class_button_rect.collidepoint(mx, my):
                open_class_menu()





    # ---------- MOVEMENT ----------
    keys = pygame.key.get_pressed()
    if not move_cooldown:
        if keys[pygame.K_UP] and player_y > 0:
            player_y -= 1
            move_cooldown = True
        if keys[pygame.K_DOWN] and player_y < MAP_H - 1:
            player_y += 1
            move_cooldown = True
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= 1
            move_cooldown = True
        if keys[pygame.K_RIGHT] and player_x < MAP_W - 1:
            player_x += 1
            move_cooldown = True

    # ---------- ENTREE DONJON ----------
    for (dx, dy), name in dungeons.items():
        if (player_x, player_y) in {(dx, dy), (dx + 1, dy), (dx, dy + 1), (dx + 1, dy + 1)}:
            enter_dungeon(name)
            player_x, player_y = 2, 2
            break

    # ---------- COMBAT AVEC MONSTRES ----------
    if is_night:
        for m in map_enemies:
            if (player_x, player_y) == (m.x, m.y):
                combat(Enemy("Monstre de la nuit", m.hp, m.atk, 10))
                map_enemies.remove(m)
                break

    # ---------- PASSIF CLASSE BOUCLIER ----------
    if player_class == "Bouclier":
        hp_ratio = player_hp / player_max_hp
        base_atk = player_base_atk
    # Si l'épée est équipée, ajouter bonus
        if equipped["arme"] == "Épée en fer":
            base_atk += 5

        if hp_ratio <= 0.5 and not bouclier_rage_active:
            bouclier_rage_active = True
            player_atk = base_atk * 2
            add_floating_message("RAGE DU BOUCLIER !", RED)
        elif hp_ratio > 0.5 and bouclier_rage_active:
            bouclier_rage_active = False
            player_atk = base_atk
            add_floating_message("Rage dissipée", CYAN)