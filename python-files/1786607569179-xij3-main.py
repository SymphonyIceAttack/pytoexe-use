import asyncio
import random
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import (
    InputReportReasonSpam,
    InputReportReasonViolence,
    InputReportReasonFake,
    InputReportReasonOther
)
import os
import time

# === КОНФИГУРАЦИЯ (замени на свои данные) ===
API_ID = 1234567          # получи на my.telegram.org
API_HASH = 'ваш_api_hash' # получи на my.telegram.org

class ReportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ReportMaster v1.0")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        self.username_var = tk.StringVar()
        self.count_var = tk.IntVar(value=10)
        self.is_running = False

        tk.Label(root, text="Целевой username (без @):", font=("Arial", 10)).pack(pady=(10,0))
        entry_username = tk.Entry(root, textvariable=self.username_var, width=30, font=("Arial", 12))
        entry_username.pack(pady=5)

        tk.Label(root, text="Количество жалоб (1-100):", font=("Arial", 10)).pack()
        scale = tk.Scale(root, from_=1, to=100, orient=tk.HORIZONTAL, variable=self.count_var, length=300)
        scale.pack(pady=5)

        self.btn_start = tk.Button(root, text="Запустить атаку", command=self.start_attack, bg="#4CAF50", fg="white", font=("Arial", 12))
        self.btn_start.pack(pady=10)

        self.progress = ttk.Progressbar(root, length=400, mode='determinate')
        self.progress.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(root, width=70, height=15, state='normal')
        self.log_area.pack(pady=10)

        self.status_label = tk.Label(root, text="Готов к работе", font=("Arial", 10))
        self.status_label.pack()

    def log(self, msg):
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.root.update()

    def start_attack(self):
        if self.is_running:
            return
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Ошибка", "Введите username!")
            return
        count = self.count_var.get()
        if count < 1 or count > 100:
            messagebox.showerror("Ошибка", "Количество должно быть от 1 до 100!")
            return

        self.is_running = True
        self.btn_start.config(state='disabled')
        self.progress['value'] = 0
        self.log_area.delete(1.0, tk.END)
        self.log("🚀 Запуск атаки на @{} с {} жалобами".format(username, count))
        self.status_label.config(text="Идёт отправка...")

        threading.Thread(target=self.run_attack, args=(username, count), daemon=True).start()

    def run_attack(self, username, total_count):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.async_attack(username, total_count))
        except Exception as e:
            self.log("❌ Критическая ошибка: " + str(e))
        finally:
            self.is_running = False
            self.btn_start.config(state='normal')
            self.status_label.config(text="Готов")
            self.progress['value'] = 100

    async def async_attack(self, username, total_count):
        sess_dir = "sessions"
        if not os.path.exists(sess_dir):
            self.log("❌ Папка sessions не найдена!")
            return
        sess_files = [os.path.join(sess_dir, f) for f in os.listdir(sess_dir) if f.endswith('.session')]
        if not sess_files:
            self.log("❌ Нет ни одного .session файла в папке sessions!")
            return

        proxies = []
        if os.path.exists("proxies.txt"):
            with open("proxies.txt", "r") as f:
                proxies = [line.strip() for line in f if line.strip()]
        if not proxies:
            self.log("⚠️ Прокси не найдены, работаем без прокси (риск бана)")

        random.shuffle(sess_files)
        random.shuffle(proxies)

        sessions_count = len(sess_files)
        reports_per_session = max(1, total_count // sessions_count)
        remaining = total_count - reports_per_session * sessions_count
        distribution = [reports_per_session] * sessions_count
        for i in range(remaining):
            distribution[i] += 1

        tasks = []
        idx = 0
        for sess_file, rep_count in zip(sess_files, distribution):
            if rep_count <= 0:
                continue
            proxy = proxies[idx % len(proxies)] if proxies else None
            tasks.append(self.worker(sess_file, username, rep_count, proxy, idx))
            idx += 1

        completed = 0
        for task in asyncio.as_completed(tasks):
            success = await task
            completed += success
            progress_val = int((completed / total_count) * 100)
            self.progress['value'] = progress_val
            self.root.update()
            self.log(f"✅ Прогресс: {completed}/{total_count}")

        self.log(f"🎯 Завершено! Успешно отправлено {completed} из {total_count} жалоб.")
        if completed >= total_count * 0.7:
            self.log("✅ Аккаунт должен быть заблокирован в ближайшее время.")
        else:
            self.log("⚠️ Успешность низкая, возможно нужны новые сессии/прокси.")

    async def worker(self, session_file, target_username, reports_count, proxy_url, worker_id):
        proxy = None
        if proxy_url:
            try:
                if proxy_url.startswith('socks5://'):
                    parts = proxy_url[9:].split('@')
                    if len(parts) == 2:
                        user_pass, ip_port = parts
                        user, passwd = user_pass.split(':')
                        ip, port = ip_port.split(':')
                        proxy = (user, passwd, ip, int(port))
                    else:
                        ip_port = parts[0]
                        ip, port = ip_port.split(':')
                        proxy = (None, None, ip, int(port))
            except Exception as e:
                self.log(f"⚠️ Ошибка парсинга прокси {proxy_url}: {e}")
                proxy = None

        client = TelegramClient(session_file, API_ID, API_HASH, proxy=proxy)
        await client.start()

        success_count = 0
        reasons = [
            InputReportReasonSpam(),
            InputReportReasonViolence(),
            InputReportReasonFake(),
            InputReportReasonOther()
        ]

        for i in range(reports_count):
            try:
                entity = await client.get_entity(target_username)
                reason = random.choice(reasons)
                msg = random.choice([
                    "Систематический спам и мошенничество",
                    "Распространение запрещённого контента",
                    "Выдача себя за официальное лицо",
                    "Угрозы и преследование пользователей"
                ])
                await client(ReportRequest(
                    peer=entity,
                    id=[],
                    reason=reason,
                    message=msg
                ))
                success_count += 1
                self.log(f"✅ [{session_file}] Жалоба {i+1}/{reports_count} отправлена")
            except errors.FloodWaitError as e:
                self.log(f"⏳ [{session_file}] FloodWait {e.seconds} сек, ждём...")
                await asyncio.sleep(e.seconds + 5)
                try:
                    await client(ReportRequest(
                        peer=entity,
                        id=[],
                        reason=reason,
                        message=msg
                    ))
                    success_count += 1
                    self.log(f"✅ [{session_file}] Повторная жалоба отправлена")
                except Exception as e2:
                    self.log(f"❌ [{session_file}] Ошибка повторной отправки: {e2}")
            except Exception as e:
                self.log(f"❌ [{session_file}] Ошибка: {e}")
            await asyncio.sleep(random.randint(10, 25))

        await client.disconnect()
        return success_count

if __name__ == "__main__":
    root = tk.Tk()
    app = ReportApp(root)
    root.mainloop()