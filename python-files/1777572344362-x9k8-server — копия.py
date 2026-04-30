# server.py
import asyncio
import sqlite3
import hashlib
import base64
from datetime import datetime
from pathlib import Path

DB_NAME = "messenger.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS contacts (
                    user_id INTEGER,
                    contact_id INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(contact_id) REFERENCES users(id),
                    PRIMARY KEY(user_id, contact_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    creator_id INTEGER,
                    FOREIGN KEY(creator_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS group_members (
                    group_id INTEGER,
                    user_id INTEGER,
                    FOREIGN KEY(group_id) REFERENCES groups(id),
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    PRIMARY KEY(group_id, user_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER,
                    to_user_id INTEGER,
                    to_group_id INTEGER,
                    message TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    delivered INTEGER DEFAULT 0,
                    FOREIGN KEY(from_user_id) REFERENCES users(id),
                    FOREIGN KEY(to_user_id) REFERENCES users(id),
                    FOREIGN KEY(to_group_id) REFERENCES groups(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS avatars (
                    user_id INTEGER PRIMARY KEY,
                    avatar_base64 TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS group_avatars (
                    group_id INTEGER PRIMARY KEY,
                    avatar_base64 TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(group_id) REFERENCES groups(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS hidden_messages (
                    user_id INTEGER,
                    message_id INTEGER,
                    PRIMARY KEY (user_id, message_id))''')
    try:
        c.execute("ALTER TABLE messages ADD COLUMN delivered INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

online_users = {}
avatar_uploads = {}          # user_id -> chunks
group_avatar_uploads = {}    # (group_id, user_id) -> chunks

async def handle_command(reader, writer, username, command, args, user_id):
    if command == "add_contact":
        if not args:
            return "[CMD] Ошибка: укажите имя контакта"
        contact_name = args[0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if contact_name == username:
            conn.close()
            return "[CMD] Нельзя добавить самого себя"
        c.execute("SELECT id FROM users WHERE username=?", (contact_name,))
        row = c.fetchone()
        if not row:
            conn.close()
            return f"[CMD] Пользователь {contact_name} не найден"
        contact_id = row[0]
        c.execute("SELECT 1 FROM contacts WHERE user_id=? AND contact_id=?", (user_id, contact_id))
        if c.fetchone():
            conn.close()
            return "[CMD] Этот контакт уже добавлен"
        c.execute("INSERT INTO contacts (user_id, contact_id) VALUES (?, ?)", (user_id, contact_id))
        c.execute("INSERT INTO contacts (user_id, contact_id) VALUES (?, ?)", (contact_id, user_id))
        conn.commit()
        conn.close()
        return f"[CMD] Контакт {contact_name} добавлен"

    elif command == "create_group":
        if len(args) < 2:
            return "[CMD] Ошибка: укажите название группы и минимум одного участника"
        group_name = args[0]
        members = args[1:]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO groups (name, creator_id) VALUES (?, ?)", (group_name, user_id))
        group_id = c.lastrowid
        c.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, user_id))
        added = []
        for m in members:
            c.execute("SELECT id FROM users WHERE username=?", (m,))
            row = c.fetchone()
            if row:
                c.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, row[0]))
                added.append(m)
            else:
                added.append(f"{m} (не найден)")
        conn.commit()
        conn.close()
        return f"[CMD] Группа '{group_name}' создана. Участники: {', '.join(added)}"

    elif command == "set_avatar_start":
        if len(args) < 1:
            return "[CMD] Ошибка: укажите количество частей"
        total_chunks = int(args[0])
        avatar_uploads[user_id] = {"chunks": {}, "total_chunks": total_chunks}
        return "[CMD] OK"

    elif command == "set_avatar_chunk":
        if len(args) < 2:
            return "[CMD] Ошибка: укажите индекс части и данные"
        chunk_index = int(args[0])
        chunk_data = args[1]
        if user_id not in avatar_uploads:
            return "[CMD] Ошибка: сессия загрузки аватара не найдена"
        upload = avatar_uploads[user_id]
        upload["chunks"][chunk_index] = chunk_data
        if len(upload["chunks"]) == upload["total_chunks"]:
            full_b64 = "".join(upload["chunks"][i] for i in range(upload["total_chunks"]))
            full_b64 = full_b64.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            try:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("REPLACE INTO avatars (user_id, avatar_base64, updated_at) VALUES (?, ?, ?)",
                          (user_id, full_b64, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                del avatar_uploads[user_id]
                return "[CMD] Аватар успешно обновлён"
            except Exception as e:
                del avatar_uploads[user_id]
                return f"[CMD] Ошибка сохранения аватара: {e}"
        return "[CMD] CHUNK_OK"

    elif command == "get_avatar":
        if len(args) < 1:
            return "[CMD] Укажите имя пользователя"
        target_user = args[0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=?", (target_user,))
        row = c.fetchone()
        if not row:
            conn.close()
            return f"[CMD] Пользователь {target_user} не найден"
        target_id = row[0]
        c.execute("SELECT avatar_base64 FROM avatars WHERE user_id=?", (target_id,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            data = row[0].strip().replace("\n", "").replace("\r", "").replace(" ", "")
            chunk_size = 8000
            chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
            total = len(chunks)
            writer.write(f"[CMD] AVATAR_START {target_user} {total}\n".encode())
            await writer.drain()
            for idx, chunk in enumerate(chunks):
                writer.write(f"[CMD] AVATAR_CHUNK {idx} {chunk}\n".encode())
                await writer.drain()
            writer.write(f"[CMD] AVATAR_END\n".encode())
            await writer.drain()
            return None
        else:
            return "[CMD] AVATAR_DATA None"

    # --- Групповые аватарки ---
    elif command == "set_group_avatar_start":
        if len(args) < 2:
            return "[CMD] Ошибка: укажите название группы и количество частей"
        group_name = args[0]
        total_chunks = int(args[1])
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM groups WHERE name=?", (group_name,))
        row = c.fetchone()
        if not row:
            conn.close()
            return f"[CMD] Группа '{group_name}' не найдена"
        group_id = row[0]
        c.execute("SELECT 1 FROM group_members WHERE group_id=? AND user_id=?", (group_id, user_id))
        if not c.fetchone():
            conn.close()
            return "[CMD] Вы не состоите в этой группе"
        conn.close()
        key = (group_id, user_id)
        group_avatar_uploads[key] = {"chunks": {}, "total_chunks": total_chunks, "group_id": group_id, "group_name": group_name}
        return "[CMD] OK"

    elif command == "set_group_avatar_chunk":
        if len(args) < 2:
            return "[CMD] Ошибка: укажите индекс части и данные"
        chunk_index = int(args[0])
        chunk_data = args[1]
        found_key = None
        for key in group_avatar_uploads:
            if key[1] == user_id:
                found_key = key
                break
        if not found_key:
            return "[CMD] Ошибка: сессия загрузки аватара группы не найдена"
        upload = group_avatar_uploads[found_key]
        upload["chunks"][chunk_index] = chunk_data
        if len(upload["chunks"]) == upload["total_chunks"]:
            full_b64 = "".join(upload["chunks"][i] for i in range(upload["total_chunks"]))
            full_b64 = full_b64.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            try:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("REPLACE INTO group_avatars (group_id, avatar_base64, updated_at) VALUES (?, ?, ?)",
                          (upload["group_id"], full_b64, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                del group_avatar_uploads[found_key]
                return f"[CMD] Аватар группы '{upload['group_name']}' успешно обновлён"
            except Exception as e:
                del group_avatar_uploads[found_key]
                return f"[CMD] Ошибка сохранения аватара группы: {e}"
        return "[CMD] CHUNK_OK"

    elif command == "get_group_avatar":
        if len(args) < 1:
            return "[CMD] Укажите название группы"
        group_name = args[0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM groups WHERE name=?", (group_name,))
        row = c.fetchone()
        if not row:
            conn.close()
            return f"[CMD] Группа '{group_name}' не найдена"
        group_id = row[0]
        c.execute("SELECT avatar_base64 FROM group_avatars WHERE group_id=?", (group_id,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            data = row[0].strip().replace("\n", "").replace("\r", "").replace(" ", "")
            chunk_size = 8000
            chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
            total = len(chunks)
            writer.write(f"[CMD] GROUP_AVATAR_START {group_name} {total}\n".encode())
            await writer.drain()
            for idx, chunk in enumerate(chunks):
                writer.write(f"[CMD] GROUP_AVATAR_CHUNK {idx} {chunk}\n".encode())
                await writer.drain()
            writer.write(f"[CMD] GROUP_AVATAR_END\n".encode())
            await writer.drain()
            return None
        else:
            return "[CMD] GROUP_AVATAR_DATA None"

    # --- Отправка сообщений ---
    elif command == "send":
        if len(args) < 2:
            return "[CMD] Ошибка: укажите получателя и текст сообщения"
        recipient = args[0]
        message_text = " ".join(args[1:])
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        now_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("SELECT id FROM groups WHERE name=?", (recipient,))
        group_row = c.fetchone()
        if group_row:
            group_id = group_row[0]
            c.execute("INSERT INTO messages (from_user_id, to_group_id, message, timestamp, delivered) VALUES (?, ?, ?, ?, 1)",
                      (user_id, group_id, message_text, now_local))
            conn.commit()
            c.execute("SELECT user_id FROM group_members WHERE group_id=?", (group_id,))
            members = [row[0] for row in c.fetchall()]
            for member_id in members:
                c.execute("SELECT username FROM users WHERE id=?", (member_id,))
                member_name = c.fetchone()[0]
                if member_name in online_users and member_name != username:
                    target_writer = online_users[member_name][0]
                    display = f"[MSG] [ГРУППА {recipient}] {username}: {message_text}"
                    target_writer.write((display + "\n").encode())
                    await target_writer.drain()
            conn.close()
            return f"[CMD] Сообщение в группу '{recipient}' отправлено"
        else:
            c.execute("SELECT id FROM users WHERE username=?", (recipient,))
            to_row = c.fetchone()
            if not to_row:
                conn.close()
                return f"[CMD] Пользователь {recipient} не найден"
            to_id = to_row[0]
            c.execute("INSERT INTO messages (from_user_id, to_user_id, message, timestamp, delivered) VALUES (?, ?, ?, ?, 0)",
                      (user_id, to_id, message_text, now_local))
            conn.commit()
            if recipient in online_users:
                target_writer = online_users[recipient][0]
                display = f"[MSG] {username} (личное): {message_text}"
                target_writer.write((display + "\n").encode())
                await target_writer.drain()
                c.execute("UPDATE messages SET delivered = 1 WHERE from_user_id=? AND to_user_id=? AND message=? AND timestamp=?",
                          (user_id, to_id, message_text, now_local))
                conn.commit()
                conn.close()
                return f"[CMD] Сообщение для {recipient} доставлено"
            else:
                conn.close()
                return f"[CMD] Сообщение для {recipient} сохранено (пользователь офлайн)"

    # --- Удаление сообщений ---
    elif command == "delete_message":
        if len(args) < 2:
            return "[CMD] Ошибка: укажите ID сообщения и тип удаления (self/all)"
        msg_id = int(args[0])
        delete_type = args[1]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT from_user_id, to_user_id, to_group_id FROM messages WHERE id=?", (msg_id,))
        msg = c.fetchone()
        if not msg:
            conn.close()
            return "[CMD] Сообщение не найдено"
        from_user_id, to_user_id, to_group_id = msg
        if delete_type == "all":
            if from_user_id != user_id:
                conn.close()
                return "[CMD] Вы можете удалить у всех только свои сообщения"
            c.execute("DELETE FROM messages WHERE id=?", (msg_id,))
            conn.commit()
            conn.close()
            return "[CMD] Сообщение удалено у всех"
        elif delete_type == "self":
            c.execute("INSERT OR IGNORE INTO hidden_messages (user_id, message_id) VALUES (?, ?)", (user_id, msg_id))
            conn.commit()
            conn.close()
            return "[CMD] Сообщение скрыто у вас"
        else:
            conn.close()
            return "[CMD] Неверный тип удаления (используйте self или all)"

    # --- История ---
    elif command == "history":
        if not args:
            return "[CMD] Укажите имя пользователя или группы"
        target = args[0]
        limit = 50
        if len(args) > 1 and args[1].isdigit():
            limit = int(args[1])
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM groups WHERE name=?", (target,))
        group_row = c.fetchone()
        if group_row:
            group_id = group_row[0]
            c.execute("SELECT 1 FROM group_members WHERE group_id=? AND user_id=?", (group_id, user_id))
            if not c.fetchone():
                conn.close()
                return "[CMD] Вы не состоите в этой группе"
            c.execute('''SELECT m.id, u.username, m.message, m.timestamp 
                         FROM messages m
                         JOIN users u ON m.from_user_id = u.id
                         WHERE m.to_group_id = ?
                         AND NOT EXISTS (SELECT 1 FROM hidden_messages hm WHERE hm.user_id=? AND hm.message_id=m.id)
                         ORDER BY m.timestamp DESC LIMIT ?''', (group_id, user_id, limit))
            rows = c.fetchall()
            if not rows:
                conn.close()
                return f"[CMD] История группы '{target}' пуста"
            result = [f"[CMD] === История группы {target} ==="]
            for r in reversed(rows):
                result.append(f"[CMD] {r[3]} {r[1]}: {r[2]} (id:{r[0]})")
            conn.close()
            return "\n".join(result)
        else:
            c.execute("SELECT id FROM users WHERE username=?", (target,))
            other_row = c.fetchone()
            if not other_row:
                conn.close()
                return f"[CMD] Пользователь {target} не найден"
            other_id = other_row[0]
            c.execute('''SELECT m.id, u.username, m.message, m.timestamp 
                         FROM messages m
                         JOIN users u ON m.from_user_id = u.id
                         WHERE ((m.from_user_id=? AND m.to_user_id=?) OR (m.from_user_id=? AND m.to_user_id=?))
                         AND NOT EXISTS (SELECT 1 FROM hidden_messages hm WHERE hm.user_id=? AND hm.message_id=m.id)
                         ORDER BY m.timestamp DESC LIMIT ?''',
                      (user_id, other_id, other_id, user_id, user_id, limit))
            rows = c.fetchall()
            if not rows:
                conn.close()
                return f"[CMD] Нет истории с {target}"
            result = [f"[CMD] === История с {target} ==="]
            for r in reversed(rows):
                result.append(f"[CMD] {r[3]} {r[1]}: {r[2]} (id:{r[0]})")
            conn.close()
            return "\n".join(result)

    # --- Контакты (с онлайн‑статусами) ---
    elif command == "contacts":
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT u.username FROM contacts c
                     JOIN users u ON c.contact_id = u.id
                     WHERE c.user_id = ?''', (user_id,))
        rows = c.fetchall()
        conn.close()
        if not rows:
            return "[CMD] У вас нет контактов"
        contact_list = []
        for (username_,) in rows:
            is_online = username_ in online_users
            contact_list.append(f"{username_}|{'online' if is_online else 'offline'}")
        return "[CMD] Контакты: " + ";".join(contact_list)

    # --- Список групп (только названия) ---
    elif command == "groups":
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT g.name FROM groups g
                     JOIN group_members gm ON g.id = gm.group_id
                     WHERE gm.user_id = ?''', (user_id,))
        groups = [row[0] for row in c.fetchall()]
        conn.close()
        if not groups:
            return "[CMD] Вы не состоите ни в одной группе"
        return "[CMD] Группы: " + ", ".join(groups)

    # --- Добавление участника в группу ---
    elif command == "add_to_group":
        if len(args) < 2:
            return "[CMD] Ошибка: укажите название группы и имя пользователя"
        group_name = args[0]
        target_username = args[1]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM groups WHERE name=?", (group_name,))
        group_row = c.fetchone()
        if not group_row:
            conn.close()
            return f"[CMD] Группа '{group_name}' не найдена"
        group_id = group_row[0]
        c.execute("SELECT 1 FROM group_members WHERE group_id=? AND user_id=?", (group_id, user_id))
        if not c.fetchone():
            conn.close()
            return "[CMD] Вы не состоите в этой группе"
        c.execute("SELECT id FROM users WHERE username=?", (target_username,))
        target_row = c.fetchone()
        if not target_row:
            conn.close()
            return f"[CMD] Пользователь {target_username} не найден"
        target_id = target_row[0]
        c.execute("SELECT 1 FROM group_members WHERE group_id=? AND user_id=?", (group_id, target_id))
        if c.fetchone():
            conn.close()
            return f"[CMD] Пользователь {target_username} уже состоит в группе"
        c.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, target_id))
        conn.commit()
        conn.close()
        if target_username in online_users:
            target_writer = online_users[target_username][0]
            target_writer.write(f"[CMD] Вы добавлены в группу {group_name}\n".encode())
            await target_writer.drain()
        return f"[CMD] Пользователь {target_username} добавлен в группу {group_name}"

    # --- Статус пользователя (онлайн/офлайн) ---
    elif command == "get_status":
        if len(args) < 1:
            return "[CMD] Укажите имя пользователя"
        target_user = args[0]
        is_online = target_user in online_users
        return f"[CMD] STATUS {target_user}|{'online' if is_online else 'offline'}"

    # --- Список участников группы ---
    elif command == "get_group_members":
        if len(args) < 1:
            return "[CMD] Ошибка: укажите название группы"
        group_name = args[0]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM groups WHERE name=?", (group_name,))
        group_row = c.fetchone()
        if not group_row:
            conn.close()
            return f"[CMD] Группа '{group_name}' не найдена"
        group_id = group_row[0]
        c.execute("SELECT 1 FROM group_members WHERE group_id=? AND user_id=?", (group_id, user_id))
        if not c.fetchone():
            conn.close()
            return "[CMD] Вы не состоите в этой группе"
        c.execute('''SELECT u.username FROM group_members gm
                     JOIN users u ON gm.user_id = u.id
                     WHERE gm.group_id = ?''', (group_id,))
        members = c.fetchall()
        conn.close()
        members_list = [username for (username,) in members]
        return f"[CMD] Участники группы {group_name}: " + ", ".join(members_list)

    # --- Переименование группы ---
    elif command == "rename_group":
        if len(args) < 2:
            return "[CMD] Ошибка: укажите текущее и новое название группы"
        old_name = args[0]
        new_name = args[1]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM groups WHERE name=?", (old_name,))
        row = c.fetchone()
        if not row:
            conn.close()
            return f"[CMD] Группа '{old_name}' не найдена"
        group_id = row[0]
        c.execute("SELECT 1 FROM group_members WHERE group_id=? AND user_id=?", (group_id, user_id))
        if not c.fetchone():
            conn.close()
            return "[CMD] Вы не состоите в этой группе"
        c.execute("SELECT id FROM groups WHERE name=? AND id != ?", (new_name, group_id))
        if c.fetchone():
            conn.close()
            return f"[CMD] Группа с именем '{new_name}' уже существует"
        c.execute("UPDATE groups SET name=? WHERE id=?", (new_name, group_id))
        conn.commit()
        c.execute("SELECT user_id FROM group_members WHERE group_id=?", (group_id,))
        members = [row[0] for row in c.fetchall()]
        for member_id in members:
            c.execute("SELECT username FROM users WHERE id=?", (member_id,))
            member_name = c.fetchone()[0]
            if member_name in online_users:
                target_writer = online_users[member_name][0]
                target_writer.write(f"[CMD] GROUP_RENAMED {old_name}|{new_name}\n".encode())
                await target_writer.drain()
        conn.close()
        return f"[CMD] Группа переименована в '{new_name}'"

    else:
        return "[CMD] Неизвестная команда"

async def deliver_offline_messages(writer, username, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT u.username, m.message, m.id, m.timestamp 
                 FROM messages m
                 JOIN users u ON m.from_user_id = u.id
                 WHERE m.to_user_id = ? AND m.delivered = 0
                 AND NOT EXISTS (SELECT 1 FROM hidden_messages hm WHERE hm.user_id=? AND hm.message_id=m.id)''', (user_id, user_id))
    personal = c.fetchall()
    c.execute('''SELECT g.name, u.username, m.message, m.id, m.timestamp
                 FROM messages m
                 JOIN groups g ON m.to_group_id = g.id
                 JOIN users u ON m.from_user_id = u.id
                 JOIN group_members gm ON g.id = gm.group_id
                 WHERE gm.user_id = ? AND m.delivered = 0
                 AND NOT EXISTS (SELECT 1 FROM hidden_messages hm WHERE hm.user_id=? AND hm.message_id=m.id)''', (user_id, user_id))
    group_msgs = c.fetchall()
    for msg in personal:
        sender, text, msg_id, ts = msg
        writer.write(f"[MSG] {sender} (личное): {text}\n".encode())
        await writer.drain()
    for msg in group_msgs:
        group, sender, text, msg_id, ts = msg
        writer.write(f"[MSG] [ГРУППА {group}] {sender}: {text}\n".encode())
        await writer.drain()
    c.execute("UPDATE messages SET delivered = 1 WHERE (to_user_id = ? OR to_group_id IN (SELECT group_id FROM group_members WHERE user_id=?)) AND delivered = 0", (user_id, user_id))
    conn.commit()
    conn.close()

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Новое подключение {addr}")
    username = None
    user_id = None
    authenticated = False
    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            message = data.decode().strip()
            if not message:
                continue
            if not message.startswith('/'):
                writer.write("[CMD] Неизвестная команда. Используйте /help\n".encode())
                await writer.drain()
                continue
            parts = message.split()
            cmd = parts[0][1:]
            args = parts[1:]

            if cmd == "register":
                if len(args) != 2:
                    writer.write("[CMD] Использование: /register username password\n".encode())
                    await writer.drain()
                    continue
                reg_username, reg_password = args
                hashed = hash_password(reg_password)
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (reg_username, hashed))
                    conn.commit()
                    writer.write(f"[CMD] Пользователь {reg_username} успешно зарегистрирован\n".encode())
                except sqlite3.IntegrityError:
                    writer.write("[CMD] Имя пользователя уже занято\n".encode())
                conn.close()
                await writer.drain()

            elif cmd == "login":
                if authenticated:
                    writer.write("[CMD] Вы уже вошли\n".encode())
                    await writer.drain()
                    continue
                if len(args) != 2:
                    writer.write("[CMD] Использование: /login username password\n".encode())
                    await writer.drain()
                    continue
                login_username, login_password = args
                hashed = hash_password(login_password)
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT id FROM users WHERE username=? AND password=?", (login_username, hashed))
                row = c.fetchone()
                if row:
                    authenticated = True
                    username = login_username
                    user_id = row[0]
                    online_users[username] = (writer, user_id)
                    writer.write(f"[CMD] Добро пожаловать, {username}!\n".encode())
                    await writer.drain()
                    await deliver_offline_messages(writer, username, user_id)
                else:
                    writer.write("[CMD] Неверное имя пользователя или пароль\n".encode())
                    await writer.drain()
                conn.close()

            elif cmd == "logout":
                if authenticated:
                    writer.write("[CMD] Вы вышли из системы\n".encode())
                    await writer.drain()
                    online_users.pop(username, None)
                    authenticated = False
                    username = None
                    user_id = None
                else:
                    writer.write("[CMD] Вы не авторизованы\n".encode())
                    await writer.drain()

            elif cmd == "quit":
                writer.write("[CMD] До свидания!\n".encode())
                await writer.drain()
                break

            elif cmd == "help":
                help_text = """
[CMD] Доступные команды:
/register username password
/login username password
/logout
/add_contact username
/create_group group_name member1 member2 ...
/send recipient message
/delete_message message_id self|all
/history user_or_group [limit]
/contacts
/groups
/add_to_group group_name username
/set_avatar_start total_chunks
/set_avatar_chunk index chunk_data
/get_avatar username
/get_group_avatar group_name
/set_group_avatar_start group_name total_chunks
/set_group_avatar_chunk index chunk_data
/rename_group old_name new_name
/get_status username
/get_group_members group_name
/quit
"""
                writer.write(help_text.encode())
                await writer.drain()

            else:
                if not authenticated:
                    writer.write("[CMD] Сначала войдите: /login username password\n".encode())
                    await writer.drain()
                    continue
                result = await handle_command(reader, writer, username, cmd, args, user_id)
                if result:
                    writer.write((result + "\n").encode())
                    await writer.drain()

    except Exception as e:
        print(f"Ошибка в обработке клиента {addr}: {e}")
    finally:
        if authenticated and username:
            online_users.pop(username, None)
        writer.close()
        await writer.wait_closed()
        print(f"Отключение {addr}")

async def main():
    init_db()
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)
    print("Сервер запущен на 127.0.0.1:8888")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())