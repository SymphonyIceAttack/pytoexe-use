import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

# Constants
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
K_COULOMB = 10**6
K_CONVERTER_ATTRACTION = 10**6
K_CONVERTER_REPULSION = 10**6
K_NEUTRAL_POSITIVE_ATTRACTION = 10**6
DT = 0.016
DAMPING = 1
MIN_DISTANCE = 10
PARTICLE_RADIUS_BASE = 8
CONVERTER_RADIUS = 12
WAVE_SPEED = 400
WAVE_LIFETIME = 60
NEUTRAL_DECOMPOSE_MIN = 600
NEUTRAL_DECOMPOSE_MAX = 1200
FUSION_SPEED_THRESHOLD = 200

class Wave:
    def __init__(self, x, y, vx, vy, color=(1.0, 1.0, 1.0)):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = WAVE_LIFETIME
        self.radius = 3.0
        self.max_radius = 20.0
        self.color = color
        
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= 1
        self.radius += 0.3
        
    def is_alive(self):
        return self.lifetime > 0
        
    def draw(self):
        alpha = self.lifetime / WAVE_LIFETIME
        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        
        glLineWidth(2.0 * alpha)
        glColor4f(self.color[0], self.color[1], self.color[2], alpha * 0.8)
        glBegin(GL_LINE_LOOP)
        for angle in range(0, 361, 30):
            rad = math.radians(angle)
            glVertex2f(self.radius * math.cos(rad), self.radius * math.sin(rad))
        glEnd()
        
        glColor4f(self.color[0], self.color[1], self.color[2], alpha * 0.3)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(0, 0)
        for angle in range(0, 361, 30):
            rad = math.radians(angle)
            glVertex2f(self.radius * 0.7 * math.cos(rad), self.radius * 0.7 * math.sin(rad))
        glEnd()
        
        glPopMatrix()

class Particle:
    def __init__(self, x, y, mass, charge, vx=0, vy=0):
        self.x = x
        self.y = y
        self.mass = mass
        self.charge = charge
        self.vx = vx
        self.vy = vy
        self.ax = 0
        self.ay = 0
        self.trail = []
        self.max_trail = 40
        self.radius = PARTICLE_RADIUS_BASE + mass * 2
        self.collision_flash = 0
        self.particle_type = self.determine_type()
        self.conversion_cooldown = 0
        self.flip_flash = 0
        self.decompose_timer = 0
        self.is_decomposing = False
        self.fusion_flash = 0
        
        if self.particle_type == "neutral":
            self.decompose_timer = random.randint(NEUTRAL_DECOMPOSE_MIN, NEUTRAL_DECOMPOSE_MAX)
        
    def determine_type(self):
        if self.mass == 1.0 and self.charge == 0:
            return "converter"
        elif self.charge > 0:
            return "positive"
        elif self.charge < 0:
            return "negative"
        elif self.charge == 0:
            return "neutral"
        return "neutral"
    
    def become_neutral(self):
        self.charge = 0
        self.particle_type = "neutral"
        self.collision_flash = 2.0
        self.radius = PARTICLE_RADIUS_BASE + self.mass * 1.5
        self.decompose_timer = random.randint(NEUTRAL_DECOMPOSE_MIN, NEUTRAL_DECOMPOSE_MAX)
        self.is_decomposing = False
    
    def become_converter(self):
        self.charge = 0
        self.mass = 1.0
        self.particle_type = "converter"
        self.radius = CONVERTER_RADIUS
        self.fusion_flash = 3.0
        self.collision_flash = 3.0
        self.is_decomposing = False
        self.decompose_timer = 0
    
    def flip_charge(self):
        self.charge = -self.charge
        self.particle_type = self.determine_type()
        self.flip_flash = 2.0
        self.collision_flash = 2.0
    
    def start_decomposing(self):
        self.is_decomposing = True
        self.decompose_timer = 60
    
    def update_trail(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)
    
    def apply_force(self, fx, fy):
        self.ax += fx / self.mass
        self.ay += fy / self.mass
    
    def update(self, dt):
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.vx *= DAMPING
        self.vy *= DAMPING
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.ax = 0
        self.ay = 0
        
        if self.conversion_cooldown > 0:
            self.conversion_cooldown -= 1
        
        if self.particle_type == "neutral" and not self.is_decomposing:
            self.decompose_timer -= 1
            if self.decompose_timer <= 0:
                self.start_decomposing()
        
        if self.is_decomposing:
            self.decompose_timer -= 1
            self.radius = PARTICLE_RADIUS_BASE + self.mass * 1.5 + math.sin(self.decompose_timer * 0.5) * 3
        
        bounce_factor = 0.85
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = abs(self.vx) * bounce_factor
            self.collision_flash = 1.0
        elif self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx = -abs(self.vx) * bounce_factor
            self.collision_flash = 1.0
            
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy = abs(self.vy) * bounce_factor
            self.collision_flash = 1.0
        elif self.y + self.radius > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.radius
            self.vy = -abs(self.vy) * bounce_factor
            self.collision_flash = 1.0
        
        self.collision_flash *= 0.9
        self.flip_flash *= 0.85
        self.fusion_flash *= 0.9
        self.update_trail()
    
    def draw(self):
        if len(self.trail) > 1:
            glBegin(GL_LINE_STRIP)
            for i, (tx, ty) in enumerate(self.trail):
                fade = i / len(self.trail)
                if self.particle_type == "positive":
                    glColor4f(1.0, 0.0, 0.0, 0.6 * fade)
                elif self.particle_type == "negative":
                    glColor4f(0.0, 0.0, 1.0, 0.6 * fade)
                elif self.particle_type == "converter":
                    if self.fusion_flash > 0.5:
                        glColor4f(1.0, 1.0, 0.5, 0.8 * fade)
                    else:
                        glColor4f(1.0, 1.0, 0.0, 0.6 * fade)
                elif self.particle_type == "neutral":
                    if self.is_decomposing:
                        glColor4f(1.0, 0.5, 0.0, 0.8 * fade)
                    else:
                        glColor4f(0.5, 0.5, 0.5, 0.6 * fade)
            glEnd()
        
        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        
        glBegin(GL_TRIANGLE_FAN)
        if self.particle_type == "positive":
            if self.flip_flash > 0.5:
                if int(self.flip_flash * 10) % 2 == 0:
                    glColor3f(1.0, 0.0, 0.0)
                else:
                    glColor3f(0.0, 0.0, 1.0)
            elif self.collision_flash > 0.1:
                glColor3f(1.0, 0.5, 0.5)
            else:
                glColor3f(1.0, 0.0, 0.0)
        elif self.particle_type == "negative":
            if self.flip_flash > 0.5:
                if int(self.flip_flash * 10) % 2 == 0:
                    glColor3f(0.0, 0.0, 1.0)
                else:
                    glColor3f(1.0, 0.0, 0.0)
            elif self.collision_flash > 0.1:
                glColor3f(0.5, 0.5, 1.0)
            else:
                glColor3f(0.0, 0.0, 1.0)
        elif self.particle_type == "converter":
            if self.fusion_flash > 1.0:
                hue = (self.fusion_flash * 5) % 1.0
                if hue < 0.33:
                    glColor3f(1.0, hue * 3, 0.0)
                elif hue < 0.66:
                    glColor3f(1.0 - (hue - 0.33) * 3, 1.0, 0.0)
                else:
                    glColor3f(0.0, 1.0, (hue - 0.66) * 3)
            elif self.collision_flash > 0.5:
                if int(self.collision_flash * 10) % 2 == 0:
                    glColor3f(1.0, 1.0, 1.0)
                else:
                    glColor3f(1.0, 0.5, 0.0)
            elif self.collision_flash > 0.1:
                glColor3f(1.0, 1.0, 0.5)
            else:
                glColor3f(1.0, 1.0, 0.0)
        elif self.particle_type == "neutral":
            if self.is_decomposing:
                pulse = (math.sin(self.decompose_timer * 0.3) + 1) / 2
                glColor3f(1.0, 0.5 + pulse * 0.5, 0.0 + pulse * 0.5)
            elif self.collision_flash > 0.5:
                glColor3f(1.0, 1.0, 1.0)
            elif self.collision_flash > 0.1:
                glColor3f(0.8, 0.8, 0.8)
            else:
                glColor3f(0.5, 0.5, 0.5)
        
        glVertex2f(0, 0)
        for angle in range(0, 361, 10):
            rad = math.radians(angle)
            glVertex2f(self.radius * math.cos(rad), self.radius * math.sin(rad))
        glEnd()
        
        glLineWidth(1.5)
        if self.particle_type == "positive":
            glColor3f(0.7, 0.0, 0.0)
        elif self.particle_type == "negative":
            glColor3f(0.0, 0.0, 0.7)
        elif self.particle_type == "converter":
            if self.fusion_flash > 1.0:
                glColor3f(1.0, 0.8, 0.0)
            else:
                glColor3f(0.7, 0.7, 0.0)
        elif self.particle_type == "neutral":
            if self.is_decomposing:
                glColor3f(1.0, 0.5, 0.0)
            else:
                glColor3f(0.3, 0.3, 0.3)
        
        glBegin(GL_LINE_LOOP)
        for angle in range(0, 361, 30):
            rad = math.radians(angle)
            glVertex2f(self.radius * math.cos(rad), self.radius * math.sin(rad))
        glEnd()
        
        glLineWidth(2.0)
        if self.particle_type == "positive":
            glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_LINES)
            glVertex2f(-self.radius * 0.5, 0)
            glVertex2f(self.radius * 0.5, 0)
            glVertex2f(0, -self.radius * 0.5)
            glVertex2f(0, self.radius * 0.5)
            glEnd()
        elif self.particle_type == "negative":
            glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_LINES)
            glVertex2f(-self.radius * 0.5, 0)
            glVertex2f(self.radius * 0.5, 0)
            glEnd()
        elif self.particle_type == "converter":
            glColor3f(0.0, 0.0, 0.0)
            glBegin(GL_LINES)
            glVertex2f(-self.radius * 0.35, -self.radius * 0.35)
            glVertex2f(self.radius * 0.35, self.radius * 0.35)
            glVertex2f(-self.radius * 0.35, self.radius * 0.35)
            glVertex2f(self.radius * 0.35, -self.radius * 0.35)
            glEnd()
        elif self.particle_type == "neutral" and self.is_decomposing:
            glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_LINES)
            glVertex2f(-self.radius * 0.4, -self.radius * 0.2)
            glVertex2f(-self.radius * 0.1, self.radius * 0.1)
            glVertex2f(self.radius * 0.1, -self.radius * 0.1)
            glVertex2f(self.radius * 0.4, self.radius * 0.2)
            glEnd()
        
        glPopMatrix()

class ElectromagneticSimulation:
    def __init__(self):
        self.particles = []
        self.waves = []
        self.selected_particle = None
        self.paused = False
        self.spawn_mode = None
        self.spawn_cooldown = 0
        self.show_menu = False
        
    def add_particle(self, x, y, mass, charge, vx=0, vy=0):
        self.particles.append(Particle(x, y, mass, charge, vx, vy))
    
    def add_converter_particle(self, x, y, vx=0, vy=0):
        particle = Particle(x, y, 1.0, 0, vx, vy)
        particle.particle_type = "converter"
        particle.radius = CONVERTER_RADIUS
        self.particles.append(particle)
    
    def create_wave(self, x, y, direction_x, direction_y, color=(1.0, 1.0, 1.0)):
        magnitude = math.sqrt(direction_x**2 + direction_y**2)
        if magnitude > 0:
            direction_x = direction_x / magnitude * WAVE_SPEED
            direction_y = direction_y / magnitude * WAVE_SPEED
        else:
            angle = random.uniform(0, 2 * math.pi)
            direction_x = math.cos(angle) * WAVE_SPEED
            direction_y = math.sin(angle) * WAVE_SPEED
        
        for i in range(3):
            offset_angle = random.uniform(-0.5, 0.5)
            wave_x = direction_x * math.cos(offset_angle) - direction_y * math.sin(offset_angle)
            wave_y = direction_x * math.sin(offset_angle) + direction_y * math.cos(offset_angle)
            self.waves.append(Wave(x, y, wave_x, wave_y, color))
    
    def create_fusion_waves(self, x, y):
        for i in range(12):
            wave_angle = (2 * math.pi * i) / 12
            wave_vx = math.cos(wave_angle) * WAVE_SPEED * 1.2
            wave_vy = math.sin(wave_angle) * WAVE_SPEED * 1.2
            self.waves.append(Wave(x, y, wave_vx, wave_vy, (1.0, 1.0, 0.0)))
    
    def decompose_neutral(self, neutral):
        x = neutral.x
        y = neutral.y
        mass = neutral.mass / 2
        
        angle = random.uniform(0, 2 * math.pi)
        speed = 150
        
        vx1 = math.cos(angle) * speed
        vy1 = math.sin(angle) * speed
        self.add_particle(x, y, mass, abs(neutral.mass * 0.5), vx1, vy1)
        
        vx2 = math.cos(angle + math.pi) * speed
        vy2 = math.sin(angle + math.pi) * speed
        self.add_particle(x, y, mass, -abs(neutral.mass * 0.5), vx2, vy2)
        
        for i in range(8):
            wave_angle = (2 * math.pi * i) / 8
            wave_vx = math.cos(wave_angle) * WAVE_SPEED * 0.7
            wave_vy = math.sin(wave_angle) * WAVE_SPEED * 0.7
            self.waves.append(Wave(x, y, wave_vx, wave_vy, (1.0, 0.5, 0.0)))
    
    def handle_converter_collision(self, converter, charged_particle):
        converter_x = converter.x
        converter_y = converter.y
        
        dx = charged_particle.x - converter.x
        dy = charged_particle.y - converter.y
        
        wave_dx = -dx
        wave_dy = -dy
        
        self.create_wave(converter_x, converter_y, wave_dx, wave_dy)
        
        charged_particle.flip_charge()
        converter.become_neutral()
    
    def handle_fusion(self, positive, negative):
        x = (positive.x + negative.x) / 2
        y = (positive.y + negative.y) / 2
        
        self.create_fusion_waves(x, y)
        
        if positive in self.particles:
            self.particles.remove(positive)
        if negative in self.particles:
            self.particles.remove(negative)
        
        self.add_converter_particle(x, y, 
                                   (positive.vx + negative.vx) / 2,
                                   (positive.vy + negative.vy) / 2)
    
    def check_particle_collisions(self):
        particles_to_fuse = []
        
        for i in range(len(self.particles)):
            for j in range(i + 1, len(self.particles)):
                p1 = self.particles[i]
                p2 = self.particles[j]
                
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                distance = math.sqrt(dx**2 + dy**2)
                
                min_dist = p1.radius + p2.radius
                
                if distance < min_dist and distance > 0:
                    if p1.particle_type == "positive" and p2.particle_type == "negative":
                        rel_speed = math.sqrt((p1.vx - p2.vx)**2 + (p1.vy - p2.vy)**2)
                        if rel_speed >= FUSION_SPEED_THRESHOLD:
                            particles_to_fuse.append((p1, p2))
                            continue
                    elif p2.particle_type == "positive" and p1.particle_type == "negative":
                        rel_speed = math.sqrt((p1.vx - p2.vx)**2 + (p1.vy - p2.vy)**2)
                        if rel_speed >= FUSION_SPEED_THRESHOLD:
                            particles_to_fuse.append((p2, p1))
                            continue
                    
                    if p1.particle_type == "converter" and p2.particle_type in ["positive", "negative"]:
                        if p1.conversion_cooldown <= 0:
                            self.handle_converter_collision(p1, p2)
                            p1.conversion_cooldown = 10
                        self.resolve_elastic_collision(p1, p2)
                    elif p2.particle_type == "converter" and p1.particle_type in ["positive", "negative"]:
                        if p2.conversion_cooldown <= 0:
                            self.handle_converter_collision(p2, p1)
                            p2.conversion_cooldown = 10
                        self.resolve_elastic_collision(p1, p2)
                    elif p1.particle_type == "converter" and p2.particle_type == "converter":
                        self.resolve_converter_repulsion(p1, p2)
                    else:
                        self.resolve_elastic_collision(p1, p2)
        
        for pos, neg in particles_to_fuse:
            self.handle_fusion(pos, neg)
    
    def resolve_converter_repulsion(self, c1, c2):
        dx = c2.x - c1.x
        dy = c2.y - c1.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            c1.x += random.uniform(-5, 5)
            c1.y += random.uniform(-5, 5)
            return
        
        nx = dx / distance
        ny = dy / distance
        
        repulsion_strength = 500.0
        impulse_magnitude = repulsion_strength / (distance * distance)
        
        c1.vx -= impulse_magnitude * nx
        c1.vy -= impulse_magnitude * ny
        c2.vx += impulse_magnitude * nx
        c2.vy += impulse_magnitude * ny
        
        min_dist = c1.radius + c2.radius
        overlap = min_dist - distance
        separation_x = nx * overlap * 0.5
        separation_y = ny * overlap * 0.5
        
        c1.x -= separation_x
        c1.y -= separation_y
        c2.x += separation_x
        c2.y += separation_y
        
        c1.collision_flash = 1.0
        c2.collision_flash = 1.0
    
    def resolve_elastic_collision(self, p1, p2):
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:
            return
        
        nx = dx / distance
        ny = dy / distance
        
        dvx = p2.vx - p1.vx
        dvy = p2.vy - p1.vy
        dv_normal = dvx * nx + dvy * ny
        
        if dv_normal > 0:
            return
        
        restitution = 0.9
        reduced_mass = (p1.mass * p2.mass) / (p1.mass + p2.mass)
        impulse_magnitude = -(1 + restitution) * dv_normal * reduced_mass
        
        impulse_x = impulse_magnitude * nx
        impulse_y = impulse_magnitude * ny
        
        p1.vx -= impulse_x / p1.mass
        p1.vy -= impulse_y / p1.mass
        p2.vx += impulse_x / p2.mass
        p2.vy += impulse_y / p2.mass
        
        min_dist = p1.radius + p2.radius
        overlap = min_dist - distance
        separation_x = nx * overlap * 0.5
        separation_y = ny * overlap * 0.5
        
        p1.x -= separation_x
        p1.y -= separation_y
        p2.x += separation_x
        p2.y += separation_y
        
        p1.collision_flash = 1.0
        p2.collision_flash = 1.0
    
    def calculate_forces(self):
        for p in self.particles:
            p.ax = 0
            p.ay = 0
        
        for i, p1 in enumerate(self.particles):
            for j, p2 in enumerate(self.particles):
                if i >= j:
                    continue
                
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < MIN_DISTANCE:
                    distance = MIN_DISTANCE
                
                if distance > 0:
                    dx /= distance
                    dy /= distance
                
                if p1.particle_type == "neutral" and p2.particle_type == "positive":
                    force_magnitude = K_NEUTRAL_POSITIVE_ATTRACTION / (distance**2)
                    p1.apply_force(force_magnitude * dx, force_magnitude * dy)
                    p2.apply_force(-force_magnitude * dx, -force_magnitude * dy)
                    continue
                elif p2.particle_type == "neutral" and p1.particle_type == "positive":
                    force_magnitude = K_NEUTRAL_POSITIVE_ATTRACTION / (distance**2)
                    p2.apply_force(-force_magnitude * dx, -force_magnitude * dy)
                    p1.apply_force(force_magnitude * dx, force_magnitude * dy)
                    continue
                
                if p1.particle_type == "converter" and p2.particle_type in ["positive", "negative"]:
                    force_magnitude = K_CONVERTER_ATTRACTION / (distance**2)
                    p1.apply_force(force_magnitude * dx, force_magnitude * dy)
                    p2.apply_force(-force_magnitude * dx, -force_magnitude * dy)
                    continue
                elif p2.particle_type == "converter" and p1.particle_type in ["positive", "negative"]:
                    force_magnitude = K_CONVERTER_ATTRACTION / (distance**2)
                    p2.apply_force(-force_magnitude * dx, -force_magnitude * dy)
                    p1.apply_force(force_magnitude * dx, force_magnitude * dy)
                    continue
                
                if p1.particle_type == "converter" and p2.particle_type == "converter":
                    force_magnitude = K_CONVERTER_REPULSION / (distance**2)
                    p1.apply_force(-force_magnitude * dx, -force_magnitude * dy)
                    p2.apply_force(force_magnitude * dx, force_magnitude * dy)
                    continue
                
                if (p1.particle_type in ["neutral", "converter"] and 
                    p2.particle_type in ["neutral", "converter"]):
                    continue
                
                if p1.particle_type in ["positive", "negative"] and p2.particle_type in ["positive", "negative"]:
                    force_magnitude = K_COULOMB * p1.charge * p2.charge / (distance**2)
                    p1.apply_force(-force_magnitude * dx, -force_magnitude * dy)
                    p2.apply_force(force_magnitude * dx, force_magnitude * dy)
    
    def update(self):
        if not self.paused and not self.show_menu:
            self.calculate_forces()
            self.check_particle_collisions()
            
            particles_to_remove = []
            for particle in self.particles:
                if particle.is_decomposing and particle.decompose_timer <= 0:
                    self.decompose_neutral(particle)
                    particles_to_remove.append(particle)
            
            for particle in particles_to_remove:
                if particle in self.particles:
                    self.particles.remove(particle)
            
            for particle in self.particles:
                particle.update(DT)
            
            for wave in self.waves:
                wave.update(DT)
            
            self.waves = [wave for wave in self.waves if wave.is_alive()]
            
            if self.spawn_cooldown > 0:
                self.spawn_cooldown -= 1
    
    def spawn_particle_at_center(self, particle_type):
        if self.spawn_cooldown > 0:
            return
        
        x = SCREEN_WIDTH // 2 + random.uniform(-50, 50)
        y = SCREEN_HEIGHT // 2 + random.uniform(-50, 50)
        
        if particle_type == "positive":
            mass = random.uniform(1.0, 3.0)
            charge = random.uniform(0.5, 2.0)
            self.add_particle(x, y, mass, charge, 
                            random.uniform(-100, 100),
                            random.uniform(-100, 100))
        elif particle_type == "negative":
            mass = random.uniform(1.0, 3.0)
            charge = -random.uniform(0.5, 2.0)
            self.add_particle(x, y, mass, charge,
                            random.uniform(-100, 100),
                            random.uniform(-100, 100))
        elif particle_type == "converter":
            self.add_converter_particle(x, y,
                                      random.uniform(-50, 50),
                                      random.uniform(-50, 50))
        
        self.spawn_cooldown = 10
    
    def draw_walls(self):
        glLineWidth(2.0)
        glColor3f(0.5, 0.5, 0.5)
        glBegin(GL_LINE_LOOP)
        glVertex2f(0, 0)
        glVertex2f(SCREEN_WIDTH, 0)
        glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT)
        glVertex2f(0, SCREEN_HEIGHT)
        glEnd()
    
    def draw_grid(self):
        glColor4f(0.15, 0.15, 0.15, 0.5)
        glLineWidth(0.5)
        glBegin(GL_LINES)
        grid_spacing = 100
        for x in range(0, SCREEN_WIDTH + 1, grid_spacing):
            glVertex2f(x, 0)
            glVertex2f(x, SCREEN_HEIGHT)
        for y in range(0, SCREEN_HEIGHT + 1, grid_spacing):
            glVertex2f(0, y)
            glVertex2f(SCREEN_WIDTH, y)
        glEnd()
    
    def draw(self):
        self.draw_grid()
        self.draw_walls()
        
        for wave in self.waves:
            wave.draw()
        
        for particle in self.particles:
            particle.draw()
    
    def handle_click(self, x, y):
        if self.show_menu:
            return
            
        for particle in self.particles:
            distance = math.sqrt((x - particle.x)**2 + (y - particle.y)**2)
            if distance < particle.radius * 1.5:
                self.selected_particle = particle
                return
        
        if self.spawn_mode == "positive":
            mass = random.uniform(1.0, 3.0)
            charge = random.uniform(0.5, 2.0)
            self.add_particle(x, y, mass, charge)
        elif self.spawn_mode == "negative":
            mass = random.uniform(1.0, 3.0)
            charge = -random.uniform(0.5, 2.0)
            self.add_particle(x, y, mass, charge)
        elif self.spawn_mode == "converter":
            self.add_converter_particle(x, y)

simulation = ElectromagneticSimulation()

def draw_text(x, y, text, color=(1.0, 1.0, 1.0)):
    glColor3f(color[0], color[1], color[2])
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))

def draw_menu():
    # Darken background
    glColor4f(0.0, 0.0, 0.0, 0.85)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(SCREEN_WIDTH, 0)
    glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT)
    glVertex2f(0, SCREEN_HEIGHT)
    glEnd()
    
    # Menu box - centered
    menu_w = 500
    menu_h = 650
    menu_x = (SCREEN_WIDTH - menu_w) // 2
    menu_y = (SCREEN_HEIGHT - menu_h) // 2
    
    # Menu background
    glColor4f(0.1, 0.1, 0.15, 0.95)
    glBegin(GL_QUADS)
    glVertex2f(menu_x, menu_y)
    glVertex2f(menu_x + menu_w, menu_y)
    glVertex2f(menu_x + menu_w, menu_y + menu_h)
    glVertex2f(menu_x, menu_y + menu_h)
    glEnd()
    
    # Menu border
    glLineWidth(3.0)
    glColor3f(0.3, 0.5, 0.8)
    glBegin(GL_LINE_LOOP)
    glVertex2f(menu_x, menu_y)
    glVertex2f(menu_x + menu_w, menu_y)
    glVertex2f(menu_x + menu_w, menu_y + menu_h)
    glVertex2f(menu_x, menu_y + menu_h)
    glEnd()
    
    # Title
    title_x = menu_x + (menu_w - 300) // 2
    draw_text(title_x, menu_y + menu_h - 50, "SIMULATION CONTROLS", (0.3, 0.7, 1.0))
    
    y_pos = menu_y + menu_h - 90
    line_spacing = 25
    
    sections = [
        ("SPAWNING", (1.0, 1.0, 0.0), [
            ("Z - Spawn positive particle", (1.0, 0.5, 0.5)),
            ("X - Spawn negative particle", (0.5, 0.5, 1.0)),
            ("C - Spawn converter particle", (1.0, 1.0, 0.5)),
        ]),
        ("SPAWN MODES", (1.0, 1.0, 0.0), [
            ("1 - Positive mode", (1.0, 0.5, 0.5)),
            ("2 - Negative mode", (0.5, 0.5, 1.0)),
            ("3 - Converter mode", (1.0, 1.0, 0.5)),
            ("0 - Clear spawn mode", (0.7, 0.7, 0.7)),
        ]),
        ("SIMULATION", (1.0, 1.0, 0.0), [
            ("SPACE - Pause/Resume", (0.7, 1.0, 0.7)),
            ("R - Add random particles", (1.0, 0.8, 0.5)),
            ("V - Clear all", (1.0, 0.5, 0.5)),
        ]),
        ("MOUSE", (1.0, 1.0, 0.0), [
            ("Left Click - Place/Select", (0.8, 0.8, 1.0)),
            ("Middle Click - Clear all", (0.8, 0.8, 1.0)),
            ("Drag - Move particle", (0.8, 0.8, 1.0)),
        ]),
        ("PARTICLES", (1.0, 1.0, 0.0), [
            ("RED (+) - Positive", (1.0, 0.3, 0.3)),
            ("BLUE (-) - Negative", (0.3, 0.3, 1.0)),
            ("YELLOW (X) - Converter", (1.0, 1.0, 0.3)),
            ("GRAY - Neutral", (0.6, 0.6, 0.6)),
        ]),
    ]
    
    for section_title, section_color, items in sections:
        draw_text(menu_x + 30, y_pos, section_title, section_color)
        y_pos -= line_spacing
        for item_text, item_color in items:
            draw_text(menu_x + 50, y_pos, item_text, item_color)
            y_pos -= line_spacing
        y_pos -= 5  # Extra space between sections
    
    # Bottom text
    draw_text(menu_x + 120, menu_y - 25, "PRESS ESC TO CLOSE", (1.0, 1.0, 1.0))

def init_gl():
    glClearColor(0.05, 0.05, 0.08, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    
    simulation.draw()
    draw_ui()
    
    if simulation.show_menu:
        draw_menu()
    
    glutSwapBuffers()

def draw_ui():
    if simulation.show_menu:
        return
        
    glLineWidth(2.0)
    
    # Spawn mode indicator background
    glColor4f(0.0, 0.0, 0.0, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 60)
    glVertex2f(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 60)
    glVertex2f(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10)
    glVertex2f(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 10)
    glEnd()
    
    # Spawn mode indicator
    if simulation.spawn_mode == "positive":
        glColor3f(1.0, 0.0, 0.0)
    elif simulation.spawn_mode == "negative":
        glColor3f(0.0, 0.0, 1.0)
    elif simulation.spawn_mode == "converter":
        glColor3f(1.0, 1.0, 0.0)
    else:
        glColor3f(0.5, 0.5, 0.5)
    
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(SCREEN_WIDTH - 170, SCREEN_HEIGHT - 35)
    for angle in range(0, 361, 10):
        rad = math.radians(angle)
        glVertex2f(SCREEN_WIDTH - 170 + 10 * math.cos(rad), 
                   SCREEN_HEIGHT - 35 + 10 * math.sin(rad))
    glEnd()
    
    # Help text
    draw_text(10, SCREEN_HEIGHT - 25, "ESC - Menu", (0.7, 0.7, 0.7))

def update(value):
    simulation.update()
    glutPostRedisplay()
    glutTimerFunc(int(DT * 1000), update, 0)

def keyboard(key, x, y):
    key = key.decode('utf-8').lower()
    
    if key == '\x1b':  # ESC key
        simulation.show_menu = not simulation.show_menu
        return
    
    if simulation.show_menu:
        return
    
    if key == ' ':
        simulation.paused = not simulation.paused
    elif key == 'v':
        simulation.particles.clear()
        simulation.waves.clear()
    elif key == 'r':
        for _ in range(5):
            x = random.uniform(100, SCREEN_WIDTH - 100)
            y = random.uniform(100, SCREEN_HEIGHT - 100)
            mass = random.uniform(0.5, 5.0)
            charge = random.choice([-1, 1]) * random.uniform(0.3, 3.0)
            simulation.add_particle(x, y, mass, charge,
                                  random.uniform(-150, 150),
                                  random.uniform(-150, 150))
    elif key == 'z':
        simulation.spawn_particle_at_center("positive")
    elif key == 'x':
        simulation.spawn_particle_at_center("negative")
    elif key == 'c':
        simulation.spawn_particle_at_center("converter")
    elif key == '1':
        simulation.spawn_mode = "positive"
    elif key == '2':
        simulation.spawn_mode = "negative"
    elif key == '3':
        simulation.spawn_mode = "converter"
    elif key == '0':
        simulation.spawn_mode = None

def mouse(button, state, x, y):
    if simulation.show_menu:
        return
        
    window_width = glutGet(GLUT_WINDOW_WIDTH)
    window_height = glutGet(GLUT_WINDOW_HEIGHT)
    
    sim_x = (x / window_width) * SCREEN_WIDTH
    sim_y = ((window_height - y) / window_height) * SCREEN_HEIGHT
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        simulation.handle_click(sim_x, sim_y)
    elif button == GLUT_LEFT_BUTTON and state == GLUT_UP:
        simulation.selected_particle = None
    elif button == GLUT_MIDDLE_BUTTON and state == GLUT_DOWN:
        simulation.particles.clear()
        simulation.waves.clear()

def motion(x, y):
    if simulation.show_menu:
        return
        
    window_width = glutGet(GLUT_WINDOW_WIDTH)
    window_height = glutGet(GLUT_WINDOW_HEIGHT)
    
    sim_x = (x / window_width) * SCREEN_WIDTH
    sim_y = ((window_height - y) / window_height) * SCREEN_HEIGHT
    
    if simulation.selected_particle:
        simulation.selected_particle.x = sim_x
        simulation.selected_particle.y = sim_y
        simulation.selected_particle.vx = 0
        simulation.selected_particle.vy = 0

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_ALPHA)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Electromagnetic Particle Simulation")
    
    init_gl()
    
    simulation.add_particle(400, 300, 2.0, 2.0, 0, 60)
    simulation.add_particle(800, 500, 3.0, -2.0, 0, -40)
    simulation.add_particle(1200, 400, 1.5, 1.5, -30, 0)
    simulation.add_particle(600, 700, 2.5, -2.5, 50, -30)
    simulation.add_converter_particle(960, 540, 0, 0)
    simulation.add_converter_particle(800, 400, 20, -20)
    
    glutDisplayFunc(display)
    glutTimerFunc(0, update, 0)
    glutKeyboardFunc(keyboard)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    
    print("=" * 60)
    print("ELECTROMAGNETIC PARTICLE SIMULATION")
    print("=" * 60)
    print("\nWindow Mode - {}x{}".format(WINDOW_WIDTH, WINDOW_HEIGHT))
    print("Simulation Area - {}x{}".format(SCREEN_WIDTH, SCREEN_HEIGHT))
    print("\nPress ESC to open controls menu")
    print("Close window or Alt+F4 to exit")
    print("=" * 60)
    
    glutMainLoop()

if __name__ == "__main__":
    main()