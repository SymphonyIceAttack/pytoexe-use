import pygame
import sys
from random import randint

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Угадай число")
clock = pygame.time.Clock()

# Цвета — современная тёмная тема
BG_COLOR = (12, 18, 36)           # Глубокий чёрно-синий
ACCENT_COLOR = (255, 215, 0)      # Золото
TEXT_COLOR = (240, 240, 255)
SUCCESS_COLOR = (0, 200, 120)
DANGER_COLOR = (220, 60, 60)
INPUT_COLOR = (40, 55, 90)
NUMBER_BG = (30, 45, 80)

# Шрифты — современные и красивые
font_title = pygame.font.SysFont("Arial", 50, bold=True)
font_balance = pygame.font.SysFont("Arial", 36, bold=False)
font_label = pygame.font.SysFont("Arial", 30)
font_number = pygame.font.SysFont("Arial", 60, bold=True)
font_result = pygame.font.SysFont("Arial", 40, bold=True)

# === Параметры игры ===
money = 100
bet = ""
game_state = "bet"  # 'bet', 'guess', 'result'
n1 = n2 = n3 = kakoe = 0
result_msg = ""

def draw_text(text, font, color, x, y, center=True):
    surf = font.render(text, True, color)
    if center:
        rect = surf.get_rect(center=(x, y))
    else:
        rect = surf.get_rect(x=x, y=y)
    screen.blit(surf, rect)

def draw_input_box(x, y, w, h, text="", active=False):
    color = (50, 70, 110) if active else (40, 55, 90)
    pygame.draw.rect(screen, color, (x, y, w, h), border_radius=12)
    pygame.draw.rect(screen, ACCENT_COLOR, (x, y, w, h), 3, border_radius=12)
    draw_text(text if text else "0", font_number, TEXT_COLOR, x + w // 2, y + h // 2)

def draw_number_button(num, x, y, w=180, h=120, hover=False):
    color = (ACCENT_COLOR if hover else NUMBER_BG)
    pygame.draw.rect(screen, color, (x, y, w, h), border_radius=16)
    pygame.draw.rect(screen, ACCENT_COLOR, (x, y, w, h), 3, border_radius=16)
    draw_text(str(num), font_number, TEXT_COLOR, x + w // 2, y + h // 2)

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(BG_COLOR)

    # === Обработка событий ===
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if game_state == "bet":
                if event.key == pygame.K_RETURN and bet.isdigit() and int(bet) > 0:
                    bet_value = int(bet)
                    if bet_value > money:
                        result_msg = "Недостаточно денег!"
                    else:
                        game_state = "guess"
                        bet = int(bet)
                        n1 = randint(1, 10)
                        n2 = randint(1, 10)
                        n3 = randint(1, 10)
                        kakoe = [n1, n2, n3][randint(0, 2)]
                        result_msg = ""
                elif event.key == pygame.K_BACKSPACE:
                    bet = bet[:-1]
                elif event.unicode.isdigit():
                    bet += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Области чисел в состоянии "угадай"
            num_y = 400
            num_h = 120
            left_btn = 180 <= mouse_pos[0] <= 180 + 180 and num_y <= mouse_pos[1] <= num_y + num_h
            mid_btn = 410 <= mouse_pos[0] <= 410 + 180 and num_y <= mouse_pos[1] <= num_y + num_h
            right_btn = 640 <= mouse_pos[0] <= 640 + 180 and num_y <= mouse_pos[1] <= num_y + num_h

            if game_state == "bet":
                if 350 <= mouse_pos[0] <= 650 and 300 <= mouse_pos[1] <= 380:
                    pass  # поле активируется по клику, но не переходит дальше без Enter
                else:
                    pass

            elif game_state == "guess":
                if left_btn:
                    if n1 == kakoe:
                        money += bet
                        result_msg = "🎉 ВЫ ВЫИГРАЛИ!"
                    else:
                        money -= bet
                        result_msg = "💥 ВЫ ПРОИГРАЛИ!"
                    game_state = "result"
                elif mid_btn:
                    if n2 == kakoe:
                        money += bet
                        result_msg = "🎉 ВЫ ВЫИГРАЛИ!"
                    else:
                        money -= bet
                        result_msg = "💥 ВЫ ПРОИГРАЛИ!"
                    game_state = "result"
                elif right_btn:
                    if n3 == kakoe:
                        money += bet
                        result_msg = "🎉 ВЫ ВЫИГРАЛИ!"
                    else:
                        money -= bet
                        result_msg = "💥 ВЫ ПРОИГРАЛИ!"
                    game_state = "result"

            elif game_state == "result":
                if 375 <= mouse_pos[0] <= 625 and 420 <= mouse_pos[1] <= 480:
                    if money <= 0:
                        money = 100
                    game_state = "bet"
                    bet = ""
                    result_msg = ""

    # === Отрисовка интерфейса ===
    # Заголовок — только "Угадай число"
    draw_text("УГАДАЙ ЧИСЛО", font_title, ACCENT_COLOR, WIDTH // 2, 60)

    # Баланс — без символа 💰
    draw_text(f"Баланс: {money}", font_balance, TEXT_COLOR, WIDTH // 2, 130)

    # Сообщение об ошибке
    if result_msg and "деньги" in result_msg:
        draw_text(result_msg, font_label, DANGER_COLOR, WIDTH // 2, 200)

    if game_state == "bet":
        draw_text("Введите ставку:", font_label, TEXT_COLOR, WIDTH // 2, 250)
        draw_input_box(350, 300, 300, 80, str(bet) if bet else "")

    elif game_state == "guess":
        draw_text("Выберите число кликом:", font_label, TEXT_COLOR, WIDTH // 2, 250)

        # Кнопки с числами
        draw_number_button(n1, 180, 400, hover=180 <= mouse_pos[0] <= 360 and 400 <= mouse_pos[1] <= 520)
        draw_number_button(n2, 410, 400, hover=410 <= mouse_pos[0] <= 590 and 400 <= mouse_pos[1] <= 520)
        draw_number_button(n3, 640, 400, hover=640 <= mouse_pos[0] <= 820 and 400 <= mouse_pos[1] <= 520)

    elif game_state == "result":
        draw_text(result_msg, font_result,
                  SUCCESS_COLOR if "ВЫИГРАЛИ" in result_msg else DANGER_COLOR,
                  WIDTH // 2, 250)
        draw_text(f"Выигрышное число: {kakoe}", font_label, ACCENT_COLOR, WIDTH // 2, 320)
        btn_text = "🔄 Играть снова" if money > 0 else "🎮 Начать сначала"
        draw_text(btn_text, font_label, TEXT_COLOR, WIDTH // 2, 420)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()




