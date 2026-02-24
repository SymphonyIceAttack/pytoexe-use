
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import shutil
import requests
from threading import Thread


def check_java():
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        if "java version" in result.stderr or "openjdk version" in result.stderr:
            return True
    except FileNotFoundError:
        pass
    return False


class MinecraftServerLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Server Launcher")
        self.root.geometry("700x500")
        self.server_dir = os.path.join(os.getcwd(), "server")
        self.server_jar = os.path.join(self.server_dir, "server.jar")

        # UI Components
        self.create_widgets()

        # Check and create server directory
        self.setup_server_directory()

    def create_widgets(self):
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=10)

        label_title = tk.Label(frame_top, text="Minecraft 开服器", font=("Arial", 18))
        label_title.pack()

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.btn_launch = tk.Button(btn_frame, text="启动服务器", command=self.launch_server, width=15)
        self.btn_launch.grid(row=0, column=0, padx=5)

        self.btn_download = tk.Button(btn_frame, text="下载服务端", command=self.download_server, width=15)
        self.btn_download.grid(row=0, column=1, padx=5)

        self.btn_stop = tk.Button(btn_frame, text="停止服务器", state=tk.DISABLED, command=self.stop_server, width=15)
        self.btn_stop.grid(row=0, column=2, padx=5)

        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)

        label_cmd = tk.Label(input_frame, text="发送指令:")
        label_cmd.grid(row=0, column=0, sticky='w')

        self.entry_cmd = tk.Entry(input_frame, width=50)
        self.entry_cmd.bind("<Return>", lambda event: self.send_command())
        self.entry_cmd.grid(row=0, column=1, padx=5)

        self.btn_send = tk.Button(input_frame, text="发送", command=self.send_command)
        self.btn_send.grid(row=0, column=2, padx=5)

        log_label = tk.Label(self.root, text="控制台输出:", anchor='w')
        log_label.pack(fill='x', padx=10)

        self.console_log = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=15)
        self.console_log.pack(fill='both', expand=True, padx=10, pady=5)

    def setup_server_directory(self):
        if not os.path.exists(self.server_dir):
            os.makedirs(self.server_dir)
            self.log_message("[INFO] 已创建 server 文件夹。\n")
        else:
            self.log_message("[INFO] server 文件夹已存在。\n")

        if not os.path.isfile(self.server_jar):
            self.log_message("[WARN] 找不到 server.jar，请点击'下载服务端'按钮获取官方服务端！\n")
        else:
            self.log_message("[INFO] 发现已存在的 server.jar\n")

    def download_server(self):
        if os.path.isfile(self.server_jar):
            response = messagebox.askyesno("文件已存在", "server.jar已存在，是否覆盖？")
            if not response:
                return

        self.log_message("[INFO] 开始下载 Minecraft 服务端...\n")
        self.btn_download.config(state=tk.DISABLED, text="下载中...")
        
        # Start download in a separate thread to prevent UI freezing
        download_thread = Thread(target=self._download_server_thread)
        download_thread.daemon = True
        download_thread.start()

    def _download_server_thread(self):
        try:
            # Official Minecraft server download URL (1.20.1 version)
            url = "https://piston-data.mojang.com/v1/objects/8f3112a1049751cc472ec13e397eade5336ca7ae/server.jar"
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(self.server_jar, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.root.after(0, lambda: self.log_message("[SUCCESS] Minecraft 服务端下载完成！\n"))
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"[ERROR] 下载失败: {str(e)}\n"))
        finally:
            self.root.after(0, lambda: self.btn_download.config(state=tk.NORMAL, text="下载服务端"))

    def launch_server(self):
        if not check_java():
            messagebox.showerror("Java未安装", "系统找不到 Java 运行环境，请先安装 JDK 或 JRE 并配置好 PATH。")
            return

        if not os.path.isfile(self.server_jar):
            response = messagebox.askyesno(
                "缺少服务端",
                "未能找到 server.jar，是否立即下载官方服务端？"
            )
            if response:
                self.download_server()
                return
            else:
                response = messagebox.askyesno(
                    "缺少服务端",
                    "是否选择本地文件导入？"
                )
                if response:
                    jar_path = filedialog.askopenfilename(filetypes=[("JAR files", "*.jar")])
                    if jar_path:
                        shutil.copy(jar_path, self.server_jar)
                        self.log_message(f"[INFO] 成功复制 {os.path.basename(jar_path)} 到 server 文件夹。\n")
                    else:
                        self.log_message("[ERROR] 用户取消了文件选择。\n")
                        return
                else:
                    self.log_message("[ERROR] 启动失败：无法定位 server.jar\n")
                    return

        self.log_message("[INFO] 正在尝试启动 Minecraft 服务器...\n")
        try:
            self.process = subprocess.Popen(
                ["java", "-Xmx1024M", "-Xms1024M", "-jar", "server.jar", "nogui"],
                cwd=self.server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            self.btn_launch.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.read_process_output()
        except Exception as e:
            self.log_message(f"[ERROR] 启动过程中发生异常：{e}\n")

    def read_process_output(self):
        line = self.process.stdout.readline()
        if line:
            self.log_message(line)
            self.root.after(100, self.read_process_output)
        elif self.process.poll() is not None:
            self.log_message("[INFO] 服务器进程结束。\n")
            self.on_server_exit()

    def send_command(self):
        cmd = self.entry_cmd.get().strip()
        if hasattr(self, 'process') and self.process.stdin.writable():
            try:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()
                self.entry_cmd.delete(0, tk.END)
                self.log_message(f">>> {cmd}\n")
            except Exception as e:
                self.log_message(f"[ERROR] 输入命令出错：{str(e)}\n")

    def stop_server(self):
        self.send_command_to_proc("stop")

    def send_command_to_proc(self, cmd):
        if hasattr(self, 'process'):
            try:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()
                self.log_message(f">>> {cmd}\n")
            except Exception as e:
                self.log_message(f"[ERROR] 命令执行出错：{str(e)}\n")

    def on_server_exit(self):
        self.btn_launch.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

    def log_message(self, message):
        self.console_log.insert(tk.END, message)
        self.console_log.yview(tk.END)


if __name__ == "__main__":
    app_root = tk.Tk()
    app = MinecraftServerLauncher(app_root)
    app_root.mainloop()
