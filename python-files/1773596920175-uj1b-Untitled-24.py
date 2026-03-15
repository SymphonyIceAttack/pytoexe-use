#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ПОМОЩНИК ПО КОРМЛЕНИЮ ПТЕНЦА
Вес вводится вручную, остальное выбирается из списка
"""

# ==================== ДАННЫЕ ====================

# Корма с инструкциями
FEEDS = {
    1: {
        "name": "Мраморный таракан",
        "preparation": "Маленьких - целиком, крупных - раздавить, удалить ноги",
        "method": "Пинцетом, головой вперед",
        "warning": "Много хитина, не перекармливать маленьких",
        "small": "2-3 штуки за раз",
        "medium": "3-5 штук за раз",
        "large": "5-8 штук за раз"
    },
    2: {
        "name": "Сверчок",
        "preparation": "У крупных удалить задние ноги",
        "method": "Пинцетом, можно надавить",
        "warning": "Могут кусаться - лучше убивать",
        "small": "2-3 штуки за раз",
        "medium": "3-5 штук за раз",
        "large": "5-8 штук за раз"
    },
    3: {
        "name": "Мучной червь",
        "preparation": "Раздавить голову",
        "method": "Пинцетом, можно разрезать",
        "warning": "Много хитина, не только им",
        "small": "1-2 штуки за раз",
        "medium": "2-3 штуки за раз",
        "large": "3-4 штуки за раз"
    },
    4: {
        "name": "Зофобас",
        "preparation": "ОБЯЗАТЕЛЬНО раздавить голову!",
        "method": "Разрезать на кусочки",
        "warning": "ОЧЕНЬ ЖИРНЫЙ! Только изредка",
        "small": "1 шт на 2-3 кормления",
        "medium": "1 шт на 2 кормления",
        "large": "1 шт за раз"
    },
    5: {
        "name": "Вареное яйцо (желток)",
        "preparation": "Сварить, желток размять с водой",
        "method": "Шприцем без иглы, по капле",
        "warning": "ТОЛЬКО 1-2 ДНЯ! Много жира",
        "small": "с горошину",
        "medium": "с фасолину",
        "large": "с лесной орех"
    },
    6: {
        "name": "Творог обезжиренный",
        "preparation": "Смешать с водой до сметаны",
        "method": "Шприцем или кисточкой",
        "warning": "ТОЛЬКО обезжиренный! 1-2 дня",
        "small": "с горошину",
        "medium": "с фасолину",
        "large": "с лесной орех"
    }
}

# ==================== ФУНКЦИИ ====================

def print_header(text):
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def get_choice(prompt, min_val, max_val):
    while True:
        try:
            choice = int(input(prompt))
            if min_val <= choice <= max_val:
                return choice
            print(f"Введите число от {min_val} до {max_val}")
        except ValueError:
            print("Ошибка! Введите число")

def get_weight():
    while True:
        try:
            weight = float(input("Введите вес птенца в граммах (например: 25): "))
            if weight > 0:
                return weight
            print("Вес должен быть положительным числом")
        except ValueError:
            print("Ошибка! Введите число (можно с точкой, например: 25.5)")

# ==================== ОСНОВНАЯ ПРОГРАММА ====================

def main():
    print_header("ПОМОЩНИК ПО КОРМЛЕНИЮ ПТЕНЦА")
    
    # ШАГ 1 - ВИД ПТИЦЫ
    print("\n1. ВИД ПТИЦЫ:")
    print("  1 - Стриж")
    print("  2 - Зяблик/Синица/Воробей")
    print("  3 - Не знаю/Другой")
    bird = get_choice("  Ваш выбор (1-3): ", 1, 3)
    
    # ШАГ 2 - ВЕС (вводим руками)
    print("\n2. ВЕС ПТЕНЦА:")
    weight = get_weight()
    
    # ШАГ 3 - ВОЗРАСТ
    print("\n3. ВОЗРАСТ:")
    print("  1 - Новорожденный (голый, глаза закрыты)")
    print("  2 - Подросший (есть перья, глаза открыты)")
    print("  3 - Слеток (почти летает)")
    age = get_choice("  Ваш выбор (1-3): ", 1, 3)
    
    # ШАГ 4 - КОРМ
    print("\n4. ЧЕМ КОРМИТЬ:")
    for num, feed in FEEDS.items():
        print(f"  {num} - {feed['name']}")
    feed = get_choice("  Ваш выбор (1-6): ", 1, 6)
    
    # ========== РАСЧЕТ ==========
    # Коэффициенты кормления
    if age == 1:  # новорожденный
        koef = 0.08
        feedings = 8
        interval = 3
    elif age == 2:  # подросший
        koef = 0.10
        feedings = 6
        interval = 4
    else:  # слеток
        koef = 0.12
        feedings = 4
        interval = 6
    
    portion = weight * koef
    
    # ========== РЕЗУЛЬТАТ ==========
    print_header("РЕЗУЛЬТАТ")
    
    print(f"\n🐦 Вес птенца: {weight} г")
    print(f"⏰ Кормить КАЖДЫЕ {interval} ЧАСА")
    print(f"📅 Всего кормлений: {feedings} раз в день")
    print(f"🍽️ На ОДНО кормление: {portion:.2f} г ({portion*1000:.0f} мг)")
    
    print(f"\n🍖 {FEEDS[feed]['name']}:")
    print(f"  • КАК ГОТОВИТЬ: {FEEDS[feed]['preparation']}")
    print(f"  • КАК ДАВАТЬ: {FEEDS[feed]['method']}")
    print(f"  • ⚠️ {FEEDS[feed]['warning']}")
    
    # Количество штук (примерно)
    if weight < 20:
        print(f"  • Примерно: {FEEDS[feed]['small']}")
    elif weight < 50:
        print(f"  • Примерно: {FEEDS[feed]['medium']}")
    else:
        print(f"  • Примерно: {FEEDS[feed]['large']}")
    
    print("\n" + "=" * 60)
    print("💊 КАЛЬЦИЙ ОБЯЗАТЕЛЕН!")
    print("Если кормите больше 2-3 дней:")
    print("  • Растолките яичную скорлупу")
    print("  • Обваливайте насекомых в порошке")
    print("=" * 60)
    
    print("\n❌ НЕЛЬЗЯ:")
    print("  • Хлеб, молоко, еду со стола")
    print("  • Дождевых червей")
    print("  • Целых крупных насекомых")
    
    print("\n" + "=" * 60)
    print("🍀 УДАЧИ!")
    print("=" * 60)
    
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nДо свидания!")
    except Exception as e:
        print(f"\nОшибка: {e}")
        input("Нажмите Enter...")