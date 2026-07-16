import json
import requests
import websocket

DEBUG_PORT = 9222

def get_websocket_url():
    """Получает актуальный WebSocket URL отладки."""
    try:
        response = requests.get(f'http://localhost:{DEBUG_PORT}/json/list', timeout=3)
        data = response.json()
        if not data:
            raise Exception("Нет активных вкладок. Откройте любую страницу в браузере.")
        ws_url = data[0].get('webSocketDebuggerUrl')
        if not ws_url:
            raise Exception("Поле webSocketDebuggerUrl отсутствует в ответе.")
        return ws_url
    except requests.exceptions.ConnectionError:
        raise Exception(f"Не удалось подключиться к порту {DEBUG_PORT}. Убедитесь, что браузер запущен с флагом --remote-debugging-port={DEBUG_PORT}.")
    except Exception as e:
        raise Exception(f"Ошибка получения WebSocket URL: {e}")

def get_cookies(ws_url):
    """Подключается к WebSocket и запрашивает все cookie."""
    ws = websocket.create_connection(ws_url)
    
    # Пробуем современный метод Storage.getCookies
    cmd = json.dumps({"id": 1, "method": "Storage.getCookies"})
    ws.send(cmd)
    result = ws.recv()
    ws.close()
    
    response = json.loads(result)
    if "result" in response and "cookies" in response["result"]:
        return response["result"]["cookies"]
    
    # Если не сработал, пробуем старый метод Network.getAllCookies
    ws = websocket.create_connection(ws_url)
    cmd = json.dumps({"id": 2, "method": "Network.getAllCookies"})
    ws.send(cmd)
    result = ws.recv()
    ws.close()
    
    response = json.loads(result)
    return response.get("result", {}).get("cookies", [])

if __name__ == "__main__":
    try:
        print("[*] Получаем актуальный WebSocket URL...")
        ws_url = get_websocket_url()
        print(f"[*] Подключаемся к {ws_url}")
        
        cookies = get_cookies(ws_url)
        if cookies:
            with open("cookies.json", "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=4, ensure_ascii=False)
            print(f"[+] Успешно! Извлечено {len(cookies)} cookie. Сохранено в cookies.json")
        else:
            print("[-] Cookie не получены. Возможно, браузер не авторизован или нет открытых страниц.")
    except Exception as e:
        print(f"[-] Ошибка: {e}")