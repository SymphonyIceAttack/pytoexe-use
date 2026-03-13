"""
Арина AI - Финальная версия для EXE
"""

import os
import sys
import json
import getpass
from datetime import datetime
from google import genai
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Важно для EXE!
import matplotlib.pyplot as plt

class ArinaAI:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model = 'models/gemini-2.5-flash'
        self.user_name = "Арина"
        self.reminders = []
        self.notes = []
        self.data_file = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__), 'arina_data.json')
        self.load_data()
        print(f"\n✅ Помощник создан для {self.user_name}")

    def ask(self, question):
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"[Для {self.user_name}] {question}"
            )
            return response.text
        except Exception as e:
            return f"Ошибка: {e}"

    def add_reminder(self, text, time):
        self.reminders.append({'text': text, 'time': time, 'created': datetime.now().strftime("%Y-%m-%d %H:%M")})
        self.save_data()
        return f"✅ Напоминание: {text} на {time}"

    def get_reminders(self):
        if not self.reminders:
            return "📭 Нет напоминаний"
        result = "📋 ВАШИ НАПОМИНАНИЯ:\n"
        for i, r in enumerate(self.reminders, 1):
            result += f"{i}. {r['text']} - {r['time']}\n"
        return result

    def add_note(self, title, content):
        self.notes.append({'title': title, 'content': content, 'date': datetime.now().strftime("%Y-%m-%d")})
        self.save_data()
        return f"📝 Заметка '{title}' сохранена"

    def search_notes(self, keyword):
        found = [n for n in self.notes if keyword.lower() in n['title'].lower()]
        if not found:
            return f"🔍 Ничего не найдено по '{keyword}'"
        result = f"🔍 Результаты поиска '{keyword}':\n"
        for n in found:
            result += f"📌 {n['title']} ({n['date']})\n"
        return result

    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({'reminders': self.reminders, 'notes': self.notes}, f, ensure_ascii=False)
        except:
            pass

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.reminders = data.get('reminders', [])
                    self.notes = data.get('notes', [])
        except:
            pass

def plot_graph():
    print("\n" + "="*50)
    print("📈 ПОСТРОЕНИЕ ГРАФИКА")
    print("="*50)
    print("Примеры: x**2, sin(x), cos(x), x**3")

    func = input("\nВведите функцию f(x) = ")
    try:
        x_min = float(input("Начало x: "))
        x_max = float(input("Конец x: "))
        x = np.linspace(x_min, x_max, 500)

        safe_func = func.replace('sin', 'np.sin').replace('cos', 'np.cos')
        safe_func = safe_func.replace('tan', 'np.tan').replace('exp', 'np.exp')
        safe_func = safe_func.replace('sqrt', 'np.sqrt')

        y = eval(safe_func)

        plt.figure(figsize=(10, 6))
        plt.plot(x, y, 'b-', linewidth=2)
        plt.grid(True, alpha=0.3)
        plt.xlabel('x')
        plt.ylabel('f(x)')
        plt.title(f'f(x) = {func}')
        plt.show()

    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    # Настройка кодировки для Windows
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

    print("="*60)
    print("           🤖 АРИНА - AI ПОМОЩНИК")
    print("="*60)

    # Получаем API ключ
    print("\n🔑 Введите ваш API ключ от Google AI Studio")
    api_key = getpass.getpass("Ключ: ")

    if not api_key:
        print("❌ Ключ не может быть пустым!")
        input("\nНажмите Enter для выхода...")
        return

    # Создаем помощника
    try:
        ai = ArinaAI(api_key)
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        input("\nНажмите Enter для выхода...")
        return

    # Главное меню
    while True:
        print("\n" + "="*60)
        print(f"           📋 ГЛАВНОЕ МЕНЮ")
        print("="*60)
        print("1. 💬 Задать вопрос")
        print("2. ⏰ Напоминания")
        print("3. 📚 Заметки")
        print("4. 📈 Построить график")
        print("5. 💾 Сохранить данные")
        print("6. ❌ Выход")
        print("-"*60)

        choice = input("Ваш выбор (1-6): ").strip()

        if choice == '1':
            question = input("\n❓ Ваш вопрос: ")
            print("\n🤔 Думаю...")
            answer = ai.ask(question)
            print(f"\n💬 {answer}")

        elif choice == '2':
            print("\n" + ai.get_reminders())
            add = input("\n➕ Добавить напоминание? (д/н): ").lower()
            if add == 'д':
                text = input("Что нужно сделать? ")
                time = input("Когда? ")
                print(ai.add_reminder(text, time))

        elif choice == '3':
            print("\n1. Добавить заметку")
            print("2. Поиск по заметкам")
            sub = input("Выберите (1-2): ")

            if sub == '1':
                title = input("Заголовок: ")
                content = input("Содержание: ")
                print(ai.add_note(title, content))
            elif sub == '2':
                keyword = input("Что ищем? ")
                print(ai.search_notes(keyword))

        elif choice == '4':
            plot_graph()

        elif choice == '5':
            ai.save_data()
            print("✅ Данные сохранены!")

        elif choice == '6':
            ai.save_data()
            print("\n👋 До свидания, Арина!")
            print("💾 Данные сохранены")
            input("\nНажмите Enter для выхода...")
            break

        else:
            print("❌ Неверный выбор, попробуйте снова")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа завершена")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        input("Нажмите Enter...")
