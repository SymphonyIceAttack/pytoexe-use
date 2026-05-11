
import pygame
import random
import math

pygame.init()

WIDTH = 1280
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jujutsu Kaisen: Curse Battle")
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 28)
small_font = pygame.font.SysFont("arial", 20)

WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)

BLUE = (0,120,255)
PURPLE = (170,0,255)
GREEN = (0,255,0)
YELLOW = (255,255,0)
GRAY = (80,80,80)

class Character:
    def __init__(self, name, color, light_damage, heavy_damage, special_damage, domain_damage):
        self.name = name
        self.color = color
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.speed = 6
        self.size = 40
        self.hp = 500
        self.max_hp = 500
        self.level = 1
        self.exp = 0

        self.light_damage = light_damage

        self.heavy_damage = heavy_damage
        self.special_damage = special_damage
        self.domain_damage = domain_damage

        self.domain_active = False
        self.domain_timer = 0

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

    def move(self, keys):
        if keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_s]:
            self.y += self.speed
        if keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_d]:
            self.x += self.speed


        self.x = max(0, min(WIDTH-self.size, self.x))
        self.y = max(0, min(HEIGHT-self.size, self.y))

class Curse:
    def __init__(self, level):
        self.size = random.randint(30,50)
        self.x = random.randint(0, WIDTH-self.size)
        self.y = random.randint(0, HEIGHT-self.size)
        self.speed = 2 + level * 0.2
        self.hp = 50 + level * 20
        self.damage = 5 + level * 2
        self.color = (120,0,0)

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))

    def move_toward(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx*dx + dy*dy)

        if dist != 0:
            self.x += dx/dist * self.speed
            self.y += dy/dist * self.speed

characters = {
    "Gojo": Character("Gojo", BLUE, 20, 50, 100, 300),
    "Sukuna": Character("Sukuna", RED, 25, 60, 120, 350),
    "Yuta": Character("Yuta", WHITE, 18, 45, 90, 260),
    "Yuji": Character("Yuji", YELLOW, 22, 55, 95, 280),
    "Megumi": Character("Megumi", PURPLE, 16, 50, 110, 250)
}

selected = None

menu = True

while menu:
    screen.fill(BLACK)

    title = font.render("Choose Your Sorcerer", True, WHITE)
    screen.blit(title, (WIDTH//2 - 150, 100))

    y = 220
    for i, name in enumerate(characters):
        text = font.render(f"{i+1}. {name}", True, WHITE)
        screen.blit(text, (WIDTH//2 - 100, y))
        y += 70

    pygame.display.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

            quit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                selected = characters["Gojo"]
                menu = False
            if event.key == pygame.K_2:
                selected = characters["Sukuna"]
                menu = False
            if event.key == pygame.K_3:
                selected = characters["Yuta"]
                menu = False
            if event.key == pygame.K_4:
                selected = characters["Yuji"]
                menu = False
            if event.key == pygame.K_5:
                selected = characters["Megumi"]
                menu = False

player = selected

curses = []

wave = 1
spawn_timer = 0

running = True
while running:
    clock.tick(60)

    screen.fill((20,20,20))

    keys = pygame.key.get_pressed()
    player.move(keys)

    spawn_timer += 1

    if spawn_timer > 60:
        for _ in range(wave):
            curses.append(Curse(player.level))
        spawn_timer = 0

    for curse in curses[:]:
        curse.move_toward(player)
        curse.draw()


        if abs(curse.x - player.x) < 40 and abs(curse.y - player.y) < 40:
            player.hp -= curse.damage * 0.1

        if curse.hp <= 0:
            curses.remove(curse)
            player.exp += 10

    if player.exp >= 100:
        player.level += 1
        player.exp = 0
        wave += 1
        player.hp = player.max_hp

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            # LIGHT ATTACK

            if event.key == pygame.K_j:
                for curse in curses:
                    if abs(curse.x - player.x) < 120 and abs(curse.y - player.y) < 120:
                        curse.hp -= player.light_damage

            # HEAVY TECHNIQUE
            if event.key == pygame.K_k:
                for curse in curses:
                    if abs(curse.x - player.x) < 200 and abs(curse.y - player.y) < 200:
                        curse.hp -= player.heavy_damage

            # SPECIAL MOVE
            if event.key == pygame.K_l:
                for curse in curses:
                    if abs(curse.x - player.x) < 300 and abs(curse.y - player.y) < 300:
                        curse.hp -= player.special_damage


            # DOMAIN EXPANSION
            if event.key == pygame.K_u:
                player.domain_active = True
                player.domain_timer = 300

    if player.domain_active:
        pygame.draw.circle(screen, PURPLE, (player.x, player.y), 250, 5)

        for curse in curses:
            if abs(curse.x - player.x) < 250 and abs(curse.y - player.y) < 250:
                curse.hp -= player.domain_damage * 0.02

        player.domain_timer -= 1

        if player.domain_timer <= 0:
            player.domain_active = False

    player.draw()

    hp_text = small_font.render(f"HP: {int(player.hp)}", True, WHITE)
    lvl_text = small_font.render(f"Level: {player.level}", True, WHITE)
    wave_text = small_font.render(f"Wave: {wave}", True, WHITE)
    char_text = small_font.render(f"Character: {player.name}", True, WHITE)

    screen.blit(hp_text, (20,20))
    screen.blit(lvl_text, (20,50))
    screen.blit(wave_text, (20,80))
    screen.blit(char_text, (20,110))

    controls = [
        "WASD = Move",
        "J = Light Attack",
        "K = Cursed Technique",
        "L = Special Move",
        "U = Domain Expansion"
    ]


    y = 20
    for c in controls:
        text = small_font.render(c, True, WHITE)
        screen.blit(text, (1000,y))
        y += 30

    if player.hp <= 0:
        game_over = font.render("GAME OVER", True, RED)
        screen.blit(game_over, (WIDTH//2 - 100, HEIGHT//2))
        pygame.display.update()
        pygame.time.wait(3000)
        running = False

    pygame.display.update()

pygame.quit()
