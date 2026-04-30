# client_gui_custom.py (полный код)
import customtkinter as ctk
import socket
import threading
import queue
import json
import base64
import re
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
import io

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SESSION_FILE = Path.home() / ".messenger_session.json"
SETTINGS_FILE = Path.home() / ".messenger_settings.json"

class MessengerClient:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.recv_queue = queue.Queue()
        self.username = None
        self.current_chat = None
        self.current_chat_type = None

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.running = True
            threading.Thread(target=self._receive_thread, daemon=True).start()
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def _receive_thread(self):
        while self.running:
            try:
                data = self.sock.recv(65536).decode()
                if not data:
                    break
                for line in data.split('\n'):
                    if line.strip():
                        self.recv_queue.put(line.strip())
            except:
                break
        self.running = False

    def send_command(self, cmd):
        if self.sock:
            try:
                self.sock.send((cmd + '\n').encode())
            except:
                pass

    def close(self):
        self.running = False
        if self.sock:
            self.sock.close()

class MessengerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Мессенджер")
        self.geometry("950x650")
        self.minsize(800, 550)

        self.settings = self.load_settings()
        self.apply_settings()

        self.client = MessengerClient()
        self.connected = False
        self.logged_in = False
        self.contacts = []          # list of (username, is_online)
        self.groups = []            # list of group names
        self.avatars_cache = {}     # user -> CTkImage
        self.group_avatars_cache = {} # group -> CTkImage
        self.receiving_avatar = None
        self.avatar_chunks = {}
        self.expected_avatar_chunks = 0
        self.receiving_group_avatar = None
        self.group_avatar_chunks = {}
        self.expected_group_avatar_chunks = 0
        self.password_visible = False
        self.auto_login_attempted = False
        self._status_update_id = None

        self.create_login_screen()
        self.after(500, self.attempt_auto_login)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ---------- Настройки ----------
    def load_settings(self):
        default = {"theme": "dark", "color_theme": "blue", "font_size": 13}
        if not SETTINGS_FILE.exists():
            return default
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                return {**default, **data}
        except:
            return default

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f)
        except Exception as e:
            print(f"Не удалось сохранить настройки: {e}")

    def apply_settings(self):
        ctk.set_appearance_mode(self.settings["theme"])
        ctk.set_default_color_theme(self.settings["color_theme"])
        self.font_size = self.settings["font_size"]

    def rebuild_ui(self):
        if self.logged_in:
            self.create_main_ui()
            self.load_contacts_and_groups()
            self.client.send_command(f"/get_avatar {self.client.username}")

    def open_settings_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Настройки")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self)

        ctk.CTkLabel(dialog, text="Тема:").pack(pady=(20,5))
        theme_var = ctk.StringVar(value=self.settings["theme"])
        ctk.CTkOptionMenu(dialog, values=["dark","light"], variable=theme_var).pack(pady=(0,15))

        ctk.CTkLabel(dialog, text="Цветовая схема:").pack(pady=(10,5))
        color_var = ctk.StringVar(value=self.settings["color_theme"])
        ctk.CTkOptionMenu(dialog, values=["blue","dark-blue","green"], variable=color_var).pack(pady=(0,15))

        ctk.CTkLabel(dialog, text="Размер шрифта:").pack(pady=(10,5))
        font_slider = ctk.CTkSlider(dialog, from_=10, to=20, number_of_steps=10)
        font_slider.set(self.settings["font_size"])
        font_slider.pack(pady=(0,5), padx=20, fill="x")
        font_value = ctk.CTkLabel(dialog, text=f"{int(self.settings['font_size'])}")
        font_value.pack(pady=(0,15))

        def update_font_label(val):
            font_value.configure(text=str(int(val)))
        font_slider.configure(command=update_font_label)

        def save_and_apply():
            new_theme = theme_var.get()
            new_color = color_var.get()
            new_font_size = int(font_slider.get())
            if (new_theme != self.settings["theme"] or 
                new_color != self.settings["color_theme"] or 
                new_font_size != self.settings["font_size"]):
                self.settings.update({"theme":new_theme, "color_theme":new_color, "font_size":new_font_size})
                self.save_settings()
                self.apply_settings()
                self.rebuild_ui()
                messagebox.showinfo("Настройки", "Настройки применены")
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Сохранить", command=save_and_apply, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Отмена", command=dialog.destroy, width=120, fg_color="gray").pack(side="left", padx=10)

    # ---------- Сессия ----------
    def save_session(self, username, password):
        try:
            data = {"username": username, "password": base64.b64encode(password.encode()).decode()}
            with open(SESSION_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Не удалось сохранить сессию: {e}")

    def load_session(self):
        if not SESSION_FILE.exists():
            return None, None
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
            username = data.get("username")
            password_enc = data.get("password")
            if username and password_enc:
                return username, base64.b64decode(password_enc).decode()
        except Exception as e:
            print(f"Не удалось загрузить сессию: {e}")
        return None, None

    def clear_session(self):
        try:
            if SESSION_FILE.exists():
                SESSION_FILE.unlink()
        except:
            pass

    def attempt_auto_login(self):
        if self.auto_login_attempted:
            return
        self.auto_login_attempted = True
        username, password = self.load_session()
        if not username or not password:
            return
        if not self.connected:
            if not self.client.connect():
                self.status_label.configure(text="Автовход не удался: нет соединения с сервером", text_color="red")
                return
            self.connected = True
            self.after(100, self.process_incoming)
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, username)
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, password)
        self.client.send_command(f"/login {username} {password}")
        self.client.username = username
        self.status_label.configure(text="Автоматический вход...", text_color="gray")

    # ---------- Экран входа ----------
    def create_login_screen(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(expand=True, fill="both", padx=40, pady=40)
        ctk.CTkLabel(self.login_frame, text="Мессенджер", font=ctk.CTkFont(size=32, weight="bold")).pack(pady=(20,30))
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Имя пользователя", width=300, height=45)
        self.username_entry.pack(pady=10)
        password_frame = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        password_frame.pack(pady=10)
        self.password_entry = ctk.CTkEntry(password_frame, placeholder_text="Пароль", show="*", width=260, height=45)
        self.password_entry.pack(side="left", padx=(0,5))
        self.toggle_password_btn = ctk.CTkButton(password_frame, text="👁️", width=35, height=35,
                                                 command=self.toggle_password_visibility, fg_color="transparent")
        self.toggle_password_btn.pack(side="left")
        button_frame = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        self.login_btn = ctk.CTkButton(button_frame, text="Вход", width=140, height=40, command=self.do_login)
        self.login_btn.pack(side="left", padx=10)
        self.register_btn = ctk.CTkButton(button_frame, text="Регистрация", width=140, height=40,
                                          fg_color="transparent", border_width=2, command=self.do_register)
        self.register_btn.pack(side="left", padx=10)
        self.status_label = ctk.CTkLabel(self.login_frame, text="", font=ctk.CTkFont(size=12), text_color="gray")
        self.status_label.pack(pady=10)

    def toggle_password_visibility(self):
        self.password_visible = not self.password_visible
        if self.password_visible:
            self.password_entry.configure(show="")
            self.toggle_password_btn.configure(text="🙈")
        else:
            self.password_entry.configure(show="*")
            self.toggle_password_btn.configure(text="👁️")

    def do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            self.status_label.configure(text="Заполните оба поля", text_color="red")
            return
        if not self.connected:
            if not self.client.connect():
                self.status_label.configure(text="Не удалось подключиться к серверу", text_color="red")
                return
            self.connected = True
            self.after(100, self.process_incoming)
        self.client.send_command(f"/login {username} {password}")
        self.client.username = username
        self.status_label.configure(text="Выполняется вход...", text_color="gray")

    def do_register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            self.status_label.configure(text="Заполните оба поля", text_color="red")
            return
        if not self.connected:
            if not self.client.connect():
                self.status_label.configure(text="Не удалось подключиться к серверу", text_color="red")
                return
            self.connected = True
            self.after(100, self.process_incoming)
        self.client.send_command(f"/register {username} {password}")
        self.status_label.configure(text="Регистрация...", text_color="gray")

    # ---------- Обработка входящих сообщений ----------
    def process_incoming(self):
        try:
            while True:
                msg = self.client.recv_queue.get_nowait()
                self.after(0, lambda m=msg: self.handle_server_message(m))
        except queue.Empty:
            pass
        finally:
            if self.connected:
                self.after(100, self.process_incoming)

    def handle_server_message(self, msg):
        if msg.startswith("[CMD]"):
            cmd_response = msg[5:].strip()
            # Успешный вход
            if cmd_response.startswith("Добро пожаловать") and not self.logged_in:
                self.logged_in = True
                username = self.username_entry.get().strip()
                password = self.password_entry.get().strip()
                if username and password:
                    self.save_session(username, password)
                self.create_main_ui()
                self.load_contacts_and_groups()
                self.client.send_command(f"/get_avatar {self.client.username}")
                return

            # Список контактов (с онлайн‑статусом)
            if cmd_response.startswith("Контакты:"):
                contacts_part = cmd_response.replace("Контакты:", "").strip()
                if contacts_part and contacts_part != "У вас нет контактов":
                    self.contacts = []
                    for item in contacts_part.split(";"):
                        if "|" in item:
                            username, status = item.split("|", 1)
                            self.contacts.append((username, status == "online"))
                        else:
                            self.contacts.append((item, False))
                else:
                    self.contacts = []
                self.refresh_contacts_list()
                for contact, _ in self.contacts:
                    if contact not in self.avatars_cache:
                        self.client.send_command(f"/get_avatar {contact}")
                return

            # Список групп
            if cmd_response.startswith("Группы:"):
                groups_str = cmd_response.replace("Группы:", "").strip()
                self.groups = [g.strip() for g in groups_str.split(",")] if groups_str and groups_str != "Вы не состоите ни в одной группе" else []
                self.refresh_groups_list()
                for group in self.groups:
                    if group not in self.group_avatars_cache:
                        self.client.send_command(f"/get_group_avatar {group}")
                return

            # Статус контакта
            if cmd_response.startswith("STATUS"):
                parts = cmd_response.split(maxsplit=1)
                if len(parts) == 2:
                    data = parts[1]
                    if "|" in data:
                        username, status = data.split("|")
                        if username == self.client.current_chat and self.client.current_chat_type == "user":
                            self.update_chat_title_status(status == "online")
                return

            # Аватар пользователя (чанки)
            if cmd_response.startswith("AVATAR_START"):
                parts = cmd_response.split()
                if len(parts) == 3:
                    self.receiving_avatar = parts[1]
                    self.expected_avatar_chunks = int(parts[2])
                    self.avatar_chunks = {}
                return
            if cmd_response.startswith("AVATAR_CHUNK"):
                if self.receiving_avatar:
                    parts = cmd_response.split(maxsplit=2)
                    if len(parts) == 3:
                        idx = int(parts[1])
                        chunk = parts[2]
                        self.avatar_chunks[idx] = chunk
                return
            if cmd_response.startswith("AVATAR_END"):
                if self.receiving_avatar and len(self.avatar_chunks) == self.expected_avatar_chunks:
                    full_b64 = "".join(self.avatar_chunks[i] for i in range(self.expected_avatar_chunks))
                    full_b64 = full_b64.strip().replace("\n", "").replace("\r", "").replace(" ", "")
                    missing_padding = len(full_b64) % 4
                    if missing_padding:
                        full_b64 += "=" * (4 - missing_padding)
                    try:
                        img_data = base64.b64decode(full_b64)
                        img = Image.open(io.BytesIO(img_data))
                        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
                        self.avatars_cache[self.receiving_avatar] = ctk_img
                        if self.receiving_avatar == self.client.username and hasattr(self, 'user_avatar_label'):
                            self.user_avatar_label.configure(image=ctk_img, text="")
                        self.refresh_contacts_list()
                        if (hasattr(self, 'client') and self.client.current_chat_type == "user" and 
                            self.client.current_chat == self.receiving_avatar):
                            self.chat_avatar_label.configure(image=ctk_img, text="")
                    except Exception as e:
                        print(f"Ошибка загрузки аватара {self.receiving_avatar}: {e}")
                    self.receiving_avatar = None
                    self.avatar_chunks = {}
                return
            if cmd_response.startswith("AVATAR_DATA None"):
                return

            # Аватар группы (чанки)
            if cmd_response.startswith("GROUP_AVATAR_START"):
                parts = cmd_response.split()
                if len(parts) == 3:
                    self.receiving_group_avatar = parts[1]
                    self.expected_group_avatar_chunks = int(parts[2])
                    self.group_avatar_chunks = {}
                return
            if cmd_response.startswith("GROUP_AVATAR_CHUNK"):
                if self.receiving_group_avatar:
                    parts = cmd_response.split(maxsplit=2)
                    if len(parts) == 3:
                        idx = int(parts[1])
                        chunk = parts[2]
                        self.group_avatar_chunks[idx] = chunk
                return
            if cmd_response.startswith("GROUP_AVATAR_END"):
                if self.receiving_group_avatar and len(self.group_avatar_chunks) == self.expected_group_avatar_chunks:
                    full_b64 = "".join(self.group_avatar_chunks[i] for i in range(self.expected_group_avatar_chunks))
                    full_b64 = full_b64.strip().replace("\n", "").replace("\r", "").replace(" ", "")
                    missing_padding = len(full_b64) % 4
                    if missing_padding:
                        full_b64 += "=" * (4 - missing_padding)
                    try:
                        img_data = base64.b64decode(full_b64)
                        img = Image.open(io.BytesIO(img_data))
                        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
                        self.group_avatars_cache[self.receiving_group_avatar] = ctk_img
                        self.refresh_groups_list()
                        if self.client.current_chat_type == "group" and self.client.current_chat == self.receiving_group_avatar:
                            self.chat_avatar_label.configure(image=ctk_img, text="")
                    except Exception as e:
                        print(f"Ошибка загрузки аватара группы {self.receiving_group_avatar}: {e}")
                    self.receiving_group_avatar = None
                    self.group_avatar_chunks = {}
                return
            if cmd_response.startswith("GROUP_AVATAR_DATA None"):
                return

            # История
            if cmd_response.startswith("=== История"):
                self.display_history(cmd_response)
                return

            # Разные уведомления
            if cmd_response.startswith("Контакт") and "добавлен" in cmd_response:
                self.add_system_message(cmd_response)
                self.load_contacts_and_groups()
                return
            if cmd_response.startswith("Группа") and "создана" in cmd_response:
                self.add_system_message(cmd_response)
                self.load_contacts_and_groups()
                return
            if cmd_response == "Этот контакт уже добавлен":
                self.add_system_message(cmd_response)
                return
            if cmd_response.startswith("Пользователь") and "не найден" in cmd_response:
                self.add_system_message(cmd_response)
                return
            if cmd_response == "Нельзя добавить самого себя":
                self.add_system_message(cmd_response)
                return
            if cmd_response.startswith("Пользователь") and "добавлен в группу" in cmd_response:
                self.add_system_message(cmd_response)
                self.load_contacts_and_groups()
                return
            if cmd_response.startswith("Вы добавлены в группу"):
                self.add_system_message(cmd_response)
                self.load_contacts_and_groups()
                return
            if cmd_response == "Аватар успешно обновлён":
                self.add_system_message(cmd_response)
                self.client.send_command(f"/get_avatar {self.client.username}")
                return
            if cmd_response.startswith("Аватар группы"):
                self.add_system_message(cmd_response)
                if self.client.current_chat_type == "group":
                    self.client.send_command(f"/get_group_avatar {self.client.current_chat}")
                return
            if cmd_response.startswith("Участники группы"):
                messagebox.showinfo("Участники группы", cmd_response)
                return
            if cmd_response.startswith("GROUP_RENAMED"):
                parts = cmd_response.split(maxsplit=1)
                if len(parts) == 2:
                    old_name, new_name = parts[1].split("|")
                    self.load_contacts_and_groups()
                    if self.client.current_chat == old_name:
                        self.client.current_chat = new_name
                        self.update_chat_title_status()
                    self.add_system_message(f"Группа '{old_name}' переименована в '{new_name}'")
                return

            if self.logged_in:
                self.add_system_message(cmd_response)

        elif msg.startswith("[MSG]"):
            chat_msg = msg[5:].strip()
            if self.logged_in:
                self.append_chat_message(chat_msg)
        else:
            if self.logged_in:
                self.add_system_message(msg)

    def load_contacts_and_groups(self):
        self.client.send_command("/contacts")
        self.client.send_command("/groups")

    def refresh_contacts_list(self):
        for widget in self.contacts_frame.winfo_children():
            widget.destroy()
        for username, is_online in self.contacts:
            contact_frame = ctk.CTkFrame(self.contacts_frame, fg_color="transparent")
            contact_frame.pack(fill="x", pady=2, padx=5)
            if username in self.avatars_cache:
                avatar_label = ctk.CTkLabel(contact_frame, image=self.avatars_cache[username], text="", width=40, height=40)
            else:
                avatar_label = ctk.CTkLabel(contact_frame, text="📷", width=40, height=40, font=ctk.CTkFont(size=20))
            avatar_label.pack(side="left", padx=5, pady=5)
            status_text = "🟢" if is_online else "⚫"
            name_label = ctk.CTkLabel(contact_frame, text=f"{username} {status_text}", font=ctk.CTkFont(size=14), anchor="w")
            name_label.pack(side="left", fill="x", expand=True, padx=5)
            contact_frame.bind("<Button-1>", lambda e, u=username: self.on_contact_select(u))
            name_label.bind("<Button-1>", lambda e, u=username: self.on_contact_select(u))
            avatar_label.bind("<Button-1>", lambda e, u=username: self.on_contact_select(u))

    def refresh_groups_list(self):
        for widget in self.groups_frame.winfo_children():
            widget.destroy()
        for group in self.groups:
            group_frame = ctk.CTkFrame(self.groups_frame, fg_color="transparent")
            group_frame.pack(fill="x", pady=2, padx=5)
            if group in self.group_avatars_cache:
                avatar_label = ctk.CTkLabel(group_frame, image=self.group_avatars_cache[group], text="", width=40, height=40)
            else:
                avatar_label = ctk.CTkLabel(group_frame, text="👥", width=40, height=40, font=ctk.CTkFont(size=20))
            avatar_label.pack(side="left", padx=5, pady=5)
            name_label = ctk.CTkLabel(group_frame, text=group, font=ctk.CTkFont(size=14), anchor="w")
            name_label.pack(side="left", fill="x", expand=True, padx=5)
            group_frame.bind("<Button-1>", lambda e, g=group: self.on_group_select(g))
            name_label.bind("<Button-1>", lambda e, g=group: self.on_group_select(g))
            avatar_label.bind("<Button-1>", lambda e, g=group: self.on_group_select(g))

    # ---------- Отображение чата ----------
    def append_chat_message(self, line):
        self.chat_area.configure(state="normal")
        self.chat_area.insert("end", line + "\n")
        self.chat_area.configure(state="disabled")
        self.chat_area.see("end")

    def display_history(self, history_text):
        self.chat_area.configure(state="normal")
        self.chat_area.delete("1.0", "end")
        lines = history_text.split('\n')
        for line in lines:
            if line.startswith("[CMD] === История"):
                continue
            if line.startswith("[CMD]"):
                line = line[5:].strip()
                if line and not line.startswith("==="):
                    self.chat_area.insert("end", line + "\n")
        self.chat_area.configure(state="disabled")
        self.chat_area.see("end")

    def add_system_message(self, text):
        self.chat_area.configure(state="normal")
        self.chat_area.insert("end", f"[Система] {text}\n", "system")
        self.chat_area.tag_config("system", foreground="gray")
        self.chat_area.configure(state="disabled")
        self.chat_area.see("end")

    # ---------- Главный интерфейс ----------
    def create_main_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.top_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(5,0))
        self.settings_btn = ctk.CTkButton(self.top_frame, text="⚙️", width=40, height=40,
                                          command=self.open_settings_dialog, fg_color="transparent", hover_color="gray30")
        self.settings_btn.pack(side="right", padx=10, pady=5)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.left_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.left_frame.grid(row=1, column=0, sticky="nsew")
        self.left_frame.grid_propagate(False)

        # Блок текущего пользователя
        user_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        user_frame.pack(fill="x", padx=10, pady=(10,5))
        self.user_avatar_label = ctk.CTkLabel(user_frame, text="📷", width=40, height=40, font=ctk.CTkFont(size=20))
        self.user_avatar_label.pack(side="left", padx=(0,10))
        self.user_name_label = ctk.CTkLabel(user_frame, text=self.client.username, font=ctk.CTkFont(size=16, weight="bold"))
        self.user_name_label.pack(side="left", fill="x", expand=True)
        change_avatar_btn = ctk.CTkButton(user_frame, text="✏️", width=30, height=30, command=self.change_avatar)
        change_avatar_btn.pack(side="right", padx=5)

        ctk.CTkFrame(self.left_frame, height=2, fg_color="gray20").pack(fill="x", padx=10, pady=5)

        # Контакты
        ctk.CTkLabel(self.left_frame, text="📞 Контакты", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x", padx=15, pady=(10,5))
        self.contacts_frame = ctk.CTkScrollableFrame(self.left_frame, height=200, fg_color="transparent")
        self.contacts_frame.pack(fill="x", padx=10, pady=5)

        # Группы
        ctk.CTkLabel(self.left_frame, text="👥 Группы", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x", padx=15, pady=(10,5))
        self.groups_frame = ctk.CTkScrollableFrame(self.left_frame, height=150, fg_color="transparent")
        self.groups_frame.pack(fill="x", padx=10, pady=5)

        # Кнопки действий
        btn_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=10)
        ctk.CTkButton(btn_frame, text="➕ Добавить контакт", command=self.add_contact_dialog, height=35).pack(fill="x", pady=3)
        ctk.CTkButton(btn_frame, text="👥 Создать группу", command=self.create_group_dialog, height=35).pack(fill="x", pady=3)
        ctk.CTkButton(btn_frame, text="🔄 Обновить", command=self.load_contacts_and_groups, height=35, fg_color="gray30").pack(fill="x", pady=3)
        ctk.CTkButton(btn_frame, text="🚪 Выйти", command=self.logout, height=35, fg_color="darkred", hover_color="red").pack(fill="x", pady=(20,3))

        # Правая панель
        self.right_frame = ctk.CTkFrame(self, corner_radius=0)
        self.right_frame.grid(row=1, column=1, sticky="nsew")
        self.chat_title_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.chat_title_frame.pack(fill="x", padx=10, pady=(10,5))
        self.chat_avatar_label = ctk.CTkLabel(self.chat_title_frame, text="", width=40, height=40)
        self.chat_avatar_label.pack(side="left", padx=(0,10))
        self.chat_title = ctk.CTkLabel(self.chat_title_frame, text="Выберите чат", font=ctk.CTkFont(size=18, weight="bold"))
        self.chat_title.pack(side="left", fill="x", expand=True)

        ctk.CTkFrame(self.right_frame, height=2, fg_color="gray20").pack(fill="x", padx=10, pady=5)

        self.chat_area = ctk.CTkTextbox(self.right_frame, wrap="word", font=ctk.CTkFont(size=self.font_size), state="disabled")
        self.chat_area.pack(fill="both", expand=True, padx=10, pady=10)

        # Кнопки действий в чате
        actions_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        actions_frame.pack(fill="x", padx=10, pady=(0,5))
        self.add_member_btn = ctk.CTkButton(actions_frame, text="➕ Добавить участника", width=150, height=30,
                                            command=self.add_member_dialog, fg_color="green", hover_color="darkgreen")
        self.add_member_btn.pack(side="left", padx=(0,10))
        self.group_members_btn = ctk.CTkButton(actions_frame, text="👥 Участники", width=130, height=30,
                                               command=self.show_group_members, fg_color="gray30")
        self.group_members_btn.pack(side="left", padx=(0,10))
        self.delete_msg_btn = ctk.CTkButton(actions_frame, text="🗑 Удалить сообщение", width=150, height=30,
                                            command=self.delete_message_dialog, fg_color="darkred", hover_color="red")
        self.delete_msg_btn.pack(side="left")
        self.add_member_btn.pack_forget()
        self.group_members_btn.pack_forget()

        # Поле ввода сообщения
        input_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0,15))
        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Введите сообщение...", height=40)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0,10))
        self.message_entry.bind("<Return>", self.send_message)
        ctk.CTkButton(input_frame, text="Отправить", width=100, height=40, command=self.send_message).pack(side="right")

    # --- Аватар пользователя ---
    def change_avatar(self):
        file_path = filedialog.askopenfilename(title="Выберите изображение для аватара", filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if not file_path:
            return
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                if width != 40 or height != 40:
                    answer = messagebox.askyesno(
                        "Неверный размер",
                        f"Размер изображения {width}x{height}, рекомендуется 40x40.\n\nАвтоматически масштабировать до 40x40?"
                    )
                    if answer:
                        img = img.resize((40, 40), Image.Resampling.LANCZOS)
                        buf = io.BytesIO()
                        img.save(buf, format='PNG')
                        img_data = base64.b64encode(buf.getvalue()).decode()
                    else:
                        return
                else:
                    with open(file_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode()
            img_data = img_data.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            chunk_size = 4000
            chunks = [img_data[i:i+chunk_size] for i in range(0, len(img_data), chunk_size)]
            total = len(chunks)
            self.client.send_command(f"/set_avatar_start {total}")
            self.after(200, lambda: self.send_avatar_chunks(chunks))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить аватар: {e}")

    def send_avatar_chunks(self, chunks):
        for idx, chunk in enumerate(chunks):
            self.client.send_command(f"/set_avatar_chunk {idx} {chunk}")
        self.add_system_message("Аватар отправляется...")

    # --- Аватар группы ---
    def change_group_avatar(self):
        if not self.client.current_chat or self.client.current_chat_type != "group":
            messagebox.showinfo("Внимание", "Эта функция доступна только для групповых чатов")
            return
        file_path = filedialog.askopenfilename(title="Выберите изображение для аватара группы", filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if not file_path:
            return
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                if width != 40 or height != 40:
                    answer = messagebox.askyesno(
                        "Неверный размер",
                        f"Размер изображения {width}x{height}, рекомендуется 40x40.\n\nАвтоматически масштабировать до 40x40?"
                    )
                    if answer:
                        img = img.resize((40, 40), Image.Resampling.LANCZOS)
                        buf = io.BytesIO()
                        img.save(buf, format='PNG')
                        img_data = base64.b64encode(buf.getvalue()).decode()
                    else:
                        return
                else:
                    with open(file_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode()
            img_data = img_data.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            chunk_size = 4000
            chunks = [img_data[i:i+chunk_size] for i in range(0, len(img_data), chunk_size)]
            total = len(chunks)
            group_name = self.client.current_chat
            self.client.send_command(f"/set_group_avatar_start {group_name} {total}")
            self.after(200, lambda: self.send_group_avatar_chunks(chunks))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить аватар группы: {e}")

    def send_group_avatar_chunks(self, chunks):
        for idx, chunk in enumerate(chunks):
            self.client.send_command(f"/set_group_avatar_chunk {idx} {chunk}")
        self.add_system_message("Аватар группы отправляется...")

    # --- Обновление заголовка чата и меню группы ---
    def update_chat_title_status(self, is_online=None):
        if self.client.current_chat_type == "user":
            if is_online is None:
                self.client.send_command(f"/get_status {self.client.current_chat}")
                return
            status_text = "в сети" if is_online else "не в сети"
            self.chat_title.configure(text=f"Чат с {self.client.current_chat} - {status_text}")
        else:
            self.chat_title.configure(text=f"Группа {self.client.current_chat}")
            if not hasattr(self, 'group_settings_btn'):
                self.group_settings_btn = ctk.CTkButton(self.chat_title_frame, text="⚙️", width=30, height=30,
                                                        command=self.open_group_settings, fg_color="transparent")
                self.group_settings_btn.pack(side="right", padx=5)
            else:
                self.group_settings_btn.pack(side="right", padx=5)

    def open_group_settings(self):
        if not self.client.current_chat or self.client.current_chat_type != "group":
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title("Настройки группы")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self)
        ctk.CTkLabel(dialog, text=f"Группа: {self.client.current_chat}", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        rename_btn = ctk.CTkButton(dialog, text="✏️ Переименовать группу", command=lambda: self.rename_group_dialog(dialog))
        rename_btn.pack(pady=10)
        avatar_btn = ctk.CTkButton(dialog, text="🖼️ Сменить аватар", command=lambda: [dialog.destroy(), self.change_group_avatar()])
        avatar_btn.pack(pady=10)

    def rename_group_dialog(self, parent_dialog):
        parent_dialog.destroy()
        new_name = simpledialog.askstring("Переименование группы", "Введите новое название группы:", parent=self)
        if new_name and new_name.strip():
            self.client.send_command(f"/rename_group {self.client.current_chat} {new_name.strip()}")

    def _schedule_status_update(self):
        if hasattr(self, '_status_update_id') and self._status_update_id:
            self.after_cancel(self._status_update_id)
        self._status_update_id = self.after(30000, self.update_current_contact_status)

    def update_current_contact_status(self):
        if self.client.current_chat and self.client.current_chat_type == "user":
            self.client.send_command(f"/get_status {self.client.current_chat}")
        self._schedule_status_update()

    def show_group_members(self):
        if not self.client.current_chat or self.client.current_chat_type != "group":
            messagebox.showinfo("Внимание", "Эта функция доступна только для групповых чатов")
            return
        self.client.send_command(f"/get_group_members {self.client.current_chat}")

    def on_contact_select(self, username):
        if username != self.client.current_chat or self.client.current_chat_type != "user":
            self.client.current_chat = username
            self.client.current_chat_type = "user"
            self.update_chat_title_status()
            self.add_member_btn.pack_forget()
            self.group_members_btn.pack_forget()
            if hasattr(self, 'group_settings_btn'):
                self.group_settings_btn.pack_forget()
            if username in self.avatars_cache:
                self.chat_avatar_label.configure(image=self.avatars_cache[username], text="")
            else:
                self.chat_avatar_label.configure(image="", text="📷")
                self.client.send_command(f"/get_avatar {username}")
            self.client.send_command(f"/history {username} 50")
            self._schedule_status_update()

    def on_group_select(self, group):
        if group != self.client.current_chat or self.client.current_chat_type != "group":
            self.client.current_chat = group
            self.client.current_chat_type = "group"
            self.update_chat_title_status()
            self.add_member_btn.pack(side="left", padx=(0,10))
            self.group_members_btn.pack(side="left", padx=(0,10))
            if group in self.group_avatars_cache:
                self.chat_avatar_label.configure(image=self.group_avatars_cache[group], text="")
            else:
                self.chat_avatar_label.configure(image="", text="👥")
                self.client.send_command(f"/get_group_avatar {group}")
            self.client.send_command(f"/history {group} 50")

    def send_message(self, event=None):
        if not self.client.current_chat:
            messagebox.showinfo("Внимание", "Сначала выберите чат")
            return
        msg = self.message_entry.get().strip()
        if not msg:
            return
        self.client.send_command(f"/send {self.client.current_chat} {msg}")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.append_chat_message(f"{timestamp} Я: {msg}")
        self.message_entry.delete(0, "end")

    def add_member_dialog(self):
        if not self.client.current_chat or self.client.current_chat_type != "group":
            messagebox.showinfo("Внимание", "Эта функция доступна только для групповых чатов")
            return
        username = simpledialog.askstring("Добавить участника", "Введите имя пользователя:")
        if username and username.strip():
            self.client.send_command(f"/add_to_group {self.client.current_chat} {username.strip()}")

    def delete_message_dialog(self):
        if not self.client.current_chat:
            messagebox.showinfo("Внимание", "Сначала выберите чат")
            return
        msg_id = simpledialog.askstring("Удаление сообщения", "Введите ID сообщения (из истории):")
        if not msg_id:
            return
        delete_type = simpledialog.askstring("Удаление сообщения", "Тип удаления:\nself - только у себя\nall - у всех (только для своих сообщений)")
        if delete_type not in ["self", "all"]:
            messagebox.showerror("Ошибка", "Неверный тип. Используйте self или all")
            return
        self.client.send_command(f"/delete_message {msg_id} {delete_type}")
        self.client.send_command(f"/history {self.client.current_chat} 50")

    def add_contact_dialog(self):
        username = ctk.CTkInputDialog(text="Введите имя пользователя:", title="Добавить контакт").get_input()
        if username:
            self.client.send_command(f"/add_contact {username}")

    def create_group_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Создать группу")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self)
        ctk.CTkLabel(dialog, text="Название группы:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20,15))
        name_entry = ctk.CTkEntry(dialog, width=300, height=35)
        name_entry.pack(pady=(0,15))
        ctk.CTkLabel(dialog, text="Участники (через пробел):").pack(pady=(10,5))
        members_entry = ctk.CTkEntry(dialog, width=300, height=35)
        members_entry.pack(pady=(0,20))
        def do_create():
            name = name_entry.get().strip()
            members = members_entry.get().strip().split()
            if name and members:
                self.client.send_command(f"/create_group {name} " + " ".join(members))
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Заполните все поля")
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Отмена", width=100, command=dialog.destroy, fg_color="gray30").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Создать", width=100, command=do_create).pack(side="left", padx=10)

    def logout(self):
        self.client.send_command("/logout")
        self.logged_in = False
        self.client.close()
        self.connected = False
        self.clear_session()
        self.create_login_screen()

    def on_closing(self):
        if self.logged_in:
            self.client.send_command("/logout")
        self.client.close()
        self.destroy()

if __name__ == "__main__":
    app = MessengerGUI()
    app.mainloop()