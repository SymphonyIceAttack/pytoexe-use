#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ПОМОЩНИК ПО КОРМЛЕНИЮ ПТЕНЦА
Всё выбирается из списков - ничего не нужно вводить вручную!
"""

import os
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


# ==================== КЛАССЫ ДАННЫХ ====================

class BirdType(Enum):
    """Типы птиц для выбора"""
    SWIFT = ("Стриж", "черный, быстрый, длинные крылья", "Насекомоядная")
    SMALL_SONG = ("Мелкая певчая", "Зяблик, синица, воробей, зарянка", "Насекомоядная/Всеядная")
    PIGEON = ("Голубь", "крупный, серый или белый", "Зерноядная")
    CROW = ("Ворона/Грач", "крупная черная птица", "Всеядная")
    UNKNOWN = ("Не знаю / Другой вид", "универсальные рекомендации", "?")
    
    def __init__(self, name: str, description: str, diet: str):
        self.display_name = name
        self.description = description
        self.diet = diet


class AgeStage(Enum):
    """Стадия развития - только выбор из списка"""
    NEWBORN = ("Новорожденный", "Совсем голый или редкий пух, глаза закрыты", 0.08, 8)
    NESTLING = ("Птенец в гнезде", "Есть пух и перья, глаза открыты, сидит", 0.10, 6)
    FLEDGLING = ("Слеток", "Почти оперился, прыгает, пробует летать", 0.12, 4)
    
    def __init__(self, name: str, description: str, portion_coef: float, feedings: int):
        self.display_name = name
        self.description = description
        self.portion_coef = portion_coef
        self.feedings_per_day = feedings


@dataclass
class Feed:
    """Корм с полным описанием"""
    id: int
    name: str
    short_name: str  # короткое название для меню
    type_: str  # "основной", "экстренный", "добавка"
    preparation: str
    method: str
    warning: str
    is_emergency: bool  # можно ли дать сразу
    price: str  # где найти


# ==================== БАЗА ДАННЫХ ====================

# Корма с понятными описаниями
FEEDS = [
    Feed(
        id=1,
        name="Мраморный таракан (Nauphoeta cinerea)",
        short_name="Мраморный таракан",
        type_="основной",
        preparation="Мелких тараканов давать целиком, крупных - раздавить пинцетом, удалить жесткие ноги",
        method="Кормить пинцетом, подносить головой вперед",
        warning="Не давать слишком много жестких частей маленьким птенцам",
        is_emergency=True,
        price="Можно купить в зоомагазине"
    ),
    Feed(
        id=2,
        name="Сверчок домовый",
        short_name="Сверчок",
        type_="основной",
        preparation="Мелких давать целиком, у крупных удалить задние ноги (они жесткие и острые)",
        method="Пинцетом, можно слегка надавить, чтобы вытекли внутренности",
        warning="Сверчки могут кусаться - лучше убивать перед кормлением",
        is_emergency=True,
        price="Зоомагазин, зоорынок"
    ),
    Feed(
        id=3,
        name="Туркестанский таракан (Shelfordella)",
        short_name="Красный таракан",
        type_="основной",
        preparation="Мягче мраморного, мелких целиком, крупных раздавить",
        method="Пинцетом",
        warning="Самцы летают - будьте осторожны при кормлении",
        is_emergency=True,
        price="Зоомагазин, дороже мраморного"
    ),
    Feed(
        id=4,
        name="Мучной червь",
        short_name="Мучной червь",
        type_="дополнительный",
        preparation="Желательно раздавить голову пинцетом",
        method="Пинцетом, мелкими кусочками",
        warning="Много хитина, не подходит как единственный корм",
        is_emergency=True,
        price="Есть в любом зоомагазине, недорого"
    ),
    Feed(
        id=5,
        name="Зофобас",
        short_name="Зофобас (крупный червь)",
        type_="дополнительный",
        preparation="❗ ОБЯЗАТЕЛЬНО раздавить голову! Очень сильные челюсти!",
        method="Разрезать на кусочки, давать пинцетом",
        warning="Очень жирный, нельзя кормить постоянно. Не давать целиком!",
        is_emergency=False,
        price="Зоомагазин, дороже мучного червя"
    ),
    Feed(
        id=6,
        name="Яйцо вареное (желток)",
        short_name="Вареное яйцо",
        type_="экстренный",
        preparation="Сварить вкрутую, взять желток, размять с каплей воды до кашицы",
        method="Шприцем без иглы или маленькой палочкой",
        warning="ТОЛЬКО на 1-2 дня! Много жира, нет клетчатки",
        is_emergency=True,
        price="Есть в каждом доме"
    ),
    Feed(
        id=7,
        name="Творог обезжиренный",
        short_name="Обезжиренный творог",
        type_="экстренный",
        preparation="Смешать с водой до консистенции сметаны",
        method="Шприцем без иглы или кисточкой",
        warning="Только обезжиренный! Не более 2 дней",
        is_emergency=True,
        price="Продуктовый магазин"
    ),
    Feed(
        id=8,
        name="Гаммарус (сушеный рачок)",
        short_name="Гаммарус",
        type_="дополнительный",
        preparation="Замочить в теплой воде на 10-15 минут, измельчить",
        method="Пинцетом, мелкими кусочками",
        warning="Обязательно размачивать! Сухой - опасно",
        is_emergency=False,
        price="Зоомагазин, недорого"
    ),
    Feed(
        id=9,
        name="Кальциевая добавка",
        short_name="Кальций (скорлупа/мел)",
        type_="добавка",
        preparation="Растолочь яичную скорлупу в муку или купить кормовой мел",
        method="Обваливать насекомых в порошке перед кормлением",
        warning="ОБЯЗАТЕЛЬНО добавлять при кормлении больше 2-3 дней!",
        is_emergency=False,
        price="Бесплатно (скорлупа) или копейки"
    )
]

# Словарь для быстрого доступа
FEEDS_DICT = {feed.id: feed for feed in FEEDS}


# ==================== ОСНОВНАЯ ЛОГИКА ====================

class BirdFeedingAssistant:
    """Помощник по кормлению птенца - всё через списки"""
    
    def __init__(self):
        self.bird_weight = 0
        self.bird_type = None
        self.age_stage = None
        self.selected_feeds = []
        
    def clear_screen(self):
        """Очистка экрана"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """Печать заголовка"""
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)
    
    def print_menu(self, options: Dict[int, str], prompt: str = "Выберите номер") -> int:
        """Показать меню и получить выбор"""
        for num, text in options.items():
            print(f"  {num}. {text}")
        print("  " + "-" * 30)
        
        while True:
            try:
                choice = int(input(f"{prompt}: "))
                if choice in options:
                    return choice
                print(f"Введите номер от {min(options.keys())} до {max(options.keys())}")
            except ValueError:
                print("Введите число")
    
    def step1_weight(self) -> bool:
        """Шаг 1: выбор веса (диапазонами)"""
        self.clear_screen()
        self.print_header("ШАГ 1: ОПРЕДЕЛЯЕМ ВЕС ПТЕНЦА")
        
        print("\nВыберите примерный вес птенца:")
        weight_options = {
            1: "Совсем крошечный (меньше 10 г) - как большой палец",
            2: "Маленький (10-30 г) - как спичечный коробок",
            3: "Средний (30-60 г) - как куриное яйцо",
            4: "Крупный (60-100 г) - как небольшое яблоко",
            5: "Очень крупный (больше 100 г) - как голубь"
        }
        
        choice = self.print_menu(weight_options, "👉 Ваш выбор")
        
        # Преобразуем выбор в примерный вес
        weight_map = {
            1: 5,    # 5 г
            2: 20,   # 20 г
            3: 45,   # 45 г
            4: 80,   # 80 г
            5: 150   # 150 г
        }
        
        self.bird_weight = weight_map[choice]
        print(f"\n✓ Принято: примерно {self.bird_weight} г")
        input("\nНажмите Enter для продолжения...")
        return True
    
    def step2_bird_type(self) -> bool:
        """Шаг 2: выбор вида птицы"""
        self.clear_screen()
        self.print_header("ШАГ 2: ОПРЕДЕЛЯЕМ ВИД ПТИЦЫ")
        
        print("\nНа кого похож птенец?")
        type_options = {
            1: f"{BirdType.SWIFT.display_name} - {BirdType.SWIFT.description}",
            2: f"{BirdType.SMALL_SONG.display_name} - {BirdType.SMALL_SONG.description}",
            3: f"{BirdType.PIGEON.display_name} - {BirdType.PIGEON.description}",
            4: f"{BirdType.CROW.display_name} - {BirdType.CROW.description}",
            5: f"{BirdType.UNKNOWN.display_name} - {BirdType.UNKNOWN.description}"
        }
        
        choice = self.print_menu(type_options, "👉 Ваш выбор")
        
        type_map = {
            1: BirdType.SWIFT,
            2: BirdType.SMALL_SONG,
            3: BirdType.PIGEON,
            4: BirdType.CROW,
            5: BirdType.UNKNOWN
        }
        
        self.bird_type = type_map[choice]
        print(f"\n✓ Выбрано: {self.bird_type.display_name}")
        input("\nНажмите Enter для продолжения...")
        return True
    
    def step3_age(self) -> bool:
        """Шаг 3: выбор возраста"""
        self.clear_screen()
        self.print_header("ШАГ 3: КАКОЙ ВОЗРАСТ (СТАДИЯ РАЗВИТИЯ)?")
        
        age_options = {
            1: f"{AgeStage.NEWBORN.display_name} - {AgeStage.NEWBORN.description}",
            2: f"{AgeStage.NESTLING.display_name} - {AgeStage.NESTLING.description}",
            3: f"{AgeStage.FLEDGLING.display_name} - {AgeStage.FLEDGLING.description}"
        }
        
        choice = self.print_menu(age_options, "👉 Ваш выбор")
        
        age_map = {
            1: AgeStage.NEWBORN,
            2: AgeStage.NESTLING,
            3: AgeStage.FLEDGLING
        }
        
        self.age_stage = age_map[choice]
        print(f"\n✓ Выбрано: {self.age_stage.display_name}")
        input("\nНажмите Enter для продолжения...")
        return True
    
    def step4_feeds(self) -> bool:
        """Шаг 4: выбор кормов"""
        self.clear_screen()
        self.print_header("ШАГ 4: ВЫБЕРИТЕ КОРМА, КОТОРЫЕ У ВАС ЕСТЬ")
        
        print(f"\n🐦 Птенец: {self.bird_type.display_name}, {self.bird_weight} г")
        print(f"📅 Стадия: {self.age_stage.display_name}")
        
        print("\n🍖 ДОСТУПНЫЕ КОРМА (выбирайте по номерам):")
        print("-" * 60)
        
        # Показываем корма с номерами
        for feed in FEEDS:
            emergency = "✅ МОЖНО СРАЗУ" if feed.is_emergency else "⚠️ С осторожностью"
            print(f"  {feed.id}. {feed.name}")
            print(f"     {emergency} | {feed.price}")
        
        print("\nВведите номера кормов через пробел (например: 1 3 5)")
        print("Или нажмите Enter, чтобы увидеть экстренные варианты")
        
        while True:
            choice = input("\n👉 Ваш выбор: ").strip()
            
            if choice == "":
                # Показать только экстренные корма
                self.clear_screen()
                print("\n🍖 ЭКСТРЕННЫЕ КОРМА (можно дать прямо сейчас):")
                emergency_feeds = [f for f in FEEDS if f.is_emergency]
                for feed in emergency_feeds:
                    print(f"  {feed.id}. {feed.name}")
                print("\nВведите номера экстренных кормов через пробел")
                continue
            
            try:
                # Разбираем введенные номера
                numbers = [int(x) for x in choice.split()]
                selected = []
                
                for num in numbers:
                    if num in FEEDS_DICT:
                        selected.append(FEEDS_DICT[num])
                    else:
                        print(f"⚠️ Номер {num} не найден, пропущен")
                
                if selected:
                    self.selected_feeds = selected
                    print(f"\n✓ Выбрано кормов: {len(selected)}")
                    input("\nНажмите Enter для продолжения...")
                    return True
                else:
                    print("❌ Не выбрано ни одного корма. Попробуйте снова")
                    
            except ValueError:
                print("❌ Вводите только числа через пробел")
    
    def step5_instructions(self):
        """Шаг 5: показать инструкции"""
        self.clear_screen()
        self.print_header("ИНСТРУКЦИЯ ПО КОРМЛЕНИЮ")
        
        print(f"\n🐦 ПТЕНЕЦ: {self.bird_type.display_name}")
        print(f"⚖️ ВЕС: примерно {self.bird_weight} г")
        print(f"📅 ВОЗРАСТ: {self.age_stage.display_name}")
        print(f"🍽️ РЕЖИМ: кормить КАЖДЫЕ {24 // self.age_stage.feedings_per_day} часа")
        print("\n" + "=" * 70)
        
        # Расчет порции
        portion_g = self.bird_weight * self.age_stage.portion_coef
        
        print(f"\n📊 НА ОДНО КОРМЛЕНИЕ:")
        print(f"  • Всего еды: {portion_g:.1f} г")
        print(f"  • Кормлений в день: {self.age_stage.feedings_per_day}")
        print(f"  • Ночные кормления: обязательно!")
        
        print("\n" + "=" * 70)
        print("🍖 ИНСТРУКЦИИ ПО ВАШИМ КОРМАМ:")
        
        for feed in self.selected_feeds:
            print(f"\n📌 {feed.name}:")
            print(f"  ПРИГОТОВЛЕНИЕ: {feed.preparation}")
            print(f"  КАК ДАВАТЬ: {feed.method}")
            if feed.warning:
                print(f"  ⚠️ ВНИМАНИЕ: {feed.warning}")
        
        # Проверяем, есть ли кальций
        has_calcium = any("Кальциевая" in f.name for f in self.selected_feeds)
        if not has_calcium:
            print("\n" + "=" * 70)
            print("⚠️ ВЫ НЕ ВЫБРАЛИ КАЛЬЦИЕВУЮ ДОБАВКУ!")
            print("При кормлении больше 2-3 дней ОБЯЗАТЕЛЬНО добавляйте кальций:")
            print("  • Растолките яичную скорлупу в порошок")
            print("  • Обваливайте насекомых в этом порошке")
            print("  • Без кальция у птенца разовьется рахит!")
        
        print("\n" + "=" * 70)
        print("💧 ВОДА:")
        print("  • Поставьте отдельную поилку с водой")
        print("  • НЕ лейте воду в клюв насильно!")
        print("  • Можно капнуть на клюв - птенец слижет")
        
        print("\n" + "=" * 70)
        print("❌ ЧЕГО НЕЛЬЗЯ ДЕЛАТЬ:")
        print("  • Не давать хлеб, молоко, еду со стола")
        print("  • Не кормить дождевыми червями (опасно!)")
        print("  • Не давать целых крупных насекомых")
        print("  • Не поить насильно")
        
        print("\n" + "=" * 70)
        print("🚨 ДАЛЬНЕЙШИЕ ДЕЙСТВИЯ:")
        print("  1. Найдите центр реабилитации диких птиц в вашем городе")
        print("  2. Или обратитесь в ветклинику")
        print("  3. Не держите птенца дольше необходимого")
        
        print("\n" + "=" * 70)
        print("🍀 УДАЧИ В ВЫХАЖИВАНИИ!")
        print("=" * 70)
        
        input("\nНажмите Enter для завершения...")
    
    def step6_again(self) -> bool:
        """Шаг 6: спросить, нужно ли еще"""
        self.clear_screen()
        self.print_header("ЧТО ДЕЛАЕМ ДАЛЬШЕ?")
        
        options = {
            1: "🔄 Рассчитать для другого набора кормов (того же птенца)",
            2: "🐦 Начать заново с другим птенцом",
            3: "🚪 Завершить работу"
        }
        
        choice = self.print_menu(options, "👉 Ваш выбор")
        
        if choice == 1:
            self.selected_feeds = []
            return self.step4_feeds() and self.step5_instructions() and self.step6_again()
        elif choice == 2:
            return False  # начать заново
        else:
            return True  # завершить
    
    def run(self):
        """Главный цикл"""
        while True:
            # Проходим все шаги
            if not self.step1_weight():
                break
            if not self.step2_bird_type():
                break
            if not self.step3_age():
                break
            if not self.step4_feeds():
                break
            
            self.step5_instructions()
            
            if self.step6_again():
                break
            
            # Сбрасываем для нового птенца
            self.bird_weight = 0
            self.bird_type = None
            self.age_stage = None
            self.selected_feeds = []
        
        print("\n👋 До свидания! Берегите птиц!")
        input("Нажмите Enter для выхода...")


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    try:
        assistant = BirdFeedingAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\n\n👋 Программа завершена")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        input("Нажмите Enter для выхода...")