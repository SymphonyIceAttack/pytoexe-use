#!usrbinenv python
# -- coding utf-8 --


Game Blocker с управлением через Telegram
Версия для Python 3.6+


import os
import sys
import time
import json
import psutil
import threading
import requests
import schedule
from datetime import datetime, timedelta
from pathlib import Path
import winreg
import ctypes
import ctypes.wintypes
import socket
import struct

# ==================== НАСТРОЙКИ ПРОГРАММЫ ====================

# Время блокировки по умолчанию (с 1600 до 1800)
BLOCK_START_HOUR = 16  # Час начала блокировки
BLOCK_END_HOUR = 18    # Час окончания блокировки

# Как часто проверять запущенные игры (в секундах)
CHECK_INTERVAL = 5

# Имя программы (используется для автозагрузки и логов)
APP_NAME = GameBlocker

# Путь к папке для логов
LOG_PATH = Path(os.environ.get('LOCALAPPDATA', '.'))  APP_NAME  'log.txt'

# ==================== НАСТРОЙКИ TELEGRAM ====================
# ВАЖНО Замените эти значения на свои!

# Токен бота - получить у @BotFather в Telegram
# Пример 1234567890ABCdefGHIjklMNOpqrsTUVwxyz
BOT_TOKEN = YOUR_BOT_TOKEN_HERE

# Ваш личный Telegram ID - узнать у @userinfobot
# Пример 123456789
ALLOWED_USER_ID = YOUR_TELEGRAM_ID

# ==================== СПИСОК ИГР ====================
# Добавляйте сюда названия процессов игр, которые нужно блокировать
# Названия должны быть такими же, как в диспетчере задач
GAME_PROCESSES = [
    # Популярные игры
    steam.exe,                    # Сам Steam (клиент)
    csgo.exe, cs2.exe,           # Counter-Strike
    dota2.exe,                     # Dota 2
    hl2.exe,                        # Half-Life 2 и игры на его движке
    portal2.exe,                    # Portal 2
    tf2.exe,                        # Team Fortress 2
    rust.exe,                       # Rust
    pubg.exe, tslgame.exe,        # PUBG
    rocketleague.exe,                # Rocket League
    cyberpunk2077.exe,               # Cyberpunk 2077
    eldenring.exe,                    # Elden Ring
    witcher3.exe,                     # Ведьмак 3
    gta5.exe,                         # GTA 5
    rdr2.exe,                         # Red Dead Redemption 2
    minecraft.exe,                    # Minecraft
    valorant.exe,                     # Valorant
    leagueoflegends.exe,               # League of Legends
    fortnite.exe,                      # Fortnite
    amongus.exe,                       # Among Us
    discord.exe,                       # Дискорд (общение в играх)
    
    # Epic Games Store
    epicgameslauncher.exe,
    fortniteclient-win64-shipping.exe,
    
    # Другие лаунчеры
    origin.exe,
    battlenet.exe,
    ubisoftconnect.exe,
    
    # Можно добавить свои игры
    # game.exe,
    # launcher.exe,
]


# ==================== КЛАСС ДЛЯ ХРАНЕНИЯ СОСТОЯНИЯ ====================
class BlockState
    Класс для хранения состояния блокировки
    
    def __init__(self)
        self.is_enabled = True           # Включена ли блокировка вообще
        self.custom_start_hour = 16       # Свой час начала
        self.custom_end_hour = 18         # Свой час окончания
        self.use_custom_time = False      # Использовать ли свое время
        self.block_until = 0              # Блокировка до указанного времени (timestamp)
        self.last_command =              # Последняя выполненная команда
        
    def to_dict(self)
        Преобразует состояние в словарь для сохранения
        return {
            'is_enabled' self.is_enabled,
            'custom_start_hour' self.custom_start_hour,
            'custom_end_hour' self.custom_end_hour,
            'use_custom_time' self.use_custom_time,
            'block_until' self.block_until,
        }
    
    def from_dict(self, data)
        Загружает состояние из словаря
        self.is_enabled = data.get('is_enabled', True)
        self.custom_start_hour = data.get('custom_start_hour', 16)
        self.custom_end_hour = data.get('custom_end_hour', 18)
        self.use_custom_time = data.get('use_custom_time', False)
        self.block_until = data.get('block_until', 0)


# ==================== КЛАСС ДЛЯ ЛОГИРОВАНИЯ ====================
class Logger
    Класс для записи логов в файл
    
    @staticmethod
    def log(message)
        Записывает сообщение в лог-файл
        try
            # Создаем папку если её нет
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # Получаем текущее время
            now = datetime.now().strftime(%Y-%m-%d %H%M%S)
            
            # Записываем в файл
            with open(LOG_PATH, 'a', encoding='utf-8') as f
                f.write(f[{now}] {message}n)
                
        except Exception as e
            print(fОшибка записи в лог {e})


# ==================== КЛАСС ДЛЯ РАБОТЫ С TELEGRAM ====================
class TelegramBot
    Класс для взаимодействия с Telegram Bot API
    
    def __init__(self, token, allowed_user_id)
        self.token = token
        self.allowed_user_id = allowed_user_id
        self.base_url = fhttpsapi.telegram.orgbot{token}
        self.last_update_id = 0
        self.running = True
        
    def send_message(self, text, parse_mode='Markdown')
        
        Отправляет сообщение в Telegram
        parse_mode 'Markdown' или 'HTML'
        
        try
            url = f{self.base_url}sendMessage
            data = {
                'chat_id' self.allowed_user_id,
                'text' text,
                'parse_mode' parse_mode
            }
            response = requests.post(url, data=data, timeout=10)
            return response.json()
        except Exception as e
            Logger.log(fОшибка отправки сообщения {e})
            return None
    
    def get_updates(self)
        Получает новые сообщения от Telegram
        try
            url = f{self.base_url}getUpdates
            data = {
                'offset' self.last_update_id + 1,
                'timeout' 5,
                'allowed_updates' ['message']
            }
            response = requests.get(url, params=data, timeout=10)
            updates = response.json()
            
            if updates.get('ok')
                for update in updates.get('result', [])
                    self.last_update_id = update['update_id']
                    yield update
        except Exception as e
            Logger.log(fОшибка получения обновлений {e})
    
    def process_commands(self, state, game_blocker)
        Обрабатывает входящие команды
        for update in self.get_updates()
            if 'message' not in update
                continue
                
            message = update['message']
            chat_id = str(message['chat']['id'])
            
            # Проверяем, что сообщение от разрешенного пользователя
            if chat_id != self.allowed_user_id
                self.send_message(⛔ У вас нет прав на управление этим ботом)
                continue
            
            # Получаем текст команды
            if 'text' not in message
                continue
                
            text = message['text'].strip()
            Logger.log(fПолучена команда {text})
            
            # Разбираем команду
            parts = text.split()
            command = parts[0].lower()
            
            # Убираем упоминание бота если есть (для групповых чатов)
            if '@' in command
                command = command.split('@')[0]
            
            # ===== ОБРАБОТКА КОМАНД =====
            
            # start или help - показать справку
            if command in ['start', 'help']
                response = self._get_help_message()
                
            # status - показать текущий статус
            elif command == 'status'
                response = self._get_status_message(state)
                
            # on - включить блокировку
            elif command == 'on'
                state.is_enabled = True
                response = ✅ Блокировка включенаnТеперь игры будут закрываться по расписанию
                
            # off - выключить блокировку
            elif command == 'off'
                state.is_enabled = False
                state.block_until = 0
                response = ❌ Блокировка выключенаnИгры больше не будут закрываться
                
            # time HH MM - установить свое время
            elif command == 'time' and len(parts) = 3
                try
                    hour = int(parts[1])
                    minute = int(parts[2])
                    
                    if 0 = hour  24 and 0 = minute  60
                        state.custom_start_hour = hour
                        state.custom_end_hour = minute
                        state.use_custom_time = True
                        
                        response = f✅ Установлено свое времяn
                        response += fБлокировка будет работать до {hour02d}{minute02d}
                    else
                        response = ❌ Неверный форматnЧасы 0-23, минуты 0-59
                except ValueError
                    response = ❌ Неверный форматnИспользуйте `time ЧЧ ММ`
                    
            # reset - сбросить на стандартное время
            elif command == 'reset'
                state.use_custom_time = False
                response = ✅ Сброшено на стандартное времяnБлокировка 1600 - 1800
                
            # block N - заблокировать на N минут
            elif command == 'block' and len(parts) = 2
                try
                    minutes = int(parts[1])
                    if minutes  0
                        state.block_until = time.time() + (minutes  60)
                        state.is_enabled = True
                        
                        response = f⏳ Временная блокировкаn
                        response += fИгры заблокированы на {minutes} минутn
                        
                        # Показываем время окончания
                        end_time = datetime.fromtimestamp(state.block_until).strftime(%H%M)
                        response += fДо {end_time}
                    else
                        response = ❌ Количество минут должно быть больше 0
                except ValueError
                    response = ❌ Неверный форматnИспользуйте `block N` (N - минуты)
                    
            # unblock - снять временную блокировку
            elif command == 'unblock'
                state.block_until = 0
                response = ✅ Временная блокировка снятаnВозврат к обычному расписанию
                
            # list - показать список игр
            elif command == 'list'
                response = self._get_games_list()
                
            # stats - показать статистику
            elif command == 'stats'
                response = self._get_stats_message(game_blocker)
                
            # killnow - принудительно закрыть все игры сейчас
            elif command == 'killnow'
                killed = game_blocker.kill_all_games()
                response = f🔫 Принудительное закрытиеnЗавершено игр {killed}
                
            # mute - отключить уведомления
            elif command == 'mute'
                game_blocker.mute_notifications = True
                response = 🔇 Уведомления отключены
                
            # unmute - включить уведомления
            elif command == 'unmute'
                game_blocker.mute_notifications = False
                response = 🔊 Уведомления включены
                
            # Неизвестная команда
            else
                response = ❌ Неизвестная командаnНапишите help для списка команд
            
            # Отправляем ответ
            self.send_message(response)
            
            # Сохраняем состояние
            game_blocker.save_state()
    
    def _get_help_message(self)
        Формирует справочное сообщение
        help_text = 🤖 Game Blocker Botnn
        help_text += Управление блокировкой игр на компьютереnn
        help_text += Доступные командыn
        help_text += ├ status - текущий статусn
        help_text += ├ on - включить блокировкуn
        help_text += ├ off - выключить блокировкуn
        help_text += ├ time `ЧЧ ММ` - установить свое времяn
        help_text += │  пример `time 20 00` (до 2000)n
        help_text += ├ reset - сбросить на 1600-1800n
        help_text += ├ block `N` - заблокировать на N минутn
        help_text += │  пример `block 30` (на полчаса)n
        help_text += ├ unblock - снять временную блокировкуn
        help_text += ├ list - список отслеживаемых игрn
        help_text += ├ stats - статистика работыn
        help_text += ├ mute - отключить уведомленияn
        help_text += ├ unmute - включить уведомленияn
        help_text += └ killnow - закрыть все игры сейчас
        return help_text
    
    def _get_status_message(self, state)
        Формирует сообщение со статусом
        # Определяем текущее состояние
        is_block_time = self._is_block_time(state)
        
        status_text = 📊 Текущий статусnn
        status_text += fБлокировка {'✅ ВКЛЮЧЕНА' if state.is_enabled else '❌ ВЫКЛЮЧЕНА'}n
        
        # Если есть временная блокировка
        if state.block_until  0
            remaining = int((state.block_until - time.time())  60)
            if remaining  0
                status_text += f⏳ Временная блокировка {remaining} минn
        
        # Расписание
        if state.use_custom_time
            status_text += f⏰ Свое расписание {state.custom_start_hour02d}00 - {state.custom_end_hour02d}00n
        else
            status_text += ⏰ Стандартное расписание 1600 - 1800n
        
        # Текущее состояние
        status_text += f⚡ Сейчас {'АКТИВНО' if is_block_time else 'ОЖИДАНИЕ'}
        
        return status_text
    
    def _get_games_list(self)
        Формирует список игр
        text = 🎮 Отслеживаемые игрыnn
        
        # Разбиваем на колонки для удобства чтения
        for i, game in enumerate(GAME_PROCESSES, 1)
            text += f`{game}`n
            if i % 5 == 0
                text += n
        
        text += fnВсего {len(GAME_PROCESSES)} игр
        return text
    
    def _get_stats_message(self, game_blocker)
        Формирует статистику
        # Получаем запущенные игры
        running_games = game_blocker.get_running_games()
        
        # Получаем время работы системы (Windows)
        uptime_seconds = self._get_system_uptime()
        uptime_hours = uptime_seconds  3600
        
        stats = 📈 Статистикаnn
        stats += fВсего игр в списке {len(GAME_PROCESSES)}n
        stats += fСейчас запущено игр {len(running_games)}n
        
        if running_games
            stats += nЗапущенные игрыn
            for game in running_games[5]  # Показываем первые 5
                stats += f├ {game}n
            if len(running_games)  5
                stats += f└ ...и еще {len(running_games) - 5}n
        
        stats += fn⏱ Время работы ПК {uptime_hours.1f} часов
        
        return stats
    
    def _is_block_time(self, state)
        Проверяет, время ли блокировки сейчас
        if not state.is_enabled
            return False
        
        now = datetime.now()
        
        # Проверяем временную блокировку
        if state.block_until  0
            if time.time()  state.block_until
                return True
            else
                state.block_until = 0
        
        # Проверяем по расписанию
        current_hour = now.hour
        
        if state.use_custom_time
            return state.custom_start_hour = current_hour  state.custom_end_hour
        else
            return BLOCK_START_HOUR = current_hour  BLOCK_END_HOUR
    
    def _get_system_uptime(self)
        Получает время работы системы в секундах (Windows)
        try
            kernel32 = ctypes.windll.kernel32
            tick = kernel32.GetTickCount64()
            return tick  1000
        except
            return 0


# ==================== ОСНОВНОЙ КЛАСС БЛОКИРОВЩИКА ====================
class GameBlocker
    Главный класс программы
    
    def __init__(self)
        self.state = BlockState()
        self.bot = None
        self.running = True
        self.last_notification_time = 0
        self.mute_notifications = False
        self.games_killed_today = 0
        
        # Загружаем сохраненное состояние
        self.load_state()
        
        # Создаем папки
        self._create_directories()
        
        # Добавляем в автозагрузку при первом запуске
        if not self.is_in_startup()
            self.add_to_startup()
    
    def _create_directories(self)
        Создает необходимые папки
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    def load_state(self)
        Загружает состояние из файла
        state_file = LOG_PATH.parent  'state.json'
        if state_file.exists()
            try
                with open(state_file, 'r', encoding='utf-8') as f
                    data = json.load(f)
                    self.state.from_dict(data)
                Logger.log(Состояние загружено)
            except Exception as e
                Logger.log(fОшибка загрузки состояния {e})
    
    def save_state(self)
        Сохраняет состояние в файл
        state_file = LOG_PATH.parent  'state.json'
        try
            with open(state_file, 'w', encoding='utf-8') as f
                json.dump(self.state.to_dict(), f, indent=2)
        except Exception as e
            Logger.log(fОшибка сохранения состояния {e})
    
    def is_block_time(self)
        Проверяет, время ли блокировки сейчас
        if not self.state.is_enabled
            return False
        
        now = datetime.now()
        
        # Проверяем временную блокировку
        if self.state.block_until  0
            if time.time()  self.state.block_until
                return True
            else
                self.state.block_until = 0
                self.save_state()
        
        # Проверяем по расписанию
        current_hour = now.hour
        
        if self.state.use_custom_time
            return self.state.custom_start_hour = current_hour  self.state.custom_end_hour
        else
            return BLOCK_START_HOUR = current_hour  BLOCK_END_HOUR
    
    def get_running_games(self)
        Возвращает список запущенных игр
        running = []
        
        try
            for proc in psutil.process_iter(['name', 'pid'])
                try
                    proc_name = proc.info['name'].lower()
                    
                    # Проверяем, есть ли процесс в списке игр
                    for game in GAME_PROCESSES
                        if game.lower() in proc_name
                            running.append({
                                'name' proc.info['name'],
                                'pid' proc.info['pid']
                            })
                            break
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied)
                    pass
                    
        except Exception as e
            Logger.log(fОшибка при получении списка процессов {e})
        
        return running
    
    def kill_game(self, proc_info)
        Завершает один игровой процесс
        try
            proc = psutil.Process(proc_info['pid'])
            proc.terminate()  # Пытаемся завершить мягко
            time.sleep(1)
            
            if proc.is_running()
                proc.kill()  # Если не завершился - убиваем принудительно
            
            self.games_killed_today += 1
            Logger.log(fИгра закрыта {proc_info['name']} (PID {proc_info['pid']}))
            
            return True
            
        except Exception as e
            Logger.log(fОшибка при завершении {proc_info['name']} {e})
            return False
    
    def kill_all_games(self)
        Завершает все игровые процессы (принудительно)
        killed = 0
        games = self.get_running_games()
        
        for game in games
            if self.kill_game(game)
                killed += 1
        
        return killed
    
    def check_and_kill_games(self)
        Проверяет игры и завершает если нужно
        if not self.is_block_time()
            return
        
        games = self.get_running_games()
        
        for game in games
            # Не завершаем самого себя (хотя мы не в списке игр)
            if game['name'].lower() == 'python.exe'
                continue
                
            if self.kill_game(game)
                # Отправляем уведомление в Telegram (не чаще раза в минуту)
                if not self.mute_notifications and self.bot
                    now = time.time()
                    if now - self.last_notification_time  60
                        msg = f⚠️ Игра {game['name']} была закрыта.n
                        
                        if self.state.block_until  0
                            remaining = int((self.state.block_until - now)  60)
                            msg += f⏳ Осталось {remaining} минут
                        else
                            msg += ⏰ Текущее время в блокировке
                        
                        self.bot.send_message(msg)
                        self.last_notification_time = now
    
    def monitor_loop(self)
        Основной цикл мониторинга
        Logger.log(Мониторинг запущен)
        
        while self.running
            try
                self.check_and_kill_games()
                time.sleep(CHECK_INTERVAL)
            except Exception as e
                Logger.log(fОшибка в цикле мониторинга {e})
                time.sleep(CHECK_INTERVAL)
    
    # ===== ФУНКЦИИ ДЛЯ АВТОЗАГРУСКИ =====
    
    def add_to_startup(self)
        Добавляет программу в автозагрузку через реестр
        try
            # Получаем путь к текущему скрипту
            if getattr(sys, 'frozen', False)
                # Если скомпилировано в .exe
                exe_path = sys.executable
            else
                # Если запущено как .py
                exe_path = f'{sys.executable} {os.path.abspath(__file__)}'
            
            # Открываем ключ автозагрузки
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                rSoftwareMicrosoftWindowsCurrentVersionRun,
                0, winreg.KEY_SET_VALUE
            )
            
            # Добавляем значение
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            
            Logger.log(Добавлено в автозагрузку)
            
        except Exception as e
            Logger.log(fОшибка добавления в автозагрузку {e})
    
    def remove_from_startup(self)
        Удаляет программу из автозагрузки
        try
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                rSoftwareMicrosoftWindowsCurrentVersionRun,
                0, winreg.KEY_SET_VALUE
            )
            
            winreg.DeleteValue(key, APP_NAME)
            winreg.CloseKey(key)
            
            Logger.log(Удалено из автозагрузки)
            
        except Exception as e
            Logger.log(fОшибка удаления из автозагрузки {e})
    
    def is_in_startup(self)
        Проверяет, есть ли программа в автозагрузке
        try
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                rSoftwareMicrosoftWindowsCurrentVersionRun,
                0, winreg.KEY_READ
            )
            
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
            
        except FileNotFoundError
            return False
        except Exception as e
            Logger.log(fОшибка проверки автозагрузки {e})
            return False
    
    # ===== ФУНКЦИИ ДЛЯ ТРЕЯ (опционально) =====
    
    def setup_tray(self)
        Настраивает иконку в трее (требуется библиотека pystray)
        try
            from PIL import Image, ImageDraw
            import pystray
            
            # Создаем простую иконку
            def create_image()
                width = 64
                height = 64
                image = Image.new('RGB', (width, height), color='red')
                dc = ImageDraw.Draw(image)
                dc.rectangle([width4, height4, width34, height34], fill='white')
                return image
            
            # Функция при клике
            def on_click(icon, item)
                if str(item) == Выход
                    self.running = False
                    icon.stop()
                elif str(item) == Статус
                    status = Активен if self.is_block_time() else Ожидание
                    icon.notify(fСтатус {status}, APP_NAME)
                elif str(item) == ВклВыкл
                    self.state.is_enabled = not self.state.is_enabled
                    self.save_state()
                    icon.notify(fБлокировка {'включена' if self.state.is_enabled else 'выключена'}, APP_NAME)
            
            # Создаем меню
            menu = pystray.Menu(
                pystray.MenuItem(Статус, on_click),
                pystray.MenuItem(ВклВыкл, on_click),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(Выход, on_click)
            )
            
            # Создаем иконку
            icon = pystray.Icon(APP_NAME, create_image(), APP_NAME, menu)
            
            # Запускаем в отдельном потоке
            threading.Thread(target=icon.run, daemon=True).start()
            
        except ImportError
            Logger.log(pystray не установлен - иконка в трее не будет показана)
        except Exception as e
            Logger.log(fОшибка настройки трея {e})


# ==================== ФУНКЦИЯ ДЛЯ ПРОВЕРКИ НАСТРОЕК ====================
def check_config()
    Проверяет, заполнены ли настройки Telegram
    if BOT_TOKEN == YOUR_BOT_TOKEN_HERE or ALLOWED_USER_ID == YOUR_TELEGRAM_ID
        print(=  60)
        print(⚠️  НЕ ЗАПОЛНЕНЫ НАСТРОЙКИ TELEGRAM!)
        print(=  60)
        print(nЧтобы программа работала, нужно)
        print(n1. Написать @BotFather в Telegram)
        print(2. Создать нового бота командой newbot)
        print(3. Скопировать токен (пример 123456ABCdef))
        print(4. Написать @userinfobot и узнать свой ID)
        print(5. Вставить их в код (строки 25-26))
        print(nПосле этого запустите программу снова.)
        print(=  60)
        
        # Показываем окно с сообщением
        ctypes.windll.user32.MessageBoxW(
            0,
            Не заполнены настройки Telegram!nn
            1. Напишите @BotFather в Telegramn
            2. Создайте бота командой newbotn
            3. Скопируйте токенn
            4. Напишите @userinfobot и узнайте свой IDn
            5. Вставьте их в код (строки 25-26),
            Ошибка конфигурации,
            0x10  0x0  # MB_ICONERROR  MB_OK
        )
        return False
    return True


# ==================== ФУНКЦИЯ ДЛЯ ЗАПУСКА КАК СЛУЖБЫ ====================
def run_as_service()
    Запускает программу в фоновом режиме (без консоли)
    # Скрываем консольное окно
    wh = ctypes.windll.kernel32.GetConsoleWindow()
    if wh
        ctypes.windll.user32.ShowWindow(wh, 0)  # SW_HIDE
    
    # Запускаем основную программу
    main()


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================
def main()
    Главная функция программы
    
    # Проверяем настройки
    if not check_config()
        input(Нажмите Enter для выхода...)
        sys.exit(1)
    
    # Проверяем, не запущена ли уже программа
    try
        import win32event
        import win32api
        import winerror
        
        mutex = win32event.CreateMutex(None, False, GlobalGameBlockerMutex)
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS
            print(Программа уже запущена!)
            ctypes.windll.user32.MessageBoxW(0, Программа уже запущена!, APP_NAME, 0)
            sys.exit(0)
    except ImportError
        Logger.log(win32event не найден - проверка единственного экземпляра отключена)
    
    # Создаем блокировщик
    blocker = GameBlocker()
    
    # Создаем Telegram бота
    bot = TelegramBot(BOT_TOKEN, ALLOWED_USER_ID)
    blocker.bot = bot
    
    # Отправляем сообщение о запуске
    bot.send_message(🟢 Game Blocker запущенnКомпьютер под контролем)
    
    # Настраиваем иконку в трее (опционально)
    try
        blocker.setup_tray()
    except
        pass
    
    # Запускаем поток для обработки команд Telegram
    def telegram_worker()
        while blocker.running
            try
                bot.process_commands(blocker.state, blocker)
                time.sleep(1)
            except Exception as e
                Logger.log(fОшибка в Telegram потоке {e})
                time.sleep(5)
    
    telegram_thread = threading.Thread(target=telegram_worker, daemon=True)
    telegram_thread.start()
    
    # Запускаем основной цикл мониторинга
    try
        blocker.monitor_loop()
    except KeyboardInterrupt
        Logger.log(Получен сигнал остановки)
    finally
        # Отправляем сообщение о завершении
        bot.send_message(🔴 Game Blocker остановлен)
        blocker.running = False
        Logger.log(Программа завершена)


# ==================== ТОЧКА ВХОДА ====================
if __name__ == __main__
    # Проверяем аргументы командной строки
    if len(sys.argv)  1
        if sys.argv[1] == --install
            # Установка в автозагрузку
            blocker = GameBlocker()
            blocker.add_to_startup()
            print(✅ Программа добавлена в автозагрузку)
            sys.exit(0)
        elif sys.argv[1] == --remove
            # Удаление из автозагрузки
            blocker = GameBlocker()
            blocker.remove_from_startup()
            print(✅ Программа удалена из автозагрузки)
            sys.exit(0)
        elif sys.argv[1] == --service
            # Запуск как служба (без окна)
            run_as_service()
            sys.exit(0)
    
    # Запуск в обычном режиме
    main()