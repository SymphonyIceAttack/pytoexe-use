import pygame
import random
import sys

pygame.init()

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

WIDTH = 1000
HEIGHT = 600
FPS = 60

WORLD_WIDTH = 5000

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Run & Gun - Contra Style")
clock = pygame.time.Clock()

# Colors
SKY = (30, 45, 75)
GROUND = (45, 100, 45)
PLAYER_COLOR = (50, 180, 255)
PLAYER_DARK = (20, 80, 150)
ENEMY_COLOR = (220, 60, 60)
BOSS_COLOR = (160, 40, 180)
BULLET_COLOR = (255, 240, 50)
ENEMY_BULLET = (255, 100, 50)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TREE_COLOR = (30, 100, 45)

font = pygame.font.Font(None, 32)
big_font = pygame.font.Font(None, 72)


# --------------------------------------------------
# PLAYER
# --------------------------------------------------

class Player:
    def __init__(self):
        self.rect = pygame.Rect(100, 400, 40, 60)

        self.x_velocity = 0
        self.y_velocity = 0

        self.speed = 5
        self.jump_power = -13
        self.gravity = 0.6

        self.on_ground = False

        self.health = 5
        self.lives = 3
        self.score = 0

        self.shoot_cooldown = 0
        self.invincible_timer = 0

        self.facing = 1

    def update(self, keys, platforms):
        self.x_velocity = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x_velocity = -self.speed
            self.facing = -1

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x_velocity = self.speed
            self.facing = 1

        if (keys[pygame.K_SPACE] or keys[pygame.K_w]
                or keys[pygame.K_UP]) and self.on_ground:
            self.y_velocity = self.jump_power
            self.on_ground = False

        # Horizontal movement
        self.rect.x += self.x_velocity

        # Keep player inside world
        self.rect.x = max(0, min(WORLD_WIDTH - self.rect.width, self.rect.x))

        # Gravity
        self.y_velocity += self.gravity
        self.rect.y += self.y_velocity

        self.on_ground = False

        # Platform collision
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.y_velocity > 0 and self.rect.bottom <= platform.bottom:
                    self.rect.bottom = platform.top
                    self.y_velocity = 0
                    self.on_ground = True

        # Shooting cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.invincible_timer > 0:
            self.invincible_timer -= 1

    def shoot(self):
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = 12

            bullet_x = self.rect.centerx + self.facing * 25
            bullet_y = self.rect.centery

            return Bullet(
                bullet_x,
                bullet_y,
                self.facing * 12,
                True
            )

        return None

    def damage(self):
        if self.invincible_timer <= 0:
            self.health -= 1
            self.invincible_timer = 90

            if self.health <= 0:
                self.lives -= 1

                if self.lives > 0:
                    self.health = 5
                    self.rect.x = max(100, self.rect.x - 500)
                    self.rect.y = 300
                else:
                    return True

        return False

    def draw(self, surface, camera_x):
        # Blink while invincible
        if self.invincible_timer > 0 and self.invincible_timer % 10 < 5:
            return

        x = self.rect.x - camera_x
        y = self.rect.y

        # Body
        pygame.draw.rect(
            surface,
            PLAYER_COLOR,
            (x + 10, y + 15, 25, 35)
        )

        # Head
        pygame.draw.circle(
            surface,
            (230, 190, 150),
            (x + 25, y + 10),
            10
        )

        # Legs
        pygame.draw.rect(
            surface,
            PLAYER_DARK,
            (x + 10, y + 45, 8, 15)
        )

        pygame.draw.rect(
            surface,
            PLAYER_DARK,
            (x + 27, y + 45, 8, 15)
        )

        # Gun
        if self.facing == 1:
            pygame.draw.rect(
                surface,
                BLACK,
                (x + 30, y + 25, 22, 6)
            )
        else:
            pygame.draw.rect(
                surface,
                BLACK,
                (x - 12, y + 25, 22, 6)
            )


# --------------------------------------------------
# BULLET
# --------------------------------------------------

class Bullet:
    def __init__(self, x, y, velocity, friendly):
        self.rect = pygame.Rect(x, y, 12, 5)
        self.velocity = velocity
        self.friendly = friendly

    def update(self):
        self.rect.x += self.velocity

    def draw(self, surface, camera_x):
        color = BULLET_COLOR if self.friendly else ENEMY_BULLET

        pygame.draw.rect(
            surface,
            color,
            (
                self.rect.x - camera_x,
                self.rect.y,
                self.rect.width,
                self.rect.height
            )
        )


# --------------------------------------------------
# ENEMY
# --------------------------------------------------

class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 55)

        self.start_x = x
        self.direction = random.choice([-1, 1])

        self.speed = 1.5

        self.health = 2

        self.shoot_timer = random.randint(60, 150)

    def update(self, player):
        self.rect.x += self.direction * self.speed

        # Patrol
        if abs(self.rect.x - self.start_x) > 120:
            self.direction *= -1

        # Shoot
        self.shoot_timer -= 1

        if self.shoot_timer <= 0:
            self.shoot_timer = random.randint(80, 160)

            if abs(player.rect.x - self.rect.x) < 600:
                direction = 1 if player.rect.centerx > self.rect.centerx else -1

                return Bullet(
                    self.rect.centerx,
                    self.rect.centery,
                    direction * 6,
                    False
                )

        return None

    def hit(self):
        self.health -= 1
        return self.health <= 0

    def draw(self, surface, camera_x):
        x = self.rect.x - camera_x
        y = self.rect.y

        # Body
        pygame.draw.rect(
            surface,
            ENEMY_COLOR,
            (x + 8, y + 15, 25, 35)
        )

        # Head
        pygame.draw.circle(
            surface,
            (180, 130, 100),
            (x + 20, y + 10),
            10
        )

        # Legs
        pygame.draw.rect(
            surface,
            BLACK,
            (x + 8, y + 45, 8, 10)
        )

        pygame.draw.rect(
            surface,
            BLACK,
            (x + 25, y + 45, 8, 10)
        )

        # Gun
        pygame.draw.rect(
            surface,
            BLACK,
            (x - 8, y + 25, 20, 5)
        )


# --------------------------------------------------
# BOSS
# --------------------------------------------------

class Boss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 100, 110)

        self.health = 30
        self.max_health = 30

        self.direction = -1
        self.speed = 2

        self.shoot_timer = 80

    def update(self, player):
        # Move toward player
        if player.rect.centerx < self.rect.centerx:
            self.rect.x -= self.speed
        else:
            self.rect.x += self.speed

        self.shoot_timer -= 1

        if self.shoot_timer <= 0:
            self.shoot_timer = 50

            direction = 1 if player.rect.centerx > self.rect.centerx else -1

            return Bullet(
                self.rect.centerx,
                self.rect.centery,
                direction * 7,
                False
            )

        return None

    def hit(self):
        self.health -= 1
        return self.health <= 0

    def draw(self, surface, camera_x):
        x = self.rect.x - camera_x
        y = self.rect.y

        # Boss body
        pygame.draw.rect(
            surface,
            BOSS_COLOR,
            (x, y + 20, 100, 90)
        )

        # Head
        pygame.draw.circle(
            surface,
            (200, 150, 130),
            (x + 50, y + 15),
            20
        )

        # Eyes
        pygame.draw.circle(
            surface,
            BLACK,
            (x + 42, y + 12),
            4
        )

        pygame.draw.circle(
            surface,
            BLACK,
            (x + 58, y + 12),
            4
        )

        # Weapon
        pygame.draw.rect(
            surface,
            BLACK,
            (x - 30, y + 50, 35, 12)
        )

        # Health bar
        pygame.draw.rect(
            surface,
            BLACK,
            (x, y - 20, 100, 10)
        )

        health_width = int(
            100 * self.health / self.max_health
        )

        pygame.draw.rect(
            surface,
            (255, 40, 40),
            (x, y - 20, health_width, 10)
        )


# --------------------------------------------------
# LEVEL
# --------------------------------------------------

platforms = []

# Main ground
platforms.append(
    pygame.Rect(0, 520, WORLD_WIDTH, 80)
)

# Platforms
platform_data = [
    (500, 430, 200, 30),
    (900, 350, 200, 30),
    (1300, 430, 250, 30),
    (1700, 330, 200, 30),
    (2100, 420, 250, 30),
    (2500, 350, 250, 30),
    (2900, 450, 300, 30),
    (3350, 370, 250, 30),
    (3750, 300, 250, 30),
    (4200, 420, 300, 30),
]

for data in platform_data:
    platforms.append(pygame.Rect(*data))


# --------------------------------------------------
# ENEMIES
# --------------------------------------------------

enemies = []

enemy_positions = [
    (600, 465),
    (1000, 295),
    (1400, 375),
    (1800, 275),
    (2200, 365),
    (2600, 295),
    (3000, 395),
    (3450, 315),
    (3850, 245),
    (4300, 365),
]

for x, y in enemy_positions:
    enemies.append(Enemy(x, y))


# Boss at end
boss = Boss(4650, 410)


# --------------------------------------------------
# BACKGROUND
# --------------------------------------------------

def draw_background(surface, camera_x):

    surface.fill(SKY)

    # Mountains
    for x in range(-500, WORLD_WIDTH, 500):
        screen_x = x - int(camera_x * 0.3)

        pygame.draw.polygon(
            surface,
            (40, 65, 85),
            [
                (screen_x, 520),
                (screen_x + 250, 250),
                (screen_x + 500, 520)
            ]
        )

    # Trees
    for x in range(100, WORLD_WIDTH, 350):
        screen_x = x - int(camera_x * 0.5)

        pygame.draw.rect(
            surface,
            (70, 50, 30),
            (screen_x, 400, 20, 120)
        )

        pygame.draw.circle(
            surface,
            TREE_COLOR,
            (screen_x + 10, 390),
            50
        )


# --------------------------------------------------
# DRAW PLATFORMS
# --------------------------------------------------

def draw_platforms(surface, camera_x):

    for platform in platforms:

        pygame.draw.rect(
            surface,
            GROUND,
            (
                platform.x - camera_x,
                platform.y,
                platform.width,
                platform.height
            )
        )

        # Grass
        pygame.draw.rect(
            surface,
            (80, 170, 60),
            (
                platform.x - camera_x,
                platform.y,
                platform.width,
                6
            )
        )


# --------------------------------------------------
# HUD
# --------------------------------------------------

def draw_hud(surface, player):

    health_text = font.render(
        f"HEALTH: {player.health}",
        True,
        WHITE
    )

    lives_text = font.render(
        f"LIVES: {player.lives}",
        True,
        WHITE
    )

    score_text = font.render(
        f"SCORE: {player.score}",
        True,
        WHITE
    )

    surface.blit(health_text, (20, 20))
    surface.blit(lives_text, (20, 50))
    surface.blit(score_text, (20, 80))


# --------------------------------------------------
# GAME OVER
# --------------------------------------------------

def game_over():

    screen.fill(BLACK)

    text = big_font.render(
        "GAME OVER",
        True,
        (255, 50, 50)
    )

    info = font.render(
        "Press ENTER to restart or ESC to quit",
        True,
        WHITE
    )

    screen.blit(
        text,
        (
            WIDTH // 2 - text.get_width() // 2,
            230
        )
    )

    screen.blit(
        info,
        (
            WIDTH // 2 - info.get_width() // 2,
            320
        )
    )

    pygame.display.flip()

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_RETURN:
                    return


# --------------------------------------------------
# WIN SCREEN
# --------------------------------------------------

def win_screen():

    screen.fill((10, 40, 20))

    text = big_font.render(
        "MISSION COMPLETE!",
        True,
        (80, 255, 100)
    )

    info = font.render(
        "Press ENTER to play again or ESC to quit",
        True,
        WHITE
    )

    screen.blit(
        text,
        (
            WIDTH // 2 - text.get_width() // 2,
            230
        )
    )

    screen.blit(
        info,
        (
            WIDTH // 2 - info.get_width() // 2,
            320
        )
    )

    pygame.display.flip()

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_RETURN:
                    return


# --------------------------------------------------
# MAIN GAME
# --------------------------------------------------

def game():

    player = Player()

    bullets = []
    enemy_bullets = []

    camera_x = 0

    boss_defeated = False

    running = True

    while running:

        clock.tick(FPS)

        # ------------------------------------------
        # EVENTS
        # ------------------------------------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if event.key in (
                    pygame.K_z,
                    pygame.K_j,
                    pygame.K_LCTRL
                ):
                    bullet = player.shoot()

                    if bullet:
                        bullets.append(bullet)

        keys = pygame.key.get_pressed()

        # ------------------------------------------
        # PLAYER
        # ------------------------------------------

        player.update(keys, platforms)

        # ------------------------------------------
        # CAMERA
        # ------------------------------------------

        camera_x = player.rect.centerx - WIDTH // 2

        camera_x = max(
            0,
            min(WORLD_WIDTH - WIDTH, camera_x)
        )

        # ------------------------------------------
        # PLAYER BULLETS
        # ------------------------------------------

        for bullet in bullets[:]:

            bullet.update()

            if bullet.rect.x < 0 or bullet.rect.x > WORLD_WIDTH:
                bullets.remove(bullet)
                continue

            # Hit enemies
            for enemy in enemies[:]:

                if bullet.rect.colliderect(enemy.rect):

                    if bullet in bullets:
                        bullets.remove(bullet)

                    if enemy.hit():
                        enemies.remove(enemy)
                        player.score += 100

                    break

            # Hit boss
            if not boss_defeated:

                if bullet.rect.colliderect(boss.rect):

                    if bullet in bullets:
                        bullets.remove(bullet)

                    if boss.hit():
                        boss_defeated = True
                        player.score += 1000

        # ------------------------------------------
        # ENEMIES
        # ------------------------------------------

        for enemy in enemies:

            enemy_bullet = enemy.update(player)

            if enemy_bullet:
                enemy_bullets.append(enemy_bullet)

            # Enemy touching player
            if enemy.rect.colliderect(player.rect):

                if player.damage():
                    game_over()
                    return

        # ------------------------------------------
        # BOSS
        # ------------------------------------------

        if not boss_defeated:

            boss_bullet = boss.update(player)

            if boss_bullet:
                enemy_bullets.append(boss_bullet)

            if boss.rect.colliderect(player.rect):

                if player.damage():
                    game_over()
                    return

        # ------------------------------------------
        # ENEMY BULLETS
        # ------------------------------------------

        for bullet in enemy_bullets[:]:

            bullet.update()

            if (
                bullet.rect.x < 0
                or bullet.rect.x > WORLD_WIDTH
            ):
                enemy_bullets.remove(bullet)
                continue

            if bullet.rect.colliderect(player.rect):

                enemy_bullets.remove(bullet)

                if player.damage():
                    game_over()
                    return

        # ------------------------------------------
        # FALLING OFF THE WORLD
        # ------------------------------------------

        if player.rect.top > HEIGHT + 100:

            if player.damage():
                game_over()
                return

            player.rect.x = max(
                100,
                player.rect.x - 300
            )

            player.rect.y = 300

        # ------------------------------------------
        # WIN CONDITION
        # ------------------------------------------

        if boss_defeated:

            win_screen()
            return

        # ------------------------------------------
        # DRAW
        # ------------------------------------------

        draw_background(screen, camera_x)

        draw_platforms(screen, camera_x)

        for enemy in enemies:
            enemy.draw(screen, camera_x)

        if not boss_defeated:
            boss.draw(screen, camera_x)

        for bullet in bullets:
            bullet.draw(screen, camera_x)

        for bullet in enemy_bullets:
            bullet.draw(screen, camera_x)

        player.draw(screen, camera_x)

        draw_hud(screen, player)

        # Controls
        controls = font.render(
            "Move: A/D or Arrows   Jump: W/Space   Shoot: Z/J",
            True,
            WHITE
        )

        screen.blit(
            controls,
            (WIDTH - controls.get_width() - 15, 15)
        )

        pygame.display.flip()


# --------------------------------------------------
# PROGRAM START
# --------------------------------------------------

while True:
    game()

