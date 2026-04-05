import pygame
import math
import random

# Инициализация BEAT 2
pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF)
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)

# Цвета
BLACK, CYAN, RED = (2, 2, 10), (0, 255, 255), (255, 30, 60)
WHITE, YELLOW = (255, 255, 255), (255, 220, 0)
GREEN, PURPLE, ORANGE = (50, 255, 50), (200, 50, 255), (255, 150, 0)


def create_glow_circle(radius, color, alpha):
    if radius <= 0: radius = 1
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for i in range(radius, 0, -3):
        current_alpha = int(alpha * (1 - i / radius) ** 2)
        pygame.draw.circle(surf, (*color, current_alpha), (radius, radius), i)
    return surf


class SmashRing:
    def __init__(self, x, y, color, growth=22):
        self.x, self.y, self.radius, self.alpha, self.color, self.growth = x, y, 10, 255, color, growth

    def update(self, dt_mult):
        self.radius += self.growth * dt_mult
        self.alpha -= 9 * dt_mult
        return self.alpha > 0

    def draw(self, surface, ox, oy):
        if self.radius <= 0: return
        s = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, max(0, int(self.alpha))), (int(self.radius), int(self.radius)),
                           int(self.radius), max(1, int(self.alpha // 15)))
        surface.blit(s, (int(self.x - self.radius + ox), int(self.y - self.radius + oy)),
                     special_flags=pygame.BLEND_RGB_ADD)


class FloatingText:
    def __init__(self, x, y, text, color):
        self.x, self.y, self.text, self.color, self.alpha = x, y, text, color, 255
        self.font = pygame.font.SysFont("Impact", 65)

    def update(self, dt_mult):
        self.y -= 3 * dt_mult;
        self.alpha -= 10 * dt_mult
        return self.alpha > 0

    def draw(self, surface):
        t = self.font.render(self.text, True, self.color)
        t.set_alpha(int(max(0, self.alpha)))
        surface.blit(t, (int(self.x - t.get_width() // 2), int(self.y)))


class Particle:
    def __init__(self, x, y, color, speed_mult=1.0):
        self.x, self.y, self.color, self.life = x, y, color, 255
        a = random.uniform(0, 6.28);
        s = random.uniform(5, 18) * speed_mult
        self.vx, self.vy = math.cos(a) * s, math.sin(a) * s

    def update(self, dt_mult):
        self.x += self.vx * dt_mult;
        self.y += self.vy * dt_mult
        self.vx *= 0.94;
        self.vy *= 0.94;
        self.life -= 7 * dt_mult
        return self.life > 0

    def draw(self, surface):
        if self.life <= 0: return
        s = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(self.life)), (5, 5), 5)
        surface.blit(s, (int(self.x - 5), int(self.y - 5)), special_flags=pygame.BLEND_RGB_ADD)


class Beat:
    def __init__(self, b_type, order, existing):
        self.type, self.order, self.radius, self.hold_progress, self.is_touching = b_type, order, 65, 0.0, False
        self.spawn_scale = 0.0
        if b_type == "speed":
            self.color = GREEN
        elif b_type == "slow":
            self.color = PURPLE
        elif b_type == "reset":
            self.color = ORANGE
        else:
            self.color = RED if b_type == "red" else (CYAN if b_type == "blue" else YELLOW)
        for _ in range(100):
            self.x, self.y = random.randint(200, WIDTH - 200), random.randint(200, HEIGHT - 200)
            if all(math.hypot(self.x - o.x, self.y - o.y) > 220 for o in existing): break

    def update_anim(self, dt_mult):
        if self.spawn_scale < 1.0: self.spawn_scale += 0.08 * dt_mult

    def draw(self, surface, ox, oy, font):
        c = WHITE if self.is_touching else self.color
        r = int(self.radius * self.spawn_scale)
        if r <= 0: return
        glow = create_glow_circle(int(r * 1.8), c, 140)
        surface.blit(glow, glow.get_rect(center=(int(self.x + ox), int(self.y + oy))),
                     special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.circle(surface, c, (int(self.x + ox), int(self.y + oy)), r, 5)
        txt = font.render(str(self.order), True, WHITE)
        surface.blit(txt, (int(self.x + ox - txt.get_width() // 2), int(self.y + oy - txt.get_height() // 2)))
        if self.type == "yellow" and self.hold_progress > 0:
            pygame.draw.arc(surface, WHITE, (
            int(self.x - 80 * self.spawn_scale + ox), int(self.y - 80 * self.spawn_scale + oy),
            int(160 * self.spawn_scale), int(160 * self.spawn_scale)), 0, self.hold_progress * 6.28, 8)


class Player:
    def __init__(self):
        self.x, self.y, self.core_r, self.glow_r, self.history = WIDTH // 2, HEIGHT // 2, 14, 52, []
        self.color, self.timer, self.smash_timer = CYAN, 1.0, 0

    def update(self, mx, my, is_holding, dt_mult, dead_anim=False):
        if not dead_anim:
            self.x += (mx - self.x) * 0.22;
            self.y += (my - self.y) * 0.22
            self.history.insert(0, (self.x, self.y))
            if len(self.history) > 22: self.history.pop()
            if not is_holding: self.timer -= 0.006 * dt_mult
        if self.smash_timer > 0: self.smash_timer -= 1

    def draw(self, surface, ox, oy):
        color = RED if self.smash_timer > 0 else CYAN
        for i, pos in enumerate(reversed(self.history)):
            px, py = pos
            f = i / len(self.history);
            glow = create_glow_circle(int(self.glow_r * f), color, int(180 * f))
            surface.blit(glow, glow.get_rect(center=(int(px + ox), int(py + oy))), special_flags=pygame.BLEND_RGB_ADD)
        t_w = 85
        if self.timer > 0:
            pygame.draw.rect(surface, (40, 40, 40), (int(self.x - t_w // 2), int(self.y - 75), t_w, 10))
            pygame.draw.rect(surface, (CYAN if self.timer > 0.3 else RED),
                             (int(self.x - t_w // 2), int(self.y - 75), int(t_w * max(0, self.timer)), 10))
        pygame.draw.circle(surface, WHITE, (int(self.x + ox), int(self.y + oy)), self.core_r)


def spawn_logic(combo):
    beats = []
    if combo < 5:
        beats.append(Beat("red", 1, []))
    elif combo < 10:
        b1 = Beat("red", 1, []);
        beats.extend([b1, Beat("blue", 2, [b1])])
    elif combo < 15:
        beats.append(Beat("yellow", 1, []))
    elif combo < 20:
        sc = random.choice(["all", "r_b", "y_b"])
        if sc == "all":
            b1 = Beat("red", 1, []);
            b2 = Beat("blue", 2, [b1])
            beats.extend([b1, b2, Beat("yellow", 3, [b1, b2])])
        elif sc == "r_b":
            b1 = Beat("red", 1, []);
            beats.extend([b1, Beat("blue", 2, [b1])])
        else:
            b1 = Beat("blue", 1, []);
            beats.extend([b1, Beat("yellow", 2, [b1])])
    else:
        if random.random() < 0.35:
            beats.append(Beat(random.choice(["speed", "slow", "reset"]), 2, []))
        else:
            b1 = Beat("red", 1, []);
            b2 = Beat("blue", 2, [b1])
            beats.extend([b1, b2, Beat("yellow", 3, [b1, b2])])
    beats.sort(key=lambda x: 0 if x.type == "blue" else (2 if x.type in ["yellow", "speed", "slow", "reset"] else 1))
    for i, b in enumerate(beats):
        if b.type not in ["speed", "slow", "reset"]: b.order = i + 1
    return beats


def main():
    best_combo = 0
    font_m, font_b, font_s = pygame.font.SysFont("Impact", 160), pygame.font.SysFont("Impact", 55), pygame.font.SysFont(
        "Impact", 90)

    while True:
        player, beats = Player(), spawn_logic(0)
        particles, rings, texts, bg_flash = [], [], [], [0, 0, 0]
        combo, shake, state, dt_mult = 0, 0, "countdown", 1.0
        start_ticks = pygame.time.get_ticks()

        while state != "restart":
            mx, my = pygame.mouse.get_pos();
            m_down = pygame.mouse.get_pressed()[0]
            ox = random.randint(-shake, shake) if shake > 0 else 0
            oy = random.randint(-shake, shake) if shake > 0 else 0
            if shake > 0: shake -= 1

            bg_flash = [max(0, c - 15) for c in bg_flash]
            screen.fill((bg_flash[0] // 6, bg_flash[1] // 6, bg_flash[2] // 6))

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                        event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE): pygame.quit(); return
                if state == "playing" and event.type == pygame.MOUSEBUTTONDOWN and beats:
                    curr = beats[0]
                    dist = math.hypot(player.x - curr.x, player.y - curr.y)
                    if dist < (player.glow_r + curr.radius):
                        if curr.type == "red":
                            msg = "BOOM!" if dist < (player.core_r + curr.radius) else "SMASH"
                            texts.append(FloatingText(curr.x, curr.y, msg, YELLOW if msg == "BOOM!" else CYAN))
                            rings.append(SmashRing(curr.x, curr.y, WHITE));
                            bg_flash = [100, 100, 255]
                            for _ in range(35): particles.append(Particle(curr.x, curr.y, RED))
                            beats.pop(0);
                            combo += 1;
                            player.timer, player.smash_timer, shake = 1.0, 12, 25
                        elif curr.type in ["speed", "slow", "reset"]:
                            curr.order -= 1;
                            shake = 15;
                            player.smash_timer = 5
                            if curr.order == 1: texts.append(FloatingText(curr.x, curr.y, "1", WHITE))
                            if curr.order <= 0:
                                bg_flash = [200, 200, 200]
                                if curr.type == "speed":
                                    dt_mult = 1.5
                                elif curr.type == "slow":
                                    dt_mult = 0.6
                                elif curr.type == "reset":
                                    dt_mult = 1.0
                                rings.append(SmashRing(curr.x, curr.y, curr.color, 40))
                                beats.pop(0);
                                combo += 3;
                                player.timer = 1.0
                        if not beats: beats = spawn_logic(combo)
                    else:
                        if not any(b.type == "blue" for b in beats): combo = 0
                elif state == "dead" and event.type == pygame.MOUSEBUTTONDOWN:
                    state = "restart"

            if state == "countdown":
                cd = 3 - (pygame.time.get_ticks() - start_ticks) // 1000
                if cd <= 0: state = "playing"
                t = font_m.render(str(max(1, cd)), True, WHITE)
                screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - t.get_height() // 2))

            elif state == "playing":
                is_holding = False
                for b in beats[:]:
                    b.update_anim(dt_mult)
                    dist = math.hypot(player.x - b.x, player.y - b.y)
                    b.is_touching = dist < (player.glow_r + b.radius)
                    if b.type == "blue" and b.is_touching:
                        texts.append(FloatingText(b.x, b.y, "TOUCH", CYAN))
                        rings.append(SmashRing(b.x, b.y, CYAN, 12));
                        bg_flash = [0, 200, 255]
                        beats.remove(b);
                        player.timer = min(1.0, player.timer + 0.25)
                        if not beats: beats = spawn_logic(combo)
                        break
                    elif b.type == "yellow" and b.is_touching and m_down and b == beats[0]:
                        is_holding = True;
                        b.hold_progress += 0.025 * dt_mult
                        bg_flash = [int(255 * b.hold_progress), int(220 * b.hold_progress), 0]
                        if b.hold_progress >= 1.0:
                            texts.append(FloatingText(b.x, b.y, "ULTRA!", YELLOW))
                            rings.append(SmashRing(b.x, b.y, YELLOW, 55));
                            bg_flash = [255, 220, 0]
                            for _ in range(60): particles.append(Particle(b.x, b.y, YELLOW, 3.0))
                            beats.pop(0);
                            combo += 2;
                            player.timer, shake = 1.0, 50
                            if not beats: beats = spawn_logic(combo)
                player.update(mx, my, is_holding, dt_mult)
                if player.timer <= 0: state = "death_shake"

            elif state == "death_shake":
                shake = 20;
                player.x += random.randint(-15, 15);
                player.y += random.randint(-15, 15)
                if pygame.time.get_ticks() % 500 < 20:
                    state = "dead";
                    bg_flash = [255, 0, 0];
                    shake = 80
                    rings.append(SmashRing(player.x, player.y, RED, 80))
                    for _ in range(120): particles.append(Particle(player.x, player.y, RED, 5.0))

            if state == "dead":
                if combo > best_combo: best_combo = combo
                d_t, s_t, b_t = font_s.render("YOU EXPLODED!", True, RED), font_b.render(
                    f"COMBO: {combo} | BEST: {best_combo}", True, WHITE), font_b.render("CLICK TO RESTART", True, CYAN)
                screen.blit(d_t, (WIDTH // 2 - d_t.get_width() // 2, HEIGHT // 2 - 100));
                screen.blit(s_t, (WIDTH // 2 - s_t.get_width() // 2, HEIGHT // 2));
                screen.blit(b_t, (WIDTH // 2 - b_t.get_width() // 2, HEIGHT // 2 + 100))

            if state in ["playing", "countdown", "death_shake"]:
                for r in rings: r.draw(screen, ox, oy)
                for b in beats: b.draw(screen, ox, oy, font_b)
                for p in particles: p.draw(screen)
                player.draw(screen, ox, oy)
                for t in texts: t.draw(screen)
                if combo > 0:
                    c_txt = font_b.render(f"x{combo}", True, WHITE)
                    screen.blit(c_txt, (WIDTH // 2 - c_txt.get_width() // 2, 80))

            particles = [p for p in particles if p.update(dt_mult)];
            rings = [r for r in rings if r.update(dt_mult)];
            texts = [t for t in texts if t.update(dt_mult)]
            pygame.display.flip();
            clock.tick(60)


if __name__ == "__main__": main()
