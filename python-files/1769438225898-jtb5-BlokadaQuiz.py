import pygame
import sys
import time

pygame.init()

WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Квиз: Вооружение Блокады Ленинграда")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 150, 255)
GREEN = (100, 255, 100)
RED = (255, 100, 100)
GRAY = (200, 200, 200)
DARKOverlay = (0, 0, 0, 128)  

font_question = pygame.font.SysFont(None, 32)
font_answer = pygame.font.SysFont(None, 36)
font_result = pygame.font.SysFont(None, 72)
font_timer = pygame.font.SysFont(None, 64)

questions = [
    ("Какой самый легендарный танк времен блокады?", ["Т-34", "Т-38", "БТ-5", "КВ-1"], 0),
    ("Какой пистолет‑пулемёт, разработанный в блокадном Ленинграде, славился простотой и надёжностью?", ["ППШ-41", "ППС-42", "МП38", "ППД-34"], 1),
    ("Какое основное стрелковое оружие использовали ленинградские ополченцы в 1941 г.?", ["Автомат ППШ", "Пистолет ТТ", "Винтовка Мосина", "Пулемёт ДП‑27"], 2),
    ("Что в блокадном Ленинграде называли «зажигалкой»?", ["Сигнальную ракету", "Лермосветительный снаряд", "Ручную гранату", "Зажигательную бомбу с напалмом"], 3),
]

current_question = 0
score = 0
game_over = False
cooldown = False  
cooldown_end_time = 0  

def draw_text(text, font, color, x, y, center=True):
    surf = font.render(text, True, color)
    if center:
        rect = surf.get_rect(center=(x, y))
    else:
        rect = surf.get_rect(topleft=(x, y))
    screen.blit(surf, rect)

def draw_button(text, x, y, w, h, color, hover_color, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if x < mouse[0] < x + w and y < mouse[1] < y + h:
        pygame.draw.rect(screen, hover_color, (x, y, w, h), border_radius=15)
        if click[0] == 1 and action is not None and not cooldown:
            action()
    else:
        pygame.draw.rect(screen, color, (x, y, w, h), border_radius=15)

    draw_text(text, font_answer, BLACK, x + w // 2, y + h // 2)

def check_answer(selected_index):
    global current_question, score, cooldown, cooldown_end_time
    if selected_index == questions[current_question][2]:
        score += 1

    cooldown = True
    cooldown_end_time = time.time() + 1.0  

def restart_game():
    global current_question, score, game_over, cooldown
    current_question = 0
    score = 0
    game_over = False
    cooldown = False

def close_game():
    break
    print("Errors dont found, closing the quiz, bye") 
    


clock = pygame.time.Clock()
running = True

while running:
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if not game_over and not cooldown:
                if event.key == pygame.K_1:
                    check_answer(0)
                elif event.key == pygame.K_2:
                    check_answer(1)
                elif event.key == pygame.K_3:
                    check_answer(2)
                elif event.key == pygame.K_4:
                    check_answer(3)
                elif event.key == pygame.K_m:
                    WIDTH, HEIGHT = 1200, 800
                    screen = pygame.display.set_mode((WIDTH, HEIGHT))
                elif event.key == pygame.K_k:
                    WIDTH, HEIGHT = 1920, 1080
                    screen = pygame.display.set_mode((WIDTH, HEIGHT))
                elif event.key == pygame.K_l:
                    WIDTH, HEIGHT = 800, 600
                    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    if not game_over:
        if cooldown:
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill(DARKOverlay)
            screen.blit(s, (0, 0))

            remaining = cooldown_end_time - time.time()
            if remaining > 0:
                draw_text(f"{int(remaining * 10) / 10:.1f}", font_timer, RED, WIDTH // 2, HEIGHT // 2)
            else:
                cooldown = False
                current_question += 1
                if current_question >= len(questions):
                    game_over = True
        else:
            question_text = questions[current_question][0]
            draw_text(question_text, font_question, BLACK, WIDTH // 2, 100)

            answers = questions[current_question][1]
            for i, answer in enumerate(answers):
                y_pos = 200 + i * 80
                draw_button(f"{i+1}. {answer}", WIDTH // 2 - 150, y_pos, 350, 60, BLUE, GREEN,
                           lambda idx=i: check_answer(idx))

            draw_text("Или нажимайте 1–4 на клавиатуре", font_answer, GRAY, WIDTH // 2, 550)
            draw_text("Изменить размер окна - буквы M(Англ), K(Англ) и L(Англ)", font_answer, GRAY, WIDTH // 2, 600)

    else:
        draw_text("Игра окончена!", font_result, BLACK, WIDTH // 2, 200)
        draw_text(f"Ваш счёт: {score} из {len(questions)}", font_result,
                 GREEN if score > 2 else RED, WIDTH // 2, 300)
        draw_button("Играть снова", WIDTH // 2 - 100, 450, 200, 60, GRAY, BLUE, restart_game)
        draw_button("Выйти", WIDTH // 2 - 100, 600, 200, 60, RED, BLUE, close_game)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
