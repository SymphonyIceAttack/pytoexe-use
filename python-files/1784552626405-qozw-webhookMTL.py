from flask import Flask, request, jsonify
import sqlite3
import json
import os
import requests
from datetime import datetime

app = Flask(__name__)

# Токен бота из MAX (замените на свой)
BOT_TOKEN = "f9LHodD0cOIci6ci3Z5QxB944HJQRvMn0mFDIvpJ_IQ707p8xkq-JXUItCzsjcFZ98guSGDXDbJ0Hdp-WBo1"
WEBHOOK_URL = "https://zvpm.cloudpub.ru/max-webhook"

# Инициализация БД
def init_db():
    conn = sqlite3.connect('max_usersMTL.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        chat_id TEXT PRIMARY KEY,
        user_id TEXT,
        name TEXT,
        first_message_date TEXT,
        last_message_date TEXT
    )''')
    conn.commit()
    conn.close()

# Сохранить пользователя
def save_user(chat_id, user_id, name="Unknown"):
    conn = sqlite3.connect('max_usersMTL.db')
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    # Проверяем, новый ли
    c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not c.fetchone():
        print(f"🆕 Новый пользователь: {chat_id} ({name})")
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                 (chat_id, user_id, name, now, now))
    else:
        print(f"👋 Известный пользователь: {name}")
        c.execute("UPDATE users SET last_message_date=? WHERE user_id=?",
                 (now, user_id))
    
    conn.commit()
    conn.close()

 # Отправить сообщение пользователя
def post_users_message(chat_id, user_id, name="Unknown"):
    
    url = "https://platform-api2.max.ru/messages?chat_id=-74084524712573"
    headers = {
        "Authorization": f"f9LHodD0cOIci6ci3Z5QxB944HJQRvMn0mFDIvpJ_IQ707p8xkq-JXUItCzsjcFZ98guSGDXDbJ0Hdp-WBo1",
        "Content-Type": "application/json"
    }
    text = f"chat_id:{chat_id}&user_id:{user_id}&name:{name}"
    data = {"text" : text}
        
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        print(f"📨 Сообщение отправлено в канал")
    else:
        print(f"❌ Ошибка отправки сообщения в канал - {response.status_code}") 
        
# Главный webhook
@app.route('/max-webhook', methods=['POST'])
def webhook():
    try:
        # Получаем данные от MAX
        data = request.get_json()
        print("📨 Получено сообщение:", json.dumps(data, ensure_ascii=False, indent=2))

        # Извлекаем ID и name пользователя (для MAX API)
        
        if data.get('update_type') == "message_created":
            user_name = data.get('message', {}).get('body', {}).get('text', 'Unknown')
        else:
            return jsonify({"status": "ok"}), 200
              
        #user_name = data.get('user', {}).get('last_name', 'Unknown') + " " + data.get('user', {}).get('first_name', 'Unknown')

        user_id = data.get('message', {}).get('sender', {}).get('user_id')
        chat_id = data.get('message', {}).get('recipient', {}).get('chat_id')
        
        if chat_id:
            save_user(chat_id, user_id, user_name)
        if chat_id:
            post_users_message(chat_id, user_id, user_name)
        
        # Отвечаем MAX "OK"
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

# Установка webhook (запустить один раз)
@app.route('/set-webhook', methods=['GET', 'POST'])
def set_webhook():
    if request.method == 'GET':
        # Просто показываем кнопку для браузера
        return '''
        <h1>Установка webhook для MAX</h1>
        <form method="POST">
            <button type="submit">Установить webhook</button>
        </form>
        '''
    
    # POST-запрос (кнопка нажата)
    import requests
    
    url = "https://platform-api2.max.ru/subscriptions"
    headers = {
        "Authorization": f"f9LHodD0cOIci6ci3Z5QxB944HJQRvMn0mFDIvpJ_IQ707p8xkq-JXUItCzsjcFZ98guSGDXDbJ0Hdp-WBo1",
        "Content-Type": "application/json"
    }
    webhook_data = {"url": WEBHOOK_URL}
    
    response = requests.post(url, headers=headers, json=webhook_data)
    
    if response.status_code == 200:
        return f'<h1>✅ Webhook установлен!</h1><p>{response.text}</p>'
    else:
        return f'<h1>❌ Ошибка:</h1><p>{response.status_code}: {response.text}</p>'


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5001)
