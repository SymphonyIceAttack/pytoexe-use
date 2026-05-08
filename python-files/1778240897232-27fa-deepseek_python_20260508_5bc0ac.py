import os
import sqlite3
import hashlib
import secrets
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, send_file, make_response
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.secret_key = 'jotos_super_secret_key_change_me_12345'

# Конфигурация загрузки файлов
UPLOAD_FOLDER = 'uploads'
SCREENSHOT_FOLDER = 'screenshots'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'zip', 'catrobat', 'sb3', 'game'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SCREENSHOT_FOLDER'] = SCREENSHOT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Инициализация базы данных ---
def init_db():
    conn = sqlite3.connect('jotos.db')
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Таблица игр
    c.execute('''CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        screenshot_path TEXT,
        game_file_path TEXT NOT NULL,
        original_filename TEXT,
        author TEXT NOT NULL,
        downloads INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author) REFERENCES users(username)
    )''')
    
    # Вставляем тестовых пользователей если их нет
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        # Пароль "1234" в хешированном виде (sha256)
        hashed = hashlib.sha256("1234".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("блабла", hashed))
        hashed2 = hashlib.sha256("qwe".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("dev", hashed2))
    
    conn.commit()
    conn.close()

init_db()

# --- HTML шаблон (пиксельный стиль) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jotos — пиксельная игровая платформа</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            image-rendering: crisp-edges;
            image-rendering: pixelated;
            font-family: 'Courier New', 'VT323', monospace;
        }
        body {
            background: #0c0e16;
            padding: 24px 20px;
            color: #ddd;
        }
        .pixel-wrapper {
            max-width: 1300px;
            margin: 0 auto;
            background: #11121c;
            border: 4px solid #3a3e64;
            box-shadow: 8px 8px 0 #050508;
            padding: 20px;
        }
        .pixel-logo-area {
            text-align: center;
            border-bottom: 3px dashed #4e5b82;
            margin-bottom: 28px;
            padding-bottom: 14px;
        }
        .jotos-logo {
            font-size: 68px;
            font-weight: bold;
            letter-spacing: 8px;
            background: linear-gradient(135deg, #ffcc77, #ff9966);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-shadow: 4px 4px 0 #5f3f1a;
            display: inline-block;
        }
        .logo-sub {
            background: #000000aa;
            padding: 4px 12px;
            font-size: 16px;
            border: 1px solid #ffaa55;
            width: fit-content;
            margin: 10px auto 0;
            color: #ffcc99;
        }
        .auth-card {
            background: #0a0a11;
            padding: 18px;
            border-left: 8px solid #f5a623;
            margin-bottom: 32px;
            display: flex;
            flex-wrap: wrap;
            gap: 24px;
        }
        .auth-box {
            background: #10111c;
            flex: 1;
            padding: 16px;
            border: 1px solid #2b2f4a;
        }
        .auth-box h3 {
            color: #ffb45e;
            border-left: 4px solid #ffaa55;
            padding-left: 10px;
            margin-bottom: 14px;
        }
        .user-panel {
            background: #191e2c;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
        }
        input, select, textarea {
            background: #010104;
            border: 2px solid #40456e;
            padding: 8px;
            width: 100%;
            color: #f0f0f0;
            margin: 8px 0;
            font-size: 15px;
        }
        .pixel-btn {
            background: #282d48;
            border: none;
            border-bottom: 4px solid #6f7bb5;
            padding: 8px 18px;
            font-weight: bold;
            color: #fff1cf;
            font-size: 17px;
            cursor: pointer;
            transition: 0.05s linear;
            margin-top: 10px;
            text-align: center;
            display: inline-block;
            text-decoration: none;
        }
        .pixel-btn:active {
            transform: translateY(2px);
            border-bottom-width: 2px;
        }
        .upload-section {
            background: #0f0f17;
            border: 3px dotted #5e6a97;
            padding: 22px;
            margin: 28px 0;
        }
        .form-group {
            margin-bottom: 18px;
        }
        .form-group label {
            display: block;
            font-weight: bold;
            margin-bottom: 6px;
            color: #e5cf97;
        }
        .games-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 26px;
            margin-top: 28px;
        }
        .game-card {
            background: #10121f;
            border: 2px solid #383e63;
        }
        .game-screenshot {
            background-color: #2a2e44;
            height: 150px;
            background-size: cover;
            background-position: center;
            border-bottom: 3px solid #f5ac4b;
            display: flex;
            align-items: flex-end;
            padding: 5px;
        }
        .game-details {
            padding: 14px;
        }
        .game-title {
            font-size: 22px;
            font-weight: bold;
            color: #ffcc77;
        }
        .game-cat {
            display: inline-block;
            background: #232842;
            padding: 3px 10px;
            font-size: 12px;
            margin: 8px 0;
            border-left: 3px solid #ffaa44;
        }
        .download-link, .delete-link {
            display: inline-block;
            background: #2f4d2f;
            padding: 7px 14px;
            margin-top: 10px;
            margin-right: 10px;
            text-decoration: none;
            color: #ffe2b5;
            font-weight: bold;
        }
        .delete-link {
            background: #572e2e;
        }
        .flash-msg {
            padding: 10px;
            margin: 10px 0;
            background: #1e3a1e;
            color: #b9ffb9;
        }
        .error-msg {
            background: #3a1e1e;
            color: #ffb0b0;
        }
        .filter-bar {
            display: flex;
            gap: 12px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        footer {
            text-align: center;
            margin-top: 40px;
            opacity: 0.7;
        }
    </style>
</head>
<body>
<div class="pixel-wrapper">
    <div class="pixel-logo-area">
        <div class="jotos-logo">JOTOS</div>
        <div class="logo-sub">▣ PIXEL GAME ARCADE ▣</div>
    </div>

    {% if not session.username %}
    <div class="auth-card">
        <div class="auth-box">
            <h3>📝 РЕГИСТРАЦИЯ (НИК УНИКАЛЕН)</h3>
            <form method="post" action="/register">
                <input type="text" name="username" placeholder="Ник: блабла" required>
                <input type="password" name="password" placeholder="Пароль: 1234" required>
                <button type="submit" class="pixel-btn">СОЗДАТЬ АККАУНТ</button>
            </form>
        </div>
        <div class="auth-box">
            <h3>🔐 ВХОД</h3>
            <form method="post" action="/login">
                <input type="text" name="username" placeholder="Ник" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <button type="submit" class="pixel-btn">ВОЙТИ</button>
            </form>
        </div>
    </div>
    {% else %}
    <div class="user-panel">
        <span>👾 Игрок: <strong>{{ session.username }}</strong> | ты можешь выкладывать игры</span>
        <a href="/logout" class="pixel-btn" style="width: auto; margin:0;">🚪 ВЫЙТИ</a>
    </div>

    <div class="upload-section">
        <h2>📀 ВЫЛОЖИТЬ НОВУЮ ИГРУ</h2>
        <form method="post" action="/upload_game" enctype="multipart/form-data">
            <div class="form-group">
                <label>🎲 НАЗВАНИЕ ИГРЫ *</label>
                <input type="text" name="title" required>
            </div>
            <div class="form-group">
                <label>📖 ОПИСАНИЕ</label>
                <textarea name="description" rows="2"></textarea>
            </div>
            <div class="form-group">
                <label>🏷️ КАТЕГОРИЯ *</label>
                <select name="category" required>
                    <option value="хоррор">👻 ХОРРОР</option>
                    <option value="платформер">🏃 ПЛАТФОРМЕР</option>
                    <option value="паркур">🧗 ПАРКУР</option>
                </select>
            </div>
            <div class="form-group">
                <label>🖼️ СКРИНШОТ (ПО ЖЕЛАНИЮ)</label>
                <input type="file" name="screenshot" accept="image/*">
            </div>
            <div class="form-group">
                <label>📦 ФАЙЛ ИГРЫ * (.catrobat, .zip, .sb3 и др.)</label>
                <input type="file" name="game_file" required>
            </div>
            <button type="submit" class="pixel-btn">🚀 ВЫЛОЖИТЬ ИГРУ</button>
        </form>
    </div>
    {% endif %}

    <div class="filter-bar">
        <a href="/?category=all" class="pixel-btn" style="width: auto;">ВСЕ</a>
        <a href="/?category=хоррор" class="pixel-btn" style="width: auto;">👻 ХОРРОР</a>
        <a href="/?category=платформер" class="pixel-btn" style="width: auto;">🏃 ПЛАТФОРМЕР</a>
        <a href="/?category=паркур" class="pixel-btn" style="width: auto;">🧗 ПАРКУР</a>
    </div>

    <h2>🎮 БИБЛИОТЕКА ИГР</h2>
    <div class="games-grid">
        {% for game in games %}
        <div class="game-card">
            <div class="game-screenshot" style="background-image: url('{{ game.screenshot_url or '/static/placeholder.png' }}');">
                {% if not game.screenshot_url %}<span style="background:#000000aa;">🎬 нет скрина</span>{% endif %}
            </div>
            <div class="game-details">
                <div class="game-title">🎮 {{ game.title }}</div>
                <div class="game-cat">
                    {% if game.category == 'хоррор' %}👻{% elif game.category == 'платформер' %}🏃{% else %}🧗{% endif %}
                    {{ game.category.upper() }}
                </div>
                <div class="game-desc">{{ game.description[:100] }}</div>
                <div style="font-size: 12px; margin: 8px 0;">✍️ {{ game.author }} | 📥 {{ game.downloads }} скач. | 📅 {{ game.created_date }}</div>
                <a href="/download/{{ game.id }}" class="download-link">⬇️ СКАЧАТЬ ФАЙЛ</a>
                {% if session.username == game.author %}
                <a href="/delete_game/{{ game.id }}" class="delete-link" onclick="return confirm('Удалить игру?')">🗑️ УДАЛИТЬ</a>
                {% endif %}
            </div>
        </div>
        {% else %}
        <div style="grid-column:1/-1; text-align:center; padding:40px;">🎲 Нет игр в этой категории. Будь первым!</div>
        {% endfor %}
    </div>
    <footer>⚡ JOTOS — загружай игры, качай файлы. Все данные хранятся в SQLite.</footer>
</div>

{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        {% for category, message in messages %}
        <div style="position:fixed; bottom:20px; right:20px; background:#1e1e2a; border-left:4px solid #ffaa55; padding:12px; max-width:300px;">
            {{ message }}
        </div>
        {% endfor %}
    {% endif %}
{% endwith %}
</body>
</html>
"""

# --- Роуты Flask ---
@app.route('/')
def index():
    category = request.args.get('category', 'all')
    conn = sqlite3.connect('jotos.db')
    c = conn.cursor()
    
    if category == 'all':
        c.execute("SELECT * FROM games ORDER BY created_at DESC")
    else:
        c.execute("SELECT * FROM games WHERE category = ? ORDER BY created_at DESC", (category,))
    
    games_raw = c.fetchall()
    games = []
    for g in games_raw:
        games.append({
            'id': g[0],
            'title': g[1],
            'description': g[2],
            'category': g[3],
            'screenshot_url': f"/screenshots/{g[4]}" if g[4] and os.path.exists(os.path.join(app.config['SCREENSHOT_FOLDER'], g[4])) else None,
            'game_file': g[5],
            'author': g[7],
            'downloads': g[8],
            'created_date': datetime.strptime(g[9], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y') if g[9] else 'недавно'
        })
    conn.close()
    return render_template_string(HTML_TEMPLATE, games=games, session=session)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    
    if not username or not password:
        return "Заполните все поля", 400
    
    conn = sqlite3.connect('jotos.db')
    c = conn.cursor()
    
    # Проверка уникальности ника
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return "❌ Ник занят! Выберите другой.", 400
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect('jotos.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['username'] = username
        return redirect(url_for('index'))
    return "Неверный ник или пароль", 400

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/upload_game', methods=['POST'])
def upload_game():
    if 'username' not in session:
        return "Не авторизован", 401
    
    title = request.form['title'].strip()
    description = request.form['description'].strip()
    category = request.form['category']
    
    if not title or not category:
        return "Название и категория обязательны", 400
    
    # Обработка скриншота
    screenshot_filename = None
    if 'screenshot' in request.files:
        screenshot = request.files['screenshot']
        if screenshot and screenshot.filename and allowed_file(screenshot.filename):
            ext = screenshot.filename.rsplit('.', 1)[1].lower()
            screenshot_filename = f"{secrets.token_hex(8)}.{ext}"
            screenshot.save(os.path.join(app.config['SCREENSHOT_FOLDER'], screenshot_filename))
    
    # Обработка файла игры
    if 'game_file' not in request.files:
        return "Файл игры обязателен", 400
    
    game_file = request.files['game_file']
    if not game_file or not game_file.filename:
        return "Файл игры обязателен", 400
    
    original_filename = secure_filename(game_file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'bin'
    game_filename = f"{secrets.token_hex(16)}.{ext}"
    game_file.save(os.path.join(app.config['UPLOAD_FOLDER'], game_filename))
    
    conn = sqlite3.connect('jotos.db')
    c = conn.cursor()
    c.execute('''INSERT INTO games (title, description, category, screenshot_path, game_file_path, original_filename, author)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (title, description, category, screenshot_filename, game_filename, original_filename, session['username']))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/download/<int:game_id>')
def download_game(game_id):
    conn = sqlite3.connect('jotos.db')
    c = conn.cursor()
    c.execute("SELECT game_file_path, original_filename, downloads FROM games WHERE id = ?", (game_id,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return "Игра не найдена", 404
    
    game_file_path, original_filename, downloads = result
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], game_file_path)
    
    if not os.path.exists(full_path):
        conn.close()
        return "Файл игры не найден на сервере", 404
    
    # Увеличиваем счётчик скачиваний
    c.execute("UPDATE games SET downloads = downloads + 1 WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()
    
    return send_file(full_path, as_attachment=True, download_name=original_filename)

@app.route('/delete_game/<int:game_id>')
def delete_game(game_id):
    if 'username' not in session:
        return "Не авторизован", 401
    
    conn = sqlite3.connect('jotos.db')
    c = conn.cursor()
    
    # Проверяем, что пользователь — автор
    c.execute("SELECT author, screenshot_path, game_file_path FROM games WHERE id = ?", (game_id,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return "Игра не найдена", 404
    
    author, screenshot_path, game_file_path = result
    
    if author != session['username']:
        conn.close()
        return "Вы не можете удалить чужую игру", 403
    
    # Удаляем файлы
    if screenshot_path:
        scr_path = os.path.join(app.config['SCREENSHOT_FOLDER'], screenshot_path)
        if os.path.exists(scr_path):
            os.remove(scr_path)
    
    game_path = os.path.join(app.config['UPLOAD_FOLDER'], game_file_path)
    if os.path.exists(game_path):
        os.remove(game_path)
    
    c.execute("DELETE FROM games WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

# Создаём заглушку для отсутствующих скриншотов
@app.route('/static/placeholder.png')
def placeholder():
    from flask import send_file
    import io
    from PIL import Image, ImageDraw
    
    img = Image.new('RGB', (300, 150), color=(30, 30, 50))
    draw = ImageDraw.Draw(img)
    draw.text((80, 60), "JOTOS", fill=(255, 200, 100))
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/screenshots/<filename>')
def serve_screenshot(filename):
    return send_file(os.path.join(app.config['SCREENSHOT_FOLDER'], filename))

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════╗
    ║       JOTOS — Пиксельная игровая платформа║
    ║                                           ║
    ║  Запуск сервера...                        ║
    ║  Открой в браузере: http://localhost:5000 ║
    ║                                           ║
    ║  Тестовые аккаунты:                       ║
    ║    блабла / 1234                          ║
    ║    dev / qwe                              ║
    ╚═══════════════════════════════════════════╝
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)