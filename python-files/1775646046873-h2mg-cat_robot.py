import pygame
import time
import subprocess

# Инициализация Pygame
pygame.init()

# Размеры окна
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Котик-робот ждёт USB!")

# Загрузка изображений
eyes_closed = pygame.image.load("images/eyes_closed.png")
eyes_open = pygame.image.load("images/eyes_open.png")
happy_eyes = pygame.image.load("images/happy_eyes.png")
purring = pygame.image.load("images/purring.png")

# Позиция мордочки
x, y = WIDTH // 2 - 100, HEIGHT // 2 - 100

# Функция проверки USB
def check_usb():
    try:
        if sys.platform.startswith('win'):
            result = subprocess.run(['wmic', 'logicaldisk', 'get', 'caption'], capture_output=True, text=True)
            return len(result.stdout.split()) > 1
        else:
            result = subprocess.run(['lsusb'], capture_output=True, text=True)
            return "Bus" in result.stdout
    except:
        return False

# Основной цикл
running = True
usb_detected = False

while running:
    screen.fill((255, 255, 255))  # Белый фон

    # Рисуем мордочку в зависимости от состояния
    if not usb_detected:
        screen.blit(eyes_open, (x, y))
        pygame.display.flip()
        time.sleep(1)
    else:
        # Анимация радости
        for img in [happy_eyes, purring, happy_eyes]:
            screen.blit(img, (x, y))
            pygame.display.flip()
            time.sleep(0.5)
        usb_detected = False  # Сброс после анимации

    # Проверяем USB
    if check_usb() and not usb_detected:
        usb_detected = True

    # Обработка выхода
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()