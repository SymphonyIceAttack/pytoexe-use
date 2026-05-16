import asyncio
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
import pyperclip
import os
import json
import re
import random
from telethon import errors, TelegramClient, events

API_ID = 31383707
API_HASH = "b217042cd944a335b4a715c45c4fe135"
SESSION_FILE = "nexus_user.session"
HASH_FILE = "nexus_hash.json"
MESSAGES_BACKUP_FILE = "messages_backup.json"
AUTO_REPLY_FILE = "auto_reply_config.json"

DEFAULT_MESSAGES = [
    "привет надо роботу?",
    "ворк надо?",
    "ку ворк интересует?",
    "надо работу?",
    "привет тебе ворк надо?",
    "надо тебе подзаработать?"
]

DEFAULT_AUTO_REPLY = "Доброго дня! Ми шукаємо людей на підробіток. Відгукніться, якщо цікаво."


class NexusLogin:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.root.title("NEXUS | АВТОРИЗАЦІЯ")
        self.root.geometry("500x450")
        self.root.configure(bg='#0a0a0a')
        self.phone_code_hash = None
        self.current_phone = None
        self.setup_ui()

    def setup_ui(self):
        main = tk.Frame(self.root, bg='#0a0a0a')
        main.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        tk.Label(main, text="🔐 NEXUS AUTH", font=('Courier New', 20, 'bold'),
                bg='#0a0a0a', fg='#ff00cc').pack(pady=10)

        tk.Label(main, text="📞 ТВІЙ НОМЕР ТЕЛЕФОНУ", bg='#0a0a0a', fg='#00ffcc').pack(anchor=tk.W)
        self.phone_entry = ttk.Entry(main, width=35)
        self.phone_entry.pack(fill=tk.X, pady=5)
        self.phone_entry.insert(0, "+380")

        tk.Label(main, text="🔑 КОД ПІДТВЕРДЖЕННЯ", bg='#0a0a0a', fg='#00ffcc').pack(anchor=tk.W)
        self.code_entry = ttk.Entry(main, width=35)
        self.code_entry.pack(fill=tk.X, pady=5)

        self.send_btn = tk.Button(main, text="📨 ЗАПИТАТИ КОД", command=self.send_code,
                                  bg='#ffaa00', fg='black', relief=tk.FLAT, pady=5)
        self.send_btn.pack(pady=5)

        self.login_btn = tk.Button(main, text="🚀 УВІЙТИ", command=self.do_login,
                                   bg='#00ff88', fg='black', relief=tk.FLAT, pady=5)
        self.login_btn.pack(pady=5)

        self.status = tk.Label(main, text="", bg='#0a0a0a', fg='#ff4444')
        self.status.pack()

        self.log_area = scrolledtext.ScrolledText(main, height=8, bg='#0f0f0f', fg='#00ffcc')
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=10)
        self.log("⚡ NEXUS AUTH READY")

    def log(self, msg):
        self.log_area.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)

    def send_code(self):
        phone = self.phone_entry.get().strip()
        if not phone or phone == "+380":
            self.status.config(text="❌ ВВЕДИ НОМЕР")
            return
        self.status.config(text="⏳ НАДСИЛАЄМО...")
        self.send_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._send_code_thread, args=(phone,), daemon=True).start()

    def _send_code_thread(self, phone):
        async def send():
            client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
            await client.connect()
            try:
                result = await client.send_code_request(phone)
                self.phone_code_hash = result.phone_code_hash
                self.current_phone = phone
                with open(HASH_FILE, 'w') as f:
                    json.dump({"phone": phone, "hash": self.phone_code_hash}, f)
                self.log(f"✅ Код надіслано на {phone}")
                self.root.after(0, lambda: self.status.config(text="✅ Код надіслано, перевір Telegram", fg='#00ffcc'))
            except Exception as err:
                self.log(f"❌ ПОМИЛКА: {err}")
                self.root.after(0, lambda: self.status.config(text=f"❌ {err}", fg='#ff4444'))
            finally:
                await client.disconnect()
                self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL))
        asyncio.run(send())

    def do_login(self):
        code = self.code_entry.get().strip()
        if not code:
            self.status.config(text="❌ ВВЕДИ КОД")
            return
        if os.path.exists(HASH_FILE):
            with open(HASH_FILE, 'r') as f:
                data = json.load(f)
                self.phone_code_hash = data.get("hash")
                self.current_phone = data.get("phone")
        if not self.phone_code_hash:
            self.status.config(text="❌ СПОЧАТКУ ЗАПИТАЙ КОД")
            return
        self.status.config(text="⏳ ВХІД...")
        self.login_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._login_thread, args=(code,), daemon=True).start()

    def _login_thread(self, code):
        async def login():
            client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
            await client.connect()
            try:
                await client.sign_in(phone=self.current_phone, code=code, phone_code_hash=self.phone_code_hash)
                self.log("✅ ВХІД УСПІШНИЙ")
                self.root.after(0, lambda: self.status.config(text="✅ ВХІД ВИКОНАНО!"))
                await client.disconnect()
                self.root.after(0, self.on_success)
            except errors.PhoneCodeExpiredError:
                self.log("❌ КОД ЗАСТАРІВ, ЗАПИТАЙ НОВИЙ")
                self.root.after(0, lambda: self.status.config(text="❌ КОД ЗАСТАРІВ", fg='#ff4444'))
                self.root.after(0, lambda: self.login_btn.config(state=tk.NORMAL))
            except Exception as err:
                self.log(f"❌ ПОМИЛКА: {err}")
                self.root.after(0, lambda: self.status.config(text=f"❌ {err}", fg='#ff4444'))
                self.root.after(0, lambda: self.login_btn.config(state=tk.NORMAL))
        asyncio.run(login())


class NexusMain:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS TOOL | ПАРСЕР + РОЗСИЛКА + АВТОВІДПОВІДАЧ")
        self.root.geometry("1200x1000")
        self.root.configure(bg='#0a0a0a')
        self.users_list = []
        self.auto_reply_text = DEFAULT_AUTO_REPLY
        self.client = None
        self.loop = None
        self.client_ready = False
        
        self.messages_list = self.load_messages()
        self.load_auto_reply_config()
        
        self.setup_ui()
        self.start_client_and_loop()

    def setup_ui(self):
        main = tk.Frame(self.root, bg='#0a0a0a')
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(main, text="NEXUS SOFTWARE", font=('Courier New', 22, 'bold'),
                bg='#0a0a0a', fg='#ff00cc').pack(pady=(0, 15))

        top_frame = tk.Frame(main, bg='#0a0a0a')
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        log_frame = tk.LabelFrame(top_frame, text="📜 КОНСОЛЬ", bg='#1a1a1a', fg='#00ffcc')
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.log_area = scrolledtext.ScrolledText(log_frame, height=15, bg='#0f0f0f', fg='#00ffcc', font=('Consolas', 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        auto_reply_frame = tk.LabelFrame(top_frame, text="🤖 АВТОВІДПОВІДАЧ (ТІЛЬКИ НА '+' В ЛС)", bg='#1a1a1a', fg='#ffcc00')
        auto_reply_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(auto_reply_frame, text="ТЕКСТ ВІДПОВІДІ:", bg='#1a1a1a', fg='white').pack(anchor='w', padx=10, pady=(10,0))
        self.reply_text_widget = scrolledtext.ScrolledText(auto_reply_frame, height=8, bg='#0f0f0f', fg='white')
        self.reply_text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.reply_text_widget.insert(tk.END, self.auto_reply_text)
        
        btn_auto_frame = tk.Frame(auto_reply_frame, bg='#1a1a1a')
        btn_auto_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.auto_reply_enabled = tk.BooleanVar(value=True)
        tk.Checkbutton(btn_auto_frame, text="✅ АКТИВУВАТИ", variable=self.auto_reply_enabled, 
                      bg='#1a1a1a', fg='#00ffcc', selectcolor='#1a1a1a').pack(side=tk.LEFT)
        
        tk.Button(btn_auto_frame, text="💾 ЗБЕРЕГТИ", command=self.save_auto_reply_config,
                 bg='#ffaa00', fg='black', relief=tk.FLAT, padx=10).pack(side=tk.RIGHT)
        
        info_label = tk.Label(auto_reply_frame, text="🔹 Умови відповіді:\n- Особисте повідомлення (ЛС)\n- Містить символ '+'\n- Відправник не бот", 
                            bg='#1a1a1a', fg='#888888', justify=tk.LEFT)
        info_label.pack(anchor='w', padx=10, pady=5)

        parser_frame = tk.LabelFrame(main, text="📡 ПАРСЕР (хто писав у каналі/групі)", bg='#1a1a1a', fg='#ffcc00')
        parser_frame.pack(fill=tk.X, pady=(0, 10))

        row1 = tk.Frame(parser_frame, bg='#1a1a1a')
        row1.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(row1, text="ПОСИЛАННЯ:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
        self.link_entry = ttk.Entry(row1, width=60)
        self.link_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(row1, text="📋 ВСТАВИТИ", command=self.paste_link, bg='#ff00cc', fg='black', relief=tk.FLAT, padx=10).pack(side=tk.RIGHT)

        row2 = tk.Frame(parser_frame, bg='#1a1a1a')
        row2.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(row2, text="ЛІМІТ ПОВІДОМЛЕНЬ (0=всі):", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
        self.limit_msgs = tk.IntVar(value=500)
        tk.Spinbox(row2, from_=0, to=50000, textvariable=self.limit_msgs, width=10).pack(side=tk.LEFT, padx=5)
        self.parse_btn = tk.Button(row2, text="🚀 СТАРТ ПАРСИНГУ", command=self.start_parser, bg='#00ff88', fg='black', relief=tk.FLAT, padx=15)
        self.parse_btn.pack(side=tk.RIGHT)

        spam_frame = tk.LabelFrame(main, text="💣 РОЗСИЛКА (різні тексти різним людям)", bg='#1a1a1a', fg='#ff4444')
        spam_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(spam_frame, text="📋 ПОВІДОМЛЕННЯ (кожному наступне по колу):", bg='#1a1a1a', fg='#ffaa00').pack(anchor='w', padx=10, pady=(5,0))
        self.messages_text = scrolledtext.ScrolledText(spam_frame, height=6, bg='#0f0f0f', fg='white')
        self.messages_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.messages_text.insert(tk.END, "\n".join(self.messages_list))
        self.messages_text.bind('<KeyRelease>', self.save_messages)

        controls = tk.Frame(spam_frame, bg='#1a1a1a')
        controls.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(controls, text="📂 ФАЙЛ З ЮЗЕРНЕЙМАМИ:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
        self.user_file_path = tk.StringVar()
        ttk.Entry(controls, textvariable=self.user_file_path, width=30).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="📂 ВИБРАТИ", command=self.choose_user_file, bg='#ffaa00', fg='black', relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="📂 ЗАВАНТАЖИТИ", command=self.load_users_from_selected_file, bg='#ffaa00', fg='black', relief=tk.FLAT, padx=10).pack(side=tk.LEFT, padx=5)

        limits = tk.Frame(spam_frame, bg='#1a1a1a')
        limits.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(limits, text="⏱️ ЗАТРИМКА (сек):", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
        self.delay_var = tk.DoubleVar(value=15.0)
        tk.Spinbox(limits, from_=10, to=60, increment=1, textvariable=self.delay_var, width=5).pack(side=tk.LEFT, padx=5)
        
        self.random_var = tk.BooleanVar(value=True)
        tk.Checkbutton(limits, text="🔀 Рандомізація", variable=self.random_var, bg='#1a1a1a', fg='white', selectcolor='#1a1a1a').pack(side=tk.LEFT, padx=10)

        tk.Label(limits, text="🔢 ЛІМІТ РОЗСИЛКИ (0=всі):", bg='#1a1a1a', fg='white').pack(side=tk.LEFT, padx=(20,5))
        self.limit_spam = tk.IntVar(value=0)
        tk.Spinbox(limits, from_=0, to=5000, increment=50, textvariable=self.limit_spam, width=8).pack(side=tk.LEFT, padx=5)

        self.spam_btn = tk.Button(controls, text="🔥 РОЗСЛАТИ", command=self.start_spam, bg='#ff4444', fg='white', relief=tk.FLAT, padx=15)
        self.spam_btn.pack(side=tk.RIGHT)

        self.status = tk.Label(main, text="✅ ГОТОВ", bg='#0a0a0a', fg='#00ffcc')
        self.status.pack(pady=5)
        
        self.log("⚡ АКТИВОВАНО")
        self.log("🤖 АВТОВІДПОВІДАЧ: реагує ТІЛЬКИ на '+' у ЛС")

    def start_client_and_loop(self):
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            async def init():
                self.client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
                await self.client.start()
                self.client_ready = True
                self.log("🔌 ОСНОВНИЙ КЛІЄНТ ПІДКЛЮЧЕНО")
                
                @self.client.on(events.NewMessage(incoming=True))
                async def handler(event):
                    if not self.auto_reply_enabled.get():
                        return
                    if event.is_group or event.is_channel:
                        return
                    msg_text = event.raw_text or event.message.message or ""
                    if '+' not in msg_text:
                        return
                    sender = await event.get_sender()
                    if sender and sender.bot:
                        return
                    reply_text = self.reply_text_widget.get("1.0", tk.END).strip()
                    if reply_text:
                        try:
                            await event.reply(reply_text)
                            self.log(f"🤖 Відповідь на '+' від @{sender.username if sender.username else sender.id}")
                        except Exception as e:
                            self.log(f"❌ Помилка: {e}")
                
                await self.client.run_until_disconnected()
            
            self.loop.run_until_complete(init())
        
        threading.Thread(target=run_loop, daemon=True).start()

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_area.see(tk.END)

    def paste_link(self):
        try:
            self.link_entry.delete(0, tk.END)
            self.link_entry.insert(0, pyperclip.paste())
            self.log("📌 ПОСИЛАННЯ ВСТАВЛЕНО")
        except Exception as e:
            self.log(f"❌ ПОМИЛКА: {e}")

    def choose_user_file(self):
        f = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if f:
            self.user_file_path.set(f)
            self.log(f"📂 ВИБРАНО ФАЙЛ: {f}")

    def load_users_from_selected_file(self):
        path = self.user_file_path.get().strip()
        if not path or not os.path.exists(path):
            self.log("❌ ФАЙЛ НЕ ЗНАЙДЕНО")
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            self.users_list = []
            for line in lines:
                match = re.search(r'(@\w+)', line)
                if match:
                    self.users_list.append(match.group(1))
            self.log(f"✅ ЗАВАНТАЖЕНО {len(self.users_list)} ЮЗЕРНЕЙМІВ")
            self.status.config(text=f"📂 {len(self.users_list)} юзерів")
        except Exception as e:
            self.log(f"❌ ПОМИЛКА: {e}")

    def load_messages(self):
        if os.path.exists(MESSAGES_BACKUP_FILE):
            try:
                with open(MESSAGES_BACKUP_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return DEFAULT_MESSAGES.copy()
        return DEFAULT_MESSAGES.copy()

    def save_messages(self, event=None):
        try:
            txt = self.messages_text.get("1.0", tk.END).strip()
            msgs = [m.strip() for m in txt.split("\n") if m.strip()]
            if msgs:
                with open(MESSAGES_BACKUP_FILE, 'w', encoding='utf-8') as f:
                    json.dump(msgs, f, indent=2, ensure_ascii=False)
        except:
            pass

    def load_auto_reply_config(self):
        if os.path.exists(AUTO_REPLY_FILE):
            try:
                with open(AUTO_REPLY_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.auto_reply_text = config.get("reply_text", DEFAULT_AUTO_REPLY)
                    self.auto_reply_enabled.set(config.get("enabled", True))
            except:
                pass

    def save_auto_reply_config(self):
        try:
            config = {
                "reply_text": self.reply_text_widget.get("1.0", tk.END).strip(),
                "enabled": self.auto_reply_enabled.get()
            }
            with open(AUTO_REPLY_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.auto_reply_text = config["reply_text"]
            self.log("💾 Налаштування збережено")
        except Exception as e:
            self.log(f"❌ Помилка: {e}")

    def start_parser(self):
        link = self.link_entry.get().strip()
        if not link:
            self.log("❌ ВВЕДИ ПОСИЛАННЯ")
            return
        
        if not self.client_ready:
            self.log("⏳ ЗАЧЕКАЙТЕ, КЛІЄНТ ЩЕ ПІДКЛЮЧАЄТЬСЯ...")
            self.parse_btn.config(state=tk.NORMAL, text="🚀 СТАРТ ПАРСИНГУ")
            return
        
        self.parse_btn.config(state=tk.DISABLED, text="⏳...")
        threading.Thread(target=self._parse_task, args=(link,), daemon=True).start()

    def _parse_task(self, link):
        async def parse():
            try:
                if not self.client_ready:
                    self.log("❌ КЛІЄНТ НЕ ГОТОВИЙ")
                    return
                
                self.log("🔐 ПІДКЛЮЧЕНО")
                self.log("🔄 ПРОГРІВАЮ КЕШ...")
                await self.client.get_dialogs()
                self.log("✅ КЕШ ГОТОВИЙ")

                entity = await self.client.get_entity(link)
                chat_title = entity.title if hasattr(entity, 'title') else link
                self.log(f"📢 ПАРСИНГ: {chat_title}")

                limit = self.limit_msgs.get() if self.limit_msgs.get() > 0 else None
                users_dict = {}
                count = 0

                async for msg in self.client.iter_messages(entity, limit=limit, wait_time=1):
                    if msg.sender_id and hasattr(msg, 'sender') and msg.sender:
                        user = msg.sender
                        if hasattr(user, 'bot') and not user.bot and hasattr(user, 'username') and user.username:
                            uname = f"@{user.username}"
                            if uname not in users_dict:
                                users_dict[uname] = {
                                    "name": user.first_name or "АНОНІМ",
                                    "username": uname
                                }
                    count += 1
                    if count % 200 == 0:
                        self.log(f"📥 ОБРОБЛЕНО: {count}, ЗНАЙДЕНО: {len(users_dict)}")
                    await asyncio.sleep(0.05)

                self.log(f"🏁 ПЕРЕГЛЯНУТО: {count}")
                self.log(f"✅ ЗНАЙДЕНО: {len(users_dict)}")

                if users_dict:
                    fname = f"nexus_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(fname, 'w', encoding='utf-8') as f:
                        for u in users_dict.values():
                            f.write(f"{u['name']} - {u['username']}\n")
                    self.users_list = list(users_dict.keys())
                    self.log(f"💾 ФАЙЛ: {fname}")
                    self.log(f"✅ ЗАВАНТАЖЕНО {len(self.users_list)} ЮЗЕРНЕЙМІВ")
                else:
                    self.log("⚠️ НЕ ЗНАЙДЕНО ЖОДНОГО ЮЗЕРНЕЙМА")
                    self.users_list = []
                    
            except errors.FloodWaitError as e:
                wait_time = e.seconds
                self.log(f"⛔ TELEGRAM БЛОКУЄ: ЧЕКАТИ {wait_time} СЕКУНД!")
                self.log(f"📌 ПРОГРАМА ПРИЗУПИНЕНА НА {wait_time//60} ХВИЛИН")
                await asyncio.sleep(wait_time)
                self.log("✅ ОЧІКУВАННЯ ЗАКІНЧИЛОСЬ, СПРОБУЙТЕ ЗНОВУ")
            except Exception as e:
                self.log(f"❌ ПОМИЛКА ПАРСИНГУ: {e}")

        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(parse(), self.loop)
        else:
            self.log("❌ LOOP НЕ АКТИВНИЙ")
        
        self.parse_btn.config(state=tk.NORMAL, text="🚀 СТАРТ ПАРСИНГУ")

    def start_spam(self):
        if not self.users_list:
            self.log("❌ НЕМАЄ ЮЗЕРНЕЙМІВ")
            return
        msgs = self.messages_text.get("1.0", tk.END).strip().split("\n")
        msgs = [m.strip() for m in msgs if m.strip()]
        if not msgs:
            self.log("❌ НЕМАЄ ПОВІДОМЛЕНЬ")
            return
        limit = self.limit_spam.get()
        targets = self.users_list[:limit] if limit>0 else self.users_list
        if not messagebox.askyesno("❗ УВАГА", f"РОЗСЛАТИ {len(targets)} ЮЗЕРАМ?\nЗАТРИМКА {self.delay_var.get()} сек"):
            return
        self.spam_btn.config(state=tk.DISABLED, text="⏳...")
        threading.Thread(target=self._spam_task, args=(targets, msgs), daemon=True).start()

    def _spam_task(self, users, msgs):
        async def spam():
            if not self.client_ready:
                self.log("❌ КЛІЄНТ НЕ ГОТОВИЙ")
                return
            
            delay = self.delay_var.get()
            rand = self.random_var.get()
            sent = 0
            total = len(users)
            for i, u in enumerate(users, 1):
                txt = msgs[(i-1) % len(msgs)]
                cur_delay = delay + (random.uniform(-5,5) if rand else 0)
                cur_delay = max(5, cur_delay)
                try:
                    ent = await self.client.get_entity(u)
                    if getattr(ent, 'bot', False):
                        self.log(f"🤖 [{i}/{total}] {u} - БОТ")
                        continue
                    await self.client.send_message(ent, txt)
                    self.log(f"✅ [{i}/{total}] {u}")
                    sent += 1
                    await asyncio.sleep(cur_delay)
                except errors.FloodWaitError as e:
                    wait_time = e.seconds
                    self.log(f"⚠️ FLOODWAIT: ЧЕКАЮ {wait_time} СЕК")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    self.log(f"❌ ПОМИЛКА {u}: {e}")
            self.log(f"🏁 ВІДПРАВЛЕНО {sent}/{total}")

        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(spam(), self.loop)
        else:
            self.log("❌ LOOP НЕ АКТИВНИЙ")
        
        self.spam_btn.config(state=tk.NORMAL, text="🔥 РОЗСЛАТИ")


def start_main():
    for w in root.winfo_children():
        w.destroy()
    NexusMain(root)


if __name__ == "__main__":
    try:
        import telethon
        import pyperclip
    except ImportError:
        import subprocess
        subprocess.run(["pip", "install", "telethon", "pyperclip"])
        import telethon
        import pyperclip
    root = tk.Tk()
    NexusLogin(root, start_main)
    root.mainloop()