import os
import sys
import asyncio
import random
import time
import logging
from datetime import datetime
import discord
from discord.ext import commands

# ==================== НАСТРОЙКИ ====================
RESTART_DELAY = 5
start_time = datetime.now()
logging.basicConfig(
    filename='discord_logger.txt',
    level=logging.ERROR,
    format='%(asctime)s — %(message)s'
)

# ==================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ====================
tasks_spam = []          # для .spam
tasks_spam_media = []    # для .spammedia
tasks_ping = []          # для .ping
tasks_ping_media = []    # для .pingmedia
tasks_ping_video = []    # для .pingvideo

afk_enabled = False
afk_reason = ''
afk_media_url = ''
afk_users = set()
afk_start_time = None

us_users = {}            # автоответ текст
usp_users = {}           # автоответ фото
usv_users = {}           # автоответ видео
last_reply_time = {}
last_reply_time_photo = {}
last_reply_time_video = {}

namebot = 'DISCORD HELPER'
media_menu = ''  # можно задать через .link

# Шаблоны для оскорблений (твои сохранены)
shablon = [
    "садовыми ножницами исполосоваю сонную артерию твоей мамаши",
    "из вырезанных голов твоей родословной построю пьедестал",
    "экзартикуляционирую вульву твоей матери да бы её пробило на красный фонтан метаморфозы",
    "вывалю путем эякуляции твои кишки в ванну, и заставлю купаться тебя в этом бульоне",
    "раздербеню твои атрофированные рёбра словно гнилую ограду",
    "даже трупные черви скулят от амбре развороченной могилы твоей родни",
    "отвар из твоих квашенных костей вылью в канализацию",
    "твоя морда это адов тигель где плавится дерьмище, но я лишь вычерпаю это ведром и вылью тебе в глотачку",
    "вспорю твой живот хуём вместо ножа, дабы вынуть кишечнополостные трубы и сплести из них удавку",
    "размозжу твой хрупкий таз гидравлическим прессом, ребёнок хуйни",
]

# ==================== РАБОТА С ФАЙЛАМИ ====================
def read_api_key(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def ensure_settings_folder():
    if not os.path.exists('settings'):
        os.makedirs('settings')

# ==================== ИНИЦИАЛИЗАЦИЯ ====================
ensure_settings_folder()
token = read_api_key('settings/discord_token.txt')

if not token:
    token = input('Введите Discord токен: ')
    with open('settings/discord_token.txt', 'w') as f:
        f.write(token)
    print('Токен сохранен в settings/discord_token.txt')

# Создаем клиента
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
client = commands.Bot(command_prefix='.', self_bot=True, intents=intents, help_command=None)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
async def safe_edit(message, text):
    """Безопасное редактирование сообщения"""
    try:
        await message.edit(content=text)
    except:
        pass

async def get_channel_from_mention_or_id(ctx, channel_input):
    """Получить объект канала по упоминанию или ID"""
    try:
        # Если это упоминание <#123456>
        if channel_input.startswith('<#') and channel_input.endswith('>'):
            channel_id = int(channel_input[2:-1])
            return ctx.guild.get_channel(channel_id) if ctx.guild else client.get_channel(channel_id)
        # Если это просто ID
        else:
            channel_id = int(channel_input)
            return ctx.guild.get_channel(channel_id) if ctx.guild else client.get_channel(channel_id)
    except:
        return None

async def get_user_from_mention_or_id(ctx, user_input):
    """Получить объект пользователя по упоминанию или ID"""
    try:
        if user_input.startswith('<@') and user_input.endswith('>'):
            user_id = int(user_input.replace('<@', '').replace('>', '').replace('!', ''))
            return await client.fetch_user(user_id)
        else:
            return await client.fetch_user(int(user_input))
    except:
        return None

def load_lines_from_file(filename):
    """Загрузить строки из файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

# ==================== ЛОГИРОВАНИЕ УДАЛЕННЫХ СООБЩЕНИЙ ====================
@client.event
async def on_message_delete(message):
    try:
        with open('deleted_messages_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] Канал: {message.channel.id} | Автор: {message.author} ({message.author.id}) | Текст: {message.content}\n")
    except Exception as e:
        logging.error(f'Ошибка логирования: {e}')

# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

@client.command(name='help')
async def help_command(ctx):
    """Показать меню помощи"""
    await ctx.message.delete()
    
    menu = f'''⸸ **{namebot}** ⸸

**Спам команды:**
`.spam <канал> <задержка> <файл.txt> [префикс]` — спам текстом
`.spammedia <канал> <задержка> <файл.txt> <URL фото> [префикс]` — спам с фото
`.spamvideo <канал> <задержка> <файл.txt> <URL видео> [префикс]` — спам с видео
`.spamoff <канал>` — выключить спам

**Пинг команды:**
`.ping <канал> <юзер> <задержка> <файл.txt> [префикс]` — пинг текстом
`.pingmedia <канал> <юзер> <задержка> <файл.txt> <URL фото> [префикс]` — пинг с фото
`.pingvideo <канал> <юзер> <задержка> <файл.txt> <URL видео> [префикс]` — пинг с видео
`.pingoff <канал>` — выключить пинг

**Автоответчики:**
`.autoreply <юзер> <задержка> <файл.txt> [префикс]` — автоответ текстом
`.autophoto <юзер> <задержка> <файл.txt> <URL фото> [префикс]` — автоответ с фото
`.autovideo <юзер> <задержка> <файл.txt> <URL видео> [префикс]` — автоответ с видео
`.autoff <юзер>` — выключить автоответ

**AFK:**
`.afk on <причина> [URL фото]` — включить AFK
`.afk off` — выключить AFK

**Файлы:**
`.files` — показать все .txt файлы
`.save` (реплай на .txt) — сохранить файл
`.unsave <файл.txt>` — удалить файл
`.unload <файл.txt>` — выгрузить файл в чат

**Инфо:**
`.id` — показать ID канала
`.user` (реплай на сообщение) — показать ID юзера
`.times` — время работы бота

**Кастомизация:**
`.title <имя>` — сменить имя бота
`.link <URL>` — сменить фото в меню

**Юзер:** `{ctx.author}` 
**ID:** `{ctx.author.id}`'''

    if media_menu:
        try:
            await ctx.send(menu, file=discord.File(media_menu) if os.path.exists(media_menu) else None)
        except:
            await ctx.send(menu)
    else:
        await ctx.send(menu)

# ==================== СПАМ КОМАНДЫ ====================

@client.command(name='spam')
async def spam_command(ctx, channel_input: str, delay: int, filename: str, *, prefix: str = ''):
    """Спам текстом в канал"""
    await ctx.message.delete()
    
    channel = await get_channel_from_mention_or_id(ctx, channel_input)
    if not channel:
        await ctx.send('❌ Канал не найден', delete_after=3)
        return
    
    lines = load_lines_from_file(filename)
    if not lines:
        await ctx.send(f'❌ Файл `{filename}` не найден или пуст', delete_after=3)
        return
    
    channel_id = channel.id
    tasks_spam.append(channel_id)
    
    await ctx.send(f'✅ Спам запущен в {channel.mention}\n⏱ Задержка: {delay}с\n📁 Файл: {filename}\n🛑 Для остановки: `.spamoff {channel_id}`', delete_after=5)
    
    try:
        while channel_id in tasks_spam:
            for line in lines:
                if channel_id not in tasks_spam:
                    break
                text = f"{prefix} {line}".strip() if prefix else line
                await channel.send(text)
                await asyncio.sleep(delay + random.uniform(-0.5, 1.5))
    except Exception as e:
        logging.error(f'Ошибка в spam: {e}')

@client.command(name='spammedia')
async def spammedia_command(ctx, channel_input: str, delay: int, filename: str, media_url: str, *, prefix: str = ''):
    """Спам с фото в канал"""
    await ctx.message.delete()
    
    channel = await get_channel_from_mention_or_id(ctx, channel_input)
    if not channel:
        await ctx.send('❌ Канал не найден', delete_after=3)
        return
    
    lines = load_lines_from_file(filename)
    if not lines:
        await ctx.send(f'❌ Файл `{filename}` не найден или пуст', delete_after=3)
        return
    
    channel_id = channel.id
    tasks_spam_media.append(channel_id)
    
    await ctx.send(f'✅ Спам с фото запущен в {channel.mention}\n⏱ Задержка: {delay}с\n📁 Файл: {filename}\n🖼 Фото: {media_url}\n🛑 Для остановки: `.spamoff {channel_id}`', delete_after=5)
    
    try:
        while channel_id in tasks_spam_media:
            for line in lines:
                if channel_id not in tasks_spam_media:
                    break
                text = f"{prefix} {line}".strip() if prefix else line
                await channel.send(text, file=discord.File(media_url) if os.path.exists(media_url) else None)
                if not os.path.exists(media_url):
                    await channel.send(f"{text}\n{media_url}")
                await asyncio.sleep(delay + random.uniform(-0.5, 1.5))
    except Exception as e:
        logging.error(f'Ошибка в spammedia: {e}')

@client.command(name='spamvideo')
async def spamvideo_command(ctx, channel_input: str, delay: int, filename: str, media_url: str, *, prefix: str = ''):
    """Спам с видео в канал"""
    await ctx.message.delete()
    
    channel = await get_channel_from_mention_or_id(ctx, channel_input)
    if not channel:
        await ctx.send('❌ Канал не найден', delete_after=3)
        return
    
    lines = load_lines_from_file(filename)
    if not lines:
        await ctx.send(f'❌ Файл `{filename}` не найден или пуст', delete_after=3)
        return
    
    channel_id = channel.id
    await ctx.send(f'✅ Спам с видео запущен в {channel.mention}\n⏱ Задержка: {delay}с\n📁 Файл: {filename}\n🎬 Видео: {media_url}\n🛑 Для остановки: `.spamoff {channel_id}`', delete_after=5)
    
    try:
        while channel_id in tasks_spam_media:  # используем тот же список
            for line in lines:
                if channel_id not in tasks_spam_media:
                    break
                text = f"{prefix} {line}".strip() if prefix else line
                if os.path.exists(media_url):
                    await channel.send(text, file=discord.File(media_url))
                else:
                    await channel.send(f"{text}\n{media_url}")
                await asyncio.sleep(delay + random.uniform(-0.5, 1.5))
    except Exception as e:
        logging.error(f'Ошибка в spamvideo: {e}')

@client.command(name='spamoff')
async def spamoff_command(ctx, channel_input: str):
    """Остановить спам в канале"""
    await ctx.message.delete()
    
    channel = await get_channel_from_mention_or_id(ctx, channel_input)
    if not channel:
        await ctx.send('❌ Канал не найден', delete_after=3)
        return
    
    channel_id = channel.id
    stopped = False
    
    if channel_id in tasks_spam:
        tasks_spam.remove(channel_id)
        stopped = True
    if channel_id in tasks_spam_media:
        tasks_spam_media.remove(channel_id)
        stopped = True
    
    if stopped:
        await ctx.send(f'✅ Спам остановлен в {channel.mention}', delete_after=3)
    else:
        await ctx.send(f'❌ Спам не был запущен в {channel.mention}', delete_after=3)

# ==================== ПИНГ КОМАНДЫ ====================

@client.command(name='ping')
async def ping_command(ctx, channel_input: str, user_input: str, delay: int, filename: str, *, prefix: str = ''):
    """Пинг юзера текстом"""
    await ctx.message.delete()
    
    channel = await get_channel_from_mention_or_id(ctx, channel_input)
    user = await get_user_from_mention_or_id(ctx, user_input)
    
    if not channel or not user:
        await ctx.send('❌ Канал или юзер не найдены', delete_after=3)
        return
    
    lines = load_lines_from_file(filename)
    if not lines:
        await ctx.send(f'❌ Файл `{filename}` не найден или пуст', delete_after=3)
        return
    
    channel_id = channel.id
    tasks_ping.append(channel_id)
    
    await ctx.send(f'✅ Пинг запущен на {user.mention} в {channel.mention}\n⏱ Задержка: {delay}с\n📁 Файл: {filename}\n🛑 Для остановки: `.pingoff {channel_id}`', delete_after=5)
    
    try:
        while channel_id in tasks_ping:
            for line in lines:
                if channel_id not in tasks_ping:
                    break
                text = f"{user.mention} {prefix} {line}".strip() if prefix else f"{user.mention} {line}"
                await channel.send(text)
                await asyncio.sleep(delay + random.uniform(-0.5, 1.5))
    except Exception as e:
        logging.error(f'Ошибка в ping: {e}')

@client.command(name='pingmedia')
async def pingmedia_command(ctx, channel_input: str, user_input: str, delay: int, filename: str, media_url: str, *, prefix: str = ''):
    """Пинг юзера с фото"""
    await ctx.message.delete()
    
    channel = await get_channel_from_mention_or_id(ctx, channel_input)
    user = await get_user_from_mention_or_id(ctx, user_input)
    
    if not channel or not user:
        await ctx.send('❌ Канал или юзер не найдены', delete_after=3)
        return
    
    lines = load_lines_from_file(filename)
    if not lines:
        await ctx.send(f'❌ Файл `{filename}` не найден или пуст', delete_after=3)
        return
    
    channel_id = channel.id
    tasks_ping_media.append(channel_id)
    
    await ctx.send(f'✅ Пинг с фото запущен на {user.mention} в {channel.mention}\n⏱ Задержка: {delay}с\n📁 Файл: {filename}\n🛑 Для остановки: `.pingoff {channel_id}`', delete_after=5)
    
    try:
        while channel_id in tasks_ping_media:
            for line in lines:
                if channel_id not in tasks_ping_media:
                    break
                text = f"{user.mention} {prefix} {line}".strip() if prefix else f"{user.mention} {line}"
                if os.path.exists(media_url):
                    await channel.send(text, file=discord.File(media_url))
                else:
                    await channel.send(f"{text}\n{media_url}")
                await asyncio.sleep(delay + random.uniform(-0.5, 1.5))
    except Exception as e:
        logging.error(f'Ошибка в pingmedia: {e}')

@client.command(name='pingvideo')
async def pingvideo_command(ctx, channel_input: str, user_input: str, delay: int, filename: str, media_url: str, *, prefix: str = ''):
    """Пинг юзера с видео"""
    await ctx.message.delete()
    
    channel = await get_channel_from_mention_or_id(ctx, channel_input)
    user = await get_user_from_mention_or_id(ctx, user_input)
    
    if not channel or not user:
        await ctx.send('❌ Канал или юзер не найдены', delete_after=3)
        return
    
    lines = load_lines_from_file(filename)
    if not lines:
        await ctx.send(f'❌ Файл `{filename}` не найден или пуст', delete_after=3)
        return
    
    channel_id = channel.id
    tasks_ping_video.append(channel_id)
    
    await ctx.send(f'✅ Пинг с видео запущен на {user.mention} в {channel.mention}\n⏱ Задержка: {delay}с\n📁 Файл: {filename}\n🛑 Для остановки: `.pingoff {channel_id}`', delete_after=5)
    
    try:
        while channel_id in tasks_ping_video:
            for line in lines:
                if channel_id not in tasks_ping_video:
                    break
                text = f"{user.mention} {prefix} {line}".strip() if prefix else f"{user.mention} {line}"
                if os.path.exists(media_url):
                    await channel.send(text, file=discord.File(media_url))
                else:
                    await channel.send(f"{text}\n{media_url}")
                await asyncio.sleep(delay + random.uniform(-0.5, 1.5))
    except Exception as e:
        logging.error(f'Ошибка в pingvideo: {e}')

@client.command(name='pingoff')
async def pingoff_command(ctx, channel_input: str):
    """Остановить пинг в канале"""
    await ctx.message.delete()
    
    channel = await get_channel_from_mention_or_id(ctx, channel_input)
    if not channel:
        await ctx.send('❌ Канал не найден', delete_after=3)
        return
    
    channel_id = channel.id
    stopped = False
    
    for lst in [tasks_ping, tasks_ping_media, tasks_ping_video]:
        if channel_id in lst:
            lst.remove(channel_id)
            stopped = True
    
    if stopped:
        await ctx.send(f'✅ Пинг остановлен в {channel.mention}', delete_after=3)
    else:
        await ctx.send(f'❌ Пинг не был запущен в {channel.mention}', delete_after=3)

# ==================== АВТООТВЕТЧИКИ ====================

@client.command(name='autoreply')
async def autoreply_command(ctx, user_input: str, delay: int, filename: str, *, prefix: str = ''):
    """Автоответ текстом"""
    await ctx.message.delete()
    
    user = await get_user_from_mention_or_id(ctx, user_input)
    if not user:
        await ctx.send('❌ Юзер не найден', delete_after=3)
        return
    
    lines = load_lines_from_file(filename)
    if not lines:
        await ctx.send(f'❌ Файл `{filename}` не найден или пуст', delete_after=3)
        return
    
    us_users[user.id] = {
        'delay': delay,
        'filename': filename,
        'prefix': prefix,
        'lines': lines
    }
    
    await ctx.send(f'✅ Автоответ текстом включен для {user.mention}\n⏱ Задержка: {delay}с\n📁 Файл: {filename}\n🛑 Для остановки: `.autoff {user.id}`', delete_after=5)

@client.command(name='autophoto')
async def autophoto_command(ctx, user_input: str, delay: int, filename: str, media_url: str, *, prefix: str = ''):
    """Автоответ с фото"""
    await ctx.message.delete()
    
    user = await get_user_from_mention_or_id(ctx, user_input)
    if not user:
        await ctx.send('❌ Юзер не найден', delete_after=3)
        return
    
    lines = load_lines_from_file(filename)
    if not lines:
        await ctx.send(f'❌ Файл `{filename}` не найден или пуст', delete_after=3)
        return
    
    usp_users[user.id] = {
        'delay': delay,
        'filename': filename,
        'media_url': media_url,
        'prefix': prefix,
        'lines': lines
    }
    
    await ctx.send(f'✅ Автоответ с фото включен для {user.mention}\n⏱ Задержка: {delay}с\n📁 Файл: {filename}\n🖼 Фото: {media_url}\n🛑 Для остановки: `.autoff {user.id}`', delete_after=5)

@client.command(name='autovideo')
async def autovideo_command(ctx, user_input: str, delay: int, filename: str, media_url: str, *, prefix: str = ''):
    """Автоответ с видео"""
    await ctx.message.delete()
    
    user = await get_user_from_mention_or_id(ctx, user_input)
    if not user:
        await ctx.send('❌ Юзер не найден', delete_after=3)
        return
    
    lines = load_lines_from_file(filename)
    if not lines:
        await ctx.send(f'❌ Файл `{filename}` не найден или пуст', delete_after=3)
        return
    
    usv_users[user.id] = {
        'delay': delay,
        'filename': filename,
        'media_url': media_url,
        'prefix': prefix,
        'lines': lines
    }
    
    await ctx.send(f'✅ Автоответ с видео включен для {user.mention}\n⏱ Задержка: {delay}с\n📁 Файл: {filename}\n🎬 Видео: {media_url}\n🛑 Для остановки: `.autoff {user.id}`', delete_after=5)

@client.command(name='autoff')
async def autoff_command(ctx, user_input: str):
    """Выключить автоответ"""
    await ctx.message.delete()
    
    user = await get_user_from_mention_or_id(ctx, user_input)
    if not user:
        await ctx.send('❌ Юзер не найден', delete_after=3)
        return
    
    removed = False
    for d in [us_users, usp_users, usv_users]:
        if user.id in d:
            del d[user.id]
            removed = True
    
    if removed:
        await ctx.send(f'✅ Автоответ выключен для {user.mention}', delete_after=3)
    else:
        await ctx.send(f'❌ Автоответ не был включен для {user.mention}', delete_after=3)

# ==================== ОБРАБОТЧИК ВХОДЯЩИХ СООБЩЕНИЙ (АВТООТВЕТЫ + AFK) ====================

@client.event
async def on_message(message):
    # Игнорируем свои сообщения и ботов
    if message.author == client.user or message.author.bot:
        return
    
    # AFK ответ
    global afk_enabled, afk_reason, afk_media_url, afk_start_time
    if afk_enabled and message.author.id not in afk_users:
        if isinstance(message.channel, discord.DMChannel):
            now = datetime.now()
            duration = now - afk_start_time
            time_str = f'{duration.days} дн {duration.seconds // 3600} ч {duration.seconds // 60 % 60} мин'
            
            afk_message = f'🚫 Я в AFK\n⏱ Время: {time_str}\n📝 Причина: {afk_reason}'
            
            if afk_media_url and os.path.exists(afk_media_url):
                await message.channel.send(afk_message, file=discord.File(afk_media_url))
            elif afk_media_url:
                await message.channel.send(f"{afk_message}\n{afk_media_url}")
            else:
                await message.channel.send(afk_message)
            
            afk_users.add(message.author.id)
    
    # Автоответ текстом
    if message.author.id in us_users:
        data = us_users[message.author.id]
        now = time.time()
        if message.author.id not in last_reply_time or now - last_reply_time.get(message.author.id, 0) >= data['delay']:
            last_reply_time[message.author.id] = now
            line = random.choice(data['lines'])
            text = f"{data['prefix']} {line}".strip() if data['prefix'] else line
            await asyncio.sleep(data['delay'])
            await message.channel.send(text)
    
    # Автоответ с фото
    if message.author.id in usp_users:
        data = usp_users[message.author.id]
        now = time.time()
        if message.author.id not in last_reply_time_photo or now - last_reply_time_photo.get(message.author.id, 0) >= data['delay']:
            last_reply_time_photo[message.author.id] = now
            line = random.choice(data['lines'])
            text = f"{data['prefix']} {line}".strip() if data['prefix'] else line
            await asyncio.sleep(data['delay'])
            if os.path.exists(data['media_url']):
                await message.channel.send(text, file=discord.File(data['media_url']))
            else:
                await message.channel.send(f"{text}\n{data['media_url']}")
    
    # Автоответ с видео
    if message.author.id in usv_users:
        data = usv_users[message.author.id]
        now = time.time()
        if message.author.id not in last_reply_time_video or now - last_reply_time_video.get(message.author.id, 0) >= data['delay']:
            last_reply_time_video[message.author.id] = now
            line = random.choice(data['lines'])
            text = f"{data['prefix']} {line}".strip() if data['prefix'] else line
            await asyncio.sleep(data['delay'])
            if os.path.exists(data['media_url']):
                await message.channel.send(text, file=discord.File(data['media_url']))
            else:
                await message.channel.send(f"{text}\n{data['media_url']}")
    
    # Обработка команд (префикс .)
    if message.content.startswith('.'):
        await client.process_commands(message)

# ==================== AFK ====================

@client.command(name='afk')
async def afk_command(ctx, action: str = None, *, reason: str = ''):
    """Включить/выключить AFK"""
    global afk_enabled, afk_reason, afk_media_url, afk_start_time
    
    await ctx.message.delete()
    
    if action and action.lower() == 'on':
        afk_enabled = True
        afk_start_time = datetime.now()
        afk_users.clear()
        
        # Парсим причину и URL фото
        parts = reason.split()
        afk_reason = ''
        afk_media_url = ''
        
        for part in parts:
            if part.startswith('http') and (part.endswith(('.jpg', '.png', '.gif', '.jpeg')) or 'discord' in part):
                afk_media_url = part
            else:
                afk_reason += part + ' '
        
        afk_reason = afk_reason.strip() or 'Не указана'
        
        msg = f'✅ AFK включен\n📝 Причина: {afk_reason}'
        if afk_media_url:
            msg += f'\n🖼 Фото: {afk_media_url}'
        await ctx.send(msg, delete_after=5)
    
    elif action and action.lower() == 'off':
        afk_enabled = False
        afk_reason = ''
        afk_media_url = ''
        afk_start_time = None
        afk_users.clear()
        await ctx.send('✅ AFK выключен', delete_after=5)
    
    else:
        await ctx.send('❌ Используй: `.afk on причина [URL фото]` или `.afk off`', delete_after=5)

# ==================== ФАЙЛОВЫЕ КОМАНДЫ ====================

@client.command(name='files')
async def files_command(ctx):
    """Показать все .txt файлы"""
    await ctx.message.delete()
    
    files = [f for f in os.listdir() if f.endswith('.txt') and f not in ['discord_logger.txt', 'deleted_messages_log.txt']]
    
    if files:
        files_text = '\n'.join([f'`{f}`' for f in files])
        msg = f'📁 **Файлы:**\n{files_text}\n\n💾 `.save` (реплай) — сохранить\n🗑 `.unsave файл.txt` — удалить\n📤 `.unload файл.txt` — выгрузить'
    else:
        msg = '📁 Нет .txt файлов'
    
    await ctx.send(msg)

@client.command(name='save')
async def save_command(ctx):
    """Сохранить .txt файл из реплая"""
    await ctx.message.delete()
    
    ref = ctx.message.reference
    if not ref:
        await ctx.send('❌ Нужно ответить (реплай) на сообщение с файлом', delete_after=5)
        return
    
    try:
        replied_msg = await ctx.channel.fetch_message(ref.message_id)
    except:
        await ctx.send('❌ Не могу найти сообщение', delete_after=5)
        return
    
    if not replied_msg.attachments:
        await ctx.send('❌ В сообщении нет вложений', delete_after=5)
        return
    
    attachment = replied_msg.attachments[0]
    if not attachment.filename.endswith('.txt'):
        await ctx.send('❌ Файл должен быть .txt', delete_after=5)
        return
    
    try:
        await attachment.save(attachment.filename)
        await ctx.send(f'✅ Файл `{attachment.filename}` сохранен', delete_after=5)
    except Exception as e:
        await ctx.send(f'❌ Ошибка сохранения: {e}', delete_after=5)

@client.command(name='unsave')
async def unsave_command(ctx, filename: str):
    """Удалить файл"""
    await ctx.message.delete()
    
    if not filename.endswith('.txt'):
        filename += '.txt'
    
    if os.path.exists(filename):
        try:
            os.remove(filename)
            await ctx.send(f'✅ Файл `{filename}` удален', delete_after=5)
        except:
            await ctx.send(f'❌ Ошибка удаления `{filename}`', delete_after=5)
    else:
        await ctx.send(f'❌ Файл `{filename}` не найден', delete_after=5)

@client.command(name='unload')
async def unload_command(ctx, filename: str):
    """Выгрузить файл в чат"""
    await ctx.message.delete()
    
    if not filename.endswith('.txt'):
        filename += '.txt'
    
    if os.path.exists(filename):
        try:
            await ctx.send(f'📤 Файл `{filename}`:', file=discord.File(filename))
        except Exception as e:
            await ctx.send(f'❌ Ошибка выгрузки: {e}', delete_after=5)
    else:
        await ctx.send(f'❌ Файл `{filename}` не найден', delete_after=5)

# ==================== ИНФО КОМАНДЫ ====================

@client.command(name='id')
async def id_command(ctx):
    """Показать ID канала"""
    await ctx.message.delete()
    await ctx.send(f'📌 **Канал:** {ctx.channel.mention}\n🆔 **ID:** `{ctx.channel.id}`', delete_after=10)

@client.command(name='user')
async def user_command(ctx):
    """Показать ID юзера по реплаю"""
    await ctx.message.delete()
    
    ref = ctx.message.reference
    if not ref:
        await ctx.send('❌ Нужно ответить (реплай) на сообщение юзера', delete_after=5)
        return
    
    try:
        replied_msg = await ctx.channel.fetch_message(ref.message_id)
        user = replied_msg.author
        await ctx.send(f'👤 **Юзер:** {user.mention}\n🆔 **ID:** `{user.id}`', delete_after=10)
    except:
        await ctx.send('❌ Не могу найти сообщение', delete_after=5)

@client.command(name='times')
async def times_command(ctx):
    """Время работы бота"""
    await ctx.message.delete()
    
    current_time = datetime.now()
    uptime = current_time - start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_str = f'{days} дн {hours:02d} ч {minutes:02d} мин {seconds:02d} сек'
    await ctx.send(f'⏱ **Аптайм:** `{uptime_str}`', delete_after=10)

# ==================== КАСТОМИЗАЦИЯ ====================

@client.command(name='title')
async def title_command(ctx, *, new_name: str):
    """Сменить имя бота в меню"""
    global namebot
    namebot = new_name
    await ctx.message.delete()
    await ctx.send(f'✅ Имя бота изменено на: **{namebot}**', delete_after=5)

@client.command(name='link')
async def link_command(ctx, url: str):
    """Сменить фото в меню (локальный путь или URL)"""
    global media_menu
    media_menu = url
    await ctx.message.delete()
    await ctx.send(f'✅ Фото меню изменено', delete_after=5)

# ==================== ЗАПУСК С АВТОРЕСТАРТОМ ====================

@client.event
async def on_ready():
    print(f"""
╔══════════════════════════════════════╗
║     DISCORD HELPER SELF-BOT          ║
╠══════════════════════════════════════╣
║  Залогинен как: {client.user}
║  ID: {client.user.id}
║  Серверов: {len(client.guilds)}
║  Время запуска: {datetime.now().strftime('%H:%M:%S')}
╠══════════════════════════════════════╣
║  Команды: .help
╚══════════════════════════════════════╝
    """)

async def main():
    while True:
        try:
            await client.start(token, bot=False)
        except discord.LoginFailure:
            print('❌ Неверный токен! Удали settings/discord_token.txt и перезапусти')
            os.remove('settings/discord_token.txt')
            input('Нажми Enter для выхода...')
            break
        except Exception as e:
            logging.error(f'Ошибка: {e}')
            print(f'⚠️ Ошибка: {e}')
            print(f'🔄 Перезапуск через {RESTART_DELAY} сек...')
            await asyncio.sleep(RESTART_DELAY)
            os.execv(sys.executable, ['python'] + sys.argv)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n👋 Выход...')