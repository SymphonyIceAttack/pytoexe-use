#!/usr/bin/env python3
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("✨ Запуск Cryptix...")
print(f"Путь к модулям: {sys.path[0]}")

try:
    from cryptix.app import main
    print("✅ Модуль cryptix найден")
    main()
except ImportError as e:
    print(f"❌ Ошибка: {e}")
    print("Содержимое src/cryptix:", os.listdir('src/cryptix') if os.path.exists('src/cryptix') else "папки нет")
