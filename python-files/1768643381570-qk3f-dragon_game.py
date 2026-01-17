import pygame
import random
import sys

def main():
    pygame.init()
    
    WIDTH, HEIGHT = 800, 400
    GROUND_HEIGHT = 50
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("dragon_game")
    clock = pygame.time.Clock()
    
    # Цвета
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (100, 150, 255)
    BROWN = (139, 69, 19)
    
    # Дракончик
    dragon_x = 100
    dragon_y = HEIGHT - GROUND_HEIGHT - 60
    dragon_width = 40
    dragon_height = 60
    dragon_velocity = 0
    gravity = 0.8
    jump_strength = -15
    is_jumping = False
    
    # Препятствия
    obstacles = []
    obstacle_timer = 0
    
    # Счет
    score = 0
    font = pygame.font.Font(None, 36)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not is_jumping:
                    dragon_velocity = jump_strength
                    is_jumping = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not is_jumping:
                    dragon_velocity = jump_strength
                    is_jumping = True
        
        # Движение дракончика
        dragon_velocity += gravity
        dragon_y += dragon_velocity
        
        if dragon_y > HEIGHT - GROUND_HEIGHT - dragon_height:
            dragon_y = HEIGHT - GROUND_HEIGHT - dragon_height
            dragon_velocity = 0
            is_jumping = False
        
        # Создание препятствий
        obstacle_timer += 1
        if obstacle_timer > 90:
            obstacles.append({
                'x': WIDTH,
                'width': 30,
                'height': random.randint(40, 70)
            })
            obstacle_timer = 0
        
        # Обновление препятствий
        for obstacle in obstacles[:]:
            obstacle['x'] -= 5
            
            # Проверка столкновения
            if (dragon_x < obstacle['x'] + obstacle['width'] and
                dragon_x + dragon_width > obstacle['x'] and
                dragon_y + dragon_height > HEIGHT - GROUND_HEIGHT - obstacle['height']):
                running = False
            
            # Удаление препятствий
            if obstacle['x'] + obstacle['width'] < 0:
                obstacles.remove(obstacle)
                score += 1
        
        # Отрисовка
        screen.fill(BLUE)
        
        # Земля
        pygame.draw.rect(screen, BROWN, (0, HEIGHT - GROUND_HEIGHT, WIDTH, GROUND_HEIGHT))
        
        # Дракончик
        pygame.draw.rect(screen, RED, (dragon_x, dragon_y, dragon_width, dragon_height))
        pygame.draw.circle(screen, WHITE, (dragon_x + 30, dragon_y + 15), 8)
        pygame.draw.circle(screen, BLACK, (dragon_x + 32, dragon_y + 15), 4)
        
        # Препятствия
        for obstacle in obstacles:
            obstacle_y = HEIGHT - GROUND_HEIGHT - obstacle['height']
            pygame.draw.rect(screen, GREEN, (obstacle['x'], obstacle_y, obstacle['width'], obstacle['height']))
        
        # Счет
        score_text = font.render(f"Очки: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # Инструкция
        instruction = font.render("Клик мыши или ПРОБЕЛ - прыжок", True, WHITE)
        screen.blit(instruction, (WIDTH // 2 - 150, HEIGHT - 30))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__name == "__main__":
    main()