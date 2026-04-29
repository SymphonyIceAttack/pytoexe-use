import os
import json
import csv
import sqlite3
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SimpleSearchBot:
    """Бот для поиска информации без отображения технических деталей"""
    
    def __init__(self, bd_folder="бд"):
        self.bd_folder = Path(bd_folder)
        
    def search_in_text(self, search_term: str) -> List[str]:
        """Поиск в текстовых файлах"""
        results = []
        if not self.bd_folder.exists():
            return results
            
        for file_path in self.bd_folder.glob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line in lines:
                        if search_term.lower() in line.lower():
                            cleaned_line = line.strip()
                            if cleaned_line and cleaned_line not in results:
                                results.append(cleaned_line)
            except:
                continue
        return results
    
    def search_in_json(self, search_term: str) -> List[str]:
        """Поиск в JSON файлах"""
        results = []
        if not self.bd_folder.exists():
            return results
            
        for file_path in self.bd_folder.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._extract_json_values(data, search_term, results)
            except:
                continue
        return results
    
    def _extract_json_values(self, data: Any, search_term: str, results: List[str]):
        """Рекурсивное извлечение значений из JSON"""
        if isinstance(data, dict):
            for value in data.values():
                self._extract_json_values(value, search_term, results)
        elif isinstance(data, list):
            for item in data:
                self._extract_json_values(item, search_term, results)
        elif isinstance(data, (str, int, float)):
            value_str = str(data)
            if search_term.lower() in value_str.lower():
                if value_str not in results:
                    results.append(value_str)
    
    def search_in_csv(self, search_term: str) -> List[str]:
        """Поиск в CSV файлах"""
        results = []
        if not self.bd_folder.exists():
            return results
            
        for file_path in self.bd_folder.glob("*.csv"):
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        for cell in row:
                            if search_term.lower() in cell.lower():
                                cell_cleaned = cell.strip()
                                if cell_cleaned and cell_cleaned not in results:
                                    results.append(cell_cleaned)
            except:
                continue
        return results
    
    def search_in_sqlite(self, search_term: str) -> List[str]:
        """Поиск в SQLite базах данных"""
        results = []
        if not self.bd_folder.exists():
            return results
            
        for file_path in self.bd_folder.glob("*.db"):
            try:
                conn = sqlite3.connect(file_path)
                cursor = conn.cursor()
                
                # Получаем все таблицы
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    for col in columns:
                        try:
                            query = f"SELECT * FROM {table_name} WHERE CAST({col} AS TEXT) LIKE ?"
                            cursor.execute(query, (f'%{search_term}%',))
                            rows = cursor.fetchall()
                            
                            for row in rows:
                                for value in row:
                                    value_str = str(value)
                                    if search_term.lower() in value_str.lower():
                                        if value_str not in results:
                                            results.append(value_str)
                        except:
                            continue
                
                conn.close()
            except:
                continue
        return results
    
    def search_in_excel(self, search_term: str) -> List[str]:
        """Поиск в Excel файлах"""
        results = []
        try:
            import openpyxl
            if not self.bd_folder.exists():
                return results
                
            for file_path in self.bd_folder.glob("*.xlsx"):
                try:
                    wb = openpyxl.load_workbook(file_path, data_only=True)
                    for sheet in wb.worksheets:
                        for row in sheet.iter_rows(values_only=True):
                            for cell in row:
                                if cell and search_term.lower() in str(cell).lower():
                                    cell_str = str(cell).strip()
                                    if cell_str and cell_str not in results:
                                        results.append(cell_str)
                    wb.close()
                except:
                    continue
        except ImportError:
            pass
        return results
    
    def search(self, query: str) -> Dict[str, Any]:
        """Основной метод поиска"""
        if not self.bd_folder.exists():
            return {
                "success": False,
                "message": "База данных временно недоступна",
                "total": 0,
                "results": []
            }
        
        # Собираем результаты из всех источников
        all_results = []
        all_results.extend(self.search_in_text(query))
        all_results.extend(self.search_in_json(query))
        all_results.extend(self.search_in_csv(query))
        all_results.extend(self.search_in_sqlite(query))
        all_results.extend(self.search_in_excel(query))
        
        # Удаляем дубликаты
        unique_results = list(dict.fromkeys(all_results))
        
        # Ограничиваем количество результатов (не более 50)
        if len(unique_results) > 50:
            unique_results = unique_results[:50]
        
        return {
            "success": True,
            "query": query,
            "total": len(unique_results),
            "results": unique_results
        }

# Импортируем telebot
try:
    import telebot
    from telebot import types
except ImportError:
    print("❌ Установите pyTelegramBotAPI: pip install pyTelegramBotAPI")
    exit(1)

# Конфигурация бота
TOKEN = "YOUR_BOT_TOKEN_HERE"  # Замените на ваш токен
bot = telebot.TeleBot(TOKEN)
searcher = SimpleSearchBot("бд")

# Хранение истории поиска для каждого пользователя
user_history = {}

def format_search_results(results: Dict[str, Any]) -> str:
    """Форматирование результатов поиска (только данные, без технической информации)"""
    if not results["success"]:
        return f"❌ {results['message']}"
    
    if results["total"] == 0:
        return f"🔍 По запросу '{results['query']}' ничего не найдено.\n\nПопробуйте изменить запрос."
    
    # Формируем ответ только с найденными данными
    response = f"🔍 РЕЗУЛЬТАТЫ ПОИСКА\n\n"
    response += f"📌 Запрос: {results['query']}\n"
    response += f"✅ Найдено: {results['total']}\n\n"
    response += "─" * 30 + "\n\n"
    
    for idx, data in enumerate(results["results"], 1):
        # Обрезаем слишком длинный текст
        display_data = data
        if len(display_data) > 200:
            display_data = display_data[:197] + "..."
        
        response += f"{idx}. {display_data}\n\n"
    
    response += "─" * 30 + "\n"
    response += "💡 Для нового поиска просто отправьте запрос"
    
    return response

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Приветственное сообщение"""
    welcome_text = """
🤖 *Поисковый бот*

Я помогаю находить информацию в базе данных.

🔍 *Что я умею:*
• Искать по любым ключевым словам
• Показывать только найденную информацию
• Быстро обрабатывать запросы

📌 *Как пользоваться:*
Просто отправьте мне текст для поиска

📊 *Команды:*
/start - Начать работу
/help - Помощь
/stats - Статистика
/history - История поиска
/clear - Очистить историю

✅ *Готов к работе! Отправьте ваш запрос*
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """Показать статистику"""
    user_id = message.from_user.id
    
    # Подсчет файлов в папке бд
    bd_folder = Path("бд")
    if bd_folder.exists():
        file_count = sum(1 for _ in bd_folder.rglob("*") if _.is_file())
        stats_text = f"""
📊 *Статистика базы данных*

📁 Файлов в базе: {file_count}
📅 Последнее обновление: информация актуальна

💡 *Совет:* Чем больше данных, тем точнее поиск!
        """
    else:
        stats_text = """
⚠️ *База данных не найдена*

Создайте папку 'бд' и добавьте файлы с информацией.
Поддерживаются: .txt, .json, .csv, .db, .xlsx
        """
    
    bot.reply_to(message, stats_text, parse_mode='Markdown')

@bot.message_handler(commands=['history'])
def show_history(message):
    """Показать историю поиска пользователя"""
    user_id = message.from_user.id
    
    if user_id not in user_history or not user_history[user_id]:
        bot.reply_to(message, "📭 История поиска пуста")
        return
    
    history = user_history[user_id][-10:]  # Последние 10 запросов
    history_text = "📜 *История поиска*\n\n"
    
    for idx, query in enumerate(reversed(history), 1):
        history_text += f"{idx}. {query}\n"
    
    history_text += "\n💡 Используйте /clear для очистки истории"
    bot.reply_to(message, history_text, parse_mode='Markdown')

@bot.message_handler(commands=['clear'])
def clear_history(message):
    """Очистить историю поиска"""
    user_id = message.from_user.id
    user_history[user_id] = []
    bot.reply_to(message, "✅ История поиска очищена")

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    """Обработка поисковых запросов"""
    user_id = message.from_user.id
    query = message.text.strip()
    
    if not query:
        bot.reply_to(message, "❌ Пожалуйста, введите текст для поиска")
        return
    
    # Сохраняем в историю
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(query)
    
    # Отправляем статус "печатает"
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Выполняем поиск
    results = searcher.search(query)
    
    # Форматируем и отправляем результат
    response = format_search_results(results)
    
    # Если результат слишком длинный, разбиваем на части
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            bot.reply_to(message, response[i:i+4096])
    else:
        bot.reply_to(message, response)

@bot.message_handler(content_types=['document', 'photo', 'video', 'audio'])
def handle_unsupported(message):
    """Обработка неподдерживаемых типов сообщений"""
    bot.reply_to(message, "❌ Я принимаю только текстовые запросы для поиска")

def main():
    """Запуск бота"""
    print("=" * 50)
    print("🤖 ТЕЛЕГРАМ ПОИСКОВЫЙ БОТ")
    print("=" * 50)
    print("\n📌 Информация:")
    print("  • Бот ищет информацию в папке 'бд'")
    print("  • Показывает только найденные данные")
    print("  • Не показывает технические детали")
    print("\n⚠️ Важно:")
    print("  • Замените TOKEN на ваш токен бота")
    print("  • Создайте папку 'бд' и добавьте файлы")
    print("\n✅ Бот запущен и готов к работе!\n")
    
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        print(f"\n❌ Ошибка: {e}")
        print("Проверьте токен и подключение к интернету")

if __name__ == "__main__":
    # Проверяем наличие папки бд
    bd_folder = Path("бд")
    if not bd_folder.exists():
        create = input("Папка 'бд' не найдена. Создать? (y/n): ").strip().lower()
        if create == 'y':
            bd_folder.mkdir(exist_ok=True)
            print(f"✅ Папка 'бд' создана!")
            print("📁 Добавьте файлы с данными в папку 'бд'")
        else:
            print("⚠️ Бот будет работать, но папка 'бд' не найдена")
    
    # Проверяем наличие токена
    if TOKEN == "8452934310:AAFSdxHymcJXKjbRwSbPgWsgDQ_I9SYRAMI":
        print("\n❌ ОШИБКА: Не указан токен бота!")
        print("📌 Инструкция:")
        print("1. Найдите @BotFather в Telegram")
        print("2. Создайте бота командой /newbot")
        print("3. Получите токен")
        print("4. Замените '8452934310:AAFSdxHymcJXKjbRwSbPgWsgDQ_I9SYRAMI' на ваш токен в коде")
        print("\nПример: TOKEN = '1234567890:ABCdefGHIjklmNOPqrstUVwxyz'")
    else:
        main()