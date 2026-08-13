import pygame
import sys

# -----------------------------
# INITIALIZATION
# -----------------------------

pygame.init()

WIDTH = 1000
HEIGHT = 600
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Contra Style Game")

clock = pygame.time.Clock()

# Colors
BLUE = (40, 80, 150)
GREEN = (50, 150, 60)
DARK_GREEN = (30, 100, 40)
RED = (220, 50, 50)
YELLOW = (255, 230, 50)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (120, 80, 40)


# -----------------------------
# PLAYER
# -----------------------------

class Player:

    def __init__(self):
        self.x = 100
        self.y = 400

        self.width = 40
        self.height = 60

        self.speed = 5

        self.velocity_y = 0
        self.gravity = 0.6
        self.jump_strength = -12

        self.grounded = False

        self.direction = 1

        self.health = 5
        self.lives = 3

        self.shoot_timer = 0

    @property
    def rect(self):
        return pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height
        )

    def update(self, keys, platforms):

        # Horizontal movement
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.x -= self.speed
            self.direction = -1

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.x += self.speed
            self.direction = 1

        # Keep inside level
        self.x = max(0, min(self.x, 4800))

        # Jump
        if (
            (keys[pygame.K_SPACE] or keys[pygame.K_w])
            and self.grounded
        ):
            self.velocity_y = self.jump_strength
            self.grounded = False

        # Gravity
        self.velocity_y += self.gravity
        self.y += self.velocity_y

        self.grounded = False

        # Platform collision
        player_rect = self.rect

        for platform in platforms:

            if player_rect.colliderect(platform):

                # Only land while falling
                if self.velocity_y >= 0:

                    self.y = platform.top - self.height
                    self.velocity_y = 0
                    self.grounded = True

                    player_rect = self.rect

        # Shooting cooldown
        if self.shoot_timer > 0:
            self.shoot_timer -= 1

    def shoot(self):

        if self.shoot_timer == 0:

            self.shoot_timer = 15

            if self.direction == 1:
                x = self.x + self.width
            else:
                x = self.x - 12

            return Bullet(
                x,
                self.y + 25,
                self.direction * 12,
                True
            )

        return None

    def draw(self, camera_x):

        r = self.rect

        x = r.x - camera_x

        # Body
        pygame.draw.rect(
            screen,
            BLUE,
            (x + 8, r.y + 15, 25, 30)
        )

        # Head
        pygame.draw.circle(
            screen,
            (240, 190, 140),
            (x + 20, r.y + 10),
            10
        )

        # Legs
        pygame.draw.rect(
            screen,
            DARK_GREEN,
            (x + 8, r.y + 45, 8, 15)
        )

        pygame.draw.rect(
            screen,
            DARK_GREEN,
            (x + 25, r.y + 45, 8, 15)
        )

        # Gun
        if self.direction == 1:

            pygame.draw.rect(
                screen,
                BLACK,
                (x + 28, r.y + 24, 25, 6)
            )

        else:

            pygame.draw.rect(
                screen,
                BLACK,
                (x - 13, r.y + 24, 25, 6)
            )


# -----------------------------
# BULLET
# -----------------------------

class Bullet:

    def __init__(self, x, y, velocity, player_bullet):

        self.x = x
        self.y = y

        self.velocity = velocity

        self.player_bullet = player_bullet

        self.width = 12
        self.height = 5

    @property
    def rect(self):

        return pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height
        )

    def update(self):

        self.x += self.velocity

    def draw(self, camera_x):

        color = YELLOW if self.player_bullet else RED

        pygame.draw.rect(
            screen,
            color,
            (
                int(self.x - camera_x),
                int(self.y),
                self.width,
                self.height
            )
        )


# -----------------------------
# ENEMY
# -----------------------------

class Enemy:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.width = 40
        self.height = 55

        self.direction = -1
        self.speed = 1

        self.health = 2

        self.shoot_timer = 100

    @property
    def rect(self):

        return pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height
        )

    def update(self, player):

        # Simple patrol
        self.x += self.direction * self.speed

        if self.x < 300:
            self.direction = 1

        if self.x > 4500:
            self.direction = -1

        self.shoot_timer -= 1

        if self.shoot_timer <= 0:

            self.shoot_timer = 120

            # Shoot toward player
            if player.x > self.x:
                direction = 1
            else:
                direction = -1

            return Bullet(
                self.x,
                self.y + 25,
                direction * 6,
                False
            )

        return None

    def draw(self, camera_x):

        x = self.x - camera_x

        # Body
        pygame.draw.rect(
            screen,
            RED,
            (x + 8, self.y + 15, 25, 30)
        )

        # Head
        pygame.draw.circle(
            screen,
            (190, 140, 100),
            (x + 20, self.y + 10),
            10
        )

        # Legs
        pygame.draw.rect(
            screen,
            BLACK,
            (x + 8, self.y + 45, 8, 10)
        )

        pygame.draw.rect(
            screen,
            BLACK,
            (x + 25, self.y + 45, 8, 10)
        )


# -----------------------------
# BOSS
# -----------------------------

class Boss:

    def __init__(self):

        self.x = 4600
        self.y = 400

        self.width = 100
        self.height = 100

        self.health = 20
        self.shoot_timer = 60

    @property
    def rect(self):

        return pygame.Rect(
            int(self.x),
            int(self.y),
            self.width,
            self.height
        )

    def update(self, player):

        self.shoot_timer -= 1

        if self.shoot_timer <= 0:

            self.shoot_timer = 60

            direction = 1 if player.x > self.x else -1

            return Bullet(
                self.x,
                self.y + 40,
                direction * 7,
                False
            )

        return None

    def draw(self, camera_x):

        x = self.x - camera_x

        pygame.draw.rect(
            screen,
            (150, 40, 180),
            (x, self.y, self.width, self.height)
        )

        pygame.draw.circle(
            screen,
            (220, 170, 140),
            (x + 50, self.y + 25),
            20
        )

        # Health bar background
        pygame.draw.rect(
            screen,
            BLACK,
            (x, self.y - 20, 100, 10)
        )

        # Health bar
        health_width = max(
            0,
            int(self.health * 5)
        )

        pygame.draw.rect(
            screen,
            RED,
            (x, self.y - 20, health_width, 10)
        )


# -----------------------------
# LEVEL
# -----------------------------

platforms = [

    # Main floor
    pygame.Rect(0, 520, 5000, 80),

    # Floating platforms
    pygame.Rect(500, 430, 200, 30),
    pygame.Rect(900, 350, 200, 30),
    pygame.Rect(1300, 430, 250, 30),
    pygame.Rect(1750, 350, 200, 30),
    pygame.Rect(2200, 420, 250, 30),
    pygame.Rect(2700, 350, 250, 30),
    pygame.Rect(3200, 430, 250, 30),
    pygame.Rect(3700, 350, 250, 30),
    pygame.Rect(4100, 420, 250, 30),
]


# -----------------------------
# GAME OBJECTS
# -----------------------------

player = Player()

enemies = [
    Enemy(600, 465),
    Enemy(1000, 295),
    Enemy(1400, 375),
    Enemy(1800, 295),
    Enemy(2300, 365),
    Enemy(2750, 295),
    Enemy(3250, 375),
    Enemy(3750, 295),
    Enemy(4200, 365),
]

boss = Boss()

player_bullets = []
enemy_bullets = []


# -----------------------------
# CAMERA
# -----------------------------

camera_x = 0


# -----------------------------
# FONTS
# -----------------------------

font = pygame.font.Font(None, 32)
large_font = pygame.font.Font(None, 70)


# -----------------------------
# RESET GAME
# -----------------------------

def reset_game():

    global player
    global enemies
    global boss
    global player_bullets
    global enemy_bullets

    player = Player()

    enemies = [
        Enemy(600, 465),
        Enemy(1000, 295),
        Enemy(1400, 375),
        Enemy(1800, 295),
        Enemy(2300, 365),
        Enemy(2750, 295),
        Enemy(3250, 375),
        Enemy(3750, 295),
        Enemy(4200, 365),
    ]

    boss = Boss()

    player_bullets = []
    enemy_bullets = []


# -----------------------------
# GAME OVER
# -----------------------------

def game_over():

    screen.fill(BLACK)

    text = large_font.render(
        "GAME OVER",
        True,
        RED
    )

    info = font.render(
        "Press ENTER to restart",
        True,
        WHITE
    )

    screen.blit(
        text,
        (
            WIDTH // 2 - text.get_width() // 2,
            220
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

    waiting = True

    while waiting:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_RETURN:
                    reset_game()
                    return


# -----------------------------
# WIN
# -----------------------------

def win_screen():

    screen.fill((10, 50, 20))

    text = large_font.render(
        "YOU WIN!",
        True,
        GREEN
    )

    info = font.render(
        "Press ENTER to play again",
        True,
        WHITE
    )

    screen.blit(
        text,
        (
            WIDTH // 2 - text.get_width() // 2,
            220
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

    waiting = True

    while waiting:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_RETURN:
                    reset_game()
                    return


# -----------------------------
# MAIN LOOP
# -----------------------------

running = True

while running:

    clock.tick(FPS)

    # -------------------------
    # EVENTS
    # -------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            # Shoot
            if event.key in (
                pygame.K_z,
                pygame.K_j,
                pygame.K_LCTRL
            ):

                bullet = player.shoot()

                if bullet:
                    player_bullets.append(bullet)

    # -------------------------
    # INPUT
    # -------------------------

    keys = pygame.key.get_pressed()

    # -------------------------
    # PLAYER
    # -------------------------

    player.update(keys, platforms)

    # -------------------------
    # CAMERA
    # -------------------------

    camera_x = player.x - WIDTH // 2

    camera_x = max(
        0,
        min(camera_x, 4000)
    )

    # -------------------------
    # ENEMIES
    # -------------------------

    for enemy in enemies:

        bullet = enemy.update(player)

        if bullet:
            enemy_bullets.append(bullet)

    # -------------------------
    # BOSS
    # -------------------------

    boss_bullet = boss.update(player)

    if boss_bullet:
        enemy_bullets.append(boss_bullet)

    # -------------------------
    # PLAYER BULLETS
    # -------------------------

    for bullet in player_bullets[:]:

        bullet.update()

        # Remove bullet outside level
        if bullet.x < 0 or bullet.x > 5000:

            player_bullets.remove(bullet)
            continue

        # Enemy collision
        hit_enemy = None

        for enemy in enemies:

            if bullet.rect.colliderect(enemy.rect):

                hit_enemy = enemy
                break

        if hit_enemy:

            player_bullets.remove(bullet)

            hit_enemy.health -= 1

            if hit_enemy.health <= 0:

                enemies.remove(hit_enemy)

                player.score += 100

            continue

        # Boss collision
        if bullet.rect.colliderect(boss.rect):

            player_bullets.remove(bullet)

            boss.health -= 1

            player.score += 10

            if boss.health <= 0:
                win_screen()

    # -------------------------
    # ENEMY BULLETS
    # -------------------------

    for bullet in enemy_bullets[:]:

        bullet.update()

        if bullet.x < 0 or bullet.x > 5000:

            enemy_bullets.remove(bullet)
            continue

        if bullet.rect.colliderect(player.rect):

            enemy_bullets.remove(bullet)

            player.health -= 1

            if player.health <= 0:

                player.lives -= 1

                if player.lives <= 0:

                    game_over()

                else:

                    player.health = 5
                    player.x -= 300
                    player.y = 300

    # -------------------------
    # ENEMY CONTACT
    # -------------------------

    for enemy in enemies:

        if enemy.rect.colliderect(player.rect):

            player.health -= 1

            if player.health <= 0:

                player.lives -= 1

                if player.lives <= 0:

                    game_over()

                else:

                    player.health = 5
                    player.x -= 300
                    player.y = 300

    # -------------------------
    # FALLING
    # -------------------------

    if player.y > HEIGHT + 100:

        player.lives -= 1

        if player.lives <= 0:

            game_over()

        else:

            player.health = 5
            player.x -= 300
            player.y = 300

    # -------------------------
    # DRAW BACKGROUND
    # -------------------------

    screen.fill((35, 55, 90))

    # Mountains
    for x in range(-500, 5500, 500):

        screen_x = x - camera_x * 0.3

        pygame.draw.polygon(
            screen,
            (45, 70, 90),
            [
                (screen_x, 520),
                (screen_x + 250, 250),
                (screen_x + 500, 520)
            ]
        )

    # -------------------------
    # DRAW PLATFORMS
    # -------------------------

    for platform in platforms:

        pygame.draw.rect(
            screen,
            GREEN,
            (
                platform.x - camera_x,
                platform.y,
                platform.width,
                platform.height
            )
        )

        pygame.draw.rect(
            screen,
            DARK_GREEN,
            (
                platform.x - camera_x,
                platform.y,
                platform.width,
                6
            )
        )

    # -------------------------
    # DRAW ENEMIES
    # -------------------------

    for enemy in enemies:
        enemy.draw(camera_x)

    # -------------------------
    # DRAW BOSS
    # -------------------------

    boss.draw(camera_x)

    # -------------------------
    # DRAW BULLETS
    # -------------------------

    for bullet in player_bullets:
        bullet.draw(camera_x)

    for bullet in enemy_bullets:
        bullet.draw(camera_x)

    # -------------------------
    # DRAW PLAYER
    # -------------------------

    player.draw(camera_x)

    # -------------------------
    # HUD
    # -------------------------

    hud = font.render(
        f"Health: {player.health}   "
        f"Lives: {player.lives}   "
        f"Score: {player.score}",
        True,
        WHITE
    )

    screen.blit(hud, (20, 20))

    controls = font.render(
        "A/D = Move   SPACE = Jump   Z = Shoot",
        True,
        WHITE
    )

    screen.blit(
        controls,
        (20, 55)
    )

    pygame.display.flip()


pygame.quit()
