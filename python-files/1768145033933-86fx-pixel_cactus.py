import pygame, random, sys
pygame.init()

# --- ПАРАМЕТРЫ ЭКРАНА ---
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pixel Cactus Night")
clock = pygame.time.Clock()

# --- ЦВЕТА ---
NIGHT_TOP = (10, 10, 30)
NIGHT_BOTTOM = (30, 30, 60)
WHITE = (220, 220, 255)
GREEN = (40, 180, 90)
DARK_GREEN = (20, 120, 60)
SKIN = (255, 220, 180)
BLACK = (0, 0, 0)
RED = (200, 40, 40)

# --- ЗВЁЗДЫ ---
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT//2)) for _ in range(40)]
def draw_night_background():
    for y in range(HEIGHT):
        color = (
            NIGHT_TOP[0] + (NIGHT_BOTTOM[0]-NIGHT_TOP[0])*y//HEIGHT,
            NIGHT_TOP[1] + (NIGHT_BOTTOM[1]-NIGHT_TOP[1])*y//HEIGHT,
            NIGHT_TOP[2] + (NIGHT_BOTTOM[2]-NIGHT_TOP[2])*y//HEIGHT,
        )
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))
    for star in stars:
        pygame.draw.rect(screen, WHITE, (*star, 2, 2))

# --- ИГРОК ---
def draw_player(x, y):
    pygame.draw.rect(screen, (80, 120, 255), (x+4, y+12, 8, 14))
    pygame.draw.rect(screen, SKIN, (x+4, y, 8, 8))
    pygame.draw.rect(screen, BLACK, (x+4, y+26, 4, 6))
    pygame.draw.rect(screen, BLACK, (x+8, y+26, 4, 6))

# --- КАКТУС ---
def draw_cactus(x, y):
    pygame.draw.rect(screen, GREEN, (x+6, y, 8, 26))
    pygame.draw.rect(screen, DARK_GREEN, (x+2, y+10, 6, 6))
    pygame.draw.rect(screen, DARK_GREEN, (x+12, y+10, 6, 6))

# --- ЧАСТИЦЫ СМЕРТИ ---
particles = []
def spawn_particles(x, y):
    for _ in range(25):
        particles.append({"x":x,"y":y,"vx":random.randint(-5,5),"vy":random.randint(-8,-2),"life":random.randint(20,40)})

def update_particles():
    for p in particles[:]:
        p["vy"] += 0.5
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
        pygame.draw.rect(screen, RED, (p["x"], p["y"], 3, 3))
        if p["life"] <= 0: particles.remove(p)

# --- ПЕРЕМЕННЫЕ ---
player_x, player_y, player_vel_y = 100, 300, 0
gravity, jump_power, on_ground = 1, -15, True
cactus_x, cactus_y, speed = WIDTH, 300, 6
dead, death_timer, text_scale, text_alpha = False, 0, 0.5, 0

# --- ЦИКЛ ИГРЫ ---
running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_SPACE:
                if not dead and on_ground:
                    player_vel_y=jump_power
                    on_ground=False
                elif dead and death_timer>60:  # рестарт
                    dead=False
                    death_timer=0
                    text_scale=0.5
                    text_alpha=0
                    player_x=100
                    player_y=300
                    player_vel_y=0
                    on_ground=True
                    cactus_x=WIDTH
                    particles.clear()

    # --- ЛОГИКА ---
    if not dead:
        player_vel_y += gravity
        player_y += player_vel_y
        if player_y>=300:
            player_y=300
            player_vel_y=0
            on_ground=True
        cactus_x -= speed
        if cactus_x<-20: cactus_x=WIDTH+random.randint(200,400)
        if pygame.Rect(player_x,player_y,16,32).colliderect(pygame.Rect(cactus_x,cactus_y,20,26)):
            dead=True
            player_vel_y=-10
            spawn_particles(player_x+8,player_y+16)
    else:
        player_vel_y+=gravity
        player_y+=player_vel_y
        update_particles()
        death_timer+=1
        text_scale=min(1.2,text_scale+0.01)
        text_alpha=min(255,text_alpha+5)

    # --- ОТРИСОВКА ---
    draw_night_background()
    draw_cactus(cactus_x,cactus_y)
    if not dead: draw_player(player_x,player_y)
    else:
        font=pygame.font.SysFont("consolas",int(48*text_scale),bold=True)
        text=font.render("YOU DIED",True,RED)
        text.set_alpha(text_alpha)
        screen.blit(text,(WIDTH//2-text.get_width()//2,100))

    pygame.display.flip()

pygame.quit()
sys.exit()
