import os
import uuid
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template_string, abort

app = Flask(__name__)
DATABASE = 'calendar.db'

import sqlite3

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS calendars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL DEFAULT 'Новый календарь',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calendar_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                event_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (calendar_id) REFERENCES calendars (id)
            )
        ''')

index_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Онлайн-календарь</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-5">
    <div class="text-center mb-5">
        <h1>📅 Календарь</h1>
        <p class="lead">Создайте календарь и поделитесь ссылкой — любой сможет добавлять события.</p>
    </div>
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow-sm">
                <div class="card-body text-center">
                    <h5 class="card-title">Создать календарь</h5>
                    <form action="/create" method="POST">
                        <div class="mb-3">
                            <input type="text" name="title" class="form-control" placeholder="Название календаря" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Создать</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
'''

calendar_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{{ calendar.title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>{{ calendar.title }}</h2>
        <button class="btn btn-outline-secondary">
            <i class="bi bi-share-fill"></i> Копировать ссылку
        </button>
    </div>

    <div class="row">
        <div class="col-md-5">
            <div class="card shadow-sm mb-4">
                <div class="card-header fw-bold">Добавить событие</div>
                <div class="card-body">
                    <form method="POST" action="/calendar/{{ calendar.uuid }}/add_event">
                        <div class="mb-3">
                            <input type="text" name="title" class="form-control" placeholder="Название события" required>
                        </div>
                        <div class="mb-3">
                            <input type="date" name="date" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-success w-100">Добавить</button>
                    </form>
                </div>
            </div>
        </div>

        <div class="col-md-7">
            <div class="card shadow-sm">
                <div class="card-header fw-bold">События календаря</div>
                <div class="card-body">
                    {% if events %}
                        <div class="list-group list-group-flush">
                        {% for ev in events %}
                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>{{ ev.title }}</strong>
                                    <br><small class="text-muted">{{ ev.event_date }}</small>
                                </div>
                                <a href="/calendar/{{ calendar.uuid }}/delete_event/{{ ev.id }}"
                                   class="btn btn-sm btn-outline-danger"
                                   onclick="return confirm('Удалить событие?')">
                                    <i class="bi bi-trash"></i>
                                </a>
                            </div>
                        {% endfor %}
                        </div>
                    {% else %}
                        <p class="text-muted mb-0">Событий пока нет. Добавьте первое!</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(index_html)

@app.route('/create', methods=['POST'])
def create_calendar():
    title = request.form.get('title', 'Без названия').strip()
    if not title:
        title = 'Новый календарь'
    uid = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute('INSERT INTO calendars (uuid, title) VALUES (?, ?)', (uid, title))
    return redirect(url_for('view_calendar', uuid=uid))

@app.route('/calendar/<uuid>')
def view_calendar(uuid):
    with get_db() as conn:
        calendar = conn.execute('SELECT * FROM calendars WHERE uuid = ?', (uuid,)).fetchone()
        if not calendar:
            abort(404, description="Календарь не найден")
        events = conn.execute(
            'SELECT * FROM events WHERE calendar_id = ? ORDER BY event_date DESC, id DESC',
            (calendar['id'],)
        ).fetchall()
    return render_template_string(calendar_html, calendar=calendar, events=events)

@app.route('/calendar/<uuid>/add_event', methods=['POST'])
def add_event(uuid):
    title = request.form.get('title', '').strip()
    date = request.form.get('date', '').strip()
    if not title or not date:
        abort(400, description="Заполните название и дату события")

    with get_db() as conn:
        calendar = conn.execute('SELECT id FROM calendars WHERE uuid = ?', (uuid,)).fetchone()
        if not calendar:
            abort(404, description="Календарь не найден")
        conn.execute(
            'INSERT INTO events (calendar_id, title, event_date) VALUES (?, ?, ?)',
            (calendar['id'], title, date)
        )
    return redirect(url_for('view_calendar', uuid=uuid))

@app.route('/calendar/<uuid>/delete_event/<int:event_id>')
def delete_event(uuid, event_id):
    with get_db() as conn:
        calendar = conn.execute('SELECT id FROM calendars WHERE uuid = ?', (uuid,)).fetchone()
        if not calendar:
            abort(404, description="Календарь не найден")
        conn.execute(
            'DELETE FROM events WHERE id = ? AND calendar_id = ?',
            (event_id, calendar['id'])
        )
    return redirect(url_for('view_calendar', uuid=uuid))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)