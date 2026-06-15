import pygame
import sys
import math
import random

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Настройки окна
WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Калькулятор 69 Edition")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Попытка загрузить медиафайлы (если файлов нет, программа создаст заглушки, чтобы не вылетать)
def load_image(name, fallback_color, size):
    try:
        img = pygame.image.load(name).convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        surf = pygame.Surface(size)
        surf.fill(fallback_color)
        return surf

def load_sound(name):
    try:
        return pygame.mixer.Sound(name)
    except:
        return None

# Загрузка ассетов
bg_img = load_image("sigmaface.png", (30, 30, 30), (WIDTH, HEIGHT))
sound_click = load_sound("click.wav")
sound_shot = load_sound("shot.wav")

# Загрузка тянок ( placeholders, если нет gif/png )
girl_l = load_image("girl_left.png", (255, 105, 180), (150, 400))
girl_r = load_image("girl_right.png", (255, 105, 180), (150, 400))

# Шрифты
font_huge = pygame.font.SysFont("Arial", 60, bold=True)
font_btn = pygame.font.SysFont("Impact", 32)
font_stars = pygame.font.SysFont("Impact", 45)

# Переменные калькулятора
expr = ""
display_text = "0"

# Координаты центрального блока калькулятора
calc_rect = pygame.Rect(200, 100, 500, 500)

# Кнопки калькулятора
buttons = [
    ('7', 220, 240), ('8', 295, 240), ('9', 370, 240), ('/', 445, 240), ('C', 520, 240),
    ('4', 220, 315), ('5', 295, 315), ('6', 370, 315), ('*', 445, 315), ('(', 520, 315),
    ('1', 220, 390), ('2', 295, 390), ('3', 370, 390), ('-', 445, 390), (')', 520, 390),
    ('0', 220, 465), ('.', 295, 465), ('+', 370, 465), ('=', 445, 465),
]
btn_size = 65

# Эффекты
money_particles = []
show_money_rain = False
money_timer = 0
hue = 0
logo_angle = 0

# Спрятать стандартный курсор
pygame.mouse.set_visible(False)

clock = pygame.time.Clock()
running = True

while running:
    clock.tick(60)
    hue = (hue + 2) % 360
    
    # Неоновый переливающийся цвет
    neon_color = pygame.Color(0)
    neon_color.hsva = (hue, 100, 100, 100)
    
    # Рендеринг бэкграунда (Сигма фейс)
    screen.blit(bg_img, (0, 0))
    
    # Танцующие аниме тян (эффект покачивания влево-вправо вместо гифок)
    dance_offset = math.sin(pygame.time.get_ticks() * 0.005) * 15
    screen.blit(girl_l, (20 + dance_offset, 150 + dance_offset // 2))
    screen.blit(girl_r, (WIDTH - 170 - dance_offset, 150 - dance_offset // 2))
    
    # Окно калькулятора с неоновой рамкой
    pygame.draw.rect(screen, (10, 10, 10), calc_rect)
    pygame.draw.rect(screen, neon_color, calc_rect, 6)
    
    # Логотип "69" (крутящийся слева вверху)
    logo_angle = (logo_angle + 4) % 360
    logo_surf = font_huge.render("69", True, neon_color)
    rotated_logo = pygame.transform.rotate(logo_surf, logo_angle)
    logo_rect = rotated_logo.get_rect(center=(90, 80))
    screen.blit(rotated_logo, logo_rect)
    
    # 5 Звезд Розыска GTA SA (справа вверху)
    # В GTA оригинальный цвет звезд — тускло-золотой/желтый
    for i in range(5):
        star_text = font_stars.render("★", True, (240, 180, 0))
        screen.blit(star_text, (WIDTH - 240 + i * 40, 40))
        
    # Дисплей калькулятора
    disp_box = pygame.Rect(220, 130, 460, 80)
    pygame.draw.rect(screen, (20, 20, 20), disp_box)
    pygame.draw.rect(screen, neon_color, disp_box, 2)
    
    # Отрезаем текст, если он слишком длинный
    txt_surf = font_huge.render(display_text[-13:], True, (0, 255, 65)) # Ярко-зеленый хакерский цвет
    screen.blit(txt_surf, (230, 135))
    
    # Отрисовка кнопок
    mouse_pos = pygame.mouse.get_pos()
    for btn, x, y in buttons:
        btn_rect = pygame.Rect(x, y, btn_size if btn != '=' else btn_size * 2 + 10, btn_size)
        
        # Подсветка при наведении
        if btn_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, neon_color, btn_rect)
            b_txt = font_btn.render(btn, True, BLACK)
        else:
            pygame.draw.rect(screen, (30, 30, 30), btn_rect)
            pygame.draw.rect(screen, neon_color, btn_rect, 2)
            b_txt = font_btn.render(btn, True, WHITE)
            
        screen.blit(b_txt, (btn_rect.x + (btn_rect.width - b_txt.get_width())//2, btn_rect.y + 12))

    # Логика денежного дождя
    if show_money_rain:
        if pygame.time.get_ticks() < money_timer:
            if random.random() < 0.3: # Спавн новых купюр
                money_particles.append([random.randint(200, 700), 0, random.randint(4, 8)])
        else:
            show_money_rain = False
            
    for p in money_particles[:]:
        p[1] += p[2] # Падение вниз
        # Рисуем зеленую "купюру" $
        m_txt = font_btn.render("$", True, (0, 255, 0))
        screen.blit(m_txt, (p[0], p[1]))
        if p[1] > HEIGHT:
            money_particles.remove(p)

    # Обработка событий
    for event in pygame.event.get_complete():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Звук выстрела на любой клик мыши
            if sound_shot: sound_shot.play()
            
            # Проверка нажатий на кнопки калькулятора
            for btn, x, y in buttons:
                btn_rect = pygame.Rect(x, y, btn_size if btn != '=' else btn_size * 2 + 10, btn_size)
                if btn_rect.collidepoint(event.pos):
                    if sound_click: sound_click.play()
                    
                    if btn == 'C':
                        expr = ""
                        display_text = "0"
                    elif btn == '=':
                        try:
                            # Магия вычислений
                            res = str(eval(expr))
                            display_text = res
                            expr = res
                            # Триггерим денежный дождь на 3 секунды
                            show_money_rain = True
                            money_timer = pygame.time.get_ticks() + 3000
                        except:
                            display_text = "ERROR"
                            expr = ""
                    else:
                        if expr == "0" or display_text == "ERROR":
                            expr = ""
                        expr += btn
                        display_text = expr

    # Кастомный курсор-прицел
    cx, cy = mouse_pos
    pygame.draw.circle(screen, (255, 0, 0), (cx, cy), 15, 2)
    pygame.draw.line(screen, (255, 0, 0), (cx - 22, cy), (cx + 22, cy), 2)
    pygame.draw.line(screen, (255, 0, 0), (cx, cy - 22), (cx, cy + 22), 2)
    pygame.draw.circle(screen, (255, 0, 0), (cx, cy), 2)

    pygame.display.flip()

pygame.quit()
sys.exit()