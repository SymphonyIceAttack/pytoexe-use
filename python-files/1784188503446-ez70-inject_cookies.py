import json
import requests
import websocket
import time

DEBUG_PORT = 9222
COOKIE_FILE = "cookies.json"

def get_websocket_url():
    """Получает актуальный WebSocket URL отладки."""
    try:
        response = requests.get(f'http://localhost:{DEBUG_PORT}/json/list', timeout=2)
        data = response.json()
        if not data:
            raise Exception("Нет активных вкладок. Откройте страницу в браузере.")
        ws_url = data[0].get('webSocketDebuggerUrl')
        if not ws_url:
            raise Exception("Поле webSocketDebuggerUrl отсутствует в ответе.")
        return ws_url
    except requests.exceptions.ConnectionError:
        raise Exception(f"Не удалось подключиться к порту {DEBUG_PORT}. Убедитесь, что браузер запущен с флагом --remote-debugging-port={DEBUG_PORT} и --remote-allow-origins=*")
    except Exception as e:
        raise Exception(f"Ошибка получения WebSocket URL: {e}")

def inject_cookies(ws_url, cookies):
    """Внедряет список кук в браузер через CDP."""
    ws = websocket.create_connection(ws_url)
    
    success_count = 0
    fail_count = 0
    
    for cookie in cookies:
        # Извлекаем параметры куки с дефолтными значениями
        params = {
            "name": cookie.get("name"),
            "value": cookie.get("value"),
            "domain": cookie.get("domain", ""),
            "path": cookie.get("path", "/"),
            "secure": cookie.get("secure", False),
            "httpOnly": cookie.get("httpOnly", False),
            "sameSite": cookie.get("sameSite", "Lax")  # возможны значения: "Strict", "Lax", "None"
        }
        # Если есть expires (в секундах с эпохи), преобразуем в число
        if "expires" in cookie and cookie["expires"]:
            params["expires"] = cookie["expires"]
        # Если есть значение expirationDate (альтернативное поле)
        elif "expirationDate" in cookie and cookie["expirationDate"]:
            params["expires"] = cookie["expirationDate"]
        
        # Отправляем команду
        command = {
            "id": 1,  # можно использовать одинаковый id, т.к. ответы приходят последовательно
            "method": "Network.setCookie",
            "params": params
        }
        ws.send(json.dumps(command))
        
        # Получаем ответ (можно не обрабатывать, но для отладки проверим)
        try:
            response = ws.recv()
            resp_data = json.loads(response)
            if "result" in resp_data and resp_data["result"].get("success", False):
                success_count += 1
                print(f"[+] Внедрена кука: {cookie['name']} для {cookie.get('domain', '')}")
            else:
                fail_count += 1
                print(f"[-] Ошибка внедрения куки: {cookie['name']} ({resp_data.get('error', {}).get('message', 'неизвестная ошибка')})")
        except Exception as e:
            fail_count += 1
            print(f"[-] Ошибка при получении ответа для {cookie['name']}: {e}")
    
    ws.close()
    return success_count, fail_count

if __name__ == "__main__":
    try:
        # 1. Читаем файл с куками
        print("[*] Чтение cookies.json...")
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        print(f"[*] Найдено {len(cookies)} кук.")
        
        # 2. Получаем WebSocket URL
        print("[*] Получаем актуальный WebSocket URL...")
        ws_url = get_websocket_url()
        print(f"[*] Подключаемся к {ws_url}")
        
        # 3. Внедряем куки
        print("[*] Начинаем внедрение...")
        success, fail = inject_cookies(ws_url, cookies)
        
        print(f"\n[+] Внедрено успешно: {success}")
        print(f"[-] Ошибок внедрения: {fail}")
        print("\n[!] Теперь обновите страницы в браузере — вы должны быть авторизованы!")
        
    except Exception as e:
        print(f"[-] Ошибка: {e}")