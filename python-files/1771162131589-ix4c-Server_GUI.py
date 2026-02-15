
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import datetime
import os
import time
import configparser
import hashlib
import logging
import subprocess
import ctypes
import sys
from playsound import playsound

# --- НАСТРОЙКИ ---
USERS_CONFIG_FILE = 'config.ini'
LOG_FILE = 'chat_server.log'
SERVER_PORT = 55555
DEFAULT_NICK_COLOR = "#FFFFFF"
ADMIN_NAME = "Админ"

# --- ЛОГИРОВАНИЕ ---
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s', encoding='utf-8')
logger = logging.getLogger()

# --- ЗВУК ---
SOUND_FILE = 'notification.mp3'
ADMIN_SOUND_ENABLED = os.path.exists(SOUND_FILE)

# --- СИСТЕМНЫЕ ФУНКЦИИ ---

def is_admin():
    """Проверка прав администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def manage_firewall(port, action="add"):
    """Управление портами Брандмауэра Windows"""
    if not is_admin():
        return False # Нет прав - ничего не делаем
    
    rule_name = "Python_Chat_Server_Rule"
    if action == "add":
        cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=TCP localport={port}'
    else:
        cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
    
    try:
        subprocess.run(cmd, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except:
        return False

def get_local_ip():
    """Определение локального IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
        s.close()
    except:
        IP = '127.0.0.1'
    return IP

# --- ГРАФИКА ---

class ServerGUI:
    def __init__(self, master):
        self.master = master
        master.title("Python CHAT SERVER")
        master.geometry("950x650")
        
        self.registered_users = {}
        self.clients = []
        self.is_running = False
        self.local_ip = get_local_ip()

        # Верхняя панель
        self.top_frame = tk.Frame(master, bg='#f0f0f0')
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.start_btn = tk.Button(self.top_frame, text="ЗАПУСТИТЬ СЕРВЕР", command=self.start_server, 
                                   bg='#aaffaa', width=20, font=('Arial', 9, 'bold'))
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.info_label = tk.Label(self.top_frame, text=f"IP СЕРВЕРА: {self.local_ip}", 
                                   fg='blue', font=('Arial', 10, 'bold'))
        self.info_label.pack(side=tk.LEFT, padx=20)

        self.status_label = tk.Label(self.top_frame, text="Статус: Остановлен", fg='red', font=('Arial', 10, 'bold'))
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Сайдбар
        self.side_frame = tk.Frame(master, width=200, bg='#e0e0e0')
        self.side_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        tk.Label(self.side_frame, text="В СЕТИ:", bg='#e0e0e0', font=('Arial', 10, 'bold')).pack(pady=5)
        self.clients_listbox = tk.Listbox(self.side_frame, width=25)
        self.clients_listbox.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        # История чата
        self.chat_history = scrolledtext.ScrolledText(master, state='disabled', wrap='word', 
                                                      font=('Arial', 11), bg='#1e1e1e', fg='#ffffff')
        self.chat_history.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Поле ввода
        self.input_frame = tk.Frame(master)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        self.message_entry = tk.Entry(self.input_frame, font=('Arial', 11))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.message_entry.bind("<Return>", lambda e: self.send_admin_message())
        
        self.send_btn = tk.Button(self.input_frame, text="Отправить", command=self.send_admin_message, 
                                  width=15, bg='#00ff00')
        self.send_btn.pack(side=tk.RIGHT, padx=5)

        self.chat_history.tag_configure("system", foreground="orange")
        self.chat_history.tag_configure("admin", foreground="#00ff00", font=("Arial", 11, "bold"))

        self.load_users()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log_and_display(self, message, tag=None):
        self.chat_history.config(state='normal')
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        if tag == "admin":
            self.chat_history.insert(tk.END, f"[{ts}] Admin: {message}\n", "admin")
            logger.info(f"Admin: {message}")
        elif tag == "system":
            self.chat_history.insert(tk.END, message + "\n", "system")
            logger.info(message)
        else:
            self.chat_history.insert(tk.END, message + "\n")
            logger.info(message)
        self.chat_history.yview(tk.END)
        self.chat_history.config(state='disabled')

    def start_server(self):
        if self.is_running: return
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.bind(('0.0.0.0', SERVER_PORT))
            self.server_sock.listen()
            self.is_running = True
            
            # Пытаемся открыть Брандмауэр
            fw_status = manage_firewall(SERVER_PORT, "add")
            
            self.status_label.config(text="Статус: РАБОТАЕТ", fg='green')
            self.start_btn.config(state=tk.DISABLED)
            
            threading.Thread(target=self.accept_connections, daemon=True).start()
            
            self.log_and_display(f"[СИСТЕМА]: Сервер запущен на {self.local_ip}", "system")
            if not fw_status:
                self.log_and_display("[ВНИМАНИЕ]: Не удалось настроить Брандмауэр (нет прав админа).", "system")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка запуска: {e}")

    def on_closing(self):
        manage_firewall(SERVER_PORT, "delete")
        self.is_running = False
        self.master.destroy()

    def load_users(self):
        config = configparser.ConfigParser()
        try:
            config.read(USERS_CONFIG_FILE, encoding='utf-8')
            if 'USERS' in config:
                for nick, data in config.items('USERS'):
                    clean_nick = nick.strip().lower()
                    pwd = data.split(',')[0].strip()
                    color = data.split(',')[1].strip() if ',' in data else "#FFFFFF"
                    self.registered_users[clean_nick] = {'password': pwd, 'color': color}
        except: pass

    def accept_connections(self):
        while self.is_running:
            try:
                sock, addr = self.server_sock.accept()
                threading.Thread(target=self.auth, args=(sock,), daemon=True).start()
            except: break

    def auth(self, sock):
        try:
            data = sock.recv(1024).decode('utf-8')
            nick, pwd_hash = data.split(':', 1)
            nick_low = nick.strip().lower()

            if nick_low in self.registered_users and self.registered_users[nick_low]['password'] == pwd_hash.strip():
                color = self.registered_users[nick_low]['color']
                sock.send(f"AUTH_SUCCESS:{nick}:{color}".encode('utf-8'))
                
                # USER_LIST
                current_users = ",".join(self.clients_listbox.get(0, tk.END))
                time.sleep(0.1)
                sock.send(f"USER_LIST:{current_users}".encode('utf-8'))

                self.clients.append(sock)
                self.master.after(0, lambda: self.clients_listbox.insert(tk.END, nick))
                
                join_msg = f"[СИСТЕМА] [{datetime.datetime.now().strftime('%H:%M:%S')}]: {nick} вошел в чат!"
                self.log_and_display(join_msg, "system")
                self.broadcast(join_msg)
                self.handle_client(sock, nick)
            else:
                sock.send("AUTH_FAILED".encode('utf-8'))
                sock.close()
        except: pass

    def handle_client(self, sock, nick):
        try:
            while self.is_running:
                msg = sock.recv(1024).decode('utf-8')
                if not msg: break
                self.log_and_display(msg)
                self.broadcast(msg)
                if ADMIN_SOUND_ENABLED:
                    threading.Thread(target=lambda: playsound(SOUND_FILE), daemon=True).start()
        except: pass
        finally:
            if sock in self.clients: self.clients.remove(sock)
            self.master.after(0, lambda: self.remove_nick(nick))
            exit_msg = f"[СИСТЕМА] [{datetime.datetime.now().strftime('%H:%M:%S')}]: {nick} покинул чат."
            self.log_and_display(exit_msg, "system")
            self.broadcast(exit_msg)
            sock.close()

    def remove_nick(self, nick):
        items = self.clients_listbox.get(0, tk.END)
        if nick in items: self.clients_listbox.delete(items.index(nick))

    def broadcast(self, message):
        for c in self.clients:
            try: c.send(message.encode('utf-8'))
            except: pass

    def send_admin_message(self):
        text = self.message_entry.get().strip()
        if text and self.is_running:
            ts = datetime.datetime.now().strftime('%H:%M:%S')
            self.broadcast(f"[{ts}] Админ: {text}")
            self.log_and_display(text, "admin")
            self.message_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()
