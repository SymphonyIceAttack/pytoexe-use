import pygame
import random
import sys

pygame.init()

# Screen settings
WIDTH, HEIGHT = 700, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gravity Flip Madness Final")

# Colors
WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
RED = (220, 50, 50)
GREEN = (50, 200, 100)
BLUE = (50, 150, 250)
COLORS = [WHITE, (200,220,255), (255,220,200), (220,255,200)]

# Fonts
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 50)

clock = pygame.time.Clock()

# Player settings
player_width, player_height = 40, 40
player_x = WIDTH // 2
player_y = HEIGHT - player_height - 10
player_speed = 5
jump_power = 10
gravity = 0.5
velocity_y = 0
on_ground = False

# Platforms
platforms = [pygame.Rect(0, HEIGHT-20, WIDTH, 20)]
moving_platforms = []
platform_speeds = []
for i in range(3):
    x = random.randint(50, WIDTH-150)
    y = random.randint(100, HEIGHT-50)
    plat = pygame.Rect(x, y, 100, 10)
    moving_platforms.append(plat)
    platform_speeds.append(random.choice([-2,2]))
    platforms.append(plat)

# Goal
goal = pygame.Rect(random.randint(50, WIDTH-50), 50, 30, 30)

# Game state
score = 0
combo = 0
gravity_direction = 1  # 1 = down, -1 = up
flip_timer = 0
flip_interval = 180  # frames (~3 sec)
game_over = False
background_color = random.choice(COLORS)

def draw_text(text, color, x, y, font_to_use=font):
    surf = font_to_use.render(text, True, color)
    screen.blit(surf, (x, y))

while True:
    screen.fill(background_color)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            # Reset game
            player_x = WIDTH // 2
            player_y = HEIGHT - player_height - 10
            velocity_y = 0
            gravity_direction = 1
            flip_timer = 0
            score = 0
            combo = 0
            game_over = False
            background_color = random.choice(COLORS)
            goal.x = random.randint(50, WIDTH-50)
            goal.y = random.randint(50, HEIGHT-50)

    if not game_over:
        flip_timer += 1

        # Auto flip gravity every flip_interval frames
        if flip_timer >= flip_interval:
            gravity_direction *= -1
            flip_timer = 0
            background_color = random.choice(COLORS)
            # Move goal randomly as part of surprise
            goal.x = random.randint(50, WIDTH-50)
            goal.y = random.randint(50, HEIGHT-50)

        # Move moving platforms
        for i, plat in enumerate(moving_platforms):
            plat.x += platform_speeds[i]
            if plat.left < 0 or plat.right > WIDTH:
                platform_speeds[i] *= -1

        # Player movement
        if keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_RIGHT]:
            player_x += player_speed
        if keys[pygame.K_SPACE] and on_ground:
            velocity_y = -jump_power * gravity_direction
            on_ground = False

        velocity_y += gravity * gravity_direction
        player_y += velocity_y

        # Platform collision
        on_ground = False
        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
        for plat in platforms:
            if player_rect.colliderect(plat):
                if gravity_direction == 1 and velocity_y > 0:
                    player_y = plat.top - player_height
                    velocity_y = 0
                    on_ground = True
                elif gravity_direction == -1 and velocity_y < 0:
                    player_y = plat.bottom
                    velocity_y = 0
                    on_ground = True

        # Goal collision
        if player_rect.colliderect(goal):
            score += 1 + combo
            combo += 1
            goal.x = random.randint(50, WIDTH-50)
            goal.y = random.randint(50, HEIGHT-50)
        else:
            combo = 0

        # Keep player in screen
        if player_y > HEIGHT or player_y < -player_height:
            game_over = True

        # Draw platforms
        for plat in platforms:
            pygame.draw.rect(screen, BLUE, plat)

        # Draw player
        pygame.draw.rect(screen, RED, player_rect)

        # Draw goal
        pygame.draw.rect(screen, GREEN, goal)

        # Draw info
        draw_text(f"Score: {score}", BLACK, 10, 10)
        draw_text(f"Combo: {combo}", BLACK, 10, 40)
        if gravity_direction == -1:
            draw_text("⚡ Gravity UP!", RED, WIDTH//2 - 60, 10, big_font)
        else:
            draw_text("⚡ Gravity DOWN!", BLUE, WIDTH//2 - 70, 10, big_font)

    else:
        draw_text("💥 Game Over!", RED, WIDTH//2 - 100, HEIGHT//2 - 30, big_font)
        draw_text("Press R to Restart", BLACK, WIDTH//2 - 100, HEIGHT//2 + 20)

    clock.tick(60)
    pygame.display.flip()
