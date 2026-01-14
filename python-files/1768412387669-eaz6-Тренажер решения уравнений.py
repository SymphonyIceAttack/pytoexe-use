import random
import sympy
import os
import webbrowser

import re
import pygame

# Инициализация Pygame
pygame.init()

# Константы
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BACKGROUND_COLOR = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)
FONT_SIZE = 24
LINE_SPACING = 30  # Интервал между строками для прокрутки

# Получение пути к директории, где находится скрипт
script_dir = os.path.dirname(__file__)
background_path = os.path.join(script_dir, "фон 2.webp")

# Создание окна
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Тренажер уравнений")
font = pygame.font.SysFont('Arial', FONT_SIZE)

# Загрузка фона
background = pygame.image.load(background_path)
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Функция для разбиения длинной строки на несколько строк
def wrap_text(text, max_width):
    """
    Разбивает текст на строки, чтобы они помещались в max_width пикселей
    """
    words = text.split(' ')
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        # Проверяем ширину слова
        word_surface = font.render(word, True, TEXT_COLOR)
        word_width = word_surface.get_width()
        
        # Если слово само по себе длиннее max_width, разбиваем его
        if word_width > max_width:
            # Если есть текущая строка, сохраняем её
            if current_line:
                lines.append(' '.join(current_line))
                current_line = []
                current_width = 0
            
            # Разбиваем длинное слово на части
            char_width = font.size('M')[0]  # Примерная ширина символа
            chars_per_line = max_width // char_width
            for i in range(0, len(word), chars_per_line):
                lines.append(word[i:i+chars_per_line])
        else:
            # Проверяем, поместится ли слово в текущую строку
            space_width = font.size(' ')[0] if current_line else 0
            if current_width + space_width + word_width <= max_width:
                current_line.append(word)
                current_width += space_width + word_width
            else:
                # Сохраняем текущую строку и начинаем новую
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
    
    # Добавляем последнюю строку
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines if lines else [text]

# Функция для отображения текста на экране
def draw_text(text, x, y):
    text_surface = font.render(text, True, TEXT_COLOR)
    screen.blit(text_surface, (x, y))

# Функция ввода текста
def get_input(prompt, allow_text=False, additional_lines=None, allow_esc=False, initial_text='', bottom_lines=None):
    """
    additional_lines - список строк для отображения перед полем ввода (например, текст задачи)
    allow_esc - разрешить выход по ESC (вернет 'esc')
    initial_text - начальный текст в поле ввода
    bottom_lines - список строк для отображения под полем ввода (например, сообщение об ошибке)
    """
    input_box = pygame.Rect(50, 100, 700, 50)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = initial_text
    done = False
    esc_pressed = False
    
    # Вычисляем начальную позицию для prompt с учетом дополнительных строк
    if additional_lines:
        start_y = 50
        # Переносим все строки задачи
        max_text_width = SCREEN_WIDTH - 100
        all_wrapped_lines = []
        for line in additional_lines:
            wrapped = wrap_text(line, max_text_width)
            all_wrapped_lines.extend(wrapped)
        
        # Вычисляем, сколько строк помещается на экране
        # Оставляем место для prompt, поля ввода и сообщения об ошибке
        available_height = SCREEN_HEIGHT - 200  # Больше места для текста задачи
        max_visible_lines = available_height // 25  # Уменьшаем межстрочный интервал для большего текста
        
        # Показываем столько строк, сколько помещается
        visible_lines = all_wrapped_lines[:max_visible_lines]
        prompt_y = start_y + len(visible_lines) * 25 + 10
        input_box.y = min(prompt_y + 30, SCREEN_HEIGHT - 100)
        
        # Если поле ввода слишком низко, корректируем
        if input_box.y > SCREEN_HEIGHT - 100:
            input_box.y = SCREEN_HEIGHT - 100
            prompt_y = input_box.y - 30
            # Пересчитываем, сколько строк можем показать
            max_visible_lines = max(5, (prompt_y - start_y - 10) // 25)
            visible_lines = all_wrapped_lines[:max_visible_lines]
    else:
        start_y = 50
        prompt_y = 50
        input_box.y = 100
        visible_lines = []
        all_wrapped_lines = []

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and allow_esc:
                    esc_pressed = True
                    done = True
                elif active:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        if allow_text:
                            text += event.unicode
                        else:
                            if event.unicode in '0123456789-.,;[]':
                                text += event.unicode

        # Отображаем фон
        screen.blit(background, (0, 0))
        
        # Отображаем дополнительные строки (например, задачу)
        y = start_y
        if additional_lines:
            # Максимальная ширина для текста (с учетом отступов)
            max_text_width = SCREEN_WIDTH - 100  # 50 с каждой стороны
            
            # Обрабатываем и переносим каждую строку
            wrapped_lines = []
            for line in additional_lines:
                wrapped = wrap_text(line, max_text_width)
                wrapped_lines.extend(wrapped)
            
            # Показываем столько строк, сколько помещается на экране
            # Используем уже подготовленные visible_lines
            for line in visible_lines:
                draw_text(line, 50, y)
                y += 25  # Уменьшаем межстрочный интервал для большего текста
            
            # Если текст задачи не поместился полностью, показываем подсказку
            if len(all_wrapped_lines) > len(visible_lines):
                draw_text("... (текст продолжается, прокрутите вниз)", 50, y)
        
        # Отображаем prompt (переносим, если длинный)
        max_text_width = SCREEN_WIDTH - 100
        prompt_wrapped = wrap_text(prompt, max_text_width)
        prompt_y_current = prompt_y
        for prompt_line in prompt_wrapped:
            draw_text(prompt_line, 50, prompt_y_current)
            prompt_y_current += 30
        # Корректируем позицию поля ввода, если prompt занял несколько строк
        if len(prompt_wrapped) > 1:
            input_box.y = prompt_y_current + 10
        
        # Учитываем место для сообщения об ошибке под полем ввода
        bottom_space_needed = 0
        if bottom_lines:
            max_text_width = SCREEN_WIDTH - 100
            for line in bottom_lines:
                if line:
                    wrapped = wrap_text(line, max_text_width)
                    bottom_space_needed += len(wrapped) * 25 + 10
        
        # Проверяем, что поле ввода и сообщение об ошибке не выходят за пределы экрана
        if input_box.y + input_box.height + bottom_space_needed > SCREEN_HEIGHT - 20:
            # Сдвигаем поле ввода выше, если нужно
            input_box.y = SCREEN_HEIGHT - input_box.height - bottom_space_needed - 20
            # Не позволяем полю ввода уйти слишком высоко
            if input_box.y < 150:
                input_box.y = 150
        
        # Отображаем поле ввода
        txt_surface = font.render(text, True, TEXT_COLOR)
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        
        # Отображаем курсор, если поле активно (без мерцания)
        if active:
            cursor_x = input_box.x + 5 + txt_surface.get_width()
            pygame.draw.line(screen, TEXT_COLOR, (cursor_x, input_box.y + 5), 
                           (cursor_x, input_box.y + input_box.height - 5), 2)
        
        pygame.draw.rect(screen, color, input_box, 2)
        
        # Отображаем текст под полем ввода (например, сообщение об ошибке)
        if bottom_lines:
            max_text_width = SCREEN_WIDTH - 100
            # Позиция под полем ввода с небольшим отступом
            bottom_y = input_box.y + input_box.height + 10
            for line in bottom_lines:
                if line:  # Проверяем, что строка не пустая
                    wrapped = wrap_text(line, max_text_width)
                    for wrapped_line in wrapped:
                        if bottom_y < SCREEN_HEIGHT - 20:  # Оставляем место внизу
                            draw_text(wrapped_line, 50, bottom_y)
                            bottom_y += 25  # Меньший интервал для сообщения об ошибке
        
        pygame.display.flip()

    if esc_pressed:
        return 'esc'
    return text.strip()

# Форматирование списка ответов в строку [x;y;...]
def format_solution(solution):
    if not solution:
        return "[]"
    # Удаляем .0 для целых чисел
    formatted = [str(int(x)) if x.is_integer() else str(x) for x in solution]
    return f"[{';'.join(formatted)}]"

# Генерация легкого уравнения с целым корнем
def easy_equation():
    a = random.randint(1, 10)
    x = random.randint(-10, 10)  # Целый корень
    b = -a * x  # ax + b = 0 => b = -ax

    # Формируем уравнение, опуская коэффициент 1
    equation = f"x" if a == 1 else f"{a}x"
    if b < 0:
        equation += f" - {-b}"
    elif b > 0:
        equation += f" + {b}"
    equation += " = 0"

    return equation, [x]  # Возвращаем список для единообразия

# Генерация квадратного уравнения с целыми корнями
def medium_equation():
    while True:
        x1 = random.randint(-5, 5)  # Первый корень
        x2 = random.randint(-5, 5)  # Второй корень
        a = random.randint(1, 5)    # Коэффициент при x²

        # Уравнение: a(x - x1)(x - x2) = ax² - a(x1 + x2)x + a*x1*x2
        b = -a * (x1 + x2)
        c = a * x1 * x2

        if a != 0:
            break

    # Формируем уравнение, опуская коэффициент 1
    equation = f"x²" if a == 1 else f"{a}x²"
    if b != 0:  # Пропускаем член, если b == 0
        if b == 1:
            equation += f" + x"
        elif b == -1:
            equation += f" - x"
        elif b < 0:
            equation += f" - {-b}x"
        elif b > 0:
            equation += f" + {b}x"
    if c != 0:  # Пропускаем член, если c == 0
        if c < 0:
            equation += f" - {-c}"
        elif c > 0:
            equation += f" + {c}"
    equation += " = 0"

    solutions = [x1, x2] if x1 != x2 else [x1]
    return equation, sorted(solutions)  # Сортируем для единообразия

# Генерация кубического уравнения с хотя бы одним целым корнем
def hard_equation():
    while True:
        x1 = random.randint(-3, 3)  # Целый корень
        a = random.randint(1, 3)
        b = random.randint(-5, 5)
        c = random.randint(-5, 5)

        # Формируем уравнение: a(x - x1)(x² + bx + c) = 0
        # Разложение: ax³ + (ab - ax1)x² + (ac - abx1)x - acx1 = 0
        coef_b = a * b - a * x1
        coef_c = a * c - a * b * x1
        coef_d = -a * c * x1

        # Формируем уравнение, опуская коэффициент 1
        equation = f"x³" if a == 1 else f"{a}x³"
        if coef_b != 0:  # Пропускаем член, если coef_b == 0
            if coef_b == 1:
                equation += f" + x²"
            elif coef_b == -1:
                equation += f" - x²"
            elif coef_b < 0:
                equation += f" - {-coef_b}x²"
            elif coef_b > 0:
                equation += f" + {coef_b}x²"
        if coef_c != 0:  # Пропускаем член, если coef_c == 0
            if coef_c == 1:
                equation += f" + x"
            elif coef_c == -1:
                equation += f" - x"
            elif coef_c < 0:
                equation += f" - {-coef_c}x"
            elif coef_c > 0:
                equation += f" + {coef_c}x"
        if coef_d != 0:  # Пропускаем член, если coef_d == 0
            if coef_d < 0:
                equation += f" - {-coef_d}"
            elif coef_d > 0:
                equation += f" + {coef_d}"
        equation += " = 0"

        x = sympy.Symbol('x')
        solutions = sympy.solve(a * x**3 + coef_b * x**2 + coef_c * x + coef_d, x)
        real_solutions = [round(float(sol.evalf()), 2) for sol in solutions if sol.is_real]
        if real_solutions:  # Проверяем, есть ли действительные корни
            break

    return equation, sorted(real_solutions)

# Основная игра
def ask_equations(equations):
    score = 0
    mistakes = []
    user_answers = []  # Список для хранения пользовательских ответов

    for eq, solution in equations:
        user_answer = None
        for attempt in range(3):
            prompt = f"Решите уравнение: {eq} (введите ответ в формате [x;y]) "
            user_answer = get_input(prompt, allow_text=True).strip()

            try:
                # Проверяем, что ответ в квадратных скобках
                if not (user_answer.startswith('[') and user_answer.endswith(']')):
                    raise ValueError("Ответ должен быть в квадратных скобках.")

                # Преобразуем строку в список чисел
                user_answer_processed = user_answer[1:-1].strip()
                if user_answer_processed:  # Если список не пуст
                    user_solutions = [round(float(x.strip()), 2) for x in user_answer_processed.split(';')]
                else:
                    user_solutions = []

                # Сравниваем списки решений (с учетом сортировки)
                if sorted(user_solutions) == sorted(solution):
                    draw_text("Правильно! Отличная работа!", 50, 200)
                    pygame.display.flip()
                    pygame.time.wait(2000)
                    score += 1
                    user_answers.append((eq, user_answer, solution))
                    break
                else:
                    draw_text("Неправильно. Попробуйте еще раз.", 50, 200)
                    pygame.display.flip()
                    pygame.time.wait(2000)
            except (ValueError, SyntaxError):
                draw_text("Ошибка ввода. Ответ должен быть в формате [x;y].", 50, 200)
                pygame.display.flip()
                pygame.time.wait(2000)
        else:
            mistakes.append((eq, solution))
            user_answers.append((eq, user_answer, solution))
            screen.blit(background, (0, 0))
            draw_text(f"Неправильно. Ответ: {format_solution(solution)}", 50, 300)
            pygame.display.flip()
            
            # Автоматически переходим к следующему уравнению через 2 секунды
            start_time = pygame.time.get_ticks()
            while pygame.time.get_ticks() - start_time < 2000:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                pygame.time.wait(50)

    return score, mistakes, user_answers

# Функция для генерации случайного уравнения
def random_equation():
    level = random.choice([1, 2, 3])
    if level == 1:
        return easy_equation()
    elif level == 2:
        return medium_equation()
    else:
        return hard_equation()

# ========== РЕЖИМ 2: 16 задание ЕГЭ - Экономические задачи ==========

# Функция для извлечения числа из ответа (может содержать текст)
def extract_number_from_answer(answer):
    """
    Извлекает число из ответа, который может содержать текст.
    Например: "на 220 рублей" -> 220, "через 20 месяцев" -> 20
    """
    # Пробуем найти число в ответе
    # Ищем паттерны: число, дробь, процент
    number_patterns = [
        r'(\d+[.,]\d+)',  # Дробь с запятой или точкой
        r'(\d+)',  # Целое число
    ]
    
    for pattern in number_patterns:
        match = re.search(pattern, answer)
        if match:
            num_str = match.group(1).replace(',', '.')
            try:
                return float(num_str)
            except:
                continue
    
    # Если не нашли число, возвращаем None
    return None

# Функция для парсинга задач из текстового файла
def parse_tasks_from_file(filename):
    """
    Парсит задачи из текстового файла.
    Формат: каждая задача начинается с номера (например, "1."), содержит текст и заканчивается "Ответ: ..."
    Возвращает список кортежей (текст_задачи, ответ)
    """
    tasks = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Разбиваем на строки для обработки
        lines = content.split('\n')
        
        current_task = []
        current_answer = None
        
        for line in lines:
            line = line.strip()
            
            # Проверяем, начинается ли строка с номера задачи (например, "1.", "2.", "10.", "№1.", "№2.")
            if re.match(r'^[№#]?\d+\.\s*', line):
                # Если есть предыдущая задача, сохраняем её
                if current_task and current_answer is not None:
                    problem_text = '\n'.join(current_task).strip()
                    # Убираем строку с ответом, если она есть в тексте
                    problem_text = re.sub(r'Ответ:\s*.+', '', problem_text, flags=re.IGNORECASE).strip()
                    if problem_text:
                        tasks.append((problem_text, current_answer))
                
                # Начинаем новую задачу
                # Убираем номер из начала строки (может быть "№1.", "1.", "#1.")
                task_start = re.sub(r'^[№#]?\d+\.\s*', '', line)
                current_task = [task_start] if task_start else []
                current_answer = None
            
            # Проверяем, содержит ли строка ответ
            elif re.match(r'^Ответ:\s*', line, re.IGNORECASE):
                answer_match = re.search(r'Ответ:\s*(.+)', line, re.IGNORECASE)
                if answer_match:
                    current_answer = answer_match.group(1).strip()
                    # Убираем точку в конце, если есть
                    if current_answer.endswith('.'):
                        current_answer = current_answer[:-1].strip()
            
            # Добавляем строку к текущей задаче
            elif line:  # Добавляем только непустые строки
                current_task.append(line)
        
        # Сохраняем последнюю задачу
        if current_task and current_answer is not None:
            problem_text = '\n'.join(current_task).strip()
            # Убираем строку с ответом, если она есть в тексте
            problem_text = re.sub(r'Ответ:\s*.+', '', problem_text, flags=re.IGNORECASE).strip()
            if problem_text:
                tasks.append((problem_text, current_answer))
                
    except FileNotFoundError:
        print(f"Файл {filename} не найден")
    except Exception as e:
        print(f"Ошибка при чтении файла {filename}: {e}")
    
    return tasks

# Загрузка задач для режима 2 (16.txt)
EGE_TASKS = []
# Относительный путь к файлу задач ЕГЭ (относительно директории скрипта)
ege_file_path = os.path.join(os.path.dirname(__file__), "16.txt")
EGE_TASKS = parse_tasks_from_file(ege_file_path)

# ========== РЕЖИМ 3: Практические задачи по экономике ==========

# Загрузка задач для режима 3 (Экономика.txt)
PRACTICAL_TASKS = []
# Относительный путь к файлу практических задач (относительно директории скрипта)
practical_file_path = os.path.join(os.path.dirname(__file__), "Экономика.txt")
PRACTICAL_TASKS = parse_tasks_from_file(practical_file_path)

# Функция для отображения многострочного текста с прокруткой
def show_scrollable_text(lines, title="", allow_nav=False):
    """
    Отображает многострочный текст с возможностью прокрутки
    allow_nav - разрешить навигацию стрелками влево/вправо
    """
    offset_y = 0
    line_height = 30
    hint_height = 40  # Место для подсказки внизу
    title_height = 40 if title else 0  # Место для заголовка сверху
    
    # Вычисляем максимальное смещение для контента
    content_area_height = SCREEN_HEIGHT - title_height - hint_height
    max_offset = max(0, len(lines) * line_height - content_area_height)
    
    while True:
        screen.blit(background, (0, 0))
        
        # Заголовок (фиксированный, не прокручивается)
        if title:
            draw_text(title, 50, 20)
            content_start_y = 60
        else:
            content_start_y = 50
        
        # Контент (прокручивается)
        content_end_y = SCREEN_HEIGHT - hint_height
        y = content_start_y - offset_y
        for line in lines:
            if content_start_y <= y <= content_end_y:  # Показываем только в видимой области
                draw_text(line, 50, y)
            y += line_height
        
        # Подсказка о прокрутке (внизу, фиксированная)
        hint_text = ""
        if max_offset > 0:
            hint_text = "Стрелки вверх/вниз - прокрутка"
        if allow_nav:
            if hint_text:
                hint_text += ", "
            hint_text += "←/→ - навигация, ESC - в начало"
        if hint_text:
            draw_text(hint_text, 50, SCREEN_HEIGHT - 35)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and allow_nav:
                    return 'esc'  # Возвращаем 'esc' для возврата в начало
                elif event.key == pygame.K_UP:
                    offset_y = max(0, offset_y - LINE_SPACING)
                elif event.key == pygame.K_DOWN:
                    offset_y = min(max_offset, offset_y + LINE_SPACING)
                elif allow_nav:
                    if event.key == pygame.K_LEFT:
                        return 'nav_left'
                    elif event.key == pygame.K_RIGHT:
                        return 'nav_right'
            if event.type == pygame.MOUSEWHEEL:
                offset_y = min(max_offset, max(0, offset_y - event.y * LINE_SPACING))

# Обновленная инструкция
def show_instructions_and_link():
    greeting = [
        "Добро пожаловать в Тренажер уравнений и экономических задач!",
        "",
        "Эта программа поможет вам подготовиться к ЕГЭ и",
        "научиться решать практические экономические задачи.",
        "",
        "Используйте стрелки ← → для навигации между слайдами."
    ]

    instructions = [
        "РЕЖИМ 1: Решение уравнений",
        "Выберите этот режим, если хотите тренироваться решать уравнения.",
        "Подрежимы:",
        "  - Легкий: линейные уравнения",
        "  - Средний: квадратные уравнения",
        "  - Сложный: кубические уравнения",
        "  - Случайный: уравнения всех уровней",
        "",
        "РЕЖИМ 2: 16 задание ЕГЭ - Экономические задачи",
        "Выберите этот режим для подготовки к заданию 16 ЕГЭ по математике.",
        "Типы задач:",
        "  - Задачи на кредиты (дифференцированные и аннуитетные платежи)",
        "  - Задачи на вклады с капитализацией",
        "  - Задачи на оптимизацию производства",
        "",
        "РЕЖИМ 3: Практические задачи по экономике",
        "Выберите этот режим для решения реальных задач,",
        "с которыми сталкиваются предприниматели и обычные люди.",
        "Типы задач:",
        "  - Расчет стоимости покупки со скидками",
        "  - Расчет зарплаты с налогами и премиями",
        "  - Расчет коммунальных платежей",
        "  - Расчет прибыли от бизнеса",
        "  - Расчет ипотечных платежей",
        "",
        "ОБЩИЕ ПРАВИЛА:",
        "1. Для каждого задания у вас есть 3 попытки.",
        "2. В режиме 1 ответы вводятся в формате [x;y;...].",
        "3. В режимах 2 и 3 ответы - целые числа или конечные дроби.",
        "4. Кликните на поле ввода, чтобы оно стало активным (синим).",
        "5. После правильного ответа вы получите сообщение об успехе.",
        "6. Если ответ неверный, используйте Backspace для исправления.",
        "7. В конце будет показан ваш счет и сравнение ответов.",
        "",
        "НАВИГАЦИЯ (до начала решения задач):",
        "- ESC - вернуться в начало (первый слайд)",
        "- Стрелки ← → - перейти на 1 слайд назад/вперед",
        "- Backspace - удалить символ в поле ввода",
        ""
    ]

    link_instruction = "Перед началом тренировки уравнений можете пройти теоретические мини-игры:"
    link_text = "https://learningapps.org/watch?v=p6fddkuit25"

    # Система навигации по слайдам
    current_slide = 0
    total_slides = 3  # Приветствие, Инструкция, Ссылка
    
    while True:
        if current_slide == 0:
            # Слайд 1: Приветствие
            result = show_scrollable_text(greeting, allow_nav=True)
            if result == 'esc':
                return 'esc'  # Возврат в начало
            elif result == 'nav_right':  # Стрелка вправо
                current_slide = 1
            elif result == 'nav_left':
                current_slide = total_slides - 1  # Переход к последнему слайду
        elif current_slide == 1:
            # Слайд 2: Инструкция
            result = show_scrollable_text(instructions, "ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ ТРЕНАЖЕРА", allow_nav=True)
            if result == 'esc':
                return 'esc'  # Возврат в начало
            elif result == 'nav_right':  # Стрелка вправо
                current_slide = 2
            elif result == 'nav_left':
                current_slide = 0  # Возврат к первому слайду
        elif current_slide == 2:
            # Слайд 3: Ссылка
            screen.blit(background, (0, 0))
            draw_text(link_instruction, 50, 100)
            draw_text(link_text, 50, 150)
            draw_text("→ - к главному меню, ← - назад, ESC - в начало", 50, SCREEN_HEIGHT - 30)
            pygame.display.flip()
            
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return 'esc'  # Возврат в начало
                        elif event.key == pygame.K_LEFT:
                            current_slide = 1
                            break
                        elif event.key == pygame.K_RIGHT:
                            # Стрелка вправо на последнем слайде - переход к главному меню
                            return
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        link_rect = pygame.Rect(50, 150, len(link_text) * 10, 30)
                        if link_rect.collidepoint(event.pos):
                            webbrowser.open(link_text)
                else:
                    continue
                break

# Функция для работы с экономическими задачами (режимы 2 и 3)
def ask_economic_tasks(tasks):
    """Обработка экономических задач с числовыми ответами"""
    score = 0
    mistakes = []
    user_answers = []
    
    for problem, solution in tasks:
        user_answer = None
        correct_answer = solution[0]  # Для экономических задач ответ - число или строка
        error_message = None  # Сообщение об ошибке для отображения
        
        # Определяем, является ли правильный ответ числом или строкой
        is_numeric_answer = isinstance(correct_answer, (int, float))
        
        for attempt in range(3):
            # Разбиваем задачу на строки для отображения и убираем пустые строки
            problem_lines = [line.strip() for line in problem.split('\n') if line.strip()]
            
            prompt = "Введите ответ (целое число или дробь): "
            # Передаем задачу как additional_lines, чтобы она отображалась на том же экране
            # Передаем текущий ответ, чтобы он сохранялся при ошибке
            # Передаем сообщение об ошибке как bottom_lines, чтобы оно было под полем ввода
            bottom_msg = [error_message] if error_message else None
            user_answer = get_input(prompt, allow_text=True, additional_lines=problem_lines, 
                                   initial_text=user_answer if user_answer else '',
                                   bottom_lines=bottom_msg).strip()
            
            # Проверяем ESC (хотя в режиме решения задач ESC не должен работать, но на всякий случай)
            if user_answer == 'esc':
                return score, mistakes, user_answers
            
            # Если правильный ответ - строка, сравниваем как строки
            if not is_numeric_answer:
                if user_answer.lower().strip() == str(correct_answer).lower().strip():
                    # Правильный ответ (строковое сравнение)
                    screen.blit(background, (0, 0))
                    y = 50
                    max_text_width = SCREEN_WIDTH - 100
                    # Убираем пустые строки
                    clean_problem_lines = [line.strip() for line in problem.split('\n') if line.strip()]
                    for line in clean_problem_lines:
                        wrapped = wrap_text(line, max_text_width)
                        for wrapped_line in wrapped:
                            draw_text(wrapped_line, 50, y)
                            y += 30
                    draw_text("Правильно! Отличная работа!", 50, y + 20)
                    pygame.display.flip()
                    
                    start_time = pygame.time.get_ticks()
                    while pygame.time.get_ticks() - start_time < 2000:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                exit()
                        pygame.time.wait(50)
                    
                    score += 1
                    user_answers.append((problem, user_answer, correct_answer))
                    error_message = None
                    break
                else:
                    error_message = "Неправильно. Попробуйте еще раз."
                    continue
            
            # Если правильный ответ - число, сравниваем как числа
            try:
                # Пробуем преобразовать в число (целое или дробь)
                # Заменяем запятую на точку для дробей
                user_answer_clean = user_answer.replace(',', '.')
                
                # Проверяем, является ли это дробью вида a/b
                if '/' in user_answer_clean:
                    parts = user_answer_clean.split('/')
                    if len(parts) == 2:
                        numerator = float(parts[0])
                        denominator = float(parts[1])
                        if denominator != 0:
                            user_value = numerator / denominator
                        else:
                            raise ValueError("Деление на ноль")
                    else:
                        raise ValueError("Неверный формат дроби")
                else:
                    user_value = float(user_answer_clean)
                
                # Сравниваем с точностью до 0.01
                if abs(user_value - correct_answer) < 0.01:
                    # Показываем задачу и сообщение об успехе на одном экране
                    screen.blit(background, (0, 0))
                    y = 50
                    max_text_width = SCREEN_WIDTH - 100
                    # Убираем пустые строки
                    clean_problem_lines = [line.strip() for line in problem.split('\n') if line.strip()]
                    for line in clean_problem_lines:
                        # Переносим длинные строки
                        wrapped = wrap_text(line, max_text_width)
                        for wrapped_line in wrapped:
                            draw_text(wrapped_line, 50, y)
                            y += 30
                    draw_text("Правильно! Отличная работа!", 50, y + 20)
                    pygame.display.flip()
                    
                    # Обрабатываем события во время ожидания, чтобы программа не зависала
                    start_time = pygame.time.get_ticks()
                    while pygame.time.get_ticks() - start_time < 2000:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                exit()
                        pygame.time.wait(50)
                    
                    score += 1
                    user_answers.append((problem, user_answer, correct_answer))
                    error_message = None  # Сбрасываем сообщение об ошибке
                    break  # Выходим из цикла попыток, переходим к следующей задаче
                else:
                    # Устанавливаем сообщение об ошибке для следующего ввода
                    error_message = "Неправильно. Попробуйте еще раз."
                    # Продолжаем цикл, текст останется в поле ввода
            except (ValueError, SyntaxError):
                # Устанавливаем сообщение об ошибке ввода для следующего ввода
                error_message = "Ошибка ввода. Введите число или дробь (например: 1000 или 0,5)."
                # Продолжаем цикл, текст останется в поле ввода
        else:
            error_message = None  # Сбрасываем сообщение об ошибке перед показом правильного ответа
            mistakes.append((problem, solution))
            user_answers.append((problem, user_answer, correct_answer))
            screen.blit(background, (0, 0))
            y = 50
            max_text_width = SCREEN_WIDTH - 100
            # Убираем пустые строки из problem_lines
            clean_problem_lines = [line.strip() for line in problem.split('\n') if line.strip()]
            for line in clean_problem_lines:
                # Переносим длинные строки
                wrapped = wrap_text(line, max_text_width)
                for wrapped_line in wrapped:
                    draw_text(wrapped_line, 50, y)
                    y += 30
            # Форматируем правильный ответ
            if isinstance(correct_answer, (int, float)):
                if isinstance(correct_answer, int) or (isinstance(correct_answer, float) and correct_answer.is_integer()):
                    answer_str = str(int(correct_answer))
                else:
                    answer_str = str(round(correct_answer, 2))
            else:
                # Если ответ - строка, просто выводим её
                answer_str = str(correct_answer)
            answer_msg = f"Неправильно. Правильный ответ: {answer_str}"
            answer_wrapped = wrap_text(answer_msg, max_text_width)
            for answer_line in answer_wrapped:
                draw_text(answer_line, 50, y)
                y += 30
            pygame.display.flip()
            
            # Автоматически переходим к следующей задаче через 2 секунды
            start_time = pygame.time.get_ticks()
            while pygame.time.get_ticks() - start_time < 2000:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                pygame.time.wait(50)
    
    return score, mistakes, user_answers

# Функция для выбора уровня с навигацией
def choose_level():
    """Выбор уровня с навигацией стрелками"""
    levels = [
        ("1", "Легкий - линейные уравнения"),
        ("2", "Средний - квадратные уравнения"),
        ("3", "Сложный - кубические уравнения"),
        ("4", "Случайный - уравнения всех уровней")
    ]
    current_index = 0
    
    clock = pygame.time.Clock()
    while True:
        screen.blit(background, (0, 0))
        draw_text("РЕЖИМ 1: Решение уравнений", 50, 50)
        draw_text("Выберите уровень (←/→ - навигация, цифра 1-4 - выбрать, ESC - назад):", 50, 100)
        
        y = 150
        for i, (num, desc) in enumerate(levels):
            if i == current_index:
                # Выделяем текущий выбор
                draw_text(f"> {num}. {desc} <", 50, y)
            else:
                draw_text(f"  {num}. {desc}", 50, y)
            y += 40
        
        pygame.display.flip()
        clock.tick(60)  # Ограничиваем FPS
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'esc'
                elif event.key == pygame.K_LEFT:
                    current_index = (current_index - 1) % len(levels)
                    break  # Выходим из цикла обработки событий, чтобы обновить экран
                elif event.key == pygame.K_RIGHT:
                    current_index = (current_index + 1) % len(levels)
                    break  # Выходим из цикла обработки событий, чтобы обновить экран
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                    # Прямой выбор по цифре
                    return str(event.key - pygame.K_0)

# Функция главного меню
def show_main_menu():
    """Отображает главное меню с выбором режима"""
    menu_text = [
        "ГЛАВНОЕ МЕНЮ",
        "",
        "Это программа-тренажер для решения уравнений и",
        "экономических задач. Выберите режим работы:",
        "",
        "РЕЖИМ 1: Решение уравнений",
        "  Тренировка решения линейных, квадратных и",
        "  кубических уравнений. Подходит для подготовки",
        "  к базовым заданиям ЕГЭ.",
        "",
        "РЕЖИМ 2: 16 задание ЕГЭ - Экономические задачи",
        "  Задачи на кредиты, вклады и оптимизацию.",
        "  Идеально для подготовки к заданию 16 ЕГЭ.",
        "",
        "РЕЖИМ 3: Практические задачи по экономике",
        "  Реальные задачи из жизни: покупки, зарплата,",
        "  коммунальные платежи, бизнес, ипотека.",
        "",
        "Введите номер режима (1, 2 или 3):",
        "Нажмите ESC для просмотра инструкции"
    ]
    
    while True:
        screen.blit(background, (0, 0))
        y = 50
        for line in menu_text:
            draw_text(line, 50, y)
            y += 30
        pygame.display.flip()
        
        mode = get_input("Выберите режим (1, 2, 3): ", allow_text=True, allow_esc=True).strip().lower()
        
        if mode == 'esc' or mode == 'escape':
            show_instructions_and_link()
            continue
        elif mode in ['1', '2', '3']:
            return mode
        else:
            screen.blit(background, (0, 0))
            draw_text("Неверный ввод. Введите 1, 2, 3 или нажмите ESC, чтобы вернуться в главное меню.", 50, 200)
            pygame.display.flip()
            pygame.time.wait(2000)
            continue

# Функция для отображения результатов
def show_results(score, total, user_answers, mode):
    """Отображает результаты с прокруткой"""
    offset_y = 0
    max_offset = max(0, len(user_answers) * 100 - (SCREEN_HEIGHT - 200))
    waiting = True
    
    clock = pygame.time.Clock()
    while waiting:
        screen.blit(background, (0, 0))
        draw_text(f"Ваш счет: {score}/{total}", 50, 50)
        draw_text("Сравнение ответов (стрелки вверх/вниз - прокрутка, → - продолжить):", 50, 100)
        y_offset = 150 - offset_y
        
        for i, (task, user_ans, correct_ans) in enumerate(user_answers):
            # Проверяем, попадает ли задача в видимую область
            task_start_y = y_offset
            
            # Рисуем разделительную линию перед задачей (кроме первой)
            if i > 0 and task_start_y > 150:
                pygame.draw.line(screen, (150, 150, 150), (50, task_start_y - 5), (SCREEN_WIDTH - 50, task_start_y - 5), 2)
                y_offset += 10
            
            if 0 <= y_offset <= SCREEN_HEIGHT:
                # Номер задачи
                draw_text(f"--- Задача {i + 1} ---", 50, y_offset)
                y_offset += 30
                
                # Разбиваем задачу на строки и переносим длинные строки
                task_lines = task.split('\n')
                max_text_width = SCREEN_WIDTH - 100
                for line in task_lines[:2]:  # Показываем первые 2 строки задачи
                    # Переносим длинные строки
                    wrapped = wrap_text(line, max_text_width)
                    for wrapped_line in wrapped:
                        if 0 <= y_offset <= SCREEN_HEIGHT:
                            draw_text(wrapped_line, 50, y_offset)
                            y_offset += 25
                
                # Проверяем правильность ответа для цветового выделения
                is_correct = False
                try:
                    if isinstance(correct_ans, list):
                        user_ans_clean = user_ans.replace('[', '').replace(']', '').strip()
                        correct_ans_str = format_solution(correct_ans)
                        is_correct = (user_ans_clean == correct_ans_str.replace('[', '').replace(']', '').strip())
                    else:
                        user_ans_clean = user_ans.replace(',', '.').strip()
                        if '/' in user_ans_clean:
                            parts = user_ans_clean.split('/')
                            if len(parts) == 2:
                                user_value = float(parts[0]) / float(parts[1])
                            else:
                                user_value = float(user_ans_clean)
                        else:
                            user_value = float(user_ans_clean)
                        
                        if isinstance(correct_ans, (int, float)):
                            is_correct = abs(user_value - correct_ans) < 0.01
                except:
                    is_correct = False
                
                # Цвет для ответа пользователя
                answer_color = (0, 150, 0) if is_correct else (200, 0, 0)
                
                # Ваш ответ (с цветом)
                answer_surface = font.render(f"Ваш ответ: {user_ans}", True, answer_color)
                if 0 <= y_offset <= SCREEN_HEIGHT:
                    screen.blit(answer_surface, (50, y_offset))
                y_offset += 25
                
                # Форматируем правильный ответ
                if isinstance(correct_ans, list):
                    answer_str = format_solution(correct_ans)
                else:
                    if isinstance(correct_ans, (int, float)) and (isinstance(correct_ans, int) or correct_ans.is_integer()):
                        answer_str = str(int(correct_ans))
                    else:
                        answer_str = str(round(correct_ans, 2))
                
                draw_text(f"Правильный ответ: {answer_str}", 50, y_offset)
                y_offset += 40  # Увеличиваем отступ между задачами
        pygame.display.flip()
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    waiting = False
                elif event.key == pygame.K_UP:
                    offset_y = max(0, offset_y - LINE_SPACING)
                elif event.key == pygame.K_DOWN:
                    offset_y = min(max_offset, offset_y + LINE_SPACING)
            if event.type == pygame.MOUSEWHEEL:
                offset_y = min(max_offset, max(0, offset_y - event.y * LINE_SPACING))

# Функция для отображения итоговых результатов и выбора действия
def show_final_results(score, total, mistakes):
    """Показывает итоговые результаты с количеством правильных/неправильных ответов"""
    correct = score
    incorrect = total - score
    
    while True:
        screen.blit(background, (0, 0))
        draw_text("ИТОГОВЫЕ РЕЗУЛЬТАТЫ", 50, 50)
        draw_text(f"Всего заданий: {total}", 50, 100)
        draw_text(f"Правильных ответов: {correct}", 50, 150)
        draw_text(f"Неправильных ответов: {incorrect}", 50, 200)
        
        if total > 0:
            percentage = round((correct / total) * 100, 1)
            draw_text(f"Процент правильных ответов: {percentage}%", 50, 250)
        
        draw_text("", 50, 300)
        draw_text("Хотите продолжить или завершить сеанс?", 50, 320)
        
        pygame.display.flip()
        
        choice = get_input("Введите 'да' или 'нет': ", allow_text=True, allow_esc=False).lower().strip()
        
        if choice in ['да', 'yes', 'y', 'д', 'дa']:
            return True
        elif choice in ['нет', 'no', 'n', 'н', 'нeт']:
            return False
        else:
            screen.blit(background, (0, 0))
            draw_text("Неверный ввод. Введите 'да' или 'нет'.", 50, 200)
            pygame.display.flip()
            pygame.time.wait(2000)
            continue

# Основная функция
def main():
    while True:
        # Показываем инструкцию при первом запуске или по запросу
        result = show_instructions_and_link()
        if result == 'esc':
            # ESC возвращает в начало - показываем инструкцию снова
            continue
        
        # Главное меню
        mode = show_main_menu()
        
        if mode == '1':
            # РЕЖИМ 1: Уравнения (существующий функционал)
            while True:
                level = choose_level()
                if level == 'esc':
                    break  # Возврат в главное меню

                try:
                    count = int(get_input("Сколько уравнений хотите решить? "))
                except ValueError:
                    draw_text("Ошибка ввода. Введите корректное число.", 50, 200)
                    pygame.display.flip()
                    pygame.time.wait(2000)
                    continue

                equations = []
                for _ in range(count):
                    if level == '1':
                        equations.append(easy_equation())
                    elif level == '2':
                        equations.append(medium_equation())
                    elif level == '3':
                        equations.append(hard_equation())
                    elif level == '4':
                        equations.append(random_equation())

                score, mistakes, user_answers = ask_equations(equations)
                show_results(score, count, user_answers, 1)
                
                # Показываем итоговые результаты и выбор действия
                if not show_final_results(score, count, mistakes):
                    # Показываем слайд прощания
                    screen.blit(background, (0, 0))
                    draw_text("Спасибо за использование программы!", 50, 200)
                    draw_text("До свидания!", 50, 250)
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    return
        
        elif mode == '2':
            # РЕЖИМ 2: 16 задание ЕГЭ
            while True:
                screen.blit(background, (0, 0))
                draw_text("РЕЖИМ 2: 16 задание ЕГЭ - Экономические задачи", 50, 50)
                pygame.display.flip()
                
                try:
                    count_input = get_input("Сколько задач хотите решить?", allow_esc=True)
                    if count_input == 'esc':
                        break
                    count = int(count_input)
                except ValueError:
                    draw_text("Ошибка ввода. Введите корректное число.", 50, 200)
                    pygame.display.flip()
                    pygame.time.wait(2000)
                    continue
                
                # Проверяем, есть ли задачи в файле
                if not EGE_TASKS:
                    screen.blit(background, (0, 0))
                    draw_text("Ошибка: файл 16.txt не найден или пуст.", 50, 200)
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    continue
                
                # Ограничиваем количество задач доступным количеством
                available_count = min(count, len(EGE_TASKS))
                
                # Случайно выбираем задачи из файла
                selected_tasks = random.sample(EGE_TASKS, available_count)
                tasks = []
                for problem, answer in selected_tasks:
                    # Преобразуем ответ в число, если возможно
                    num_value = extract_number_from_answer(answer)
                    if num_value is not None:
                        tasks.append((problem, [num_value]))
                    else:
                        # Если не удалось извлечь число, пробуем стандартное преобразование
                        try:
                            answer_clean = answer.replace(',', '.').replace('%', '').strip()
                            if answer_clean.endswith('.'):
                                answer_clean = answer_clean[:-1].strip()
                            # Если это дробь вида "a/b"
                            if '/' in answer_clean:
                                parts = answer_clean.split('/')
                                if len(parts) == 2:
                                    num_value = float(parts[0]) / float(parts[1])
                                else:
                                    num_value = float(answer_clean)
                            else:
                                num_value = float(answer_clean)
                            tasks.append((problem, [num_value]))
                        except:
                            # Если не удалось преобразовать, возвращаем как строку
                            tasks.append((problem, [answer]))
                
                if not tasks:
                    continue
                
                score, mistakes, user_answers = ask_economic_tasks(tasks)
                show_results(score, count, user_answers, 2)
                
                # Показываем итоговые результаты и выбор действия
                if not show_final_results(score, count, mistakes):
                    # Показываем слайд прощания
                    screen.blit(background, (0, 0))
                    draw_text("Спасибо за использование программы!", 50, 200)
                    draw_text("До свидания!", 50, 250)
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    return
        
        elif mode == '3':
            # РЕЖИМ 3: Практические задачи
            while True:
                screen.blit(background, (0, 0))
                draw_text("РЕЖИМ 3: Практические задачи по экономике", 50, 50)
                pygame.display.flip()
                
                try:
                    count_input = get_input("Сколько задач хотите решить?", allow_esc=True)
                    if count_input == 'esc':
                        break
                    count = int(count_input)
                except ValueError:
                    draw_text("Ошибка ввода. Введите корректное число.", 50, 200)
                    pygame.display.flip()
                    pygame.time.wait(2000)
                    continue
                
                # Проверяем, есть ли задачи в файле
                if not PRACTICAL_TASKS:
                    screen.blit(background, (0, 0))
                    draw_text("Ошибка: файл Экономика.txt не найден или пуст.", 50, 200)
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    continue
                
                # Ограничиваем количество задач доступным количеством
                available_count = min(count, len(PRACTICAL_TASKS))
                
                # Случайно выбираем задачи из файла
                selected_tasks = random.sample(PRACTICAL_TASKS, available_count)
                tasks = []
                for problem, answer in selected_tasks:
                    # Преобразуем ответ в число, если возможно
                    num_value = extract_number_from_answer(answer)
                    if num_value is not None:
                        tasks.append((problem, [num_value]))
                    else:
                        # Если не удалось извлечь число, пробуем стандартное преобразование
                        try:
                            answer_clean = answer.replace(',', '.').replace('%', '').strip()
                            if answer_clean.endswith('.'):
                                answer_clean = answer_clean[:-1].strip()
                            # Если это дробь вида "a/b"
                            if '/' in answer_clean:
                                parts = answer_clean.split('/')
                                if len(parts) == 2:
                                    num_value = float(parts[0]) / float(parts[1])
                                else:
                                    num_value = float(answer_clean)
                            else:
                                num_value = float(answer_clean)
                            tasks.append((problem, [num_value]))
                        except:
                            # Если не удалось преобразовать, возвращаем как строку
                            tasks.append((problem, [answer]))
                
                if not tasks:
                    continue
                
                score, mistakes, user_answers = ask_economic_tasks(tasks)
                show_results(score, count, user_answers, 3)
                
                # Показываем итоговые результаты и выбор действия
                if not show_final_results(score, count, mistakes):
                    # Показываем слайд прощания
                    screen.blit(background, (0, 0))
                    draw_text("Спасибо за использование программы!", 50, 200)
                    draw_text("До свидания!", 50, 250)
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    return

if __name__ == "__main__":
    main()
    pygame.quit()