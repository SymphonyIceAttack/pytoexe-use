import pygame
import random
import sys

# Инициализация Pygame
pygame.init()

# Размеры окна
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Волк ловит яйца")

# Цвета
BLACK = (0, 0, 0)

# Загрузка изображений
try:
    wolf_img = pygame.image.load('wolf.png')
    egg_img = pygame.image.load('egg.png')
except:
    print("Пожалуйста, убедитесь, что файлы 'wolf.png' и 'egg.png' находятся в папке с этим скриптом.")
    sys.exit()

# Масштабируем изображения, чтобы они подходили по размеру
WOLF_WIDTH, WOLF_HEIGHT = 80, 60
wolf_img = pygame.transform.scale(wolf_img, (WOLF_WIDTH, WOLF_HEIGHT))

EGG_SIZE = 40
egg_img = pygame.transform.scale(egg_img, (EGG_SIZE, EGG_SIZE))

# Создаем объекты
class Wolf:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - WOLF_HEIGHT - 10
        self.speed = 10

    def move_left(self):
        self.x -= self.speed
        if self.x < 0:
            self.x = 0

    def move_right(self):
        self.x += self.speed
        if self.x > WIDTH - WOLF_WIDTH:
            self.x = WIDTH - WOLF_WIDTH

    def draw(self):
        screen.blit(wolf_img, (self.x, self.y))

class Egg:
    def __init__(self):
        self.x = random.randint(0, WIDTH - EGG_SIZE)
        self.y = -EGG_SIZE
        self.speed = random.randint(5, 10)

    def fall(self):
        self.y += self.speed

    def draw(self):
        screen.blit(egg_img, (self.x, self.y))

    def is_caught(self, wolf):
        wolf_rect = pygame.Rect(wolf.x, wolf.y, WOLF_WIDTH, WOLF_HEIGHT)
        egg_rect = pygame.Rect(self.x, self.y, EGG_SIZE, EGG_SIZE)
        return egg_rect.colliderect(wolf_rect)

    def is_missed(self):
        return self.y > HEIGHT

# Основная функция игры
def main():
    clock = pygame.time.Clock()
    wolf = Wolf()
    eggs = []
    spawn_event = pygame.USEREVENT + 1
    pygame.time.set_timer(spawn_event, 1000)  # спавн яйца каждую секунду
    score = 0
    font = pygame.font.SysFont(None, 36)

    running = True
    while running:
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == spawn_event:
                eggs.append(Egg())

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            wolf.move_left()
        if keys[pygame.K_RIGHT]:
            wolf.move_right()

        for egg in eggs[:]:
            egg.fall()
            if egg.is_caught(wolf):
                eggs.remove(egg)
                score += 1
            elif egg.is_missed():
                eggs.remove(egg)

        # Отрисовка объектов
        wolf.draw()
        for egg in eggs:
            egg.draw()

        # Отрисовка счета
        score_text = font.render(f"Очки: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
