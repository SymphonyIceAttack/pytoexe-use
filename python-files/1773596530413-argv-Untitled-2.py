#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ПОМОЩНИК ПО КОРМЛЕНИЮ ПТЕНЦА
Для людей, которые нашли птенца и не знают, чем и как кормить
"""

import os
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


# ==================== КЛАССЫ ДАННЫХ ====================

class BirdSpecies(Enum):
    """Виды птиц"""
    SWIFT = ("Стриж", "Насекомоядная", "Нуждается в частом кормлении, очень уязвим")
    CHAFFINCH = ("Зяблик", "Насекомоядная (птенцы)/Зерноядная (взрослые)", "В период выкармливания нужны насекомые")
    ROBIN = ("Зарянка (Малиновка)", "Насекомоядная", "Ест насекомых, пауков, червей")
    TIT = ("Синица", "Насекомоядная", "Активно ест насекомых, особенно в период роста")
    SPARROW = ("Воробей", "Всеядная", "Может есть и насекомых, и зерно")
    UNKNOWN = ("Неизвестный вид", "?", "Для птенцов неизвестного вида - универсальные рекомендации")


class FeedingStage(Enum):
    """Стадия развития птенца"""
    NEWBORN = ("Новорожденный (0-3 дня)", "Голый или с редким пухом, глаза закрыты", 0.5)
    NESTLING = ("Слепой птенец (3-7 дней)", "Пуховой, глаза закрыты или открываются", 0.7)
    FLEDGLING = ("Оперившийся (1-2 недели)", "Появляются перья, сидит в гнезде", 1.0)
    JUVENILE = ("Слеток (2-4 недели)", "Почти оперился, пробует летать", 1.3)
    UNKNOWN = ("Неизвестно", "Если не знаете возраст", 1.0)


@dataclass
class FeedingInstruction:
    """Инструкция по кормлению конкретным кормом"""
    feed_name: str
    amount_per_feeding_g: float  # грамм на одно кормление
    feedings_per_day: int  # количество кормлений в сутки
    preparation: str  # как подготовить корм
    method: str  # как давать (пинцетом, шприцем и т.д.)
    warning: str = ""  # предупреждения


@dataclass
class FeedComposition:
    """Состав корма"""
    name: str
    type_: str  # основной, дополнительный, опасный
    protein_pct: float
    fat_pct: float
    calcium_pct: float
    phosphorus_pct: float
    moisture_pct: float
    preparation: str
    feeding_method: str
    warning: str = ""
    is_emergency: bool = False  # можно ли давать в экстренном случае
    is_essential: bool = False  # обязательный компонент рациона
    price_rating: str = ""  # доступность


# ==================== БАЗА ЗНАНИЙ ====================

# База кормов с инструкциями
FEEDS_DATABASE = {
    "Мраморный таракан (Nauphoeta cinerea)": FeedComposition(
        name="Мраморный таракан",
        type_="основной",
        protein_pct=18.0,
        fat_pct=8.0,
        calcium_pct=0.1,
        phosphorus_pct=0.25,
        moisture_pct=65.0,
        preparation="Мелких тараканов давать целиком, крупных - раздавить пинцетом, удалить жесткие части",
        feeding_method="Пинцетом, предлагать головой вперед",
        warning="Не давать слишком много жестких хитиновых частей маленьким птенцам",
        is_emergency=True,
        is_essential=True,
        price_rating="Средняя цена, можно найти в зоомагазинах"
    ),
    
    "Туркестанский таракан (Shelfordella)": FeedComposition(
        name="Туркестанский таракан",
        type_="основной",
        protein_pct=17.0,
        fat_pct=7.0,
        calcium_pct=0.08,
        phosphorus_pct=0.22,
        moisture_pct=65.0,
        preparation="Мягче мраморного, можно давать целиком мелких, крупных раздавить",
        feeding_method="Пинцетом",
        warning="Самцы летают - убедитесь, что не сбегут",
        is_emergency=True,
        is_essential=True,
        price_rating="Немного дороже мраморного"
    ),
    
    "Сверчок домовый": FeedComposition(
        name="Сверчок домовый",
        type_="основной",
        protein_pct=15.0,
        fat_pct=5.0,
        calcium_pct=0.05,
        phosphorus_pct=0.2,
        moisture_pct=70.0,
        preparation="Мелких целиком, у крупных удалить задние ноги (они жесткие)",
        feeding_method="Пинцетом, можно надавить, чтобы вытекли внутренности для очень маленьких",
        warning="Сверчки могут кусаться - лучше убивать перед кормлением",
        is_emergency=True,
        is_essential=True,
        price_rating="Доступны в зоомагазинах"
    ),
    
    "Зофобас (Зофобас)": FeedComposition(
        name="Зофобас (личинка жука-чернотелки)",
        type_="дополнительный",
        protein_pct=16.0,
        fat_pct=12.0,
        calcium_pct=0.06,
        phosphorus_pct=0.21,
        moisture_pct=60.0,
        preparation="ОЧЕНЬ ВАЖНО: раздавить голову пинцетом (они очень сильные челюсти!)",
        feeding_method="Давать после раздавливания головы, можно разрезать на части",
        warning="❗ Очень жирные, нельзя кормить постоянно. Не давать целиком - могут повредить пищевод!",
        is_emergency=False,
        is_essential=False,
        price_rating="Дороже тараканов"
    ),
    
    "Мучной червь": FeedComposition(
        name="Мучной червь",
        type_="дополнительный",
        protein_pct=14.0,
        fat_pct=10.0,
        calcium_pct=0.04,
        phosphorus_pct=0.18,
        moisture_pct=62.0,
        preparation="Желательно раздавить голову, мелких можно целиком",
        feeding_method="Пинцетом",
        warning="Много хитина, не подходит как единственный корм",
        is_emergency=True,
        is_essential=False,
        price_rating="Дешево, есть во многих зоомагазинах"
    ),
    
    "Вареное яйцо (желток)": FeedComposition(
        name="Куриное яйцо вареное (желток)",
        type_="экстренный",
        protein_pct=15.0,
        fat_pct=30.0,
        calcium_pct=0.1,
        phosphorus_pct=0.5,
        moisture_pct=50.0,
        preparation="Сварить вкрутую, взять желток, размять вилкой с небольшим количеством воды до кашицы",
        feeding_method="Маленькими порциями с пинцета или шприца без иглы",
        warning="Только как экстренная помощь на 1-2 дня! Много жира, нет клетчатки",
        is_emergency=True,
        is_essential=False,
        price_rating="Есть в каждом доме"
    ),
    
    "Творог обезжиренный": FeedComposition(
        name="Творог обезжиренный",
        type_="экстренный",
        protein_pct=18.0,
        fat_pct=0.5,
        calcium_pct=0.12,
        phosphorus_pct=0.2,
        moisture_pct=80.0,
        preparation="Смешать с небольшим количеством воды до консистенции кашицы",
        feeding_method="Шприцем без иглы или маленькой кисточкой",
        warning="Только экстренно, не более 1-2 дней. Только обезжиренный!",
        is_emergency=True,
        is_essential=False,
        price_rating="Доступно"
    ),
    
    "Гаммарус сушеный": FeedComposition(
        name="Гаммарус (сушеный рачок)",
        type_="дополнительный",
        protein_pct=50.0,
        fat_pct=5.0,
        calcium_pct=5.0,
        phosphorus_pct=2.0,
        moisture_pct=10.0,
        preparation="Размочить в теплой воде на 10-15 минут, измельчить",
        feeding_method="Пинцетом, мелкими кусочками",
        warning="Хороший источник кальция, но сухой - обязательно размачивать!",
        is_emergency=False,
        is_essential=False,
        price_rating="Дешево, есть в зоомагазинах"
    ),
    
    "Кальциевая добавка": FeedComposition(
        name="Кальциевая добавка (толченая скорлупа/мел)",
        type_="добавка",
        protein_pct=0.0,
        fat_pct=0.0,
        calcium_pct=38.0,
        phosphorus_pct=0.0,
        moisture_pct=0.0,
        preparation="Растолочь яичную скорлупу в муку или купить готовый кормовой мел",
        feeding_method="Обваливать насекомых в порошке перед кормлением",
        warning="Обязательно добавлять, если кормите больше 2-3 дней!",
        is_emergency=False,
        is_essential=True,
        price_rating="Бесплатно (скорлупа) или копейки"
    )
}


# Весовые коэффициенты для расчета порций
WEIGHT_COEFFICIENTS = {
    "новорожденный": 0.08,  # 8% от веса тела за одно кормление
    "птенец": 0.10,          # 10%
    "слеток": 0.12,          # 12%
}

FEEDINGS_PER_DAY = {
    "новорожденный": 8,      # каждые 3 часа
    "птенец": 6,             # каждые 4 часа
    "слеток": 4,             # каждые 6 часов
    "ночь": 2                # ночных кормлений меньше
}


# ==================== ОСНОВНАЯ ЛОГИКА ====================

class BirdFeedingAssistant:
    """Помощник по кормлению птенца"""
    
    def __init__(self):
        self.current_step = 0
        self.bird_data = {}
        self.history = []
        
    def clear_screen(self):
        """Очистка экрана"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """Печать заголовка"""
        print("\n" + "=" * 70)
        print(f"🐦 {title}")
        print("=" * 70)
    
    def print_step(self, step_num: int, total_steps: int, description: str):
        """Показать текущий шаг"""
        print(f"\n📌 Шаг {step_num}/{total_steps}: {description}")
        print("-" * 50)
    
    def get_choice(self, options: Dict[int, str], prompt: str = "Выберите вариант") -> int:
        """Универсальная функция выбора с возможностью вернуться"""
        while True:
            print("\n" + "\n".join([f"  {k}. {v}" for k, v in options.items()]))
            print("  🔙 0. Назад / Начать сначала")
            
            try:
                choice = input(f"\n{prompt}: ").strip()
                if choice == "0":
                    return 0
                choice = int(choice)
                if choice in options:
                    return choice
            except ValueError:
                pass
            print("❌ Неверный ввод. Попробуйте снова.")
    
    def get_yes_no(self, question: str) -> bool:
        """Универсальный вопрос да/нет"""
        while True:
            answer = input(f"\n{question} (д/н): ").strip().lower()
            if answer in ['д', 'y', 'yes', 'да']:
                return True
            if answer in ['н', 'n', 'no', 'нет']:
                return False
            print("Введите 'д' или 'н'")
    
    def estimate_age_from_weight(self, weight_g: float, species: str) -> str:
        """Примерная оценка возраста по весу"""
        if weight_g < 10:
            return "новорожденный"
        elif weight_g < 30:
            return "птенец"
        else:
            return "слеток"
    
    def calculate_feeding(self, bird_weight: float, age_stage: str, feed_name: str) -> FeedingInstruction:
        """Рассчитать порцию для конкретного корма"""
        feed = FEEDS_DATABASE[feed_name]
        
        # Коэффициент размера порции (% от веса тела)
        if age_stage == "новорожденный":
            portion_coef = 0.08
            feedings = 8
        elif age_stage == "птенец":
            portion_coef = 0.10
            feedings = 6
        else:  # слеток
            portion_coef = 0.12
            feedings = 4
        
        # Расчет веса порции (в граммах)
        amount_g = bird_weight * portion_coef
        
        # Корректировка для жирных кормов (зофобас - давать меньше)
        if "Зофобас" in feed_name and amount_g > 0.5:
            amount_g = min(amount_g, 1.0)  # Не больше 1 грамма зофобаса за раз
            warning_extra = "❗ Зофобас очень жирный - лучше комбинировать с другими кормами"
        else:
            warning_extra = ""
        
        return FeedingInstruction(
            feed_name=feed_name,
            amount_per_feeding_g=round(amount_g, 2),
            feedings_per_day=feedings,
            preparation=feed.preparation,
            method=feed.feeding_method,
            warning=feed.warning + (" " + warning_extra if warning_extra else "")
        )
    
    def get_emergency_feeds(self) -> List[str]:
        """Список экстренных кормов (что можно дать сразу)"""
        return [name for name, feed in FEEDS_DATABASE.items() if feed.is_emergency]
    
    def get_essential_feeds(self) -> List[str]:
        """Список необходимых добавок"""
        return [name for name, feed in FEEDS_DATABASE.items() if feed.is_essential]
    
    def step1_welcome(self) -> bool:
        """Шаг 1: Приветствие и базовая информация"""
        self.clear_screen()
        self.print_header("ПОМОЩНИК ПО КОРМЛЕНИЮ НАЙДЕННОГО ПТЕНЦА")
        
        print("""
Вы нашли птенца? Прежде чем начать, запомните главное:

✅ ПТЕНЦА НУЖНО:
• Согреть (грелка, бутылка с теплой водой)
• Кормить часто (каждые 3-4 часа, включая ночь)
• Давать воду отдельно (не в клюв!)

❌ ПТЕНЦУ НЕЛЬЗЯ:
• Давать хлеб, молоко, еду со стола
• Кормить дождевыми червями (опасно!)
• Давать целых крупных насекомых
• Поить насильно (может захлебнуться)

⚠️ ВАЖНО: Лучшее, что вы можете сделать - 
как можно скорее передать птенца специалистам или в центр реабилитации!
        """)
        
        return self.get_yes_no("Готовы продолжить и определить рацион?")
    
    def step2_bird_info(self):
        """Шаг 2: Информация о птице"""
        self.clear_screen()
        self.print_header("ШАГ 1: ОПИШИТЕ ПТЕНЦА")
        
        # Выбор вида
        species_options = {
            1: "Стриж (черный, быстрый)",
            2: "Зяблик / Воробей / Синица (мелкая певчая)",
            3: "Зарянка (малиновка - рыжая грудка)",
            4: "Совсем маленький, не знаю кто",
            5: "Крупная птица (голубь, ворона, чайка)"
        }
        
        choice = self.get_choice(species_options, "На кого похож птенец?")
        if choice == 0:
            return False
        
        species_map = {
            1: BirdSpecies.SWIFT,
            2: BirdSpecies.CHAFFINCH,
            3: BirdSpecies.ROBIN,
            4: BirdSpecies.UNKNOWN,
            5: BirdSpecies.SPARROW
        }
        
        # Вес птицы
        while True:
            try:
                weight = float(input("\nСколько примерно весит птенец (в граммах)?\n👉 "))
                if weight > 0:
                    break
            except ValueError:
                pass
            print("Введите число (например: 15)")
        
        # Возраст/стадия
        age_options = {
            1: "Новорожденный (голый или пух, глаза закрыты)",
            2: "Птенец (пух и перья, глаза открыты, сидит в гнезде)",
            3: "Слеток (почти оперился, прыгает, пробует летать)",
            4: "Не знаю точно"
        }
        
        age_choice = self.get_choice(age_options, "Как выглядит птенец?")
        if age_choice == 0:
            return False
        
        age_map = {
            1: "новорожденный",
            2: "птенец",
            3: "слеток",
            4: "птенец"  # по умолчанию
        }
        
        self.bird_data = {
            'species': species_map[choice],
            'species_name': species_options[choice],
            'weight_g': weight,
            'age_stage': age_map[age_choice],
            'age_description': age_options[age_choice]
        }
        
        return True
    
    def step3_available_feeds(self):
        """Шаг 3: Выбор доступных кормов"""
        self.clear_screen()
        self.print_header("ШАГ 2: ЧЕМ ВЫ МОЖЕТЕ КОРМИТЬ?")
        
        print(f"\n🐦 Птенец: {self.bird_data['species_name']}")
        print(f"⚖️ Вес: {self.bird_data['weight_g']} г")
        print(f"📅 Возраст: {self.bird_data['age_description']}")
        
        print("\n✅ ЭКСТРЕННЫЕ КОРМА (можно дать прямо сейчас):")
        emergency_feeds = self.get_emergency_feeds()
        for i, feed_name in enumerate(emergency_feeds, 1):
            feed = FEEDS_DATABASE[feed_name]
            print(f"  {i}. {feed_name} - {feed.price_rating}")
        
        print("\n📦 ОСНОВНЫЕ КОРМА (лучше для постоянного кормления):")
        main_feeds = [name for name, feed in FEEDS_DATABASE.items() 
                     if feed.type_ == "основной"]
        for i, feed_name in enumerate(main_feeds, len(emergency_feeds) + 1):
            feed = FEEDS_DATABASE[feed_name]
            print(f"  {i}. {feed_name} - {feed.price_rating}")
        
        # Формируем список всех кормов для выбора
        all_feeds = emergency_feeds + main_feeds + ["Кальциевая добавка"]
        
        selected_feeds = []
        while True:
            print(f"\n📝 Введите номера кормов, которые У ВАС ЕСТЬ (через запятую или пробел)")
            print("   Например: 1,3,5 или 1 3 5")
            print("   Или введите 0 чтобы выбрать другие корма")
            
            choice = input("👉 ").strip()
            
            if choice == "0":
                return False
            
            try:
                # Разбираем ввод
                numbers = []
                for part in choice.replace(',', ' ').split():
                    if part.strip():
                        numbers.append(int(part.strip()))
                
                for num in numbers:
                    if 1 <= num <= len(all_feeds):
                        feed_name = all_feeds[num - 1]
                        if feed_name not in selected_feeds:
                            selected_feeds.append(feed_name)
                    else:
                        print(f"⚠️ Номер {num} вне диапазона, пропущен")
                
                if selected_feeds:
                    break
                    
            except ValueError:
                print("❌ Неверный формат. Введите числа через запятую.")
        
        self.bird_data['selected_feeds'] = selected_feeds
        return True
    
    def step4_show_instructions(self):
        """Шаг 4: Показать инструкции по кормлению"""
        self.clear_screen()
        self.print_header("ИНСТРУКЦИЯ ПО КОРМЛЕНИЮ")
        
        weight = self.bird_data['weight_g']
        age = self.bird_data['age_stage']
        
        print(f"\n🐦 Птенец: {self.bird_data['species_name']}")
        print(f"⚖️ Вес: {weight} г")
        print(f"📅 Возраст: {self.bird_data['age_description']}")
        print(f"🍽️ Кормить нужно КАЖДЫЕ {4 if age=='слеток' else 3} часа!")
        print("\n" + "=" * 70)
        
        # Общие рекомендации
        print("\n📋 ОБЩИЕ ПРАВИЛА:")
        print("  • Перед кормлением согрейте птенца")
        print("  • Корм должен быть комнатной температуры")
        print("  • После кормления протрите клюв")
        print("  • Вода должна быть в отдельной поилке (не в клюв!)")
        print("  • Насекомых лучше посыпать кальцием")
        
        # Инструкции для каждого выбранного корма
        print("\n🍖 ИНСТРУКЦИИ ДЛЯ ВАШИХ КОРМОВ:")
        print("-" * 70)
        
        for feed_name in self.bird_data['selected_feeds']:
            instruction = self.calculate_feeding(weight, age, feed_name)
            
            print(f"\n📌 {instruction.feed_name}:")
            print(f"  • ЗА ОДНО КОРМЛЕНИЕ: {instruction.amount_per_feeding_g} г")
            print(f"  • КОРМЛЕНИЙ В ДЕНЬ: {instruction.feedings_per_day}")
            print(f"  • КАК ГОТОВИТЬ: {instruction.preparation}")
            print(f"  • КАК ДАВАТЬ: {instruction.method}")
            
            if instruction.warning:
                print(f"  ⚠️ ВНИМАНИЕ: {instruction.warning}")
        
        # Рекомендация по кальцию
        print("\n" + "=" * 70)
        print("💊 КАЛЬЦИЙ - ЭТО ОЧЕНЬ ВАЖНО!")
        print("Если кормите больше 2-3 дней, ОБЯЗАТЕЛЬНО добавляйте кальций:")
        print("  • Обваливайте насекомых в толченой яичной скорлупе")
        print("  • Или купите кормовой мел в зоомагазине")
        print("  • Без кальция у птенца разовьется рахит!")
        
        # Режим кормления
        print("\n⏰ ПРИМЕРНЫЙ РЕЖИМ КОРМЛЕНИЯ:")
        if age == "новорожденный":
            print("  06:00, 09:00, 12:00, 15:00, 18:00, 21:00, 00:00, 03:00")
        elif age == "птенец":
            print("  06:00, 10:00, 14:00, 18:00, 22:00, 02:00")
        else:
            print("  07:00, 13:00, 19:00, 01:00")
        
        # Что делать дальше
        print("\n" + "=" * 70)
        print("🚨 ЧТО ДЕЛАТЬ ДАЛЬШЕ:")
        print("  1. Свяжитесь с центром реабилитации диких птиц")
        print("  2. Или найдите сообщество орнитологов в соцсетях")
        print("  3. Не держите птенца дольше необходимого - шансов выжить на воле больше!")
        
        print("\n" + "=" * 70)
        print("УСПЕШНОГО ВЫХАЖИВАНИЯ! 🍀")
        print("=" * 70)
        
        input("\nНажмите Enter, чтобы продолжить...")
        return True
    
    def step5_additional_help(self):
        """Шаг 5: Дополнительная помощь"""
        self.clear_screen()
        self.print_header("ДОПОЛНИТЕЛЬНАЯ ПОМОЩЬ")
        
        options = {
            1: "🔄 Рассчитать для другого набора кормов",
            2: "🐦 Начать с другим птенцом",
            3: "ℹ️ Показать инструкцию еще раз",
            4: "🚪 Завершить работу"
        }
        
        choice = self.get_choice(options, "Что делаем дальше?")
        
        if choice == 1:
            return "new_feeds"
        elif choice == 2:
            return "new_bird"
        elif choice == 3:
            return "show_again"
        elif choice == 4:
            return "exit"
        elif choice == 0:
            return "back"
        
        return "exit"
    
    def run(self):
        """Главный цикл программы"""
        while True:
            # Шаг 1: Приветствие
            if not self.step1_welcome():
                print("\nДо свидания! Если передумаете - запустите снова.")
                break
            
            # Шаг 2: Информация о птице
            if not self.step2_bird_info():
                continue
            
            while True:
                # Шаг 3: Выбор кормов
                if not self.step3_available_feeds():
                    break
                
                # Шаг 4: Показать инструкции
                self.step4_show_instructions()
                
                # Шаг 5: Что дальше
                next_action = self.step5_additional_help()
                
                if next_action == "new_feeds":
                    continue  # Выбрать другие корма для той же птицы
                elif next_action == "new_bird":
                    break  # Начать с новой птицы
                elif next_action == "show_again":
                    self.step4_show_instructions()
                elif next_action == "exit":
                    return
                elif next_action == "back":
                    break


# ==================== ЗАПУСК ====================

def main():
    """Запуск программы"""
    try:
        assistant = BirdFeedingAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\n\n👋 Программа завершена. Берегите птиц!")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")
        print("Попробуйте запустить программу снова.")


if __name__ == "__main__":
    main()