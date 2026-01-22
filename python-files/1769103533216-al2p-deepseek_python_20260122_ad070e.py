"""
Premium Bike Racing Game - "Isuru" Edition
Apple-inspired UI with Sinhala loading screen
"""

import pygame
import sys
import math
import random
from pygame.locals import *

# Initialize pygame
pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
ROAD_WIDTH = 800
CAR_WIDTH = 60
CAR_HEIGHT = 120

# Premium Apple-inspired color palette
COLORS = {
    "space_gray": (40, 40, 46),
    "silver": (210, 210, 215),
    "matte_black": (28, 28, 30),
    "pure_white": (245, 245, 247),
    "apple_red": (255, 59, 48),
    "apple_blue": (0, 122, 255),
    "apple_green": (52, 199, 89),
    "dark_gray": (22, 22, 24),
    "neon_cyan": (50, 173, 230),
    "neon_pink": (255, 55, 95)
}

# Sinhala text for loading screen (ඉසුරු)
SINHALA_TEXT = "ඉසුරු"

class Particle:
    """Premium particle effects"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(2, 6)
        self.color = random.choice([COLORS["neon_cyan"], COLORS["neon_pink"], COLORS["apple_blue"]])
        self.speed = random.uniform(1, 3)
        self.angle = random.uniform(0, 2 * math.pi)
        
    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.size *= 0.97
        return self.size > 0.5
        
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))

class PremiumButton:
    """Apple-style glassmorphism button"""
    def __init__(self, x, y, width, height, text, color=COLORS["apple_blue"]):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = self._lighten_color(color, 30)
        self.current_color = color
        self.font = pygame.font.Font(None, 36)
        self.glow = 0
        self.hovered = False
        
    def _lighten_color(self, color, amount):
        return tuple(min(255, c + amount) for c in color)
    
    def draw(self, screen):
        # Glass effect
        surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Base with blur effect
        pygame.draw.rect(surf, (*self.current_color, 180), 
                        surf.get_rect(), border_radius=15)
        
        # White overlay for glass effect
        overlay = pygame.Surface((self.rect.width, self.rect.height//3), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 60))
        surf.blit(overlay, (0, 0))
        
        # Border
        pygame.draw.rect(surf, (*self._lighten_color(self.current_color, 50), 200), 
                        surf.get_rect(), width=3, border_radius=15)
        
        screen.blit(surf, self.rect)
        
        # Text
        text_surf = self.font.render(self.text, True, COLORS["pure_white"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        target_color = self.hover_color if self.hovered else self.color
        
        # Smooth color transition
        self.current_color = tuple(
            int(self.current_color[i] + (target_color[i] - self.current_color[i]) * 0.2)
            for i in range(3)
        )
        
        return self.hovered
    
    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.hovered and mouse_pressed[0]

class PremiumGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ඉසුරු - Premium Bike Racing")
        self.clock = pygame.time.Clock()
        
        # Game states
        self.game_state = "loading"  # loading, menu, playing, game_over
        self.loading_progress = 0
        self.particles = []
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.sinhala_font = pygame.font.Font(None, 120)  # Large for Sinhala
        
        # Game elements
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT - 200
        self.player_speed = 0
        self.road_offset = 0
        self.obstacles = []
        self.score = 0
        self.game_speed = 5
        
        # Buttons
        self.play_button = PremiumButton(SCREEN_WIDTH//2 - 100, 400, 200, 60, "START RACE")
        self.quit_button = PremiumButton(SCREEN_WIDTH//2 - 100, 500, 200, 60, "QUIT", COLORS["apple_red"])
        self.restart_button = PremiumButton(SCREEN_WIDTH//2 - 100, 400, 200, 60, "RESTART")
        
        # Load sounds
        self.load_sounds()
        
    def load_sounds(self):
        """Initialize game sounds"""
        try:
            pygame.mixer.init()
            self.engine_sound = pygame.mixer.Sound(self.create_beep_sound())
            self.engine_sound.set_volume(0.3)
            self.crash_sound = pygame.mixer.Sound(self.create_crash_sound())
        except:
            self.engine_sound = None
            self.crash_sound = None
    
    def create_beep_sound(self):
        """Generate engine sound"""
        import numpy as np
        sample_rate = 22050
        duration = 0.1
        frames = int(duration * sample_rate)
        arr = np.random.randint(-32768, 32767, frames, dtype=np.int16)
        return pygame.sndarray.make_sound(arr)
    
    def create_crash_sound(self):
        """Generate crash sound"""
        import numpy as np
        sample_rate = 22050
        duration = 0.3
        frames = int(duration * sample_rate)
        arr = np.zeros(frames, dtype=np.int16)
        for i in range(frames):
            arr[i] = int(32767 * math.exp(-i/1000) * math.sin(0.1 * i) * random.uniform(-1, 1))
        return pygame.sndarray.make_sound(arr)
    
    def show_loading_screen(self):
        """Premium Apple-style loading screen with Sinhala text"""
        self.screen.fill(COLORS["matte_black"])
        
        # Animated gradient background
        for y in range(0, SCREEN_HEIGHT, 20):
            color_value = int(150 + 100 * math.sin(self.loading_progress * 0.01 + y * 0.01))
            pygame.draw.rect(self.screen, (color_value//3, color_value//3, color_value), 
                           (0, y, SCREEN_WIDTH, 20))
        
        # Sinhala text with glow effect
        glow_intensity = abs(math.sin(self.loading_progress * 0.05)) * 20
        text_surf = self.sinhala_font.render(SINHALA_TEXT, True, COLORS["neon_cyan"])
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        
        # Glow effect
        for i in range(10, 0, -1):
            glow_surf = pygame.Surface(text_rect.inflate(i*4, i*4).size, pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*COLORS["neon_cyan"], 20), 
                           glow_surf.get_rect(), border_radius=20)
            glow_pos = (text_rect.x - i*2, text_rect.y - i*2)
            self.screen.blit(glow_surf, glow_pos)
        
        self.screen.blit(text_surf, text_rect)
        
        # Subtitle
        sub_surf = self.title_font.render("PREMIUM BIKE RACING", True, COLORS["pure_white"])
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
        self.screen.blit(sub_surf, sub_rect)
        
        # Loading bar (Apple style)
        bar_width = 400
        bar_height = 20
        bar_x = SCREEN_WIDTH//2 - bar_width//2
        bar_y = SCREEN_HEIGHT//2 + 150
        
        # Background
        pygame.draw.rect(self.screen, (100, 100, 120), 
                        (bar_x, bar_y, bar_width, bar_height), border_radius=10)
        
        # Progress
        progress_width = int(bar_width * (self.loading_progress / 100))
        gradient_surf = pygame.Surface((progress_width, bar_height))
        for x in range(progress_width):
            alpha = int(255 * (0.5 + 0.5 * math.sin(x * 0.1 + self.loading_progress * 0.1)))
            pygame.draw.line(gradient_surf, (*COLORS["apple_blue"], alpha), 
                           (x, 0), (x, bar_height))
        gradient_surf.set_alpha(200)
        self.screen.blit(gradient_surf, (bar_x, bar_y))
        
        # Border
        pygame.draw.rect(self.screen, COLORS["silver"], 
                        (bar_x, bar_y, bar_width, bar_height), 2, border_radius=10)
        
        # Percentage
        percent_font = pygame.font.Font(None, 36)
        percent_text = f"{int(self.loading_progress)}%"
        percent_surf = percent_font.render(percent_text, True, COLORS["pure_white"])
        percent_rect = percent_surf.get_rect(center=(SCREEN_WIDTH//2, bar_y + 35))
        self.screen.blit(percent_surf, percent_rect)
        
        # Particles
        for particle in self.particles[:]:
            if particle.update():
                particle.draw(self.screen)
            else:
                self.particles.remove(particle)
        
        # Add new particles
        if random.random() < 0.3:
            self.particles.append(Particle(
                random.randint(bar_x, bar_x + progress_width),
                bar_y
            ))
        
        self.loading_progress += 0.5
        if self.loading_progress >= 100:
            self.game_state = "menu"
    
    def show_menu(self):
        """Premium menu screen"""
        # Animated gradient background
        self.screen.fill(COLORS["matte_black"])
        time_offset = pygame.time.get_ticks() * 0.001
        
        for i in range(100):
            y = SCREEN_HEIGHT * i / 100
            color_value = int(128 + 127 * math.sin(time_offset * 2 + i * 0.1))
            pygame.draw.line(self.screen, (color_value//4, color_value//4, color_value//2),
                           (0, y), (SCREEN_WIDTH, y))
        
        # Title with shadow
        title_text = "ඉසුරු RACING"
        shadow_offset = 5
        
        # Shadow
        shadow_surf = self.title_font.render(title_text, True, (0, 0, 0))
        shadow_rect = shadow_surf.get_rect(center=(SCREEN_WIDTH//2 + shadow_offset, 
                                                  SCREEN_HEIGHT//4 + shadow_offset))
        self.screen.blit(shadow_surf, shadow_rect)
        
        # Main title
        title_surf = self.title_font.render(title_text, True, COLORS["neon_cyan"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        self.screen.blit(title_surf, title_rect)
        
        # Update and draw buttons
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        self.play_button.update(mouse_pos)
        self.quit_button.update(mouse_pos)
        
        self.play_button.draw(self.screen)
        self.quit_button.draw(self.screen)
        
        # Handle button clicks
        if self.play_button.is_clicked(mouse_pos, mouse_pressed):
            self.game_state = "playing"
            self.reset_game()
        
        if self.quit_button.is_clicked(mouse_pos, mouse_pressed):
            pygame.quit()
            sys.exit()
        
        # Instructions
        font = pygame.font.Font(None, 28)
        instructions = [
            "CONTROLS:",
            "← → Arrow Keys: Steer",
            "↑ Arrow Key: Accelerate",
            "↓ Arrow Key: Brake",
            "SPACE: Turbo Boost",
            "Avoid obstacles and race as long as possible!"
        ]
        
        for i, line in enumerate(instructions):
            text = font.render(line, True, COLORS["silver"])
            self.screen.blit(text, (50, 600 + i * 40))
    
    def reset_game(self):
        """Reset game variables"""
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT - 200
        self.player_speed = 0
        self.road_offset = 0
        self.obstacles = []
        self.score = 0
        self.game_speed = 5
    
    def generate_obstacle(self):
        """Generate random obstacles"""
        obstacle_types = ["car", "bike", "barrier"]
        obstacle_type = random.choice(obstacle_types)
        width = random.randint(40, 80)
        height = random.randint(60, 120)
        x = random.randint(SCREEN_WIDTH//2 - ROAD_WIDTH//2 + width//2,
                          SCREEN_WIDTH//2 + ROAD_WIDTH//2 - width//2)
        
        return {
            "x": x,
            "y": -height,
            "width": width,
            "height": height,
            "type": obstacle_type,
            "color": random.choice([COLORS["apple_red"], COLORS["neon_pink"], (200, 200, 50)])
        }
    
    def draw_road(self):
        """Draw premium racing track"""
        road_x = SCREEN_WIDTH//2 - ROAD_WIDTH//2
        
        # Road surface with gradient
        for i in range(ROAD_WIDTH // 20):
            x = road_x + i * 20
            gray_value = 60 + i % 40
            pygame.draw.rect(self.screen, (gray_value, gray_value, gray_value),
                           (x, 0, 20, SCREEN_HEIGHT))
        
        # Road markings
        marking_y = (self.road_offset * 2) % 40
        while marking_y < SCREEN_HEIGHT:
            pygame.draw.rect(self.screen, COLORS["pure_white"],
                           (SCREEN_WIDTH//2 - 5, marking_y, 10, 20))
            marking_y += 40
        
        # Road borders with glow
        pygame.draw.rect(self.screen, (200, 200, 200, 100),
                        (road_x - 10, 0, 10, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, (200, 200, 200, 100),
                        (road_x + ROAD_WIDTH, 0, 10, SCREEN_HEIGHT))
    
    def draw_player(self):
        """Draw premium bike"""
        # Bike body
        bike_color = COLORS["apple_blue"]
        if self.player_speed > 10:
            bike_color = COLORS["neon_cyan"]  # Turbo effect
        
        # Main body
        pygame.draw.rect(self.screen, bike_color,
                        (self.player_x - CAR_WIDTH//2, self.player_y - CAR_HEIGHT//2,
                         CAR_WIDTH, CAR_HEIGHT), border_radius=15)
        
        # Highlights
        pygame.draw.rect(self.screen, self._lighten_color(bike_color, 50),
                        (self.player_x - CAR_WIDTH//2 + 5, self.player_y - CAR_HEIGHT//2 + 5,
                         CAR_WIDTH - 10, 20), border_radius=10)
        
        # Wheels
        pygame.draw.circle(self.screen, COLORS["matte_black"],
                          (self.player_x - 20, self.player_y + 40), 15)
        pygame.draw.circle(self.screen, COLORS["matte_black"],
                          (self.player_x + 20, self.player_y + 40), 15)
        
        # Wheel highlights
        pygame.draw.circle(self.screen, COLORS["silver"],
                          (self.player_x - 20, self.player_y + 40), 8)
        pygame.draw.circle(self.screen, COLORS["silver"],
                          (self.player_x + 20, self.player_y + 40), 8)
        
        # Speed effect
        if self.player_speed > 5:
            for i in range(3):
                trail_width = CAR_WIDTH - i * 10
                trail_height = 20 + i * 10
                alpha = 150 - i * 50
                trail_surf = pygame.Surface((trail_width, trail_height), pygame.SRCALPHA)
                pygame.draw.rect(trail_surf, (*COLORS["neon_cyan"], alpha),
                                trail_surf.get_rect(), border_radius=5)
                trail_x = self.player_x - trail_width//2
                trail_y = self.player_y + CAR_HEIGHT//2 + i * 5
                self.screen.blit(trail_surf, (trail_x, trail_y))
    
    def _lighten_color(self, color, amount):
        return tuple(min(255, c + amount) for c in color)
    
    def draw_obstacles(self):
        """Draw all obstacles"""
        for obstacle in self.obstacles:
            color = obstacle["color"]
            
            if obstacle["type"] == "car":
                # Draw car obstacle
                pygame.draw.rect(self.screen, color,
                                (obstacle["x"] - obstacle["width"]//2,
                                 obstacle["y"] - obstacle["height"]//2,
                                 obstacle["width"], obstacle["height"]),
                                border_radius=10)
                
                # Windows
                pygame.draw.rect(self.screen, (150, 200, 255),
                                (obstacle["x"] - obstacle["width"]//2 + 5,
                                 obstacle["y"] - obstacle["height"]//2 + 5,
                                 obstacle["width"] - 10, 15),
                                border_radius=5)
            
            elif obstacle["type"] == "bike":
                # Draw bike obstacle
                pygame.draw.rect(self.screen, color,
                                (obstacle["x"] - obstacle["width"]//2,
                                 obstacle["y"] - obstacle["height"]//2,
                                 obstacle["width"], obstacle["height"]),
                                border_radius=5)
                
                # Handle bars
                pygame.draw.rect(self.screen, COLORS["matte_black"],
                                (obstacle["x"] - obstacle["width"]//2 - 10,
                                 obstacle["y"],
                                 20, 5))
            
            else:  # barrier
                pygame.draw.rect(self.screen, color,
                                (obstacle["x"] - obstacle["width"]//2,
                                 obstacle["y"] - obstacle["height"]//2,
                                 obstacle["width"], obstacle["height"]))
    
    def check_collision(self):
        """Check collision with obstacles"""
        player_rect = pygame.Rect(self.player_x - CAR_WIDTH//2,
                                self.player_y - CAR_HEIGHT//2,
                                CAR_WIDTH, CAR_HEIGHT)
        
        for obstacle in self.obstacles:
            obstacle_rect = pygame.Rect(obstacle["x"] - obstacle["width"]//2,
                                       obstacle["y"] - obstacle["height"]//2,
                                       obstacle["width"], obstacle["height"])
            
            if player_rect.colliderect(obstacle_rect):
                if self.crash_sound:
                    self.crash_sound.play()
                return True
        return False
    
    def show_game_over(self):
        """Premium game over screen"""
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        game_over_font = pygame.font.Font(None, 82)
        game_over_surf = game_over_font.render("GAME OVER", True, COLORS["apple_red"])
        game_over_rect = game_over_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        self.screen.blit(game_over_surf, game_over_rect)
        
        # Score
        score_font = pygame.font.Font(None, 48)
        score_text = f"SCORE: {int(self.score)}"
        score_surf = score_font.render(score_text, True, COLORS["pure_white"])
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(score_surf, score_rect)
        
        # Update and draw restart button
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        self.restart_button.update(mouse_pos)
        self.restart_button.draw(self.screen)
        
        if self.restart_button.is_clicked(mouse_pos, mouse_pressed):
            self.game_state = "playing"
            self.reset_game()
    
    def run_game(self):
        """Main game loop"""
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
            
            # Get keyboard input
            keys = pygame.key.get_pressed()
            
            if self.game_state == "loading":
                self.show_loading_screen()
            
            elif self.game_state == "menu":
                self.show_menu()
            
            elif self.game_state == "playing":
                # Game logic
                self.screen.fill(COLORS["dark_gray"])
                
                # Handle input
                if keys[K_LEFT] and self.player_x > SCREEN_WIDTH//2 - ROAD_WIDTH//2 + CAR_WIDTH//2:
                    self.player_x -= 8
                if keys[K_RIGHT] and self.player_x < SCREEN_WIDTH//2 + ROAD_WIDTH//2 - CAR_WIDTH//2:
                    self.player_x += 8
                
                if keys[K_UP]:
                    self.player_speed += 0.2
                    if self.player_speed > 15:
                        self.player_speed = 15
                elif self.player_speed > 0:
                    self.player_speed -= 0.1
                
                if keys[K_DOWN]:
                    self.player_speed -= 0.3
                    if self.player_speed < 0:
                        self.player_speed = 0
                
                # Turbo boost
                if keys[K_SPACE] and self.player_speed > 5:
                    self.player_speed = min(20, self.player_speed + 0.5)
                
                # Update road
                self.road_offset += self.player_speed
                
                # Update obstacles
                for obstacle in self.obstacles:
                    obstacle["y"] += self.game_speed + self.player_speed * 0.5
                
                # Remove off-screen obstacles
                self.obstacles = [o for o in self.obstacles if o["y"] < SCREEN_HEIGHT + 100]
                
                # Generate new obstacles
                if random.random() < 0.02:
                    self.obstacles.append(self.generate_obstacle())
                
                # Increase difficulty
                self.game_speed += 0.0005
                
                # Update score
                self.score += self.player_speed * 0.1
                
                # Check collision
                if self.check_collision():
                    self.game_state = "game_over"
                
                # Draw everything
                self.draw_road()
                self.draw_obstacles()
                self.draw_player()
                
                # Draw HUD
                font = pygame.font.Font(None, 36)
                
                # Speedometer
                speed_text = f"SPEED: {int(self.player_speed * 10)} KM/H"
                speed_surf = font.render(speed_text, True, COLORS["pure_white"])
                self.screen.blit(speed_surf, (20, 20))
                
                # Score
                score_text = f"SCORE: {int(self.score)}"
                score_surf = font.render(score_text, True, COLORS["pure_white"])
                self.screen.blit(score_surf, (20, 60))
                
                # Boost indicator
                if keys[K_SPACE] and self.player_speed > 5:
                    boost_text = "TURBO BOOST!"
                    boost_surf = font.render(boost_text, True, COLORS["neon_pink"])
                    self.screen.blit(boost_surf, (20, 100))
            
            elif self.game_state == "game_over":
                # Draw game in background
                self.screen.fill(COLORS["dark_gray"])
                self.draw_road()
                self.draw_obstacles()
                self.draw_player()
                
                # Show game over screen
                self.show_game_over()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)

# Create and run the game
if __name__ == "__main__":
    game = PremiumGame()
    game.run_game()