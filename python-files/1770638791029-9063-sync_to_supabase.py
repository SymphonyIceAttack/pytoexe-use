# sync_to_supabase.py
import os
import time
import json
import requests
from datetime import datetime

# ╔════════════════════════════════════╗
# ║        НАСТРОЙКИ (ОБЯЗАТЕЛЬНО!)     ║
# ╚════════════════════════════════════╝

# 🔧 Замените на ваш Supabase Project URL и anon API Key
SUPABASE_URL = "https://lazdtokrqaymrrgtpmje.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxhemR0b2tycWF5bXJyZ3RwbWplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2MzI0ODUsImV4cCI6MjA4NjIwODQ4NX0.Sy9NJAPoXjQy0nMbZFHYYmzsNwz5f0BYVO456JZ6xNE"  # ← Public/anon key

# 📁 Путь к config.json (должен быть рядом с .exe)
CONFIG_PATH = "config.json"

# ⏱ Как часто проверять обновления (в секундах)
CHECK_INTERVAL = 5

# 🧱 Название таблицы в Supabase
TABLE_NAME = "leaderboard"

# 🧍 Имя игрока (можно задать здесь или брать из config.json)
PLAYER_NAME = "Player"  # Если хотите, можно добавить в config.json


# ╔════════════════════════════════════╗
# ║           ФУНКЦИИ                  ║
# ╚════════════════════════════════════╝

def read_config():
    """Читает config.json"""
    if not os.path.exists(CONFIG_PATH):
        print(f"[❌] Файл {CONFIG_PATH} не найден!")
        return None

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[❌] Ошибка чтения config.json: {e}")
        return None


def send_to_supabase(data):
    """Отправляет/обновляет запись в Supabase"""
    endpoint = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # Поиск по имени
    params = {"name": "eq." + data["name"]}

    try:
        # Попробуем обновить существующую запись
        response = requests.patch(endpoint, headers=headers, params=params, json=data)

        if response.status_code in [204, 200]:
            print(f"[✅] Обновлено: {data['name']} → {data['score']} кликов")
            return True

        # Если ничего не обновилось — значит, записи нет → вставляем новую
        if response.status_code == 404 or response.status_code == 406:
            response = requests.post(endpoint, headers=headers, json=data)

            if response.status_code == 201:
                print(f"[🆕] Добавлено: {data['name']} → {data['score']}")
                return True
            else:
                print(f"[❌] Ошибка вставки: {response.status_code} | {response.text}")
                return False

        else:
            print(f"[❌] Ошибка обновления: {response.status_code} | {response.text}")
            return False

    except Exception as e:
        print(f"[🔴] Ошибка подключения: {e}")
        return False


# ╔════════════════════════════════════╗
# ║            ЗАПУСК                  ║
# ╚════════════════════════════════════╝

if __name__ == "__main__":
    print(f"[🔄] Синхронизация с Supabase запущена (каждые {CHECK_INTERVAL} сек)")
    print(f"[📁] Читаю: {os.path.abspath(CONFIG_PATH)}")

    last_count = -1

    while True:
        config = read_config()
        if config is None:
            time.sleep(CHECK_INTERVAL)
            continue

        click_count = config.get("ClickCount", 0)
        achievements = config.get("Achievements", [])

        # Если счёт не изменился — пропускаем
        if click_count == last_count:
            time.sleep(CHECK_INTERVAL)
            continue

        # Имя игрока: из config или из скрипта
        name = config.get("PlayerName", PLAYER_NAME).strip()
        if not name:
            name = "Anonymous"

        # Подготовка данных
        data = {
            "name": name,
            "score": click_count,
            "achievements": achievements,  # Можно хранить как JSON
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

        # Отправляем
        send_to_supabase(data)
        last_count = click_count

        time.sleep(CHECK_INTERVAL)
