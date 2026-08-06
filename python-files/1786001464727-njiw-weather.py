import sys
import requests

# ⚠️ Замените на свой ключ
API_KEY = "871b34e465601b121b275ad188a2005a"

# Города и их названия для запроса (можно использовать «город,страна»)
cities = [
    {"name": "Москва",           "query": "Moscow,ru"},
    {"name": "Санкт-Петербург",  "query": "Saint Petersburg,ru"},
    {"name": "Новосибирск",      "query": "Novosibirsk,ru"},
    {"name": "Екатеринбург",     "query": "Yekaterinburg,ru"},
    {"name": "Казань",           "query": "Kazan,ru"}
]

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_weather(city_query):
    """Запрашивает погоду через API OpenWeatherMap и возвращает словарь с данными."""
    params = {
        "q": city_query,
        "appid": API_KEY,
        "units": "metric",   # температура в Цельсиях
        "lang": "ru"         # описание на русском
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return {"temperature": f"{temp:.1f}°C", "description": desc}
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети или API: {e}")
        return None
    except KeyError:
        print("Ответ API не содержит ожидаемых полей. Проверьте ключ или лимит запросов.")
        return None

def main():
    # Корректный вывод кириллицы в консоли Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    print("=== Погода (OpenWeatherMap) ===\n")
    print("Города:")
    for i, city in enumerate(cities, 1):
        print(f"{i}. {city['name']}")
    print("0. Выход")

    try:
        choice = int(input("Выберите номер города: "))
    except ValueError:
        print("Некорректный ввод.")
        return

    if choice == 0:
        return
    if choice < 1 or choice > len(cities):
        print("Неверный номер города.")
        return

    city = cities[choice - 1]
    print(f"\nЗагрузка погоды для {city['name']}...")
    weather = get_weather(city["query"])

    if weather:
        print(f"Погода в {city['name']}:")
        print(f"  Температура: {weather['temperature']}")
        print(f"  Описание:    {weather['description']}")
    else:
        print("Не удалось получить данные о погоде.")

    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()