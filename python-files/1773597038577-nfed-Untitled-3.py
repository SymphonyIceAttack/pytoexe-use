#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ПОМОЩНИК ПО КОРМЛЕНИЮ ПТЕНЦА
Выбираете вид птицы, вес и один корм - получаете инструкцию
"""

import os
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


# ==================== КЛАССЫ ДАННЫХ ====================

class BirdSpecies(Enum):
    """Виды птиц"""
    SWIFT = ("Стриж черный", "Насекомоядная", "Кормить часто, каждые 2-3 часа")
    CHAFFINCH = ("Зяблик", "Насекомоядная (птенцы)", "В период роста нужно много белка")
    ROBIN = ("Зарянка (малиновка)", "Насекомоядная", "Ест насекомых, пауков")
    TIT = ("Синица", "Насекомоядная", "Активно ест насекомых")
    SPARROW = ("Воробей", "Всеядная", "Может есть и насекомых, и зерно")
    UNKNOWN = ("Неизвестный вид", "?", "Универсальные рекомендации")
    
    def __init__(self, display_name: str, diet: str, note: str):
        self.display_name = display_name
        self.diet = diet
        self.note = note


class AgeStage(Enum):
    """Стадия развития"""
    NEWBORN = ("Новорожденный", "Голый или пух, глаза закрыты", 0.08, 8)
    NESTLING = ("Птенец", "Есть перья, глаза открыты, сидит в гнезде", 0.10, 6)
    FLEDGLING = ("Слеток", "Почти оперился, прыгает, пробует летать", 0.12, 4)
    
    def __init__(self, name: str, desc: str, portion_coef: float, feedings: int):
        self.display_name = name
        self.description = desc
        self.portion_coef = portion_coef  # % от веса за одно кормление
        self.feedings_per_day = feedings


@dataclass
class Feed:
    """Корм с инструкцией"""
    id: int
    name: str
    short_name: str
    description: str
    preparation: str
    method: str
    warning: str
    protein_pct: float  # для информации
    fat_pct: float      # для информации
    is_emergency: bool  # можно ли дать сразу
    where_to_buy: str


# ==================== БАЗА ДАННЫХ ====================

# Корма с подробными инструкциями
FEEDS = [
    Feed(
        id=1,
        name="Мраморный таракан (Nauphoeta cinerea)",
        short_name="Мраморный таракан",
        description="Мягкий, питательный, хорошо усваивается",
        preparation="Маленьких давать целиком. Крупных - раздавить пинцетом или разрезать, удалить жесткие ноги",
        method="Кормить пинцетом, подносить головой вперед. Птенец сам схватит",
        warning="Не давать слишком много хитина маленьким птенцам",
        protein_pct=18.0,
        fat_pct=8.0,
        is_emergency=True,
        where_to_buy="Зоомагазин, можно заказать онлайн"
    ),
    Feed(
        id=2,
        name="Сверчок домовый",
        short_name="Сверчок",
        description="Классический корм для насекомоядных птиц",
        preparation="Мелких давать целиком. У крупных удалить задние ноги (они острые и жесткие)",
        method="Пинцетом. Можно слегка надавить, чтобы вытекли внутренности - так легче есть",
        warning="Сверчки могут кусаться - лучше убивать перед кормлением",
        protein_pct=15.0,
        fat_pct=5.0,
        is_emergency=True,
        where_to_buy="Зоомагазин, зоорынок"
    ),
    Feed(
        id=3,
        name="Туркестанский таракан (Shelfordella)",
        short_name="Красный таракан",
        description="Мягче мраморного, хорошо поедается",
        preparation="Мелких целиком, крупных раздавить",
        method="Пинцетом",
        warning="Самцы летают - будьте осторожны при кормлении",
        protein_pct=17.0,
        fat_pct=7.0,
        is_emergency=True,
        where_to_buy="Зоомагазин"
    ),
    Feed(
        id=4,
        name="Мучной червь",
        short_name="Мучной червь",
        description="Доступный корм, но много хитина",
        preparation="Желательно раздавить голову пинцетом",
        method="Давать пинцетом, можно разрезать на части",
        warning="Много хитина, не подходит как единственный корм на долгое время",
        protein_pct=14.0,
        fat_pct=10.0,
        is_emergency=True,
        where_to_buy="Любой зоомагазин, недорого"
    ),
    Feed(
        id=5,
        name="Зофобас",
        short_name="Зофобас (крупный червь)",
        description="Очень питательный, жирный",
        preparation="❗ ОБЯЗАТЕЛЬНО раздавить голову! Очень сильные челюсти могут повредить птенца",
        method="Разрезать на кусочки, давать пинцетом",
        warning="Очень жирный, нельзя кормить постоянно. Только как лакомство или для истощенных птиц",
        protein_pct=16.0,
        fat_pct=12.0,
        is_emergency=False,
        where_to_buy="Зоомагазин"
    ),
    Feed(
        id=6,
        name="Вареное яйцо (желток)",
        short_name="Вареное яйцо",
        description="Экстренный корм, когда нет насекомых",
        preparation="Сварить вкрутую, взять желток, размять с каплей воды до консистенции кашицы",
        method="Давать с пинцета или шприца без иглы маленькими порциями",
        warning="ТОЛЬКО как экстренная помощь на 1-2 дня! Много жира, нет клетчатки и хитина",
        protein_pct=15.0,
        fat_pct=30.0,
        is_emergency=True,
        where_to_buy="Есть в каждом доме"
    ),
    Feed(
        id=7,
        name="Творог обезжиренный",
        short_name="Творог",
        description="Экстренный корм, источник кальция",
        preparation="Смешать с водой до консистенции густой сметаны",
        method="Шприцем без иглы или маленькой кисточкой",
        warning="Только обезжиренный! Не более 2 дней. Может вызвать расстройство",
        protein_pct=18.0,
        fat_pct=0.5,
        is_emergency=True,
        where_to_buy="Продуктовый магазин"
    ),
    Feed(
        id=8,
        name="Гаммарус (сушеный рачок)",
        short_name="Гаммарус",
        description="Хороший источник кальция",
        preparation="ОБЯЗАТЕЛЬНО замочить в теплой воде на 10-15 минут, затем измельчить",
        method="Давать пинцетом маленькими кусочками",
        warning="Сухим давать нельзя - разбухнет в зобу! Только размоченным",
        protein_pct=50.0,
        fat_pct=5.0,
        is_emergency=False,
        where_to_buy="Зоомагазин"
    ),
    Feed(
        id=9,
        name="Кальциевая добавка",
        short_name="Кальций",
        description="Толченая скорлупа или кормовой мел",
        preparation="Растолочь яичную скорлупу в муку или купить кормовой мел",
        method="Обваливать насекомых в порошке перед кормлением",
        warning="ОБЯЗАТЕЛЬНО добавлять при кормлении больше 2-3 дней! Без кальция рахит",
        protein_pct=0.0,
        fat_pct=0.0,
        is_emergency=False,
        where_to_buy="Скорлупа бесплатно, мел - зоомагазин"
    )
]

FEEDS_DICT = {feed.id: feed for feed in FEEDS}


# ==================== ОСНОВНАЯ ЛОГИКА ====================

class BirdFeedingAssistant:
    """Помощник по кормлению - для одного корма"""
    
    def __init__(self):
        self.bird_weight = 0
        self.bird_species = None
        self.age_stage = None
        self.selected_feed = None
        
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
    
    def step1_bird_type(self) -> bool:
        """Шаг 1: выбор вида птицы"""
        self.clear_screen()
        self.print_header("ШАГ 1: КТО ЭТОТ ПТЕНЕЦ?")
        
        options = {
            1: f"{BirdSpecies.SWIFT.display_name} - {BirdSpecies.SWIFT.diet}",
            2: f"{BirdSpecies.CHAFFINCH.display_name} - {BirdSpecies.CHAFFINCH.diet}",
            3: f"{BirdSpecies.ROBIN.display_name} - {BirdSpecies.ROBIN.diet}",
            4: f"{BirdSpecies.TIT.display_name} - {BirdSpecies.TIT.diet}",
            5: f"{BirdSpecies.SPARROW.display_name} - {BirdSpecies.SPARROW.diet}",
            6: f"{BirdSpecies.UNKNOWN.display_name} - {BirdSpecies.UNKNOWN.diet}"
        }
        
        choice = self.print_menu(options, "👉 На кого похож")
        
        species_map = {
            1: BirdSpecies.SWIFT,
            2: BirdSpecies.CHAFFINCH,
            3: BirdSpecies.ROBIN,
            4: BirdSpecies.TIT,
            5: BirdSpecies.SPARROW,
            6: BirdSpecies.UNKNOWN
        }
        
        self.bird_species = species_map[choice]
        print(f"\n✓ Выбрано: {self.bird_species.display_name}")
        print(f"  {self.bird_species.note}")
        input("\nНажмите Enter для продолжения...")
        return True
    
    def step2_weight(self) -> bool:
        """Шаг 2: выбор веса"""
        self.clear_screen()
        self.print_header("ШАГ 2: ОПРЕДЕЛЯЕМ ВЕС")
        
        print("\nВыберите примерный вес птенца:")
        options = {
            1: "Меньше 10 г (как большой палец) - крошечный",
            2: "10-30 г (как спичечный коробок) - маленький",
            3: "30-60 г (как куриное яйцо) - средний",
            4: "60-100 г (как небольшое яблоко) - крупный",
            5: "Больше 100 г (как голубь) - очень крупный"
        }
        
        choice = self.print_menu(options, "👉 Ваш выбор")
        
        weight_map = {
            1: 5,
            2: 20,
            3: 45,
            4: 80,
            5: 150
        }
        
        self.bird_weight = weight_map[choice]
        print(f"\n✓ Принято: примерно {self.bird_weight} г")
        input("\nНажмите Enter для продолжения...")
        return True
    
    def step3_age(self) -> bool:
        """Шаг 3: выбор возраста"""
        self.clear_screen()
        self.print_header("ШАГ 3: ВОЗРАСТ ПТЕНЦА")
        
        options = {
            1: f"{AgeStage.NEWBORN.display_name} - {AgeStage.NEWBORN.description}",
            2: f"{AgeStage.NESTLING.display_name} - {AgeStage.NESTLING.description}",
            3: f"{AgeStage.FLEDGLING.display_name} - {AgeStage.FLEDGLING.description}"
        }
        
        choice = self.print_menu(options, "👉 Как выглядит")
        
        age_map = {
            1: AgeStage.NEWBORN,
            2: AgeStage.NESTLING,
            3: AgeStage.FLEDGLING
        }
        
        self.age_stage = age_map[choice]
        print(f"\n✓ Выбрано: {self.age_stage.display_name}")
        input("\nНажмите Enter для продолжения...")
        return True
    
    def step4_feed(self) -> bool:
        """Шаг 4: выбор ОДНОГО корма"""
        self.clear_screen()
        self.print_header("ШАГ 4: ЧЕМ БУДЕТЕ КОРМИТЬ?")
        
        print(f"\n🐦 Птенец: {self.bird_species.display_name}, {self.bird_weight} г")
        print(f"📅 Возраст: {self.age_stage.display_name}")
        
        print("\n🍖 ДОСТУПНЫЕ КОРМА:")
        print("-" * 60)
        
        # Разделяем на экстренные и основные
        emergency_feeds = [f for f in FEEDS if f.is_emergency]
        other_feeds = [f for f in FEEDS if not f.is_emergency]
        
        print("\n✅ МОЖНО ИСПОЛЬЗОВАТЬ СРАЗУ:")
        for feed in emergency_feeds:
            print(f"  {feed.id}. {feed.name}")
            print(f"     {feed.description}")
            print(f"     🏪 {feed.where_to_buy}")
        
        print("\n⚠️ С ОСТОРОЖНОСТЬЮ (не для постоянного кормления):")
        for feed in other_feeds:
            print(f"  {feed.id}. {feed.name}")
            print(f"     {feed.description}")
            print(f"     🏪 {feed.where_to_buy}")
        
        while True:
            try:
                choice = int(input("\n👉 Введите номер выбранного корма: "))
                if choice in FEEDS_DICT:
                    self.selected_feed = FEEDS_DICT[choice]
                    break
                print("Такого номера нет в списке")
            except ValueError:
                print("Введите число")
        
        print(f"\n✓ Выбрано: {self.selected_feed.name}")
        input("\nНажмите Enter для продолжения...")
        return True
    
    def step5_instruction(self):
        """Шаг 5: показать инструкцию для выбранного корма"""
        self.clear_screen()
        self.print_header("ИНСТРУКЦИЯ ПО КОРМЛЕНИЮ")
        
        # Расчет порции
        portion_g = self.bird_weight * self.age_stage.portion_coef
        portion_mg = portion_g * 1000  # в миллиграммах для наглядности
        
        print(f"\n🐦 ПТЕНЕЦ: {self.bird_species.display_name}")
        print(f"⚖️ ВЕС: {self.bird_weight} г")
        print(f"📅 ВОЗРАСТ: {self.age_stage.display_name}")
        print("=" * 70)
        
        print(f"\n🍽️ РЕЖИМ КОРМЛЕНИЯ:")
        print(f"  • КОРМИТЬ КАЖДЫЕ {24 // self.age_stage.feedings_per_day} ЧАСА")
        print(f"  • ВСЕГО КОРМЛЕНИЙ В ДЕНЬ: {self.age_stage.feedings_per_day}")
        print(f"  • НОЧНЫЕ КОРМЛЕНИЯ: ОБЯЗАТЕЛЬНЫ!")
        
        print(f"\n📊 РАСЧЕТ ПОРЦИИ:")
        print(f"  • На одно кормление: {portion_g:.2f} ГРАММ")
        print(f"  • Это примерно {portion_mg:.0f} миллиграммов")
        
        # Переводим в примерное количество насекомых
        if "таракан" in self.selected_feed.name.lower() or "сверчок" in self.selected_feed.name.lower():
            if self.bird_weight < 20:
                print(f"  • Примерно: 2-3 мелких насекомых за раз")
            elif self.bird_weight < 50:
                print(f"  • Примерно: 3-5 средних насекомых за раз")
            else:
                print(f"  • Примерно: 5-8 насекомых за раз (или 1-2 крупных)")
        
        print("\n" + "=" * 70)
        print(f"🍖 ИНСТРУКЦИЯ ДЛЯ {self.selected_feed.name.upper()}:")
        print("-" * 70)
        print(f"\n📝 КАК ГОТОВИТЬ:")
        print(f"  {self.selected_feed.preparation}")
        
        print(f"\n🥢 КАК ДАВАТЬ:")
        print(f"  {self.selected_feed.method}")
        
        print(f"\n⚠️ ВАЖНО:")
        print(f"  {self.selected_feed.warning}")
        
        print(f"\n🏪 ГДЕ ВЗЯТЬ:")
        print(f"  {self.selected_feed.where_to_buy}")
        
        print(f"\n📊 СОСТАВ (для информации):")
        print(f"  • Белок: {self.selected_feed.protein_pct}%")
        print(f"  • Жир: {self.selected_feed.fat_pct}%")
        
        # Советы по кальцию
        if self.selected_feed.id != 9:  # если это не сама кальциевая добавка
            print("\n" + "=" * 70)
            print("💊 КАЛЬЦИЙ - ЭТО ОЧЕНЬ ВАЖНО!")
            print("Если кормите больше 2-3 дней, ОБЯЗАТЕЛЬНО добавляйте кальций:")
            print("  • Растолките яичную скорлупу в порошок")
            print("  • Обваливайте насекомых в этом порошке перед кормлением")
            print("  • Или добавьте кормовой мел (продается в зоомагазине)")
        
        print("\n" + "=" * 70)
        print("💧 ВОДА:")
        print("  • Поставьте отдельную поилку с водой")
        print("  • НЕ лейте воду в клюв насильно!")
        print("  • Можно капнуть на клюв - птенец слижет")
        
        print("\n" + "=" * 70)
        print("❌ ЧЕГО НЕЛЬЗЯ:")
        print("  • Хлеб, молоко, еду со стола")
        print("  • Дождевых червей (опасно!)")
        print("  • Целых крупных насекомых (могут повредить)")
        
        print("\n" + "=" * 70)
        print("🚨 ДАЛЬНЕЙШИЕ ДЕЙСТВИЯ:")
        print("  • Найдите центр реабилитации диких птиц в вашем городе")
        print("  • Или обратитесь в ветклинику")
        print("  • Не держите птенца дольше необходимого")
        
        print("\n" + "=" * 70)
        print("🍀 УДАЧИ В ВЫХАЖИВАНИИ!")
        print("=" * 70)
        
        input("\nНажмите Enter для завершения...")
    
    def step6_again(self) -> bool:
        """Шаг 6: спросить, нужно ли еще"""
        self.clear_screen()
        self.print_header("ЧТО ДЕЛАЕМ ДАЛЬШЕ?")
        
        options = {
            1: "🔄 Выбрать другой корм для этого же птенца",
            2: "🐦 Начать заново с другим птенцом",
            3: "🚪 Завершить работу"
        }
        
        choice = self.print_menu(options, "👉 Ваш выбор")
        
        if choice == 1:
            self.selected_feed = None
            return self.step4_feed() and self.step5_instruction() and self.step6_again()
        elif choice == 2:
            return False  # начать заново
        else:
            return True  # завершить
    
    def run(self):
        """Главный цикл"""
        while True:
            # Проходим все шаги
            if not self.step1_bird_type():
                break
            if not self.step2_weight():
                break
            if not self.step3_age():
                break
            if not self.step4_feed():
                break
            
            self.step5_instruction()
            
            if self.step6_again():
                break
            
            # Сбрасываем для нового птенца
            self.bird_weight = 0
            self.bird_species = None
            self.age_stage = None
            self.selected_feed = None
        
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