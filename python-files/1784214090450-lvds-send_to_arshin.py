import sys
import json
import requests

def send_data(json_path):
    # URL стенда АРШИН (для теста используется подсистема поверки)
    # Замените на промышленный URL при готовности
    API_URL = "https://gost.ru"
    
    # Токен доступа (получается в личном кабинете организации)
    TOKEN = "ВАШ_ЛИЧНЫЙ_ТОКЕН_ДОСТУПА"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Чтение данных от Excel
        with open(json_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        
        # Отправка пакета в АРШИН
        response = requests.post(API_URL, json=payload, headers=headers)
        
        if response.status_code == 201:
            print("SUCCESS: Пакет успешно отправлен и принят в обработку.")
            sys.exit(0)
        else:
            print(f"ERROR: Код {response.status_code}. Ответ: {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: Не указан путь к файлу данных.")
        sys.argv.exit(3)
    send_data(sys.argv[1])
