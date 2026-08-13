import pygame
import random
import math
import sys

# ============================================================
# OFFLINE BIKE RACING GAME
# Player + 5 computer bots
# ============================================================

pygame.init()

# -------------------- SETTINGS --------------------

WIDTH = 1000
HEIGHT = 700

FPS = 60

ROAD_WIDTH = 600
ROAD_LEFT = (WIDTH - ROAD_WIDTH) // 2
ROAD_RIGHT = ROAD_LEFT + ROAD_WIDTH

BIKE_WIDTH = 30
BIKE_HEIGHT = 55

TOTAL_LAPS = 3

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Offline Bike Racing")

clock = pygame.time.Clock()

# Fonts
FONT = pygame.font.SysFont("Arial", 24)
BIG_FONT = pygame.font.SysFont("Arial", 50, bold=True)
SMALL_FONT = pygame.font.SysFont("Arial", 18)


# -------------------- COLORS --------------------

GRASS = (35, 145, 55)
ROAD = (65, 65, 70)
ROAD_EDGE = (230, 230, 230)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
YELLOW = (255, 220, 40)
RED = (220, 50, 50)
BLUE = (50, 130, 255)
GREEN = (50, 220, 100)
ORANGE = (255, 145, 40)
PURPLE = (170, 70, 220)
CYAN = (40, 220, 220)


# -------------------- TRACK --------------------

# Track is represented as a long straight road.
# The world scrolls downward as bikes move.

TRACK_LENGTH = 9000

road_mark_offset = 0


# -------------------- BIKE CLASS --------------------

class Bike:
    def __init__(self, x, y, color, name, player=False):
        self.x = float(x)
        self.y = float(y)

        self.color = color
        self.name = name

        self.player = player

        self.speed = 0
        self.max_speed = 8

        self.acceleration = 0.18
        self.braking = 0.30

        self.steer_speed = 5

        self.distance = 0

        self.lap = 1

        self.finished = False

        self.finish_time = 0

        self.ai_timer = random.randint(20, 80)

    def rect(self):
        return pygame.Rect(
            int(self.x - BIKE_WIDTH / 2),
            int(self.y - BIKE_HEIGHT / 2),
            BIKE_WIDTH,
            BIKE_HEIGHT
        )

    def update_player(self, keys):

        # Accelerate
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.speed += self.acceleration
        else:
            self.speed -= 0.04

        # Brake
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed -= self.braking

        # Steering
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.steer_speed

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.steer_speed

        # Limit speed
        self.speed = max(0, min(self.speed, self.max_speed))

        # Keep bike on road
        if self.x < ROAD_LEFT + 25:
            self.x = ROAD_LEFT + 25
            self.speed *= 0.95

        if self.x > ROAD_RIGHT - 25:
            self.x = ROAD_RIGHT - 25
            self.speed *= 0.95

        self.distance += self.speed

    def update_ai(self, bikes):

        # Bots try to maintain a random target speed.
        target_speed = self.max_speed

        # Small differences make bots behave differently.
        target_speed += math.sin(self.distance / 400 + hash(self.name)) * 0.5

        if self.speed < target_speed:
            self.speed += self.acceleration * 0.7
        else:
            self.speed -= 0.04

        # Find nearby bikes and avoid them.
        for other in bikes:

            if other is self:
                continue

            vertical_difference = abs(self.y - other.y)
            horizontal_difference = abs(self.x - other.x)

            if vertical_difference < 90 and horizontal_difference < 45:

                if self.x <= other.x:
                    self.x -= 1.2
                else:
                    self.x += 1.2

                self.speed *= 0.98

        # AI steering wandering
        self.ai_timer -= 1

        if self.ai_timer <= 0:
            self.ai_timer = random.randint(30, 100)

            # Randomly move slightly
            self.ai_direction = random.choice([-1, 0, 1])

        if not hasattr(self, "ai_direction"):
            self.ai_direction = 0

        self.x += self.ai_direction * 0.8

        # Keep AI on road
        if self.x < ROAD_LEFT + 30:
            self.x = ROAD_LEFT + 30

        if self.x > ROAD_RIGHT - 30:
            self.x = ROAD_RIGHT - 30

        self.speed = max(0, min(self.speed, self.max_speed))

        self.distance += self.speed


# -------------------- CREATE BIKES --------------------

player = Bike(
    WIDTH // 2,
    HEIGHT - 120,
    RED,
    "YOU",
    True
)

bots = []

bot_colors = [
    BLUE,
    GREEN,
    ORANGE,
    PURPLE,
    CYAN
]

bot_names = [
    "BOT 1",
    "BOT 2",
    "BOT 3",
    "BOT 4",
    "BOT 5"
]

for i in range(5):

    # Spread bikes across the starting line
    x = ROAD_LEFT + 100 + i * 90

    bot = Bike(
        x,
        HEIGHT - 210,
        bot_colors[i],
        bot_names[i]
    )

    bot.max_speed = random.uniform(6.7, 7.8)

    bots.append(bot)

bikes = [player] + bots


# -------------------- RESET GAME --------------------

def reset_game():

    global player, bots, bikes, road_mark_offset

    player = Bike(
        WIDTH // 2,
        HEIGHT - 120,
        RED,
        "YOU",
        True
    )

    bots = []

    for i in range(5):

        x = ROAD_LEFT + 100 + i * 90

        bot = Bike(
            x,
            HEIGHT - 210,
            bot_colors[i],
            bot_names[i]
        )

        bot.max_speed = random.uniform(6.7, 7.8)

        bots.append(bot)

    bikes = [player] + bots

    road_mark_offset = 0


# -------------------- DRAW ROAD --------------------

def draw_track():

    global road_mark_offset

    screen.fill(GRASS)

    # Road
    pygame.draw.rect(
        screen,
        ROAD,
        (
            ROAD_LEFT,
            0,
            ROAD_WIDTH,
            HEIGHT
        )
    )

    # Road edges
    pygame.draw.rect(
        screen,
        ROAD_EDGE,
        (
            ROAD_LEFT,
            0,
            8,
            HEIGHT
        )
    )

    pygame.draw.rect(
        screen,
        ROAD_EDGE,
        (
            ROAD_RIGHT - 8,
            0,
            8,
            HEIGHT
        )
    )

    # Center road markings
    road_mark_offset += player.speed

    dash_height = 45
    gap = 35

    offset = int(road_mark_offset) % (dash_height + gap)

    y = -offset

    while y < HEIGHT:

        pygame.draw.rect(
            screen,
            YELLOW,
            (
                WIDTH // 2 - 5,
                y,
                10,
                dash_height
            )
        )

        y += dash_height + gap

    # Grass decorations
    for i in range(20):

        x = 20 + (i * 173) % 960
        y = (i * 97 + int(road_mark_offset * 0.3)) % HEIGHT

        if ROAD_LEFT - 60 < x < ROAD_RIGHT + 60:
            continue

        pygame.draw.circle(
            screen,
            GREEN,
            (x, y),
            5
        )


# -------------------- DRAW BIKE --------------------

def draw_bike(bike):

    rect = bike.rect()

    # Wheels
    pygame.draw.ellipse(
        screen,
        BLACK,
        (
            rect.x - 3,
            rect.y + 5,
            8,
            18
        )
    )

    pygame.draw.ellipse(
        screen,
        BLACK,
        (
            rect.right - 5,
            rect.y + 5,
            8,
            18
        )
    )

    # Main body
    pygame.draw.rect(
        screen,
        bike.color,
        rect,
        border_radius=8
    )

    # Seat
    pygame.draw.rect(
        screen,
        BLACK,
        (
            rect.x + 5,
            rect.y + 15,
            rect.width - 10,
            14
        ),
        border_radius=5
    )

    # Front light
    pygame.draw.circle(
        screen,
        WHITE,
        (
            rect.centerx,
            rect.y + 7
        ),
        4
    )

    # Player outline
    if bike.player:

        pygame.draw.rect(
            screen,
            WHITE,
            rect.inflate(6, 6),
            2,
            border_radius=8
        )


# -------------------- COLLISIONS --------------------

def handle_collisions():

    for i in range(len(bikes)):

        for j in range(i + 1, len(bikes)):

            a = bikes[i]
            b = bikes[j]

            if a.rect().colliderect(b.rect()):

                # Push bikes apart
                if a.x < b.x:
                    a.x -= 2
                    b.x += 2
                else:
                    a.x += 2
                    b.x -= 2

                # Small speed penalty
                a.speed *= 0.90
                b.speed *= 0.90


# -------------------- POSITION CALCULATION --------------------

def get_position(bike):

    # Sort bikes based on distance traveled.
    ordered = sorted(
        bikes,
        key=lambda b: b.distance,
        reverse=True
    )

    return ordered.index(bike) + 1


# -------------------- HUD --------------------

def draw_hud():

    position = get_position(player)

    lap = min(
        TOTAL_LAPS,
        int(player.distance // (TRACK_LENGTH / TOTAL_LAPS)) + 1
    )

    # Top information
    pygame.draw.rect(
        screen,
        (0, 0, 0, 150),
        (0, 0, WIDTH, 70)
    )

    speed_text = FONT.render(
        f"Speed: {int(player.speed * 25)} km/h",
        True,
        WHITE
    )

    position_text = FONT.render(
        f"Position: {position}/6",
        True,
        WHITE
    )

    lap_text = FONT.render(
        f"Lap: {lap}/{TOTAL_LAPS}",
        True,
        WHITE
    )

    screen.blit(speed_text, (20, 20))
    screen.blit(position_text, (250, 20))
    screen.blit(lap_text, (450, 20))

    # Controls
    controls = SMALL_FONT.render(
        "W/↑ Accelerate   S/↓ Brake   A/D or ←/→ Steer   R Restart   ESC Quit",
        True,
        WHITE
    )

    screen.blit(
        controls,
        (
            20,
            HEIGHT - 30
        )
    )


# -------------------- FINISH CHECK --------------------

race_finished = False
winner_text = ""

def check_finish():

    global race_finished, winner_text

    finish_distance = TRACK_LENGTH

    for bike in bikes:

        if bike.distance >= finish_distance and not bike.finished:

            bike.finished = True

            if bike is player:

                race_finished = True

                position = get_position(player)

                winner_text = f"You finished in {position}th place!"


# -------------------- FINISH SCREEN --------------------

def draw_finish_screen():

    pygame.draw.rect(
        screen,
        (0, 0, 0, 210),
        (
            150,
            180,
            WIDTH - 300,
            300
        )
    )

    title = BIG_FONT.render(
        "RACE FINISHED!",
        True,
        YELLOW
    )

    position = get_position(player)

    result = FONT.render(
        f"Your position: {position}/6",
        True,
        WHITE
    )

    restart = FONT.render(
        "Press R to race again",
        True,
        GREEN
    )

    quit_text = FONT.render(
        "Press ESC to quit",
        True,
        WHITE
    )

    screen.blit(
        title,
        (
            WIDTH // 2 - title.get_width() // 2,
            220
        )
    )

    screen.blit(
        result,
        (
            WIDTH // 2 - result.get_width() // 2,
            290
        )
    )

    screen.blit(
        restart,
        (
            WIDTH // 2 - restart.get_width() // 2,
            350
        )
    )

    screen.blit(
        quit_text,
        (
            WIDTH // 2 - quit_text.get_width() // 2,
            390
        )
    )


# -------------------- STARTING COUNTDOWN --------------------

def countdown():

    for number in ["3", "2", "1", "GO!"]:

        start_time = pygame.time.get_ticks()

        while pygame.time.get_ticks() - start_time < 700:

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            draw_track()

            for bike in bikes:
                draw_bike(bike)

            text = BIG_FONT.render(
                number,
                True,
                YELLOW if number != "GO!" else GREEN
            )

            screen.blit(
                text,
                (
                    WIDTH // 2 - text.get_width() // 2,
                    HEIGHT // 2 - text.get_height() // 2
                )
            )

            pygame.display.flip()
            clock.tick(FPS)


# -------------------- MAIN GAME --------------------

def main():

    global race_finished

    running = True

    countdown()

    while running:

        # ---------------- EVENTS ----------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_r:

                    reset_game()
                    race_finished = False
                    countdown()

        # ---------------- UPDATE ----------------

        if not race_finished:

            keys = pygame.key.get_pressed()

            player.update_player(keys)

            for bot in bots:
                bot.update_ai(bikes)

            handle_collisions()

            check_finish()

        # ---------------- DRAW ----------------

        draw_track()

        # Draw bots first
        for bot in bots:
            draw_bike(bot)

        # Draw player
        draw_bike(player)

        draw_hud()

        if race_finished:
            draw_finish_screen()

        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


# -------------------- RUN --------------------

if __name__ == "__main__":
    main()
