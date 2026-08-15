import os
import sys
import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk

ACCOUNTS_FILE = "users.txt"

class LanMessengerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LAN Мессенджер (Без Node.js)")
        self.root.geometry("450x550")
        self.root.configure(bg="#1e1e24")
        
        self.current_user = None
        self.server_socket = None
        self.client_socket = None
        self.is_running = False

        # Стилизация интерфейса
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TLabel", background="#1e1e24", foreground="#ffffff", font=("Segoe UI", 11))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#007acc", foreground="white", borderwidth=0)
        self.style.map("TButton", background=[("active", "#005999")])
        
        self.show_auth_screen()

    # --- ЭКРАН 1: АВТОРИЗАЦИЯ / РЕГИСТРАЦИЯ ---
    def show_auth_screen(self):
        self.clear_screen()
        
        frame = tk.Frame(self.root, bg="#2a2a35", padx=25, pady=25)
        frame.place(relx=0.5, rely=0.5, anchor="center", width=350, height=320)
        
        title = tk.Label(frame, text="Вход / Регистрация", bg="#2a2a35", fg="#ffffff", font=("Segoe UI", 16, "bold"))
        title.pack(pady=10)
        
        tk.Label(frame, text="Логин:", bg="#2a2a35", fg="#ffffff").pack(anchor="w")
        self.login_entry = tk.Entry(frame, bg="#3a3a4a", fg="#ffffff", insertbackground="white", bd=0, font=("Segoe UI", 11))
        self.login_entry.pack(fill="x", ipady=6, pady=5)
        
        tk.Label(frame, text="Пароль:", bg="#2a2a35", fg="#ffffff").pack(anchor="w")
        self.pass_entry = tk.Entry(frame, show="*", bg="#3a3a4a", fg="#ffffff", insertbackground="white", bd=0, font=("Segoe UI", 11))
        self.pass_entry.pack(fill="x", ipady=6, pady=5)
        
        btn_login = tk.Button(frame, text="Войти", bg="#28a745", fg="white", font=("Segoe UI", 11, "bold"), bd=0, command=self.handle_login)
        btn_login.pack(fill="x", ipady=6, pady=8)
        
        btn_reg = tk.Button(frame, text="Зарегистрироваться", bg="#4a4a5a", fg="white", font=("Segoe UI", 10), bd=0, command=self.handle_register)
        btn_reg.pack(fill="x", ipady=4)

    def handle_login(self):
        u, p = self.login_entry.get().strip(), self.pass_entry.get().strip()
        if not u or not p: return
        
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        file_u, file_p = line.strip().split(":", 1)
                        if file_u == u and file_p == p:
                            self.current_user = u
                            self.show_lan_screen()
                            return
        messagebox.showerror("Ошибка", "Неверный логин или пароль!")

    def handle_register(self):
        u, p = self.login_entry.get().strip(), self.pass_entry.get().strip()
        if not u or not p: 
            messagebox.showwarning("Внимание", "Заполните все поля!")
            return
        
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith(f"{u}:"):
                        messagebox.showerror("Ошибка", "Пользователь уже существует!")
                        return
                        
        with open(ACCOUNTS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{u}:{p}\n")
        messagebox.showinfo("Успех", "Аккаунт успешно создан в users.txt!")

    # --- ЭКРАН 2: НАСТРОЙКА ЛОКАЛЬНОЙ СЕТИ ---
    def show_lan_screen(self):
        self.clear_screen()
        
        frame = tk.Frame(self.root, bg="#2a2a35", padx=20, pady=20)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        welcome = tk.Label(frame, text=f"Привет, {self.current_user}!", bg="#2a2a35", fg="#00a2ff", font=("Segoe UI", 14, "bold"))
        welcome.pack(pady=5)
        
        # Блок Создания
        lbl_s = tk.Label(frame, text="Вариант 1: Создать сервер чата", bg="#2a2a35", fg="#ffcc00", font=("Segoe UI", 11, "bold"))
        lbl_s.pack(pady=10)
        self.sport_entry = tk.Entry(frame, bg="#3a3a4a", fg="#ffffff", bd=0, font=("Segoe UI", 11), justify="center")
        self.sport_entry.insert(0, "5000")
        self.sport_entry.pack(ipady=4)
        
        btn_start = tk.Button(frame, text="Создать сервер", bg="#007acc", fg="white", font=("Segoe UI", 10, "bold"), bd=0, command=self.start_server_thread)
        btn_start.pack(fill="x", ipady=6, pady=5)
        
        # Блок Подключения
        lbl_c = tk.Label(frame, text="Вариант 2: Подключиться к чату", bg="#2a2a35", fg="#28a745", font=("Segoe UI", 11, "bold"))
        lbl_c.pack(pady=10)
        
        tk.Label(frame, text="IP адрес:", bg="#2a2a35", fg="#bbb").pack()
        self.cip_entry = tk.Entry(frame, bg="#3a3a4a", fg="#ffffff", bd=0, font=("Segoe UI", 11), justify="center")
        self.cip_entry.insert(0, "127.0.0.1")
        self.cip_entry.pack(ipady=4)
        
        tk.Label(frame, text="Порт:", bg="#2a2a35", fg="#bbb").pack()
        self.cport_entry = tk.Entry(frame, bg="#3a3a4a", fg="#ffffff", bd=0, font=("Segoe UI", 11), justify="center")
        self.cport_entry.insert(0, "5000")
        self.cport_entry.pack(ipady=4, pady=5)
        
        btn_conn = tk.Button(frame, text="Подключиться", bg="#28a745", fg="white", font=("Segoe UI", 10, "bold"), bd=0, command=self.connect_to_server)
        btn_conn.pack(fill="x", ipady=6, pady=5)

    # --- ЗАПУСК СОБСТВЕННОГО СЕРВЕРА (В ОТДЕЛЬНОМ ПОТОКЕ) ---
    def start_server_thread(self):
        port = int(self.sport_entry.get().strip())
        threading.Thread(target=self.run_server, args=(port,), daemon=True).start()
        # Автоматически подключаемся к самому себе
        self.cip_entry.delete(0, tk.END)
        self.cip_entry.insert(0, "127.0.0.1")
        self.cport_entry.delete(0, tk.END)
        self.cport_entry.insert(0, str(port))
        self.connect_to_server()

    def run_server(self, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind(("0.0.0.0", port))
            self.server_socket.listen(5)
            self.server_clients = []
            
            while True:
                client_conn, addr = self.server_socket.accept()
                self.server_clients.append(client_conn)
                threading.Thread(target=self.broadcast_messages, args=(client_conn,), daemon=True).start()
        except Exception as e:
            pass

    def broadcast_messages(self, client_conn):
        while True:
            try:
                data = client_conn.recv(1024).decode("utf-8")
                if not data: break
                for client in self.server_clients:
                    try: client.send(data.encode("utf-8"))
                    except: pass
            except:
                break

    # --- ПОДКЛЮЧЕНИЕ К ЧАТУ ---
    def connect_to_server(self):
        ip = self.cip_entry.get().strip()
        port = int(self.cport_entry.get().strip())
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((ip, port))
            self.show_chat_screen()
            threading.Thread(target=self.receive_chat_messages, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к {ip}:{port}")

    # --- ЭКРАН 3: САМ ЧАТ ---
    def show_chat_screen(self):
        self.clear_screen()
        
        self.chat_text = tk.Text(self.root, bg="#15151d", fg="#ffffff", bd=0, font=("Segoe UI", 11), state="disabled")
        self.chat_text.pack(fill="both", expand=True, padx=15, pady=15)
        
        bottom_frame = tk.Frame(self.root, bg="#1e1e24")
        bottom_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.msg_entry = tk.Entry(bottom_frame, bg="#2a2a35", fg="#ffffff", insertbackground="white", bd=0, font=("Segoe UI", 11))
        self.msg_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.msg_entry.bind("<Return>", lambda event: self.send_message())
        
        btn_send = tk.Button(bottom_frame, text="Отправить", bg="#007acc", fg="white", bd=0, font=("Segoe UI", 10, "bold"), command=self.send_message)
        btn_send.pack(side="right", padx=(10, 0), ipady=6, ipadx=15)

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if not msg: return
        formatted_msg = f"{self.current_user}: {msg}"
        try:
            self.client_socket.send(formatted_msg.encode("utf-8"))
            self.msg_entry.delete(0, tk.END)
        except:
            messagebox.showerror("Ошибка", "Соединение потеряно.")

    def receive_chat_messages(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode("utf-8")
                if not data: break
                
                self.chat_text.config(state="normal")
                self.chat_text.insert(tk.END, data + "\n")
                self.chat_text.config(state="disabled")
                self.chat_text.see(tk.END)
            except:
                break

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LanMessengerApp(root)
    root.mainloop()
