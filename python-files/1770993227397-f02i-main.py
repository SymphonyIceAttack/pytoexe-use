"""
===========================================
QUIZ APPLICATION - Приложение-викторина
===========================================

Это консольное приложение для проведения викторины с визуальными подсказками.
Программа задает вопросы пользователю и показывает картинки при правильных/неправильных ответах.

СТРУКТУРА ПРОГРАММЫ:
1. Импорты библиотек
2. Вспомогательные функции (get_resource_path, kartinka)
3. Основная функция викторины (ask_question)
4. Набор вопросов с вызовами ask_question

ИСПОЛЬЗУЕМЫЕ БИБЛИОТЕКИ:
- os: работа с файловой системой
- sys: системные параметры и функции
- tkinter: создание графических окон для показа изображений
- PIL (Pillow): обработка и отображение изображений
"""

# ============================================
# ИМПОРТ НЕОБХОДИМЫХ БИБЛИОТЕК
# ============================================

import os  # Для работы с путями к файлам
import sys  # Для определения режима работы (скрипт или EXE)
import tkinter as tk  # Для создания графических окон
from lib.PIL import Image, ImageTk  # Для работы с изображениями


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================


def get_resource_path(relative_path):
    """
    Получает абсолютный путь к ресурсу (изображению, файлу).

    Эта функция необходима для корректной работы как в режиме скрипта,
    так и в режиме скомпилированного EXE-файла.

    ПАРАМЕТРЫ:
        relative_path (str): относительный путь к файлу (например, "images/image1.png")

    ВОЗВРАЩАЕТ:
        str: абсолютный путь к файлу

    КАК ЭТО РАБОТАЕТ:
        - При запуске как EXE: PyInstaller создает временную папку (_MEIPASS)
          и распаковывает туда все ресурсы. Функция возвращает путь к этой папке.
        - При запуске как скрипт: возвращает обычный абсолютный путь от текущей директории.
    """
    # Проверяем, запущена ли программа как скомпилированный EXE
    if hasattr(sys, "_MEIPASS"):
        # Если да - используем временную папку PyInstaller
        return os.path.join(sys._MEIPASS, relative_path)
    # Если нет - используем обычный путь
    return os.path.abspath(relative_path)


def kartinka(image_path, duration=3):
    """
    Показывает изображение во всплывающем окне на заданное время.

    ПАРАМЕТРЫ:
        image_path (str): путь к файлу изображения
        duration (int): время показа в секундах (по умолчанию 3 секунды)

    ВОЗВРАЩАЕТ:
        None

    КАК ЭТО РАБОТАЕТ:
        1. Получает полный путь к изображению через get_resource_path
        2. Создает окно Tkinter без рамок
        3. Загружает и масштабирует изображение (максимум 600x600 пикселей)
        4. Центрирует окно на экране
        5. Автоматически закрывает окно через заданное время
    """
    try:
        # Получаем полный путь к изображению (работает и для EXE, и для скрипта)
        full_path = get_resource_path(image_path)

        # Проверяем, существует ли файл
        if not os.path.exists(full_path):
            print(f"Ошибка: Файл не найден по пути: {full_path}")
            return

        # Создаем окно
        root = tk.Tk()
        root.title("Quiz Image")

        # Попробуем поднять окно на передний план
        root.attributes("-topmost", True)

        # Убираем рамки окна (делаем окно без заголовка и кнопок)
        root.overrideredirect(True)

        # Загружаем картинку
        img = Image.open(full_path)
        img.thumbnail((600, 600))  # Уменьшаем до 600x600, сохраняя пропорции

        # Конвертируем изображение в формат Tkinter
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(root, image=photo, bg="black")
        label.pack()

        # Центрируем окно на экране
        root.update_idletasks()  # Обновляем окно для получения размеров
        width = root.winfo_width()
        height = root.winfo_height()
        # Вычисляем координаты центра экрана
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")

        # Закрываем через заданное время (в миллисекундах)
        root.after(int(duration * 1000), root.destroy)
        root.mainloop()  # Запускаем главный цикл окна
    except Exception as e:
        print(f"Картинка не открылась: {e}")


# ============================================
# ОСНОВНАЯ ФУНКЦИЯ ВИКТОРИНЫ
# ============================================


def ask_question(lines, correct_answer, success_img):
    """
    Задает вопрос пользователю и проверяет ответ.
    Повторяет вопрос до тех пор, пока не будет дан правильный ответ.

    ПАРАМЕТРЫ:
        lines (list): список строк с текстом вопроса и вариантами ответов
        correct_answer (str или list): правильный ответ (или список правильных ответов)
        success_img (str): путь к изображению, которое показывается при правильном ответе

    ВОЗВРАЩАЕТ:
        None

    КАК ЭТО РАБОТАЕТ:
        1. Выводит вопрос и варианты ответов в консоль
        2. Получает ответ пользователя
        3. Проверяет правильность ответа
        4. При правильном ответе - показывает картинку успеха и переходит к следующему вопросу
        5. При неправильном ответе - показывает картинку ошибки и повторяет вопрос
    """
    # Бесконечный цикл - выходим только при правильном ответе
    while True:
        # Выводим все строки вопроса (текст вопроса + варианты ответов)
        for line in lines:
            print(line)

        # Получаем ответ от пользователя
        otvet = input("Enter answer: ")

        # Проверяем правильность ответа
        is_correct = False

        # Если правильных ответов несколько (список)
        if isinstance(correct_answer, list):
            if otvet in correct_answer:
                is_correct = True
        # Если правильный ответ один (строка)
        elif otvet == correct_answer:
            is_correct = True

        # Обрабатываем результат
        if is_correct:
            print("Correct!")  # Сообщаем об успехе
            kartinka(success_img)  # Показываем картинку успеха
            break  # Выходим из цикла, переходим к следующему вопросу
        else:
            print("Wrong! Try again.")  # Сообщаем об ошибке
            kartinka(r"images\image2.png")  # Показываем картинку ошибки
            # Цикл продолжается - вопрос повторяется

    # Разделитель между вопросами
    print("--------------------------------")


# ============================================
# НАБОР ВОПРОСОВ ВИКТОРИНЫ
# ============================================

# Вопрос 1
ask_question(
    [
        "The Christmas greeting is: (Рождественское приветствие звучит:)",
        "1: Happy Christmas!",
        "2: Merry Christmas!",
        "3: Lucky Christmas!",
        "4: Lovely Christmas!",
    ],
    "2",
    r"images\image1.png",
)

# Вопрос 2
ask_question(
    [
        "The main Christmas treat: (Главное рождественское угощение:)",
        "1: Duck",
        "2: Goose",
        "3: Turkey",
        "4: Chicken",
    ],
    "3",
    r"images\image3.png",
)

# Вопрос 3
ask_question(
    [
        "The symbol of Halloween is: (Символ Хэллоуина – это)",
        "1: Pumpkin",
        "2: Zucchini",
        "3: Watermelon",
        "4: Orange",
    ],
    "1",
    r"images\image4.png",
)

# Вопрос 4
ask_question(
    [
        "Which animal is most often used on Easter cards? (Какое животное чаще всего изображено на Пасхальных открытках?)",
        "1: Rabbit",
        "2: Fox",
        "3: Wolf",
        "4: Sheep",
    ],
    "1",
    r"images\image5.png",
)

# Вопрос 5
ask_question(
    [
        "Which plant is associated with St. Patrick's Day? (Какое растение ассоциируется с Днем Святого Патрика?)",
        "1: Sunflower",
        "2: Fern",
        "3: Shamrock",
        "4: Spruce",
    ],
    "3",
    r"images\image6.png",
)

# Вопрос 6
ask_question(
    [
        "One … a day, keeps doctors away!",
        "1: apple",
        "2: pear",
        "3: lemon",
        "4: ice cream",
    ],
    "1",
    r"images\image12.png",
)

# Вопрос 7
ask_question(
    ["Measure thrice and cut …", "1: once", "2: twice", "3: first", "4: last"],
    "1",
    r"images\image7.png",
)

# Вопрос 8
ask_question(
    [
        "Don’t judge a book by its ...",
        "1: Pictures",
        "2: Pages",
        "3: Cover",
        "4: Author",
    ],
    "3",
    r"images\image7.png",
)

# Вопрос 9
ask_question(
    [
        "A bird may be known by its …",
        "1: feathers",
        "2: break",
        "3: flight",
        "4: songs",
    ],
    "1",
    r"images\image7.png",
)

# Вопрос 10
ask_question(
    [
        "Which phrase is a good luck wish?",
        "1: Break a leg!",
        "2: Not a fluff or a feather!",
        "3: Best of luck!",
        "4: Blow them away!",
    ],
    ["1", "2", "3", "4"],
    r"images\image7.png",
)

# Вопрос 11
ask_question(
    [
        "What is the name of the tradition of afternoon tea drinking in England? (Как называется традиция послеобеденного чаепития в Англии?)",
        "1: 6 p.m",
        "2: 5 o'clock",
        "3: evening tea",
        "4: lunch",
    ],
    "2",
    r"images\image8.png",
)

# Вопрос 12
ask_question(
    [
        "Santa  delivers gifts through the: (Санта-Клаус доставляет подарки через:)",
        "1: backdoor",
        "2: window",
        "3: door",
        "4: chimney",
    ],
    "4",
    r"images\image9.png",
)

# Вопрос 13
ask_question(
    [
        "At Easter, parents hide, and children look for: (На Пасху родители прячутся, а дети ищут:)",
        "1: eggs",
        "2: cakes",
        "3: gifts",
        "4: candies",
    ],
    "1",
    r"images\image10.png",
)

# Вопрос 14
ask_question(
    [
        "Halloween is one of the favorite holidays of children who run through the streets in the most unusual costumes, knock on the doors of houses and greet the owners with the words:\n(Хэллоуин - один из любимых праздников детей, которые бегают по улицам в самых необычных костюмах, стучат в двери домов и приветствуют хозяев словами:)",
        "1: Happy Halloween",
        "2: Not a fluff or a feather",
        "3: Trick or treat!",
        "4: Good luck!",
    ],
    "3",
    r"images\image11.png",
)

# Вопрос 15
ask_question(
    [
        "In Ireland, it is customary to wear green clothes on St. Patrick's Day or attach a ** to one's clothing.",
        "1: Rose",
        "2: Shamrock",
        "3: Lily",
        "4: Fern",
    ],
    "2",
    r"images\image6.png",
)
