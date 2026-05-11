import math
import sys
from dataclasses import dataclass

import pygame

# ------------------------------------------------------------
# 2D car game with a spring-damper suspension model.
#
# Controls:
#   D / Right  - throttle
#   A / Left   - reverse throttle
#   Space      - brake
#   R          - reset car
#   Esc        - quit
#
# Install:
#   pip install pygame
# Run:
#   python realistic_suspension_car_game.py
# ------------------------------------------------------------

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1100, 650
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Car Suspension - spring/damper physics")
CLOCK = pygame.time.Clock()

FONT = pygame.font.SysFont("consolas", 18)
BIG_FONT = pygame.font.SysFont("consolas", 28, bold=True)

PPM = 72.0  # pixels per meter

# Physics constants. They are not random: values are roughly car-like,
# but tuned for a small arcade game.
G = 18.0                 # m/s^2, intentionally stronger for game feel
PHYSICS_DT = 1.0 / 120.0

CAR_MASS = 1150.0        # kg
CAR_INERTIA = 1850.0     # kg*m^2
BODY_LENGTH = 3.55       # m
BODY_HEIGHT = 0.78       # m
WHEELBASE = 2.65         # m
WHEEL_RADIUS = 0.34      # m

SUSPENSION_REST = 0.82   # m, free length
SUSPENSION_TRAVEL = 0.50 # m, max useful compression
SPRING_K = 62000.0       # N/m
DAMPER_C = 7600.0        # N*s/m
BUMPSTOP_K = 185000.0    # N/m after max travel
MAX_SUSP_FORCE = 98000.0 # N per wheel

ENGINE_FORCE = 7600.0    # N
REVERSE_FORCE = 4300.0   # N
BRAKE_FORCE = 14500.0    # N
ROLLING_RESIST = 95.0    # N per m/s
AIR_DRAG = 32.0          # N per (m/s)^2

# Visual colors
SKY = (147, 196, 235)
GRASS = (67, 143, 63)
DIRT = (96, 72, 49)
ROAD = (70, 72, 75)
ROAD_LINE = (210, 210, 190)
STONE = (90, 87, 82)
STONE_DARK = (55, 53, 51)
BODY = (190, 42, 36)
BODY_DARK = (108, 22, 20)
WINDOW = (95, 155, 190)
BLACK = (16, 16, 18)
WHITE = (240, 240, 235)
SPRING = (230, 210, 80)
SHOCK = (35, 35, 38)


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def sign(value):
    if value > 0.0:
        return 1.0
    if value < 0.0:
        return -1.0
    return 0.0


def rotate(v, angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return pygame.Vector2(v.x * c - v.y * s, v.x * s + v.y * c)


def cross_z_vec(omega, r):
    # 2D angular velocity omega around z crossed with vector r.
    return pygame.Vector2(-omega * r.y, omega * r.x)


@dataclass
class StoneObj:
    x: float
    radius: float

    def center_y(self, road):
        return road.base_height(self.x) + self.radius * 0.96


class Road:
    def __init__(self):
        self.stones = [
            StoneObj(8.4, 0.22),
            StoneObj(10.15, 0.29),
            StoneObj(18.4, 0.24),
            StoneObj(22.2, 0.34),
            StoneObj(31.6, 0.27),
            StoneObj(43.2, 0.38),
            StoneObj(49.8, 0.23),
        ]

    @staticmethod
    def smooth_bump(x, center, width, height):
        t = abs(x - center) / width
        if t >= 1.0:
            return 0.0
        # Smooth cosine bump.
        return height * 0.5 * (1.0 + math.cos(math.pi * t))

    def base_height(self, x):
        # A compact hand-built road profile. Keep it smooth; the stones provide sharp hits.
        y = 0.18 * math.sin(0.55 * x)
        y += 0.08 * math.sin(1.35 * x + 0.7)
        y += self.smooth_bump(x, 5.0, 2.0, 0.35)
        y += self.smooth_bump(x, 13.0, 3.8, -0.20)
        y += self.smooth_bump(x, 27.0, 5.2, 0.55)
        y += self.smooth_bump(x, 37.5, 3.6, -0.32)
        y += self.smooth_bump(x, 56.0, 6.0, 0.40)
        return y

    def surface_height(self, x):
        h = self.base_height(x)

        # Stones are circular caps sitting on the road.
        for stone in self.stones:
            dx = x - stone.x
            r = stone.radius
            if abs(dx) < r:
                cy = stone.center_y(self)
                cap = cy + math.sqrt(max(0.0, r * r - dx * dx))
                h = max(h, cap)
        return h

    def slope(self, x):
        eps = 0.03
        return (self.surface_height(x + eps) - self.surface_height(x - eps)) / (2.0 * eps)

    def tangent(self, x):
        t = pygame.Vector2(1.0, self.slope(x))
        if t.length_squared() == 0.0:
            return pygame.Vector2(1.0, 0.0)
        return t.normalize()


class Car:
    def __init__(self, road):
        self.road = road
        self.reset()

    def reset(self):
        start_x = 2.1
        self.pos = pygame.Vector2(start_x, self.road.surface_height(start_x) + 2.15)
        self.vel = pygame.Vector2(0.0, 0.0)
        self.angle = 0.0
        self.omega = 0.0
        self.wheel_spin = [0.0, 0.0]
        self.debug = []
        self.best_x = self.pos.x

    def local_to_world(self, local):
        return self.pos + rotate(local, self.angle)

    def point_velocity(self, world_point):
        r = world_point - self.pos
        return self.vel + cross_z_vec(self.omega, r)

    def apply_force(self, force, point, total):
        total["force"] += force
        r = point - self.pos
        total["torque"] += r.x * force.y - r.y * force.x

    def update(self, dt, throttle, brake):
        total = {
            "force": pygame.Vector2(0.0, -CAR_MASS * G),
            "torque": 0.0,
        }

        # Body drag in air. Tiny, but prevents infinite downhill stupidity.
        speed = self.vel.length()
        if speed > 0.001:
            total["force"] += -self.vel.normalize() * (AIR_DRAG * speed * speed)

        # Local basis of the car body.
        up = rotate(pygame.Vector2(0.0, 1.0), self.angle)
        down = -up

        rear_local = pygame.Vector2(-WHEELBASE * 0.5, -0.22)
        front_local = pygame.Vector2(WHEELBASE * 0.5, -0.22)
        anchors = [rear_local, front_local]

        suspension_results = []
        grounded_wheels = 0

        for i, local_anchor in enumerate(anchors):
            anchor = self.local_to_world(local_anchor)

            # Approximate wheel x under the angled suspension.
            probe = anchor + down * SUSPENSION_REST
            wheel_x = probe.x
            road_y = self.road.surface_height(wheel_x)
            wheel_center = pygame.Vector2(wheel_x, road_y + WHEEL_RADIUS)

            # Suspension length projected along the strut direction.
            length = (wheel_center - anchor).dot(down)
            compression = SUSPENSION_REST - length
            grounded = compression > 0.0

            force_mag = 0.0
            if grounded:
                grounded_wheels += 1
                useful_compression = clamp(compression, 0.0, SUSPENSION_TRAVEL)

                v_anchor = self.point_velocity(anchor)
                vertical_speed = v_anchor.dot(up)

                # Spring + damper.
                force_mag = SPRING_K * useful_compression - DAMPER_C * vertical_speed

                # Bump stop after travel is used.
                if compression > SUSPENSION_TRAVEL:
                    force_mag += BUMPSTOP_K * (compression - SUSPENSION_TRAVEL)

                force_mag = clamp(force_mag, 0.0, MAX_SUSP_FORCE)
                self.apply_force(up * force_mag, anchor, total)

                # Tire longitudinal force along the road tangent.
                tangent = self.road.tangent(wheel_x)
                contact_point = pygame.Vector2(wheel_x, road_y)

                v_contact = self.point_velocity(contact_point)
                v_long = v_contact.dot(tangent)

                if throttle >= 0.0:
                    drive = ENGINE_FORCE * throttle
                else:
                    drive = REVERSE_FORCE * throttle

                braking = 0.0
                if brake > 0.0 and abs(v_long) > 0.05:
                    braking = -sign(v_long) * BRAKE_FORCE * brake

                rolling = -ROLLING_RESIST * v_long

                # More vertical force means more available grip. Simple friction limit.
                mu = 1.18
                desired_tire = drive + braking + rolling
                tire_limit = mu * force_mag
                tire_force = clamp(desired_tire, -tire_limit, tire_limit)
                self.apply_force(tangent * tire_force, contact_point, total)

                # Wheel visual spin follows ground speed.
                self.wheel_spin[i] += (v_long / WHEEL_RADIUS) * dt
            else:
                wheel_center = anchor + down * SUSPENSION_REST
                self.wheel_spin[i] += throttle * 9.0 * dt

            suspension_results.append({
                "anchor": anchor,
                "wheel": wheel_center,
                "compression": max(0.0, compression),
                "force": force_mag,
                "grounded": grounded,
            })

        # Side-view "anti-pitch" stabilizer. Not a cheat: it imitates how suspension
        # geometry and weight transfer resist one end diving too much.
        if suspension_results[0]["grounded"] and suspension_results[1]["grounded"]:
            rear_c = suspension_results[0]["compression"]
            front_c = suspension_results[1]["compression"]
            transfer = clamp((front_c - rear_c) * 9500.0, -5200.0, 5200.0)
            self.apply_force(up * transfer, suspension_results[0]["anchor"], total)
            self.apply_force(-up * transfer, suspension_results[1]["anchor"], total)

        # Integrate rigid body.
        acc = total["force"] / CAR_MASS
        self.vel += acc * dt
        self.pos += self.vel * dt

        alpha = total["torque"] / CAR_INERTIA
        self.omega += alpha * dt
        self.omega *= 0.995
        self.angle += self.omega * dt

        # Keep the simulation sane after very hard hits.
        self.angle = clamp(self.angle, -1.15, 1.15)

        # Prevent the chassis from tunneling into the road.
        self.solve_body_ground_collision()

        self.debug = suspension_results
        self.best_x = max(self.best_x, self.pos.x)

    def solve_body_ground_collision(self):
        body_points = [
            pygame.Vector2(-BODY_LENGTH * 0.48, -BODY_HEIGHT * 0.50),
            pygame.Vector2(BODY_LENGTH * 0.48, -BODY_HEIGHT * 0.50),
            pygame.Vector2(-BODY_LENGTH * 0.40, BODY_HEIGHT * 0.36),
            pygame.Vector2(BODY_LENGTH * 0.38, BODY_HEIGHT * 0.34),
        ]

        max_penetration = 0.0
        for p in body_points:
            wp = self.local_to_world(p)
            ground = self.road.surface_height(wp.x)
            penetration = ground + 0.04 - wp.y
            if penetration > max_penetration:
                max_penetration = penetration

        if max_penetration > 0.0:
            self.pos.y += max_penetration
            if self.vel.y < 0.0:
                self.vel.y *= -0.16
            self.omega *= 0.72


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 1.4

    def update(self, target, road, dt):
        desired_x = target.pos.x + 3.0
        desired_y = road.surface_height(target.pos.x) + 1.35
        k = 1.0 - math.pow(0.002, dt)
        self.x += (desired_x - self.x) * k
        self.y += (desired_y - self.y) * k

    def world_to_screen(self, p):
        sx = int((p.x - self.x) * PPM + WIDTH * 0.42)
        sy = int(HEIGHT * 0.67 - (p.y - self.y) * PPM)
        return sx, sy


def draw_text(text, x, y, color=WHITE, font=FONT):
    surf = font.render(text, True, color)
    SCREEN.blit(surf, (x, y))


def draw_zigzag(start, end, teeth=7, amp=0.055):
    vec = end - start
    if vec.length_squared() < 0.001:
        return
    direction = vec.normalize()
    normal = pygame.Vector2(-direction.y, direction.x)
    pts = []
    for i in range(teeth + 1):
        t = i / teeth
        p = start.lerp(end, t)
        if 0 < i < teeth:
            p += normal * (amp if i % 2 else -amp)
        pts.append(camera.world_to_screen(p))
    pygame.draw.lines(SCREEN, SPRING, False, pts, 3)


def draw_road(road, camera):
    # Background
    SCREEN.fill(SKY)

    # Terrain polygon.
    left_x = camera.x - 10.0
    right_x = camera.x + 18.0
    samples = 170
    terrain = []
    road_line_points = []

    for i in range(samples + 1):
        x = left_x + (right_x - left_x) * i / samples
        y = road.base_height(x)
        p = pygame.Vector2(x, y)
        terrain.append(camera.world_to_screen(p))
        road_line_points.append(camera.world_to_screen(p))

    terrain.append((WIDTH + 80, HEIGHT + 80))
    terrain.append((-80, HEIGHT + 80))
    pygame.draw.polygon(SCREEN, GRASS, terrain)

    # Dirt under asphalt edge.
    dirt_points = []
    for i in range(samples + 1):
        x = left_x + (right_x - left_x) * i / samples
        dirt_points.append(camera.world_to_screen(pygame.Vector2(x, road.base_height(x) - 0.13)))
    dirt_poly = road_line_points + list(reversed(dirt_points))
    pygame.draw.polygon(SCREEN, DIRT, dirt_poly)

    # Road
    pygame.draw.lines(SCREEN, ROAD, False, road_line_points, 34)
    pygame.draw.lines(SCREEN, ROAD_LINE, False, road_line_points, 3)

    # Distance marks.
    for mark in range(-20, 100, 5):
        if left_x < mark < right_x:
            y = road.base_height(mark)
            p1 = camera.world_to_screen(pygame.Vector2(mark, y + 0.05))
            p2 = camera.world_to_screen(pygame.Vector2(mark, y - 0.10))
            pygame.draw.line(SCREEN, ROAD_LINE, p1, p2, 2)

    # Stones
    for stone in road.stones:
        if left_x - 1.0 < stone.x < right_x + 1.0:
            cy = stone.center_y(road)
            center = camera.world_to_screen(pygame.Vector2(stone.x, cy))
            radius = max(2, int(stone.radius * PPM))
            pygame.draw.circle(SCREEN, STONE_DARK, center, radius + 2)
            pygame.draw.circle(SCREEN, STONE, center, radius)
            highlight = camera.world_to_screen(pygame.Vector2(stone.x - stone.radius * 0.23, cy + stone.radius * 0.22))
            pygame.draw.circle(SCREEN, (125, 121, 112), highlight, max(2, int(radius * 0.23)))


def draw_car(car, camera):
    # Suspension and wheels first.
    for i, info in enumerate(car.debug):
        anchor = info["anchor"]
        wheel = info["wheel"]
        compression_ratio = clamp(info["compression"] / SUSPENSION_TRAVEL, 0.0, 1.0)

        pygame.draw.line(SCREEN, SHOCK, camera.world_to_screen(anchor), camera.world_to_screen(wheel), 5)
        spring_start = anchor.lerp(wheel, 0.18)
        spring_end = anchor.lerp(wheel, 0.82)
        draw_zigzag(spring_start, spring_end, teeth=8, amp=0.045)

        wc = camera.world_to_screen(wheel)
        radius = int(WHEEL_RADIUS * PPM)
        pygame.draw.circle(SCREEN, BLACK, wc, radius)
        pygame.draw.circle(SCREEN, (38, 38, 42), wc, int(radius * 0.73))
        pygame.draw.circle(SCREEN, (190, 190, 185), wc, int(radius * 0.30))

        # Spokes show wheel rotation.
        spin = car.wheel_spin[i]
        for a in (spin, spin + math.pi * 0.5):
            spoke = pygame.Vector2(math.cos(a), math.sin(a)) * WHEEL_RADIUS * 0.78
            p1 = camera.world_to_screen(wheel - spoke)
            p2 = camera.world_to_screen(wheel + spoke)
            pygame.draw.line(SCREEN, (205, 205, 200), p1, p2, 3)

        # Tiny compression bar.
        bar_top = pygame.Vector2(wheel.x + 0.46, wheel.y + 0.45)
        bar_bottom = pygame.Vector2(wheel.x + 0.46, wheel.y - 0.05)
        pygame.draw.line(SCREEN, WHITE, camera.world_to_screen(bar_bottom), camera.world_to_screen(bar_top), 2)
        filled = bar_bottom.lerp(bar_top, compression_ratio)
        pygame.draw.line(SCREEN, SPRING, camera.world_to_screen(bar_bottom), camera.world_to_screen(filled), 4)

    # Body shape.
    body_poly_local = [
        pygame.Vector2(-1.86, -0.38),
        pygame.Vector2(-1.55, 0.28),
        pygame.Vector2(-0.52, 0.43),
        pygame.Vector2(0.25, 0.58),
        pygame.Vector2(1.37, 0.34),
        pygame.Vector2(1.80, -0.12),
        pygame.Vector2(1.63, -0.40),
    ]
    body_poly = [camera.world_to_screen(car.local_to_world(p)) for p in body_poly_local]
    pygame.draw.polygon(SCREEN, BODY_DARK, body_poly)
    pygame.draw.polygon(SCREEN, BODY, body_poly[:-1])
    pygame.draw.lines(SCREEN, BLACK, True, body_poly, 3)

    # Cabin / windows.
    cabin_local = [
        pygame.Vector2(-0.55, 0.38),
        pygame.Vector2(0.13, 0.54),
        pygame.Vector2(0.92, 0.34),
        pygame.Vector2(0.55, 0.05),
        pygame.Vector2(-0.42, 0.07),
    ]
    cabin = [camera.world_to_screen(car.local_to_world(p)) for p in cabin_local]
    pygame.draw.polygon(SCREEN, WINDOW, cabin)
    pygame.draw.lines(SCREEN, BLACK, True, cabin, 2)

    # Hood line.
    p1 = camera.world_to_screen(car.local_to_world(pygame.Vector2(0.92, 0.03)))
    p2 = camera.world_to_screen(car.local_to_world(pygame.Vector2(1.56, -0.10)))
    pygame.draw.line(SCREEN, BODY_DARK, p1, p2, 3)


def draw_ui(car, throttle, brake):
    pygame.draw.rect(SCREEN, (18, 20, 23), (12, 12, 425, 118), border_radius=8)
    draw_text("D/Right - газ | A/Left - назад | Space - тормоз | R - reset", 24, 24)
    draw_text(f"speed: {car.vel.x * 3.6:6.1f} km/h   x: {car.pos.x:5.1f} m   best: {car.best_x:5.1f} m", 24, 50)
    draw_text(f"body angle: {math.degrees(car.angle):6.1f} deg   angular vel: {car.omega:5.2f}", 24, 76)

    if len(car.debug) == 2:
        rear = car.debug[0]["compression"]
        front = car.debug[1]["compression"]
        draw_text(f"suspension compression: rear {rear:4.2f} m | front {front:4.2f} m", 24, 102)

    # Pedal indicators.
    x, y = WIDTH - 180, 22
    pygame.draw.rect(SCREEN, (18, 20, 23), (x - 12, y - 10, 164, 82), border_radius=8)
    draw_text("pedals", x, y - 4)
    pygame.draw.rect(SCREEN, (70, 70, 75), (x, y + 24, 56, 16))
    pygame.draw.rect(SCREEN, (80, 190, 80), (x, y + 24, int(56 * abs(throttle)), 16))
    pygame.draw.rect(SCREEN, (70, 70, 75), (x + 75, y + 24, 56, 16))
    pygame.draw.rect(SCREEN, (210, 80, 70), (x + 75, y + 24, int(56 * brake), 16))
    draw_text("gas", x, y + 45)
    draw_text("brake", x + 75, y + 45)


road = Road()
car = Car(road)
camera = Camera()


def main():
    global camera

    accumulator = 0.0
    running = True

    while running:
        frame_dt = min(0.05, CLOCK.tick(60) / 1000.0)
        accumulator += frame_dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    car.reset()

        keys = pygame.key.get_pressed()

        throttle = 0.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            throttle += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            throttle -= 0.75

        brake = 1.0 if keys[pygame.K_SPACE] else 0.0

        while accumulator >= PHYSICS_DT:
            car.update(PHYSICS_DT, throttle, brake)
            camera.update(car, road, PHYSICS_DT)
            accumulator -= PHYSICS_DT

        # Auto reset if the car somehow escapes the universe.
        if car.pos.y < -8.0 or abs(car.pos.x) > 180.0:
            car.reset()

        draw_road(road, camera)
        draw_car(car, camera)
        draw_ui(car, throttle, brake)

        # Finish hint.
        if car.pos.x > 58.0:
            txt = BIG_FONT.render("Road complete. Press R to run it again.", True, WHITE)
            SCREEN.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 150))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
