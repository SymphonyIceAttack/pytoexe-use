import tkinter as tk
from tkinter import scrolledtext, simpledialog
import chat_core

class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")
        self.client = chat_core.ChatClient()
        # 创建界面
        self.create_widgets()
        # 先输入服务器地址，再输入昵称
        self.get_server_info()
        self.get_username()
    
    def create_widgets(self):
        # 聊天区域
        self.chat_area = scrolledtext.ScrolledText(self.root, width=60, height=20)
        self.chat_area.pack(padx=10, pady=10)
        self.chat_area.config(state=tk.DISABLED)
        # 输入区域
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=5, padx=10, fill=tk.X)
        # 消息输入框（绑定了回车）
        self.input_entry = tk.Entry(input_frame)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind("<Return>", self.send_message)#这里绑定回车
        # 消息发送按钮
        self.send_btn = tk.Button(input_frame, text="Send", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=5)
    
    def get_server_info(self):
        # 输入服务器IP
        self.server_ip = simpledialog.askstring("Server Address", "Input server IP (default 127.0.0.1):")
        if not self.server_ip:
            self.server_ip = '127.0.0.1'
        
        # 输入服务器端口
        self.server_port = simpledialog.askinteger("Server Port", "Input server port (default 12000):", minvalue=1, maxvalue=65535)
        if not self.server_port:
            self.server_port = 12000
    
    def get_username(self):
        username = simpledialog.askstring("Nickname", "Input your nickname:")
        if username:
            # 启动时传入服务器地址
            port_msg = self.client.start(username, self.server_ip, self.server_port)
            self.append_message(port_msg)
            self.append_message("input <quit> to quit the chat!")
            self.client.set_receive_callback(self.append_message)
    
    def append_message(self, msg):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, msg + "\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
    
    def send_message(self, event=None):
        content = self.input_entry.get()
        if content:
            self.client.send(content)
            self.input_entry.delete(0, tk.END)
            if content == '<quit>':
                self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientGUI(root)
    root.mainloop()