import pygame
import sys
import time

pygame.init()

# ====== НАСТРОЙКИ ОКНА ======
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Своя игра — История России")

# ====== ЦВЕТА ======
BG = (15, 15, 70)
BLUE = (25, 25, 150)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
GRAY = (90, 90, 90)
GREEN = (0, 200, 0)
RED = (200, 0, 0)

font = pygame.font.SysFont("arial", 28)
big_font = pygame.font.SysFont("arial", 42)
huge_font = pygame.font.SysFont("arial", 70)

clock = pygame.time.Clock()

# ====== ВОПРОСЫ ПО ИСТОРИИ РОССИИ ======
questions = {
    "Древняя Русь": {
        100: {"q": "Кто крестил Русь?", "a": "Владимир"},
        200: {"q": "Год крещения Руси?", "a": "988"},
        300: {"q": "Столица Древней Руси?", "a": "киев"},
 400: {"q": "Именно этот человек в 882 сделал столицей Руси киев?", "a": "Князь Олег"},
 500: {"q": "В каком году Ярослав Мудрый принял первый свод законов?", "a": "1016"}
    },
    "Романовы": {
        100: {"q": "Первый император династии Романовых?", "a": "Петр 1"},
        200: {"q": """Екатерина II после прочтения сказала:
\"Бунтовщик — хуже Пугачёва! Тот, хоть царём прикинулся, монархический строй исповедовал, а этот, революцией, надумал на Руси учинить республику!\". О каком произведении идёт речь?""", "a": "Путешествие из Петербурга в Москву"},
        300: {"q": "В каком году Романовы начали править Россией?", "a": "1613"},
  400: {"q": "Кто был первым царем из династии Романовых?", "a": "Михаил Фёдорович Романов"},
  500: {"q": "Кто был последним императором из династии Романовых?", "a": "Николай II"}
    },
    "СССР": {
        100: {"q": "Год распада СССР?", "a": "1991"},
        200: {"q": "Первый президент России?", "a": "Ельцин"},
        300: {"q": "Кто был руководителем СССР в годы ВОВ?", "a": "Сталин"},
 400: {"q": "Дата Октябрьской революции?", "a": "25-26 октября 1917"},
 500: {"q": "Год принятия первой конституции СССР?", "a": "1924"},    },
    "Историческая личность": {
        100: {"q": "Он стал одним из основоположников русского военного искусства, имеет более 7 титулов, кавалер всех российских орденов своего времени, вручавшихся мужчинам. Он всегда разделял с солдатами все тяготы походной жизни, проявлял особую заботу к быту и условиям проживания своих подчинённых, что резко сократило заболевания и смертность в русской армии. Он был противником муштры и считал человека главным фактором победы.Кто это?", "a": "А.В.Суворов"},
        200: {"q": "Хотя у него имелись все данные, чтобы быть великим государем и одним из самых обаятельных людей в империи, он достигал только того, что возбуждал страх и заставлял всех сторониться себя… Во всех местах, находившихся в его ведении ввел не только среди военных, но и среди придворных самую суровую дисциплину: опоздание на 1 минуту – арест, а большая или меньшая тщательность в прическе мужчин часто служила поводом к изгнанию. Представляться ему нужно было не иначе как в костюме времен Петра 3.Кто это?", "a": "Павел I."},
        300: {"q": "Кто создал флот и регулярную армию??", "a": "Пётр I."},
 400: {"q": "Кто явил основателем Эрмитажа в Санкт-Петербурге?", "a": "Екатерина II."},
 500: {"q": "Кто был автором аграрной реформы и подготовил Указ о праве крестьян выходить из общины с наделом?", "a": "П. А. Столыпин."},    },
    "История в фактах": {
        100: {"q": "Как называлась основная денежная единица Руси?", "a": "Куна"},
        200: {"q": "Что гласит надпись на постаменте Медного Всадника?", "a": "Петру Перьвому, Екатерина Вторая"},
        300: {"q": "За чью голову Гитлер обещал 250 тысяч немецких марок?", "a": "Юрий Левитан"},
 400: {"q": "Почему храм Спаса На Крови имеет такое название?", "a": "На этом месте был смертельно ранен Александр Второй"},
 500: {"q": "Кто был награжден орденом Иуды?", "a": "Иван Мазепа"},    }
 
}

categories = list(questions.keys())
values = [100, 200, 300,400,500]

score = 0
game_state = "board"
selected_question = None
current_category = None


current_value = None
user_input = ""
result_text = ""
result_color = WHITE

TIMER_LIMIT = 12

start_time = None

# ====== ФУНКЦИИ ======

def draw_text(text, font, color, x, y, center=True):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)

def draw_board():
    screen.fill(BG)

    cell_w = WIDTH // 3
    cell_h = HEIGHT // 4

    # Категории
    for i, cat in enumerate(categories):
        draw_text(cat, big_font, GOLD,
                  i * cell_w + cell_w // 2,
                  cell_h // 2)

    # Таблица
    for r, val in enumerate(values):
        for c, cat in enumerate(categories):
            rect = pygame.Rect(c * cell_w,
                               (r + 1) * cell_h,
                               cell_w, cell_h)

            if questions[cat][val] is None:
                pygame.draw.rect(screen, GRAY, rect)
            else:
                pygame.draw.rect(screen, BLUE, rect)
                draw_text(str(val), big_font, GOLD,
                          rect.centerx, rect.centery)

            pygame.draw.rect(screen, WHITE, rect, 3)

    draw_text(f"Счёт: {score}", font, WHITE, 20, HEIGHT - 40, False)

def draw_question():
    screen.fill(BG)

    elapsed = int(time.time() - start_time)
    remaining = max(0, TIMER_LIMIT - elapsed)

    draw_text(selected_question["q"],
              big_font, WHITE,
              WIDTH // 2, HEIGHT // 3)

    draw_text("Ответ: " + user_input,
              font, GOLD,
              WIDTH // 2, HEIGHT // 2)

    draw_text(f"Осталось времени: {remaining} сек",
              font, WHITE,
              WIDTH // 2, HEIGHT - 120)

    if result_text:
        draw_text(result_text,
                  big_font,
                  result_color,
                  WIDTH // 2,
                  HEIGHT - 200)

def draw_final():
    screen.fill(BG)
    draw_text("ИГРА ЗАВЕРШЕНА", huge_font, GOLD,
              WIDTH // 2, HEIGHT // 3)
    draw_text(f"Ваш итоговый счёт: {score}",
              big_font, WHITE,
              WIDTH // 2, HEIGHT // 2)

def all_used():
    for cat in questions:
        for val in questions[cat]:
            if questions[cat][val] is not None:
                return False
    return True

# ====== ИГРОВОЙ ЦИКЛ ======

running = True

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Выбор вопроса
        if game_state == "board" and event.type == pygame.MOUSEBUTTONDOWN:
            cell_w = WIDTH // 3
            cell_h = HEIGHT // 4
            x, y = event.pos
            col = x // cell_w
            row = y // cell_h - 1

            if 0 <= row < 3:
                cat = categories[col]
                val = values[row]

                if questions[cat][val] is not None:
                    selected_question = questions[cat][val]
                    current_category = cat
                    current_value = val
                    user_input = ""
                    result_text = ""
                    start_time = time.time()
                    game_state = "question"

        # Ввод ответа
        if game_state == "question":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if user_input.lower().strip() == selected_question["a"]:
                        score += current_value
                        result_text = "ПРАВИЛЬНО!"
                        result_color = GREEN
                    else:
                        score -= current_value
                        result_text = "НЕПРАВИЛЬНО!"
                        result_color = RED

                    questions[current_category][current_value] = None
                    pygame.time.delay(1500)

                    if all_used():
                        game_state = "final"
                    else:
                        game_state = "board"

                elif event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]
                else:
                    user_input += event.unicode

    # Таймер
    if game_state == "question":
        if time.time() - start_time >= TIMER_LIMIT:
            score -= current_value
            questions[current_category][current_value] = None
            pygame.time.delay(1500)

            if all_used():
                game_state = "final"
            else:
                game_state = "board"

    # Отрисовка
    if game_state == "board":
        draw_board()
    elif game_state == "question":
        draw_question()
    elif game_state == "final":
        draw_final()

    pygame.display.flip()

pygame.quit()
sys.exit()