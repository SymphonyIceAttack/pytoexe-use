import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUserRequest
import sqlite3
from datetime import datetime
import logging

# Настройки
API_ID = '22929583'  # Получить на my.telegram.org
API_HASH = '1d6c1fe916aa1b113911e33d78dac0f9'
BOT_TOKEN = '8422381071:AAH-Ey5OdLIlhQVTrZfiTnSCNWUu5xRaxG8'  # От @BotFather
ADMIN_ID = 7144849463  # Твой ID (узнать у @userinfobot)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация клиентов
user_client = TelegramClient('user_session', API_ID, API_HASH)
bot_client = TelegramClient('bot_session', API_ID, API_HASH)

# База данных
def init_db():
    conn = sqlite3.connect('monitor.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  tracked_username TEXT,
                  added_date TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS username_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  old_username TEXT,
                  new_username TEXT,
                  change_date TIMESTAMP)''')
    conn.commit()
    conn.close()

async def get_user_by_id(user_id):
    """Получает информацию о пользователе по ID"""
    try:
        user = await user_client.get_entity(int(user_id))
        return user
    except Exception as e:
        logger.error(f"Ошибка получения пользователя {user_id}: {e}")
        return None

async def get_user_by_username(username):
    """Получает информацию о пользователе по username"""
    try:
        if username.startswith('@'):
            username = username[1:]
        user = await user_client.get_entity(username)
        return user
    except Exception as e:
        logger.error(f"Ошибка получения пользователя {username}: {e}")
        return None

async def check_username_change(user_id, current_username):
    """Проверяет изменился ли username"""
    conn = sqlite3.connect('monitor.db')
    c = conn.cursor()
    
    # Получаем последний сохраненный username
    c.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if result:
        old_username = result[0]
        if old_username != current_username:
            # Сохраняем изменение в историю
            c.execute("""INSERT INTO username_history 
                         (user_id, old_username, new_username, change_date)
                         VALUES (?, ?, ?, ?)""",
                     (user_id, old_username, current_username, datetime.now()))
            
            # Обновляем текущий username
            c.execute("UPDATE users SET username = ? WHERE user_id = ?", 
                     (current_username, user_id))
            
            conn.commit()
            conn.close()
            return old_username
    else:
        # Если пользователь не в базе, добавляем его
        c.execute("INSERT INTO users (user_id, username, tracked_username, added_date) VALUES (?, ?, ?, ?)",
                 (user_id, current_username, current_username, datetime.now()))
        conn.commit()
    
    conn.close()
    return None

async def monitor_user(user_id):
    """Мониторит конкретного пользователя"""
    try:
        user = await get_user_by_id(user_id)
        if user:
            current_username = user.username or "нет_юзернейма"
            old_username = await check_username_change(user_id, current_username)
            
            if old_username is not None:
                # Отправляем уведомление
                message = (f"🔔 **СМЕНА ЮЗЕРНЕЙМА!**\n\n"
                          f"👤 Пользователь: {user.first_name} {user.last_name or ''}\n"
                          f"📝 ID: `{user_id}`\n"
                          f"🔄 Старый: @{old_username if old_username != 'нет_юзернейма' else 'отсутствовал'}\n"
                          f"✅ Новый: @{current_username if current_username != 'нет_юзернейма' else 'удален'}\n"
                          f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                await bot_client.send_message(ADMIN_ID, message, parse_mode='md')
                logger.info(f"Смена юзернейма у {user_id}: {old_username} -> {current_username}")
    except Exception as e:
        logger.error(f"Ошибка мониторинга пользователя {user_id}: {e}")

async def monitor_all_users():
    """Мониторит всех отслеживаемых пользователей"""
    while True:
        try:
            conn = sqlite3.connect('monitor.db')
            c = conn.cursor()
            c.execute("SELECT user_id FROM users")
            users = c.fetchall()
            conn.close()
            
            for (user_id,) in users:
                await monitor_user(user_id)
                await asyncio.sleep(2)  # Небольшая задержка между проверками
            
            # Проверяем каждые 30 секунд
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Ошибка в мониторинге: {e}")
            await asyncio.sleep(60)

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("⛔ У вас нет доступа к этому боту.")
        return
    
    await event.reply(
        "👋 **Бот для отслеживания смены юзернеймов**\n\n"
        "Команды:\n"
        "`/track_id 123456789` - отслеживать пользователя по Telegram ID\n"
        "`/track_username @username` - отслеживать по юзернейму\n"
        "`/list` - список отслеживаемых\n"
        "`/history @username` - история смен юзернейма\n"
        "`/stop 123456789` - прекратить отслеживание\n"
        "`/check @username` - проверить текущий юзернейм\n"
        "`/help` - помощь",
        parse_mode='md'
    )

@bot_client.on(events.NewMessage(pattern='/track_id (.+)'))
async def track_id_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    
    try:
        user_id = int(event.pattern_match.group(1).strip())
        user = await get_user_by_id(user_id)
        
        if user:
            current_username = user.username or "нет_юзернейма"
            
            conn = sqlite3.connect('monitor.db')
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO users (user_id, username, tracked_username, added_date) VALUES (?, ?, ?, ?)",
                     (user_id, current_username, current_username, datetime.now()))
            conn.commit()
            conn.close()
            
            await event.reply(
                f"✅ **Пользователь добавлен в отслеживание!**\n\n"
                f"👤 Имя: {user.first_name} {user.last_name or ''}\n"
                f"🆔 ID: `{user_id}`\n"
                f"📝 Текущий юзернейм: @{current_username if current_username != 'нет_юзернейма' else 'отсутствует'}",
                parse_mode='md'
            )
        else:
            await event.reply("❌ Пользователь не найден. Проверьте ID.")
    except Exception as e:
        await event.reply(f"❌ Ошибка: {str(e)}")

@bot_client.on(events.NewMessage(pattern='/track_username (.+)'))
async def track_username_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    
    username = event.pattern_match.group(1).strip()
    user = await get_user_by_username(username)
    
    if user:
        await track_id_handler(events.NewMessage(
            pattern=f'/track_id {user.id}',
            message=event.message,
            sender_id=event.sender_id
        ))
    else:
        await event.reply("❌ Пользователь не найден. Проверьте юзернейм.")

@bot_client.on(events.NewMessage(pattern='/list'))
async def list_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    
    conn = sqlite3.connect('monitor.db')
    c = conn.cursor()
    c.execute("SELECT user_id, username, added_date FROM users")
    users = c.fetchall()
    conn.close()
    
    if not users:
        await event.reply("📭 Список отслеживаемых пользователей пуст.")
        return
    
    message = "📋 **Отслеживаемые пользователи:**\n\n"
    for user_id, username, added_date in users:
        user = await get_user_by_id(user_id)
        if user:
            name = f"{user.first_name} {user.last_name or ''}".strip()
            message += f"• {name}\n  🆔 `{user_id}`\n  📝 @{username}\n  📅 {added_date[:10]}\n\n"
    
    await event.reply(message, parse_mode='md')

@bot_client.on(events.NewMessage(pattern='/stop (.+)'))
async def stop_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    
    try:
        user_id = int(event.pattern_match.group(1).strip())
        
        conn = sqlite3.connect('monitor.db')
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        deleted = c.rowcount
        conn.commit()
        conn.close()
        
        if deleted:
            await event.reply(f"✅ Пользователь с ID `{user_id}` удален из отслеживания.", parse_mode='md')
        else:
            await event.reply("❌ Пользователь не найден в списке отслеживаемых.")
    except Exception as e:
        await event.reply(f"❌ Ошибка: {str(e)}")

@bot_client.on(events.NewMessage(pattern='/history (.+)'))
async def history_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    
    query = event.pattern_match.group(1).strip()
    
    # Определяем, ID это или юзернейм
    try:
        if query.startswith('@'):
            user = await get_user_by_username(query)
            if user:
                user_id = user.id
            else:
                await event.reply("❌ Пользователь не найден.")
                return
        else:
            user_id = int(query)
    except:
        await event.reply("❌ Неверный формат. Используйте ID или @username.")
        return
    
    conn = sqlite3.connect('monitor.db')
    c = conn.cursor()
    c.execute("""SELECT old_username, new_username, change_date 
                 FROM username_history 
                 WHERE user_id = ? 
                 ORDER BY change_date DESC 
                 LIMIT 10""", (user_id,))
    history = c.fetchall()
    conn.close()
    
    if not history:
        await event.reply("📭 История изменений отсутствует.")
        return
    
    user = await get_user_by_id(user_id)
    name = f"{user.first_name} {user.last_name or ''}".strip() if user else "Неизвестно"
    
    message = f"📜 **История смен юзернейма для {name}**\n\n"
    for old, new, date in history:
        message += f"🔄 {date[:16]}\n  📍 @{old} → @{new}\n\n"
    
    await event.reply(message, parse_mode='md')

@bot_client.on(events.NewMessage(pattern='/check (.+)'))
async def check_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    
    query = event.pattern_match.group(1).strip()
    
    try:
        if query.startswith('@'):
            user = await get_user_by_username(query)
        else:
            user = await get_user_by_id(int(query))
        
        if user:
            await event.reply(
                f"👤 **Информация о пользователе:**\n\n"
                f"Имя: {user.first_name} {user.last_name or ''}\n"
                f"ID: `{user.id}`\n"
                f"Юзернейм: @{user.username if user.username else 'отсутствует'}\n"
                f"Бот: {'да' if user.bot else 'нет'}\n"
                f"Premium: {'да' if getattr(user, 'premium', False) else 'нет'}",
                parse_mode='md'
            )
        else:
            await event.reply("❌ Пользователь не найден.")
    except Exception as e:
        await event.reply(f"❌ Ошибка: {str(e)}")

@bot_client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    if event.sender_id != ADMIN_ID:
        return
    
    await event.reply(
        "ℹ️ **Помощь по командам:**\n\n"
        "🔹 `/track_id 123456789` - добавить пользователя по ID\n"
        "🔹 `/track_username @username` - добавить по юзернейму\n"
        "🔹 `/list` - показать всех отслеживаемых\n"
        "🔹 `/stop 123456789` - удалить из отслеживания\n"
        "🔹 `/history @username` - история изменений\n"
        "🔹 `/check @username` - проверить текущий статус\n"
        "🔹 `/help` - это сообщение\n\n"
        "⚡ Бот проверяет изменения каждые 30 секунд",
        parse_mode='md'
    )

async def main():
    # Инициализация
    init_db()
    
    # Запуск клиентов
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    
    logger.info("Бот запущен и готов к работе!")
    
    # Запуск мониторинга в фоне
    asyncio.create_task(monitor_all_users())
    
    # Ожидание команд
    await bot_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())