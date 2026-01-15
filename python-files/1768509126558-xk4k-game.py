# Метро: Тени Выбора — версия без видимой кармы
# 17 глав в 7 частях, скрытые последствия выборов

class Player:
    def __init__(self):
        self.name = "Артём"
        self.health = 100
        self.bullets = 120
        self.filters = 180  # минут
        self.day = 1
        self.part = 1
        self.chapter = 1
        self.inventory = ["АК-74у", "фонарик", "противогаз"]
        self.allies = []  # список союзников
        self.has_heart = False  # нашёл ли "Сердце Тьмы"


def print_status(player):
    print("\n" + "─" * 60)
    print(f"Часть {player.part}/7   Глава {player.chapter}/17")
    print(f"Здоровье: {player.health}%   Патроны: {player.bullets}")
    print(f"Фильтры: {player.filters // 60} ч   Союзники: {len(player.allies)}")
    print("─" * 60 + "\n")


def show_choice(prompt, options):
    print(prompt)
    for i, text in enumerate(options, 1):
        print(f"  {i}) {text}")
    print()

    while True:
        try:
            num = int(input("→ "))
            if 1 <= num <= len(options):
                return num
            print(f"Выбери от 1 до {len(options)}")
        except ValueError:
            print("Нужно ввести число")


def take_damage(player, amount):
    player.health -= amount
    if player.health < 0:
        player.health = 0
    return player.health > 0


def spend(player, resource, amount):
    if resource == "bullets" and player.bullets >= amount:
        player.bullets -= amount
        return True
    if resource == "filters" and player.filters >= amount:
        player.filters -= amount
        return True
    return False


# ──────────────────────────────────────────────────────────────
# ГЛАВЫ
# ──────────────────────────────────────────────────────────────

def ch1_vdnh_normal_day(player):
    print("Обычное утро на ВДНХ. Отчим просит помочь с генератором.\n")
    opt = [
        "Помочь починить генератор",
        "Сказать, что занят",
        "Поговорить о странных снах"
    ]
    res = show_choice("Что делаешь?", opt)
    if res == 1:
        print("Люди благодарны, атмосфера на станции чуть спокойнее.")
    elif res == 3:
        print("Отчим тихо рассказывает о голосах в вентиляции...")
    return True


def ch2_cry_in_tunnel(player):
    print("В туннеле слышится крик. Патруль попал в засаду.\n")
    opt = [
        "Бежать на помощь",
        "Затаиться в темноте",
        "Подождать и посмотреть, что будет"
    ]
    res = show_choice("Твоё решение?", opt)
    if res == 1:
        take_damage(player, 12)
        print("Ты успел вытащить одного из патрульных.")
    elif res == 2:
        print("Крик затихает. Становится очень тихо.")
    else:
        player.bullets += 15
        print("После боя ты подобрал несколько патронов.")
    return take_damage(player, 0)  # проверка, жив ли


def ch3_goodbye_vdnh(player):
    print("Пора уходить. Нужно добраться до Полиса.\n")
    opt = [
        "Взять припасы у товарища",
        "Оставить немного патронов для станции"
    ]
    res = show_choice("Последнее действие на ВДНХ:", opt)
    if res == 1:
        player.bullets += 40
    else:
        if spend(player, "bullets", 25):
            print("Ты оставил немного патронов...")
    player.part = 2
    return True


def ch4_rizhskaya(player):
    print("Рижская. Рейдеры требуют проход.\n")
    opt = [
        "Отдать патроны",
        "Попытаться прорваться",
        "Искать обходной путь"
    ]
    res = show_choice("Что выберешь?", opt)
    if res == 1:
        spend(player, "bullets", 60)
    elif res == 2:
        take_damage(player, 25)
        spend(player, "bullets", 30)
    else:
        spend(player, "filters", 40)
    return take_damage(player, 0)


def ch5_alexeevskaya(player):
    print("Алексеевская заброшена. Слышны шорохи.\n")
    opt = [
        "Пройти быстро и тихо",
        "Осмотреть станцию",
        "Устроить ловушку"
    ]
    res = show_choice("Как действовать?", opt)
    if res == 1:
        spend(player, "filters", 25)
    elif res == 2:
        if take_damage(player, 18):
            player.allies.append("выживший")
    else:
        spend(player, "bullets", 12)
    return take_damage(player, 0)


def ch6_prospekt_mira(player):
    print("Проспект Мира — торговая суета и подозрительные взгляды.\n")
    opt = [
        "Купить фильтры у торговца",
        "Поговорить с местным проповедником",
        "Уйти без лишних разговоров"
    ]
    res = show_choice("Твой выбор?", opt)
    if res == 1:
        if spend(player, "bullets", 45):
            player.filters += 90
    return True


def ch7_turgenevskaya(player):
    print("Тургеневская — настоящий лабиринт.\n")
    opt = [
        "Идти по основному туннелю",
        "Искать обходные пути",
        "Двигаться очень осторожно"
    ]
    res = show_choice("Как идти?", opt)
    if res == 1:
        take_damage(player, 15)
    elif res == 2:
        spend(player, "filters", 50)
    return take_damage(player, 0)


def ch8_kitay_gorod(player):
    print("Китай-город. Здесь торгуют всем.\n")
    opt = [
        "Попытаться договориться о помощи",
        "Пройти молча",
        "Угрожать, чтобы пропустили быстрее"
    ]
    res = show_choice("Что делать?", opt)
    if res == 1:
        if player.health > 40:
            player.allies.append("торговец")
    return True


def ch9_teatralnaya(player):
    print("Театральная. Напряжение между фракциями.\n")
    opt = [
        "Поддержать одну из сторон",
        "Сохранить нейтралитет",
        "Уйти как можно быстрее"
    ]
    res = show_choice("Твоё решение?", opt)
    if res == 1:
        player.allies.append("фракционер")
    return True


def ch10_polis_entrance(player):
    print("Ворота Полиса. Стража требует плату.\n")
    opt = [
        "Заплатить",
        "Попытаться убедить",
        "Прорваться силой"
    ]
    res = show_choice("Как попасть в Полис?", opt)
    if res == 1:
        spend(player, "bullets", 70)
    elif res == 3:
        take_damage(player, 30)
    return take_damage(player, 0)


def ch11_library(player):
    print("Библиотека. Здесь хранится что-то важное...\n")
    opt = [
        "Искать что-то конкретное",
        "Осмотреться и уйти",
        "Сразиться с библиотекарем"
    ]
    res = show_choice("Что будешь делать?", opt)
    if res == 1:
        if player.health > 30:
            player.has_heart = True
            print("Ты нашёл странный артефакт...")
    elif res == 3:
        spend(player, "bullets", 60)
        take_damage(player, 20)
    return take_damage(player, 0)


def ch12_surface_first_step(player):
    print("Поверхность. Воздух жжёт лёгкие.\n")
    opt = [
        "Использовать противогаз",
        "Бежать к цели без остановок"
    ]
    res = show_choice("Как двигаться?", opt)
    if res == 1:
        spend(player, "filters", 70)
    else:
        take_damage(player, 25)
    return take_damage(player, 0)


def ch13_botanical_garden(player):
    print("Ботанический сад. Зелень и кошмары.\n")
    opt = [
        "Пробиваться с боем",
        "Попытаться обойти",
        "Использовать союзника как отвлечение"
    ]
    res = show_choice("Твой план?", opt)
    if res == 1:
        spend(player, "bullets", 40)
    elif res == 3 and player.allies:
        print("Союзник помог... но ты его потерял.")
        player.allies.pop(0)
    return take_damage(player, 0)


def ch14_return_to_metro(player):
    print("Возвращение в метро. ВДНХ в беде.\n")
    opt = [
        "Броситься спасать станцию",
        "Сосредоточиться на своей цели"
    ]
    res = show_choice("Что важнее?", opt)
    if res == 1:
        take_damage(player, 35)
    return take_damage(player, 0)


def ch15_last_stand(player):
    print("Последние приготовления. Нужно решить, кого взять с собой.\n")
    opt = [
        "Собрать всех, кого можешь",
        "Идти одному"
    ]
    res = show_choice("Твой выбор?", opt)
    if res == 1 and player.allies:
        print("Союзники готовы идти до конца.")
    return True


def ch16_heart_of_darkness(player):
    print("Ты стоишь перед самым сердцем тьмы...\n")
    opt = [
        "Использовать найденный артефакт",
        "Сражаться до последнего",
        "Попробовать договориться"
    ]
    res = show_choice("Последнее решение:", opt)
    if res == 1 and player.has_heart:
        print("Артефакт вспыхнул странным светом...")
    elif res == 2:
        spend(player, "bullets", 90)
        take_damage(player, 45)
    return take_damage(player, 0)


def ch17_final_silence(player):
    print("\nВсё стихло.\n")
    print("Что осталось после тебя...\n")
    return True


def show_ending(player):
    print("\n" + "═" * 70)

    if player.has_heart and player.health > 20 and len(player.allies) >= 2:
        print("КОНЕЦ 1: Странный свет в темноте")
        print("Ты сумел остановить волну. Никто точно не знает как.")

    elif player.has_heart and len(player.allies) >= 1:
        print("КОНЕЦ 2: Цена надежды")
        print("Тёмные отступили... но ты заплатил почти всем.")

    elif player.health > 40 and len(player.allies) >= 3:
        print("КОНЕЦ 3: Последний патруль")
        print("Метро выстояло. Пока.")

    elif player.health <= 0:
        print("КОНЕЦ: Тишина")
        print("Тебя больше нет. Метро осталось без ответа.")

    elif len(player.allies) == 0:
        print("КОНЕЦ: Один в темноте")
        print("Ты дошёл до конца... но никого с собой не привёл.")

    else:
        print("КОНЕЦ: Неизвестность")
        print("Ты исчез в тенях. О тебе почти ничего не рассказывают.")

    print("═" * 70)


def main():
    player = Player()

    print("МЕТРО: ТЕНИ ВЫБОРА")
    print("Без оценок. Без подсказок. Только твои решения.\n")

    chapters = [
        ch1_vdnh_normal_day, ch2_cry_in_tunnel, ch3_goodbye_vdnh,
        ch4_rizhskaya, ch5_alexeevskaya, ch6_prospekt_mira,
        ch7_turgenevskaya, ch8_kitay_gorod, ch9_teatralnaya,
        ch10_polis_entrance, ch11_library,
        ch12_surface_first_step, ch13_botanical_garden,
        ch14_return_to_metro, ch15_last_stand,
        ch16_heart_of_darkness, ch17_final_silence
    ]

    for chapter_func in chapters:
        print_status(player)
        if not chapter_func(player):
            print("\nТы погиб...")
            return
        player.chapter += 1
        if player.chapter in [4, 7, 10, 12, 14, 16]:
            player.part += 1

    show_ending(player)


if __name__ == "__main__":
    main()