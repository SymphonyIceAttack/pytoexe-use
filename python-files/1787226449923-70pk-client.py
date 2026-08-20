import socket
import threading
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Мессенджер")
        self.root.geometry("500x500")

        self.nick = None
        self.sock = None
        self.running = True

        # Поле ввода ника
        self.nick_frame = tk.Frame(root)
        self.nick_frame.pack(pady=10)
        tk.Label(self.nick_frame, text="Ваш ник:").pack(side=tk.LEFT, padx=5)
        self.nick_entry = tk.Entry(self.nick_frame, width=20)
        self.nick_entry.pack(side=tk.LEFT, padx=5)
        self.connect_btn = tk.Button(self.nick_frame, text="Подключиться", command=self.connect)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        # Чат
        self.chat_area = scrolledtext.ScrolledText(root, state="disabled", height=20)
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Поле ввода сообщения
        self.msg_frame = tk.Frame(root)
        self.msg_frame.pack(pady=5, fill=tk.X, padx=10)
        self.msg_entry = tk.Entry(self.msg_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.send_btn = tk.Button(self.msg_frame, text="Отправить", command=self.send_message, state="disabled")
        self.send_btn.pack(side=tk.RIGHT)

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def connect(self):
        nick = self.nick_entry.get().strip()
        if not nick:
            messagebox.showerror("Ошибка", "Введите ник")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(("127.0.0.1", 5555))
            self.nick = nick
            self.sock.send(json.dumps({"nick": nick}).encode())

            self.connect_btn.config(state="disabled")
            self.nick_entry.config(state="disabled")
            self.send_btn.config(state="normal")

            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.display_message("🔌", "Подключено к серверу")
        except:
            messagebox.showerror("Ошибка", "Не удалось подключиться к серверу")

    def receive_messages(self):
        while self.running:
            try:
                data = self.sock.recv(1024).decode()
                if not data:
                    break
                msg_data = json.loads(data)
                if msg_data["type"] == "system":
                    self.display_message("⚙️", msg_data["msg"])
                else:
                    self.display_message(msg_data["nick"], msg_data["msg"])
            except:
                break

    def send_message(self):
        text = self.msg_entry.get().strip()
        if text and self.sock:
            try:
                self.sock.send(text.encode())
                self.msg_entry.delete(0, tk.END)
            except:
                self.display_message("⚠️", "Ошибка отправки")

    def display_message(self, sender, text):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, f"{sender}: {text}\n")
        self.chat_area.config(state="disabled")
        self.chat_area.see(tk.END)

    def close(self):
        self.running = False
        if self.sock:
            self.sock.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()