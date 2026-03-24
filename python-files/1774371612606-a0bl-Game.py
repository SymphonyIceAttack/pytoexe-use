import pygame

# Инициализация Pygame
pygame.init()

# Настройки экрана
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("BMW M8 Gran Coupe Drive")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
RED = (255, 0, 0)

# Характеристики автомобиля
car_width = 150
car_height = 150
car_x = screen_width // 2 - car_width // 2
car_y = screen_height - car_height - 20
car_speed = 0.1

# Загрузка изображения BMW M8 Gran Coupe (нужно будет найти картинку и сохранить как 'bmw_m8.png' в той же папке)
try:
    car_image = pygame.image.load('bmw_m8.png')
    car_image = pygame.transform.scale(car_image, (car_width, car_height))
    car_rect = car_image.get_rect(topleft=(car_x, car_y))
except pygame.error:
    print("Ошибка: Файл 'bmw_m8.png' не найден. Создание автомобиля в виде прямоугольника.")
    car_image = None
    car_rect = pygame.Rect(car_x, car_y, car_width, car_height)

# Основной игровой цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Обработка нажатий клавиш
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        car_x -= car_speed
    if keys[pygame.K_RIGHT]:
        car_x += car_speed
    if keys[pygame.K_UP]:
        car_y -= car_speed
    if keys[pygame.K_DOWN]:
        car_y += car_speed

    # Ограничение движения автомобиля в пределах экрана
    if car_x < 0:
        car_x = 0
    if car_x > screen_width - car_width:
        car_x = screen_width - car_width
    if car_y < 0:
        car_y = 0
    if car_y > screen_height - car_height:
        car_y = screen_height - car_height

    # Обновление позиции прямоугольника автомобиля, если он используется
    if car_image:
        car_rect.topleft = (car_x, car_y)
    else:
        car_rect = pygame.Rect(car_x, car_y, car_width, car_height)

    # Отрисовка
    screen.fill(DARK_GRAY)  # Затемнение фона

    # Отрисовка дороги (простой вариант)
    road_color = GRAY
    pygame.draw.rect(screen, road_color, (0, 0, screen_width, screen_height))
    pygame.draw.rect(screen, WHITE, (screen_width // 2 - 2, 0, 4, screen_height)) # Центральная линия

    # Отрисовка автомобиля
    if car_image:
        screen.blit(car_image, car_rect.topleft)
    else:
        pygame.draw.rect(screen, RED, car_rect) # Если изображение не найдено, рисуем красный прямоугольник

    # Обновление экрана
    pygame.display.flip()

# Завершение Pygame
pygame.quit()