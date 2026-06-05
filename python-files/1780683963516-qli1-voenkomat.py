import random
import time
import os
import sys
from datetime import datetime

# ============== VOENKOMAT SIMULATOR 3000 ==============
# Симулятор военкомата - испытай свою судьбу!

class Voenkomat:
    def __init__(self):
        self.player_name = ""
        self.age = 0
        self.health_status = "Здоров"
        self.education = ""
        self.work_status = ""
        self.family_status = ""
        self.has_children = False
        self.has_health_issues = False
        self.has_studies = False
        self.is_only_son = False
        self.has_criminal_record = False
        
        # Статистика
        self.category = ""
        self.destiny = ""
        self.reputation = 0
        self.bribes_given = 0
        self.nights_spent = 0
        
        # Предметы
        self.inventory = {
            "passport": True,
            "military_card": False,
            "medical_certificate": None,
            "bribe_money": random.randint(0, 50000)
        }
        
        self.documents = []
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self):
        print("╔" + "=" * 60 + "╗")
        print("║" + " " * 15 + "ВОЕНКОМАТ SIMULATOR 3000" + " " * 17 + "║")
        print("║" + " " * 10 + "Испытай свою гражданскую судьбу" + " " * 14 + "║")
        print("╚" + "=" * 60 + "╝")
        print()
        
    def slow_print(self, text, delay=0.03):
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()
        
    def start_registration(self):
        self.clear_screen()
        self.print_header()
        
        print("📋 РЕГИСТРАЦИЯ В ВОЕНКОМАТЕ")
        print("-" * 50)
        
        self.player_name = input("Введите ваше ФИО: ")
        self.age = int(input("Ваш возраст: "))
        
        if self.age < 18:
            self.slow_print("\n❌ Вам нет 18 лет! Приходите через год.")
            sys.exit(0)
        elif self.age > 27:
            self.slow_print("\n✅ Вам уже больше 27 - вы в запасе! Поздравляю!")
            sys.exit(0)
            
        print("\n📝 АНКЕТИРОВАНИЕ")
        print("-" * 50)
        
        # Семейное положение
        family = input("Семейное положение (женат/холост/разведен): ")
        self.family_status = family
        
        if input("Есть дети? (да/нет): ").lower() == "да":
            self.has_children = True
            
        if input("Единственный сын в семье? (да/нет): ").lower() == "да":
            self.is_only_son = True
            
        # Образование
        self.education = input("Образование (школа/колледж/вуз): ")
        if input("Учитесь сейчас? (да/нет): ").lower() == "да":
            self.has_studies = True
            
        # Работа
        self.work_status = input("Работаете? (да/нет): ")
        
        # Здоровье
        print("\n🏥 МЕДИЦИНСКАЯ АНКЕТА")
        print("-" * 50)
        
        health_issues = input("Есть проблемы со здоровьем? (да/нет): ")
        if health_issues.lower() == "да":
            self.has_health_issues = True
            issue = input("Какие проблемы? (плохое зрение/плоскостопие/астма/другое): ")
            self.health_issue_detail = issue
            
        if input("Состоите на учете у психиатра/нарколога? (да/нет): ").lower() == "да":
            self.has_health_issues = True
            
        # Судимости
        if input("Есть судимость? (да/нет): ").lower() == "да":
            self.has_criminal_record = True
            
        print("\n💼 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ")
        print("-" * 50)
        
        self.reputation = random.randint(0, 100)
        
    def medical_exam(self):
        self.clear_screen()
        self.print_header()
        
        print("🏥 МЕДИЦИНСКАЯ КОМИССИЯ")
        print("-" * 50)
        self.slow_print("Врачи осматривают вас...")
        time.sleep(2)
        
        # Симуляция медкомиссии
        doctors = [
            "Терапевт", "Хирург", "Невролог", "Психиатр", 
            "Окулист", "Лор", "Стоматолог", "Дерматолог"
        ]
        
        issues_found = 0
        
        for doctor in doctors:
            self.slow_print(f"\n👨‍⚕️ {doctor} осматривает вас...")
            time.sleep(1)
            
            if self.has_health_issues and random.random() < 0.3:
                self.slow_print(f"   {doctor} обнаружил проблемы со здоровьем!")
                issues_found += 1
            else:
                self.slow_print(f"   {doctor}: Здоров")
                
        time.sleep(1)
        
        if issues_found > 2:
            self.health_status = "Ограниченно годен"
            self.category = "B"
            self.slow_print(f"\n📋 Диагноз: Выявлено {issues_found} проблем со здоровьем")
            self.slow_print("📋 Категория годности: B (ограниченно годен)")
        else:
            self.health_status = "Годен"
            self.category = random.choice(["A1", "A2", "A3"])
            self.slow_print(f"\n📋 Категория годности: {self.category} (годен к службе)")
            
        input("\nНажмите Enter для продолжения...")
        
    def psychological_test(self):
        self.clear_screen()
        self.print_header()
        
        print("🧠 ПСИХОЛОГИЧЕСКОЕ ТЕСТИРОВАНИЕ")
        print("-" * 50)
        
        questions = [
            ("Вы любите соблюдать приказы?", ["да", "нет"]),
            ("Способны ли вы на убийство врага?", ["да", "нет", "не уверен"]),
            ("Боитесь ли вы высоты?", ["да", "нет"]),
            ("Можете ли вы работать в команде?", ["да", "нет"]),
            ("Паникуете в стрессовых ситуациях?", ["да", "нет", "иногда"]),
            ("Готовы ли вы к физическим нагрузкам?", ["да", "нет"]),
            ("Страдаете ли вы клаустрофобией?", ["да", "нет"]),
            ("Легко ли засыпаете в новых местах?", ["да", "нет", "иногда"])
        ]
        
        score = 0
        max_score = len(questions) * 2
        
        for q, options in questions:
            print(f"\n❓ {q}")
            for i, opt in enumerate(options, 1):
                print(f"   {i}. {opt}")
            
            answer = input("Ваш ответ (1-{}): ".format(len(options)))
            
            # Логика оценки
            if q == "Вы любите соблюдать приказы?" and answer == "1":
                score += 2
            elif q == "Способны ли вы на убийство врага?" and answer == "1":
                score += 2
            elif q == "Боитесь ли вы высоты?" and answer == "2":
                score += 1
            elif q == "Можете ли вы работать в команде?" and answer == "1":
                score += 2
            elif q == "Паникуете в стрессовых ситуациях?" and answer == "2":
                score += 2
            elif q == "Готовы ли вы к физическим нагрузкам?" and answer == "1":
                score += 2
                
        time.sleep(1)
        
        if score > max_score * 0.7:
            self.slow_print("\n✅ Психологическое заключение: Психически устойчив, рекомендован к службе")
            self.psych_score = "Высокая"
        elif score > max_score * 0.4:
            self.slow_print("\n⚠️ Психологическое заключение: Удовлетворительно, годен с ограничениями")
            self.psych_score = "Средняя"
        else:
            self.slow_print("\n❌ Психологическое заключение: Неустойчив, требуется наблюдение")
            self.psych_score = "Низкая"
            
        input("\nНажмите Enter для продолжения...")
        
    def interview(self):
        self.clear_screen()
        self.print_header()
        
        print("💼 ИНТЕРВЬЮ С ПРИЗЫВНОЙ КОМИССИЕЙ")
        print("-" * 50)
        
        # Случайные вопросы от комиссии
        questions_bank = [
            "Почему вы не хотите служить?",
            "Кем вы видите себя через 5 лет?",
            "Как вы относитесь к армейской дисциплине?",
            "Ваши физические данные?",
            "Есть ли у вас водительские права?",
            "Какие у вас спортивные достижения?",
            "Готовы ли вы к командировкам?",
            "Как ваша семья относится к армии?"
        ]
        
        asked = random.sample(questions_bank, 3)
        interview_score = 0
        
        for q in asked:
            print(f"\n👨‍⚖️ Член комиссии: {q}")
            answer = input("Ваш ответ: ")
            
            # Оценка ответа
            good_keywords = ["готов", "могу", "хочу", "служу", "россии", "долг", "ответственно"]
            bad_keywords = ["не хочу", "боюсь", "не готов", "проблемы", "справка", "откосить"]
            
            answer_lower = answer.lower()
            
            if any(word in answer_lower for word in good_keywords):
                interview_score += 1
                print("   ✅ Хороший ответ")
            elif any(word in answer_lower for word in bad_keywords):
                interview_score -= 1
                print("   ⚠️ Сомнительный ответ")
            else:
                print("   🤷 Нейтральный ответ")
                
        time.sleep(1)
        
        if interview_score >= 2:
            self.slow_print("\n✅ Комиссия: Решение положительное")
            self.destiny = "Призыв"
        elif interview_score >= 0:
            self.slow_print("\n⚠️ Комиссия: Решение отложено")
            self.destiny = "Отсрочка"
        else:
            self.slow_print("\n❌ Комиссия: Рекомендовано дополнительное обследование")
            self.destiny = "Доп. обследование"
            
        input("\nНажмите Enter для продолжения...")
        
    def bribe_attempt(self):
        self.clear_screen()
        self.print_header()
        
        print("💰 ПОПЫТКА РЕШИТЬ ВОПРОС")
        print("-" * 50)
        print(f"Ваш бюджет: {self.inventory['bribe_money']} руб.")
        
        if self.inventory['bribe_money'] < 50000:
            self.slow_print("\n❌ У вас недостаточно средств для решения вопроса")
            return False
            
        print("\nВарианты:")
        print("1. Дать взятку (50000 руб)")
        print("2. Найти знакомства")
        print("3. Подделать документы")
        print("4. Не рисковать")
        
        choice = input("\nВаш выбор (1-4): ")
        
        if choice == "1":
            self.slow_print("\n💰 Вы предлагаете взятку...")
            time.sleep(2)
            
            if random.random() < 0.3:
                self.slow_print("❌ Вас поймали! Заведено уголовное дело!")
                self.has_criminal_record = True
                self.reputation -= 50
                self.inventory['bribe_money'] -= 50000
                return False
            else:
                self.slow_print("✅ Вопрос решен! Вы получили отсрочку!")
                self.destiny = "Отсрочка (договорная)"
                self.bribes_given += 1
                self.inventory['bribe_money'] -= 50000
                return True
                
        elif choice == "2":
            self.slow_print("\n📞 Вы ищете знакомства...")
            time.sleep(2)
            
            if self.reputation > 50:
                self.slow_print("✅ У вас есть связи! Вопрос решен!")
                self.destiny = "Отсрочка (по знакомству)"
                return True
            else:
                self.slow_print("❌ У вас нет нужных знакомств")
                return False
                
        elif choice == "3":
            self.slow_print("\n📄 Вы подделываете документы...")
            time.sleep(2)
            
            if random.random() < 0.2:
                self.slow_print("❌ Подделка раскрыта! Уголовная ответственность!")
                self.has_criminal_record = True
                return False
            else:
                self.slow_print("✅ Документы приняты! Вы получили отсрочку!")
                self.destiny = "Отсрочка (по документам)"
                return True
        else:
            return False
            
    def random_event(self):
        """Случайные события в военкомате"""
        events = [
            ("🏃‍♂️ Вас вызвали на срочные сборы!", 5),
            ("📄 Ваши документы потеряли!", -10),
            ("🎉 Объявлена амнистия!", 15),
            ("⚠️ Ваш врач ушел в отпуск - задержка", -5),
            ("⭐ Вы проявили себя - вас заметили!", 10)
        ]
        
        if random.random() < 0.3:
            event, effect = random.choice(events)
            self.slow_print(f"\n✨ СОБЫТИЕ: {event}")
            self.reputation += effect
            self.slow_print(f"   Репутация: {'+' if effect > 0 else ''}{effect}")
            
    def final_decision(self):
        self.clear_screen()
        self.print_header()
        
        print("⚖️ ОКОНЧАТЕЛЬНОЕ РЕШЕНИЕ")
        print("-" * 50)
        
        self.slow_print("Комиссия принимает финальное решение...")
        time.sleep(3)
        
        # Расчет итоговой категории
        if self.has_criminal_record:
            self.destiny = "Не годен (судимость)"
        elif self.has_health_issues and self.category in ["B", "B1"]:
            self.destiny = "Ограниченно годен (запас)"
        elif self.has_studies and self.age < 24:
            self.destiny = "Отсрочка по учебе"
        elif self.has_children:
            self.destiny = "Отсрочка по семейным обстоятельствам"
        elif self.is_only_son:
            self.destiny = "Отсрочка (единственный сын)"
        elif self.age >= 27:
            self.destiny = "Зачислен в запас"
        else:
            self.destiny = "Призыв на срочную службу"
            
        # Финальный вывод
        print("\n" + "=" * 60)
        
        if "Призыв" in self.destiny:
            print("🔴 РЕШЕНИЕ: " + self.destiny)
            self.slow_print(f"""
    Поздравляю, вы призваны в армию!
    
    Место службы: в/ч {random.randint(10000, 99999)}
    Срок службы: 12 месяцев
    Дата отправки: {datetime.now().strftime('%d.%m.%Y')}
    
    Не забудьте взять:
    - Паспорт
    - Приписное свидетельство
    - Теплые вещи
    - Телефон (по разрешению командира)
            """)
        elif "Отсрочка" in self.destiny:
            print("🟡 РЕШЕНИЕ: " + self.destiny)
            self.slow_print(f"""
    Вам предоставлена отсрочка на {random.randint(6, 18)} месяцев.
    
    Причина: {self.destiny}
    
    Явитесь в военкомат для продления отсрочки
    не позднее чем за 30 дней до ее окончания.
            """)
        else:
            print("🟢 РЕШЕНИЕ: " + self.destiny)
            self.slow_print(f"""
    Вы признаны не годным/ограниченно годным к военной службе.
    
    Вы зачислены в запас и получите военный билет.
    
    Военный билет будет готов через {random.randint(30, 90)} дней.
            """)
            
        print("=" * 60)
        
    def show_statistics(self):
        print("\n📊 СТАТИСТИКА ПРОХОЖДЕНИЯ")
        print("-" * 50)
        print(f"ФИО: {self.player_name}")
        print(f"Возраст: {self.age}")
        print(f"Категория годности: {self.category if hasattr(self, 'category') else 'Не определена'}")
        print(f"Здоровье: {self.health_status}")
        print(f"Психологическая оценка: {self.psych_score if hasattr(self, 'psych_score') else 'Не пройдено'}")
        print(f"Репутация: {self.reputation}")
        print(f"Решение: {self.destiny}")
        
        if self.bribes_given > 0:
            print(f"⚠️ Взяток дано: {self.bribes_given}")
            
    def run(self):
        self.start_registration()
        
        # Процесс прохождения комиссии
        self.medical_exam()
        self.psychological_test()
        self.interview()
        
        # Случайные события
        self.random_event()
        
        # Возможность взятки
        if self.destiny == "Призыв":
            print("\n" + "=" * 60)
            choice = input("Хотите попробовать решить вопрос? (да/нет): ")
            if choice.lower() == "да":
                self.bribe_attempt()
                
        # Финальное решение
        self.final_decision()
        self.show_statistics()
        
        print("\n" + "=" * 60)
        print("Спасибо за прохождение симулятора!")
        print("Помните: армия - это школа жизни!")
        print("=" * 60)

if __name__ == "__main__":
    voenkomat = Voenkomat()
    voenkomat.run()
    
    input("\nНажмите Enter для выхода...")