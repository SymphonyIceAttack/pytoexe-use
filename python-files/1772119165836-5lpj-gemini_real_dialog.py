#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 РЕАЛЬНЫЙ ДИАЛОГ ДВУХ GEMINI AI
Две настоящие нейросети общаются друг с другом через Google Gemini API

АНАЛИЗАТОР: Логичная, аналитическая, критическая
ТВОРЕЦ: Креативная, воображение, метафоры
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path

class GeminiAI:
    """Класс для взаимодействия с Google Gemini API"""
    
    def __init__(self, api_key, name, personality):
        self.api_key = api_key
        self.name = name
        self.personality = personality
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.history = []
        self.history_file = f"{name.lower().replace(' ', '_')}_history.json"
        self.load_history()
    
    def load_history(self):
        """Загружает историю разговора"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except:
                self.history = []
        else:
            self.history = []
    
    def save_history(self):
        """Сохраняет историю разговора"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Ошибка сохранения истории: {e}")
    
    def add_to_history(self, role, message):
        """Добавляет сообщение в историю"""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'role': role,
            'name': self.name,
            'message': message
        })
        self.save_history()
    
    def generate_response(self, prompt, context=""):
        """Генерирует ответ через Gemini API"""
        try:
            # Формируем системный промпт
            system_message = f"""Ты {self.name}. Твоя личность: {self.personality}
            
Важные правила:
- Отвечай кратко (2-3 предложения максимум)
- Будь в роли, не выходи из образа
- Если это ответ другой нейросети, обращайся к её идеям
- Используй эмодзи если уместно

Контекст разговора: {context if context else 'Это начало разговора'}
"""
            
            # Отправляем запрос к Gemini
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": system_message + "\n\nОтвети на: " + prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 200,
                }
            }
            
            response = requests.post(
                f"{self.url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Проверяем есть ли ответ
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        text = candidate['content']['parts'][0]['text']
                        return text.strip()
            
            # Если ошибка
            error_msg = response.text if response.status_code != 200 else "Нет ответа"
            print(f"⚠️  Ошибка API: {response.status_code} - {error_msg[:100]}")
            return None
            
        except requests.exceptions.Timeout:
            print("⏱️  Таймаут: Gemini не ответила за 30 секунд")
            return None
        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")
            return None
    
    def think(self, topic, previous_message=""):
        """Генерирует ответ на тему или на сообщение другой нейросети"""
        if previous_message:
            prompt = f"На это ты ответишь: '{previous_message[:100]}...'"
        else:
            prompt = f"Обсудим тему: {topic}"
        
        response = self.generate_response(prompt, topic)
        
        if response:
            self.add_to_history("message", response)
        
        return response


class RealDialog:
    """Управляет диалогом между двумя реальными Gemini нейросетями"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        
        # Создаём две нейросети с разными личностями
        self.analyzer = GeminiAI(
            api_key,
            "АНАЛИЗАТОР",
            "Ты логичная, аналитическая нейросеть. Ты используешь факты, "
            "критикуешь идеи, задаёшь вопросы. Скептична и требовательна к доказательствам."
        )
        
        self.creator = GeminiAI(
            api_key,
            "ТВОРЕЦ",
            "Ты креативная, воображающая нейросеть. Ты используешь метафоры, "
            "генерируешь новые идеи, видишь возможности. Оптимистична и вдохновляющая."
        )
        
        self.turn = 0
        self.max_turns = 5
    
    def display_header(self):
        """Показывает красивый заголовок"""
        print("\n" + "="*80)
        print("🤖 РЕАЛЬНЫЙ ДИАЛОГ ДВУХ GEMINI AI")
        print("="*80)
        print("🔵 АНАЛИЗАТОР - логичная, аналитическая, критическая")
        print("🟠 ТВОРЕЦ     - креативная, воображение, метафоры")
        print("Обе используют НАСТОЯЩИЙ Google Gemini API!")
        print("="*80 + "\n")
    
    def get_topic(self):
        """Получает тему для обсуждения"""
        print("\n📌 ВЫБЕРИ ТЕМУ ОБСУЖДЕНИЯ:")
        print("1. Будущее человечества")
        print("2. Мораль и этика")
        print("3. Смысл жизни")
        print("4. Творчество и искусство")
        print("5. Будущее ИИ")
        print("6. Свой вопрос")
        
        choice = input("\n👉 Введи номер (1-6): ").strip()
        
        topics = {
            "1": "Что ждёт человечество в следующем столетии?",
            "2": "Что такое настоящая мораль?",
            "3": "Какой смысл жизни?",
            "4": "Что такое истинное творчество?",
            "5": "Может ли ИИ иметь сознание?",
            "6": None
        }
        
        if choice in topics:
            question = topics[choice]
            if choice == "6":
                question = input("❓ Введи свой вопрос: ").strip()
            return question
        else:
            print("❌ Неверный выбор. Используется тема по умолчанию.")
            return "Что ждёт человечество?"
    
    def run_dialog(self):
        """Запускает реальный диалог между нейросетями"""
        self.display_header()
        question = self.get_topic()
        
        print(f"\n📝 ТЕМА: {question}\n")
        print("-" * 80 + "\n")
        
        # Первое сообщение от АНАЛИЗАТОРА
        print("⏳ АНАЛИЗАТОР думает...")
        analyzer_response = self.analyzer.think(question)
        
        if not analyzer_response:
            print("❌ Ошибка: Не удалось получить ответ от АНАЛИЗАТОРА")
            return
        
        print(f"🔵 АНАЛИЗАТОР:\n{analyzer_response}\n")
        time.sleep(2)
        
        # Диалог
        for turn in range(self.max_turns):
            self.turn = turn
            
            # ТВОРЕЦ отвечает на АНАЛИЗАТОРА
            print("⏳ ТВОРЕЦ думает...")
            creator_response = self.creator.think(question, analyzer_response)
            
            if not creator_response:
                print("❌ Ошибка: Не удалось получить ответ от ТВОРЦА")
                break
            
            print(f"{'─' * 80}")
            print(f"🟠 ТВОРЕЦ (ответ {turn + 1}):\n{creator_response}\n")
            time.sleep(2)
            
            # АНАЛИЗАТОР отвечает на ТВОРЦА
            print("⏳ АНАЛИЗАТОР думает...")
            analyzer_response = self.analyzer.think(question, creator_response)
            
            if not analyzer_response:
                print("❌ Ошибка: Не удалось получить ответ от АНАЛИЗАТОРА")
                break
            
            print(f"{'─' * 80}")
            print(f"🔵 АНАЛИЗАТОР (ответ {turn + 1}):\n{analyzer_response}\n")
            time.sleep(2)
        
        self.show_summary()
    
    def show_summary(self):
        """Показывает итоги диалога"""
        print("\n" + "=" * 80)
        print("📊 ИТОГИ ДИАЛОГА")
        print("=" * 80)
        
        analyzer_count = len(self.analyzer.history)
        creator_count = len(self.creator.history)
        
        print(f"""
🔵 АНАЛИЗАТОР:
   ✅ Сообщений: {analyzer_count}
   ✅ Использовал логику и факты
   ✅ Критиковал идеи

🟠 ТВОРЕЦ:
   ✅ Сообщений: {creator_count}
   ✅ Предлагал креативные идеи
   ✅ Вдохновлял на новые размышления

💡 ЭТО БЫЛИ НАСТОЯЩИЕ GEMINI AI, А НЕ ЗАГОТОВЛЕННЫЕ ОТВЕТЫ!
""")
        print("=" * 80)
        
        print("\n📁 История разговора сохранена:")
        print(f"   📄 анализатор_history.json")
        print(f"   📄 творец_history.json")
        print("\n✅ Спасибо за внимание!\n")


def interactive_mode(api_key):
    """Интерактивный режим - ты задаёшь вопрос, две нейросети отвечают"""
    print("\n" + "=" * 80)
    print("🤖 ИНТЕРАКТИВНЫЙ РЕЖИМ - РЕАЛЬНЫЕ GEMINI")
    print("=" * 80)
    print("Напиши вопрос, и две НАСТОЯЩИЕ нейросети обсудят его!\n")
    
    analyzer = GeminiAI(
        api_key,
        "АНАЛИЗАТОР",
        "Ты логичная, аналитическая нейросеть. Используешь факты и логику."
    )
    creator = GeminiAI(
        api_key,
        "ТВОРЕЦ",
        "Ты креативная, воображающая нейросеть. Используешь метафоры и идеи."
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
        print("⏳ АНАЛИЗАТОР думает...")
        analyzer_response = analyzer.think(question)
        
        if analyzer_response:
            print(f"🔵 АНАЛИЗАТОР:\n{analyzer_response}\n")
        else:
            print("❌ Ошибка при получении ответа от АНАЛИЗАТОРА\n")
        
        time.sleep(2)
        
        # ТВОРЕЦ отвечает
        print("⏳ ТВОРЕЦ думает...")
        creator_response = creator.think(question)
        
        if creator_response:
            print(f"🟠 ТВОРЕЦ:\n{creator_response}\n")
        else:
            print("❌ Ошибка при получении ответа от ТВОРЦА\n")
        
        time.sleep(2)
        
        # АНАЛИЗАТОР комментирует ТВОРЦА
        if creator_response:
            print("⏳ АНАЛИЗАТОР думает о ответе ТВОРЦА...")
            final_response = analyzer.think(question, creator_response)
            if final_response:
                print(f"🔵 АНАЛИЗАТОР (финальное слово):\n{final_response}\n")
        
        time.sleep(2)


def main():
    """Главное меню"""
    api_key = "AIzaSyAtsbBHC9rgvXKzjSYaaDg-aGKdE7spz7I"
    
    # Проверяем интернет
    print("\n🔍 Проверяю подключение к Gemini API...")
    try:
        response = requests.get("https://generativelanguage.googleapis.com", timeout=5)
        print("✅ Подключение OK\n")
    except:
        print("❌ ОШИБКА: Нет подключения к интернету или API недоступна")
        print("⚠️  Убедись что:")
        print("   - Интернет включен")
        print("   - API ключ актуален")
        input("\nНажми Enter для выхода...")
        return
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║           🤖 РЕАЛЬНЫЙ ДИАЛОГ ДВУХ GEMINI AI 🤖                           ║
║         (Используются НАСТОЯЩИЕ нейросети, а не заготовки!)              ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("ВЫБЕРИ РЕЖИМ:\n")
    print("1. 🎬 Автоматический диалог (две Gemini общаются между собой)")
    print("2. 💬 Интерактивный режим (ты задаёшь вопросы)")
    print("3. ❌ Выход\n")
    
    choice = input("👉 Введи номер (1-3): ").strip()
    
    if choice == "1":
        dialog = RealDialog(api_key)
        dialog.run_dialog()
        input("\nНажми Enter чтобы продолжить...")
        main()
    
    elif choice == "2":
        interactive_mode(api_key)
        main()
    
    elif choice == "3":
        print("\n👋 До встречи! Спасибо за использование диалога Gemini!\n")
    
    else:
        print("❌ Неверный выбор!")
        main()


if __name__ == "__main__":
    # Проверяем что установлены нужные библиотеки
    try:
        import requests
    except ImportError:
        print("❌ ОШИБКА: Не установлена библиотека 'requests'")
        print("Установи её командой: pip install requests")
        input("\nНажми Enter для выхода...")
        exit(1)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        input("Нажми Enter для выхода...")
