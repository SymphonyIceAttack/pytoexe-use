input("Нажми Enter для старта...")

import asyncio
import os
import sys
import re
import traceback
from telethon import TelegramClient, events
from telethon.errors import UsernameNotOccupiedError, UsernameInvalidError
from colorama import Fore, init

init(autoreset=True)

# ================= НАСТРОЙКИ =================
API_ID = 1234567
API_HASH = "API_HASH"
REPEAT_COUNT = 1000
SEARCH_LIMIT = 5
# ============================================

BASE_DIR = os.path.dirname(
    sys.executable if getattr(sys, "frozen", False)
    else os.path.abspath(__file__)
)
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")

block_pattern = re.compile(
    r"(Мы временно ограничили|"
    r"Доступ к чату временно ограничен|"
    r"Сообщения отправлять нельзя|"
    r"Вы временно заблокированы|"
    r"\bлимит\b|\bжалоб\b|\bограничить\b)",
    re.IGNORECASE
)

SEARCH_TEXT = re.compile(r"ищем собеседника", re.IGNORECASE)

AGE_REQUEST_PATTERN = re.compile(
    r"(введите ваш возраст|неправильный возраст|возраст)",
    re.IGNORECASE
)


class ChatBlocked(Exception):
    pass


class SearchStuck(Exception):
    pass


def safe_print(text):
    try:
        print(text)
    except:
        pass


def extract_number(name):
    m = re.search(r"\d+", name)
    return int(m.group()) if m else 0


async def run_account(session_path, target_chat, custom_word):
    session_name = os.path.basename(session_path)
    client = TelegramClient(session_path, API_ID, API_HASH)

    block_event = asyncio.Event()
    search_event = asyncio.Event()
    search_counter = 0

    try:
        await client.start()

        if not await client.is_user_authorized():
            safe_print(f"{Fore.RED}❌ НЕ АВТОРИЗОВАН: {session_name}")
            return

        try:
            entity = await client.get_entity(target_chat)
        except (UsernameNotOccupiedError, UsernameInvalidError, ValueError):
            safe_print(f"{Fore.RED}❌ ЧАТ НЕ НАЙДЕН: {target_chat}")
            return

        me = await client.get_me()
        safe_print(f"{Fore.GREEN}✅ {me.id} → {target_chat}")

        @client.on(events.NewMessage(chats=entity))
        async def handler(event):
            nonlocal search_counter

            text = event.text or ""
            safe_print(f"{Fore.CYAN}[CHAT] {text}")

            if block_pattern.search(text):
                block_event.set()

            if SEARCH_TEXT.search(text):
                search_counter += 1
                safe_print(f"{Fore.YELLOW}[SEARCH] {search_counter}/{SEARCH_LIMIT}")
                if search_counter >= SEARCH_LIMIT:
                    search_event.set()
            else:
                search_counter = 0

            if event.buttons and AGE_REQUEST_PATTERN.search(text):
                for row in event.buttons:
                    for btn in row:
                        btn_text = (btn.text or "").lower()
                        if any(x in btn_text for x in [
                            "удалить возраст",
                            "не сейчас",
                            "delete age",
                            "remove age",
                            "dont ask"
                        ]):
                            safe_print(f"{Fore.MAGENTA}[BTN] Нажимаю: {btn.text}")
                            await event.click(btn)
                            return

        for _ in range(REPEAT_COUNT):
            if block_event.is_set():
                raise ChatBlocked

            if search_event.is_set():
                raise SearchStuck

            await client.send_message(entity, f"д15, пoмoчь кончить - {custom_word}")
            await asyncio.sleep(1)

            await client.send_message(entity, "пиши")
            await asyncio.sleep(0.3)

            await client.send_message(entity, "/next")
            await asyncio.sleep(4.5)

    finally:
        await client.disconnect()
        safe_print(f"{Fore.YELLOW}[-] Сессия закрыта: {session_name}")


async def main():
    chats_input = input("Введи юзернеймы чатов через запятую:\n> ").strip()
    TARGET_CHATS = [c.strip() for c in chats_input.split(",") if c.strip()]
    if not TARGET_CHATS:
        safe_print("❌ Чаты не указаны")
        return

    custom_word = input("Текст первого сообщения:\n> ").strip()
    if not custom_word:
        safe_print("❌ Пустой текст")
        return

    if not os.path.exists(SESSIONS_DIR):
        safe_print("❌ Папка sessions не найдена")
        return

    sessions = sorted(
        [
            os.path.join(SESSIONS_DIR, f)
            for f in os.listdir(SESSIONS_DIR)
            if f.endswith(".session")
        ],
        key=lambda x: extract_number(os.path.basename(x))
    )

    if not sessions:
        safe_print("❌ Нет session файлов")
        return

    safe_print(f"{Fore.GREEN}🚀 Аккаунтов: {len(sessions)} | Чатов: {len(TARGET_CHATS)}")

    for session in sessions:
        safe_print(f"\n{Fore.CYAN}👤 Аккаунт: {os.path.basename(session)}")

        for chat in TARGET_CHATS:
            safe_print(f"{Fore.YELLOW}▶ {chat}")

            try:
                await run_account(session, chat, custom_word)
            except ChatBlocked:
                safe_print(f"{Fore.RED}🚫 БЛОК — следующий чат")
            except SearchStuck:
                safe_print(f"{Fore.MAGENTA}🔁 ЗАВИС ПОИСК — следующий чат")

            await asyncio.sleep(2)

        safe_print(f"{Fore.GREEN}✅ Аккаунт завершил все чаты")
        await asyncio.sleep(3)


if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except Exception:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
