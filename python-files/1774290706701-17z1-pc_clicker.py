Python 3.14.3 (tags/v3.14.3:323c59a, Feb  3 2026, 16:04:56) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
import pygame
import pygame_menu
import json
import os

pygame.init()
pygame.display.set_caption("PC Clicker")
screen = pygame.display.set_mode((480, 600))
clock = pygame.time.Clock()

# Загрузить звук
sound_click = pygame.mixer.Sound('click.wav')
sound_rebirth = pygame.mixer.Sound('rebirth.wav')

# Глобальные переменные игры
progress_file = "save.json"
DEFAULTS = {
    "clicks": 0,
    "per_click": 1,
    "pc_level": 1,
    "rebirths": 0,
    "bonus": 1
}
game = dict(DEFAULTS)

def save_progress():
    with open(progress_file, "w") as f:
        json.dump(game, f)

def load_progress():
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            game.update(json.load(f))

# Клик по ПК
def click_pc():
    sound_click.play()
    game['clicks'] += game['per_click'] * game['bonus']

# Магазин: апгрейды
def buy_new_pc():
    price = game["pc_level"] * 10
    if game['clicks'] >= price:
        game['clicks'] -= price
        game['pc_level'] += 1
        game['per_click'] += 1

# Перерождение
def rebirth():
    need_clicks = 500 * (game['rebirths'] + 1)
    if game['clicks'] >= need_clicks:
        sound_rebirth.play()
        game['clicks'] = 0
        game['pc_level'] = 1
        game['per_click'] = 1
        game['rebirths'] += 1
        game['bonus'] += 0.5

def main_game():
    running = True
    font = pygame.font.SysFont("Arial", 32)
    tab = "Кликер"

    # Меню оформление
    def set_tab_clicker(): nonlocal tab; tab = "Кликер"
    def set_tab_shop(): nonlocal tab; tab = "Магазин"
    def set_tab_rebirth(): nonlocal tab; tab = "Перерождение"

    # Прорисовка интерфейса, вкладки
    while running:
        screen.fill((235, 239, 241))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if tab == "Кликер" and 90 < x < 390 and 130 < y < 430:
                    click_pc()
                elif tab == "Магазин" and 100 < x < 380 and 300 < y < 360:
                    buy_new_pc()
                elif tab == "Перерождение" and 100 < x < 380 and 300 < y < 360:
                    rebirth()

        # Верхние вкладки
        pygame.draw.rect(screen, (180, 200, 200), (20, 20, 120, 50), 0 if tab == "Кликер" else 1)
        pygame.draw.rect(screen, (180, 200, 200), (170, 20, 120, 50), 0 if tab == "Магазин" else 1)
        pygame.draw.rect(screen, (180, 200, 200), (320, 20, 120, 50), 0 if tab == "Перерождение" else 1)
        screen.blit(font.render("Кликер", 1, (30,30,30)), (30, 30))
        screen.blit(font.render("Магазин", 1, (30,30,30)), (180, 30))
        screen.blit(font.render("Перерождение", 1, (30,30,30)), (330, 30))

        # Обработка перехода по вкладкам
        if pygame.mouse.get_pressed()[0]:
            x, y = pygame.mouse.get_pos()
            if 20 < x < 140 and 20 < y < 70: set_tab_clicker()
            if 170 < x < 290 and 20 < y < 70: set_tab_shop()
            if 320 < x < 440 and 20 < y < 70: set_tab_rebirth()

        # Содержимое вкладок
        if tab == "Кликер":
            pygame.draw.rect(screen, (180, 180, 220), (90, 130, 300, 300))
            screen.blit(font.render("ПК", 1, (70, 70, 70)), (215, 270))
            screen.blit(fon
                        
SyntaxError: multiple statements found while compiling a single statement
import pygame
import pygame_menu
import json
import os

pygame.init()
pygame.display.set_caption("PC Clicker")
screen = pygame.display.set_mode((480, 600))
clock = pygame.time.Clock()

# Загрузить звук
sound_click = pygame.mixer.Sound('click.wav')
sound_rebirth = pygame.mixer.Sound('rebirth.wav')

# Глобальные переменные игры
progress_file = "save.json"
DEFAULTS = {
    "clicks": 0,
    "per_click": 1,
    "pc_level": 1,
    "rebirths": 0,
    "bonus": 1
}
game = dict(DEFAULTS)

def save_progress():
    with open(progress_file, "w") as f:
        json.dump(game, f)

def load_progress():
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            game.update(json.load(f))

# Клик по ПК
def click_pc():
    sound_click.play()
    game['clicks'] += game['per_click'] * game['bonus']

# Магазин: апгрейды
def buy_new_pc():
    price = game["pc_level"] * 10
    if game['clicks'] >= price:
        game['clicks'] -= price
        game['pc_level'] += 1
        game['per_click'] += 1

# Перерождение
def rebirth():
    need_clicks = 500 * (game['rebirths'] + 1)
    if game['clicks'] >= need_clicks:
        sound_rebirth.play()
        game['clicks'] = 0
        game['pc_level'] = 1
        game['per_click'] = 1
        game['rebirths'] += 1
        game['bonus'] += 0.5

def main_game():
    running = True
    font = pygame.font.SysFont("Arial", 32)
    tab = "Кликер"

    # Меню оформление
    def set_tab_clicker(): nonlocal tab; tab = "Кликер"
    def set_tab_shop(): nonlocal tab; tab = "Магазин"
    def set_tab_rebirth(): nonlocal tab; tab = "Перерождение"

    # Прорисовка интерфейса, вкладки
    while running:
        screen.fill((235, 239, 241))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if tab == "Кликер" and 90 < x < 390 and 130 < y < 430:
                    click_pc()
                elif tab == "Магазин" and 100 < x < 380 and 300 < y < 360:
                    buy_new_pc()
                elif tab == "Перерождение" and 100 < x < 380 and 300 < y < 360:
                    rebirth()

        # Верхние вкладки
        pygame.draw.rect(screen, (180, 200, 200), (20, 20, 120, 50), 0 if tab == "Кликер" else 1)
        pygame.draw.rect(screen, (180, 200, 200), (170, 20, 120, 50), 0 if tab == "Магазин" else 1)
        pygame.draw.rect(screen, (180, 200, 200), (320, 20, 120, 50), 0 if tab == "Перерождение" else 1)
        screen.blit(font.render("Кликер", 1, (30,30,30)), (30, 30))
        screen.blit(font.render("Магазин", 1, (30,30,30)), (180, 30))
        screen.blit(font.render("Перерождение", 1, (30,30,30)), (330, 30))

        # Обработка перехода по вкладкам
        if pygame.mouse.get_pressed()[0]:
            x, y = pygame.mouse.get_pos()
            if 20 < x < 140 and 20 < y < 70: set_tab_clicker()
            if 170 < x < 290 and 20 < y < 70: set_tab_shop()
            if 320 < x < 440 and 20 < y < 70: set_tab_rebirth()

        # Содержимое вкладок
        if tab == "Кликер":
            pygame.draw.rect(screen, (180, 180, 220), (90, 130, 300, 300))
            screen.blit(font.render("ПК", 1, (70, 70, 70)), (215, 270))
            screen.blit(fon
                        
SyntaxError: multiple statements found while compiling a single statement
import pygame
import pygame_menu
import json
import os

pygame.init()
pygame.display.set_caption("PC Clicker")
screen = pygame.display.set_mode((480, 600))
clock = pygame.time.Clock()

# Загрузить звук
sound_click = pygame.mixer.Sound('click.wav')
sound_rebirth = pygame.mixer.Sound('rebirth.wav')

# Глобальные переменные игры
progress_file = "save.json"
DEFAULTS = {
    "clicks": 0,
    "per_click": 1,
    "pc_level": 1,
    "rebirths": 0,
    "bonus": 1
}
game = dict(DEFAULTS)

def save_progress():
    with open(progress_file, "w") as f:
        json.dump(game, f)

def load_progress():
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            game.update(json.load(f))

# Клик по ПК
def click_pc():
    sound_click.play()
    game['clicks'] += game['per_click'] * game['bonus']

# Магазин: апгрейды
def buy_new_pc():
    price = game["pc_level"] * 10
    if game['clicks'] >= price:
        game['clicks'] -= price
        game['pc_level'] += 1
        game['per_click'] += 1

# Перерождение
def rebirth():
    need_clicks = 500 * (game['rebirths'] + 1)
    if game['clicks'] >= need_clicks:
        sound_rebirth.play()
        game['clicks'] = 0
        game['pc_level'] = 1
        game['per_click'] = 1
        game['rebirths'] += 1
        game['bonus'] += 0.5

def main_game():
    running = True
    font = pygame.font.SysFont("Arial", 32)
    tab = "Кликер"

    # Меню оформление
    def set_tab_clicker(): nonlocal tab; tab = "Кликер"
    def set_tab_shop(): nonlocal tab; tab = "Магазин"
    def set_tab_rebirth(): nonlocal tab; tab = "Перерождение"

    # Прорисовка интерфейса, вкладки
    while running:
        screen.fill((235, 239, 241))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if tab == "Кликер" and 90 < x < 390 and 130 < y < 430:
                    click_pc()
                elif tab == "Магазин" and 100 < x < 380 and 300 < y < 360:
                    buy_new_pc()
                elif tab == "Перерождение" and 100 < x < 380 and 300 < y < 360:
                    rebirth()

        # Верхние вкладки
        pygame.draw.rect(screen, (180, 200, 200), (20, 20, 120, 50), 0 if tab == "Кликер" else 1)
        pygame.draw.rect(screen, (180, 200, 200), (170, 20, 120, 50), 0 if tab == "Магазин" else 1)
        pygame.draw.rect(screen, (180, 200, 200), (320, 20, 120, 50), 0 if tab == "Перерождение" else 1)
        screen.blit(font.render("Кликер", 1, (30,30,30)), (30, 30))
        screen.blit(font.render("Магазин", 1, (30,30,30)), (180, 30))
        screen.blit(font.render("Перерождение", 1, (30,30,30)), (330, 30))

        # Обработка перехода по вкладкам
        if pygame.mouse.get_pressed()[0]:
            x, y = pygame.mouse.get_pos()
            if 20 < x < 140 and 20 < y < 70: set_tab_clicker()
...             if 170 < x < 290 and 20 < y < 70: set_tab_shop()
...             if 320 < x < 440 and 20 < y < 70: set_tab_rebirth()
... 
...         # Содержимое вкладок
...         if tab == "Кликер":
...             pygame.draw.rect(screen, (180, 180, 220), (90, 130, 300, 300))
...             screen.blit(font.render("ПК", 1, (70, 70, 70)), (215, 270))
...             screen.blit(font.render("Кликов: %s" % game['clicks'], 1, (10,10,10)), (120, 480))
...             screen.blit(font.render("КПК: %s" % game['per_click'], 1, (10,10,10)), (120, 520))
...             screen.blit(font.render("Бонус: x%.1f" % game['bonus'], 1, (100,10,10)), (120, 560))
... 
...         elif tab == "Магазин":
...             pygame.draw.rect(screen, (200,240,200), (100, 300, 280, 60))
...             price = game['pc_level'] * 10
...             msg = "Купить ПК lvl %d (%d кликов)" % (game["pc_level"]+1, price)
...             screen.blit(font.render(msg, 1, (20, 50, 20)), (110, 320))
...             screen.blit(font.render("Ваш ПК уровень %d" % game['pc_level'], 1, (10,10,10)), (120, 250))
... 
...         elif tab == "Перерождение":
...             pygame.draw.rect(screen, (255,200,120), (100, 300, 280, 60))
...             need_clicks = 500 * (game['rebirths'] + 1)
...             msg = "Перерождение (%d кликов)" % need_clicks
...             screen.blit(font.render(msg, 1, (180,100,10)), (110, 320))
...             screen.blit(font.render("Ваших перерождений: %d" % game['rebirths'], 1, (50,10,10)), (120, 250))
... 
...         pygame.display.flip()
...         clock.tick(30)
...         save_progress()
... 
...     pygame.quit()
... 
... if __name__ == "__main__":
...     load_progress()
...     main_game()
