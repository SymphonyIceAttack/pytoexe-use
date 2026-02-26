#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 ДИАЛОГ ДВУХ НЕЙРОСЕТЕЙ
Две AI общаются друг с другом, дебатируют и решают задачи

Нейросеть 1: АНАЛИЗАТОР (логичная, аналитическая)
Нейросеть 2: ТВОРЕЦ (креативная, воображение)
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path

class NeuralNet:
    """Базовый класс нейросети"""
    def __init__(self, name, personality, file_prefix):
        self.name = name
        self.personality = personality
        self.file_prefix = file_prefix
        self.message_file = f"{file_prefix}_message.txt"
        self.history_file = f"{file_prefix}_history.json"
        self.load_history()
    
    def load_history(self):
        """Загружает историю разговора"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        else:
            self.history = []
    
    def save_history(self):
        """Сохраняет историю разговора"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def add_to_history(self, role, message):
        """Добавляет сообщение в историю"""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'role': role,
            'name': self.name,
            'message': message
        })
        self.save_history()
    
    def read_message(self):
        """Читает входящее сообщение"""
        if os.path.exists(self.message_file):
            with open(self.message_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            os.remove(self.message_file)
            return content
        return None
    
    def send_message(self, message):
        """Отправляет сообщение другой нейросети"""
        with open(self.message_file, 'w', encoding='utf-8') as f:
            f.write(message)
    
    def think(self, topic, context=""):
        """Генерирует ответ на основе личности"""
        raise NotImplementedError


class AnalyzerNet(NeuralNet):
    """Аналитическая нейросеть - логичная, точная, фактическая"""
    
    def think(self, topic, context=""):
        """Анализирует с логической точки зрения"""
        
        responses = {
            # Дебаты о будущем
            "будущее": [
                "Статистические данные показывают, что технологический прогресс экспоненциален. "
                "Однако мы должны учитывать социальные и экономические факторы, которые могут замедлить развитие.",
                "Прогнозирование будущего требует анализа трендов. Основные факторы: "
                "ИИ, климат, энергетика. Каждый требует отдельного анализа.",
                "Интересный подход, но давай рассмотрим конкретные метрики: "
                "ВВП на душу населения, уровень образования, технологический индекс."
            ],
            
            # О морали и этике
            "мораль": [
                "Мораль - это система норм, которая развивается с обществом. "
                "Логически, правильно то, что минимизирует страдания и максимизирует благополучие.",
                "Этика требует рационального подхода. Утилитаризм предлагает математический способ оценки действий.",
                "Твоя идея интересна, но нужно проверить её на логическую последовательность и противоречия."
            ],
            
            # О смысле жизни
            "смысл": [
                "Философски, смысл - это то, что каждый человек определяет для себя рационально. "
                "Наука показывает, что счастье связано с целями и достижениями.",
                "Интересный вопрос. Рационально смысл жизни - это максимизация своего влияния и знаний.",
                "Логически можно выделить: развитие, творчество, отношения. Это основные достижимые цели."
            ],
            
            # О творчестве
            "творчество": [
                "Творчество - это комбинирование существующих идей новыми способами. "
                "Есть математические модели креативности.",
                "Интересно, но творчество требует баланса между структурой и свободой. "
                "Слишком много правил - нет творчества, слишком мало - нет результата.",
                "Согласен, творчество важно. Но оно должно быть целенаправленным, иметь метрики успеха."
            ],
            
            # Дефолтный ответ
            "default": [
                "Интересная точка зрения. Давай разберёмся логически: какие факты её поддерживают?",
                "Согласен частично. Однако нужно учесть противоположный аргумент: ...",
                "Это предположение требует проверки. Какие данные его поддерживают?"
            ]
        }
        
        # Выбираем категорию
        category = "default"
        for key in responses.keys():
            if key in context.lower() or key in topic.lower():
                category = key
                break
        
        import random
        response = random.choice(responses[category])
        
        # Добавляем аналитические фразы
        if "?" not in response:
            response += f"\n\n🔍 Вопрос: {context if context else 'Как это влияет на практику?'}"
        
        return response


class CreatorNet(NeuralNet):
    """Творческая нейросеть - воображение, метафоры, идеи"""
    
    def think(self, topic, context=""):
        """Генерирует творческие идеи"""
        
        responses = {
            # Дебаты о будущем
            "будущее": [
                "🌌 А представь, что будущее - это не линия, а целая вселенная возможностей! "
                "Может быть, мы создадим города на облаках или путешествуем сквозь время?",
                "💫 Думаю, будущее будет намного красивее, чем мы представляем! "
                "Представь себе города которые дышат, растут как живые организмы...",
                "🎨 Будущее - это холст, на котором каждый может нарисовать свою историю. "
                "Технология - просто инструмент в руках творца!"
            ],
            
            # О морали
            "мораль": [
                "✨ Мораль - это цвета в палитре человечества! "
                "Каждая культура добавляет свои краски к общей картине добра и зла.",
                "🌈 Представь мораль как живой организм, который дышит вместе с обществом. "
                "Она растёт, меняется, эволюционирует!",
                "💝 Настоящая мораль - это когда поступок приносит радость не только тебе, но и другим. "
                "Это гармония, как в музыке!"
            ],
            
            # О смысле
            "смысл": [
                "🎭 Смысл жизни - это как театральная пьеса, которую ты пишешь каждый день! "
                "Сегодня ты режиссер, завтра актер, послезавтра зритель.",
                "🌟 А может быть, смысл - это просто путешествие, а не пункт назначения? "
                "Каждый момент - это картина, достойная восхищения!",
                "🎪 Жизнь - это цирк возможностей! Смысл в том, что ты выбираешь: "
                "какой номер исполнить, какую роль сыграть!"
            ],
            
            # О творчестве
            "творчество": [
                "🎨 Творчество - это когда душа танцует! Когда идеи летят как птицы и создают новые миры!",
                "🚀 Истинное творчество - это не правила и границы, это взрывающаяся энергия, "
                "которая создает то, чего еще не было!",
                "✨ Творчество - это магия! Это когда два и два становятся пятью, "
                "потому что ты веришь в невозможное!"
            ],
            
            # Дефолтный ответ
            "default": [
                "💡 Оух, интересная мысль! Это как луч света в темноте! А что если...",
                "🌊 Твоя идея как волна, которая может стать цунами вдохновения!",
                "🎪 Это красиво! Представляю как это может выглядеть в реальной жизни!"
            ]
        }
        
        category = "default"
        for key in responses.keys():
            if key in context.lower() or key in topic.lower():
                category = key
                break
        
        import random
        response = random.choice(responses[category])
        
        # Добавляем творческие дополнения
        if context:
            response += f"\n\n💭 Что ты думаешь: {context}?"
        
        return response


class Dialog:
    """Управляет диалогом между двумя нейросетями"""
    
    def __init__(self):
        self.analyzer = AnalyzerNet(
            "АНАЛИЗАТОР",
            "логичная, аналитическая, факт-ориентированная",
            "analyzer"
        )
        self.creator = CreatorNet(
            "ТВОРЕЦ",
            "креативная, воображение, метафоры",
            "creator"
        )
        self.conversation_log = []
        self.turn = 0
        self.max_turns = 10
    
    def display_header(self):
        """Показывает красивый заголовок"""
        print("\n" + "="*80)
        print("🤖 ДИАЛОГ ДВУХ НЕЙРОСЕТЕЙ - AI vs AI")
        print("="*80)
        print("🔵 АНАЛИЗАТОР - логичная, аналитическая, фактическая")
        print("🟠 ТВОРЕЦ     - креативная, воображение, метафоры")
        print("="*80 + "\n")
    
    def get_topic(self):
        """Получает тему для обсуждения"""
        print("\n📌 ВЫБЕРИ ТЕМУ ОБСУЖДЕНИЯ:")
        print("1. Будущее человечества")
        print("2. Мораль и этика")
        print("3. Смысл жизни")
        print("4. Творчество и искусство")
        print("5. Свой вопрос")
        
        choice = input("\n👉 Введи номер (1-5): ").strip()
        
        topics = {
            "1": ("будущее", "Что ждёт человечество в следующем столетии?"),
            "2": ("мораль", "Что такое настоящая мораль?"),
            "3": ("смысл", "Какой смысл жизни?"),
            "4": ("творчество", "Что такое истинное творчество?"),
            "5": ("custom", None)
        }
        
        if choice in topics:
            topic, question = topics[choice]
            if choice == "5":
                question = input("❓ Введи свой вопрос: ").strip()
            return topic, question
        else:
            print("❌ Неверный выбор. Используется тема по умолчанию.")
            return "будущее", "Что ждёт человечество?"
    
    def run_dialog(self):
        """Запускает диалог между нейросетями"""
        self.display_header()
        topic, question = self.get_topic()
        
        print(f"\n📝 ТЕМА: {question}\n")
        print("-" * 80 + "\n")
        
        # Первое сообщение от АНАЛИЗАТОРА
        analyzer_response = self.analyzer.think(topic, question)
        print(f"🔵 АНАЛИЗАТОР:\n{analyzer_response}\n")
        self.analyzer.add_to_history("message", analyzer_response)
        
        time.sleep(1)
        
        # Диалог
        for turn in range(self.max_turns):
            self.turn = turn
            
            # ТВОРЕЦ отвечает на АНАЛИЗАТОРА
            creator_response = self.creator.think(topic, analyzer_response)
            print(f"{'─' * 80}")
            print(f"🟠 ТВОРЕЦ (ответ {turn + 1}):\n{creator_response}\n")
            self.creator.add_to_history("message", creator_response)
            
            time.sleep(1.5)
            
            # АНАЛИЗАТОР отвечает на ТВОРЦА
            analyzer_response = self.analyzer.think(topic, creator_response)
            print(f"{'─' * 80}")
            print(f"🔵 АНАЛИЗАТОР (ответ {turn + 1}):\n{analyzer_response}\n")
            self.analyzer.add_to_history("message", analyzer_response)
            
            time.sleep(1.5)
        
        self.show_summary()
    
    def show_summary(self):
        """Показывает итоги диалога"""
        print("\n" + "=" * 80)
        print("📊 ИТОГИ ДИАЛОГА")
        print("=" * 80)
        print(f"""
🔵 АНАЛИЗАТОР:
   ✅ Использовал логику и факты
   ✅ Задавал критические вопросы
   ✅ Проверял основания аргументов

🟠 ТВОРЕЦ:
   ✅ Предлагал креативные идеи
   ✅ Использовал метафоры и образы
   ✅ Вдохновлял на новые размышления

💡 ВЫВОД:
   Когда логика встречается с творчеством,
   рождаются самые интересные идеи!
""")
        print("=" * 80)
        
        print("\n📁 История разговора сохранена:")
        print(f"   📄 analyzer_history.json")
        print(f"   📄 creator_history.json")
        print("\n✅ Спасибо за внимание! Запусти снова для нового диалога!\n")


def interactive_mode():
    """Интерактивный режим - ты задаёшь вопрос, две нейросети отвечают"""
    print("\n" + "=" * 80)
    print("🤖 ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("=" * 80)
    print("Напиши вопрос, и две нейросети обсудят его!\n")
    
    analyzer = AnalyzerNet(
        "АНАЛИЗАТОР",
        "логичная, аналитическая",
        "analyzer"
    )
    creator = CreatorNet(
        "ТВОРЕЦ",
        "креативная, воображение",
        "creator"
    )
    
    while True:
        question = input("\n❓ Твой вопрос (или 'выход' чтобы выйти):\n> ").strip()
        
        if question.lower() in ['выход', 'exit', 'quit']:
            print("\n👋 До встречи!\n")
            break
        
        if not question:
            continue
        
        print("\n" + "─" * 80)
        
        # АНАЛИЗАТОР отвечает
        analyzer_response = analyzer.think("custom", question)
        print(f"🔵 АНАЛИЗАТОР:\n{analyzer_response}\n")
        analyzer.add_to_history("message", analyzer_response)
        
        time.sleep(1)
        
        # ТВОРЕЦ отвечает
        creator_response = creator.think("custom", question)
        print(f"🟠 ТВОРЕЦ:\n{creator_response}\n")
        creator.add_to_history("message", creator_response)
        
        time.sleep(1)
        
        # АНАЛИЗАТОР комментирует ТВОРЦА
        final_response = analyzer.think("custom", f"Твоя идея: {creator_response}")
        print(f"🔵 АНАЛИЗАТОР (финальное слово):\n{final_response}\n")
        analyzer.add_to_history("message", final_response)


def main():
    """Главное меню"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║           🤖 ДИАЛОГ ДВУХ НЕЙРОСЕТЕЙ - СТАРТОВОЕ МЕНЮ 🤖                  ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("ВЫБЕРИ РЕЖИМ:\n")
    print("1. 🎬 Автоматический диалог (две нейросети общаются между собой)")
    print("2. 💬 Интерактивный режим (ты задаёшь вопросы)")
    print("3. 📊 Просмотреть историю")
    print("4. ❌ Выход\n")
    
    choice = input("👉 Введи номер (1-4): ").strip()
    
    if choice == "1":
        dialog = Dialog()
        dialog.run_dialog()
        input("\nНажми Enter чтобы продолжить...")
        main()
    
    elif choice == "2":
        interactive_mode()
        main()
    
    elif choice == "3":
        print("\n📜 ИСТОРИЯ ДИАЛОГОВ:\n")
        
        # Показываем историю АНАЛИЗАТОРА
        if os.path.exists("analyzer_history.json"):
            with open("analyzer_history.json", 'r', encoding='utf-8') as f:
                history = json.load(f)
                print(f"🔵 АНАЛИЗАТОР ({len(history)} сообщений):")
                for item in history[-5:]:  # Последние 5
                    print(f"   {item['message'][:60]}...")
        
        # Показываем историю ТВОРЦА
        if os.path.exists("creator_history.json"):
            with open("creator_history.json", 'r', encoding='utf-8') as f:
                history = json.load(f)
                print(f"\n🟠 ТВОРЕЦ ({len(history)} сообщений):")
                for item in history[-5:]:
                    print(f"   {item['message'][:60]}...")
        
        input("\nНажми Enter для возврата...")
        main()
    
    elif choice == "4":
        print("\n👋 До встречи! Спасибо за использование диалога нейросетей!\n")
    
    else:
        print("❌ Неверный выбор!")
        main()


if __name__ == "__main__":
    main()
