import paramiko
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import re

DEFAULT_THREADS = 10

class SSHExecutorApp:
    def __init__(self, master):
        self.master = master
        master.title("华为交换机批量配置工具（自由命令）")
        master.geometry("820x680")

        self.excel_path = tk.StringVar()
        self.thread_num = tk.IntVar(value=DEFAULT_THREADS)
        self.queue = queue.Queue()
        self.running = False

        self.create_widgets()
        self.process_queue()  # 启动日志循环

    def create_widgets(self):
        # 文件选择
        frame_file = tk.LabelFrame(self.master, text="设备清单 Excel", padx=5, pady=5)
        frame_file.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_file, text="文件路径:").grid(row=0, column=0, sticky=tk.W)
        entry_file = tk.Entry(frame_file, textvariable=self.excel_path, width=60)
        entry_file.grid(row=0, column=1, padx=5)
        btn_browse = tk.Button(frame_file, text="浏览...", command=self.browse_file)
        btn_browse.grid(row=0, column=2, padx=5)

        tk.Label(frame_file, text="最大并发线程数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        spin_threads = tk.Spinbox(frame_file, from_=1, to=20, textvariable=self.thread_num, width=5)
        spin_threads.grid(row=1, column=1, sticky=tk.W, padx=5)

        # 命令输入（完全自由）
        frame_cmd = tk.LabelFrame(self.master, text="配置命令（每行一条，请勿包含 quit 命令，否则会断开连接）", padx=5, pady=5)
        frame_cmd.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.cmd_text = scrolledtext.ScrolledText(frame_cmd, height=14, font=("Consolas", 10))
        self.cmd_text.pack(fill=tk.BOTH, expand=True)
        # 预置示例（您可自行修改，或清空自行输入）
        example = """system-view
aaa
local-user xzclouduser password irreversible-cipher BMC@Manager0507
local-user xzclouduser privilege level 15
local-user xzclouduser service-type ssh
local-user xzclouduseri password irreversible-cipher BMC@Manager0507
local-user xzclouduseri privilege level 2
local-user xzclouduseri service-type ssh
local-user xzcloudusera password irreversible-cipher BMC@Manager0507
local-user xzcloudusera privilege level 1
local-user xzcloudusera service-type ssh
quit
ssh user xzclouduser
ssh user xzclouduser authentication-type password
ssh user xzclouduser service-type stelnet
ssh user xzclouduseri
ssh user xzclouduseri authentication-type password
ssh user xzclouduseri service-type stelnet
ssh user xzcloudusera
ssh user xzcloudusera authentication-type password
ssh user xzcloudusera service-type stelnet
return
save"""
        self.cmd_text.insert(tk.END, example)

        # 按钮
        frame_btn = tk.Frame(self.master)
        frame_btn.pack(fill=tk.X, padx=10, pady=5)

        btn_start = tk.Button(frame_btn, text="开始执行", command=self.start_execution, bg="#4CAF50", fg="white", width=12)
        btn_start.pack(side=tk.LEFT, padx=5)
        btn_clear = tk.Button(frame_btn, text="清空日志", command=self.clear_log, width=12)
        btn_clear.pack(side=tk.LEFT, padx=5)
        btn_exit = tk.Button(frame_btn, text="退出", command=self.master.quit, width=12)
        btn_exit.pack(side=tk.RIGHT, padx=5)

        # 日志
        frame_log = tk.LabelFrame(self.master, text="执行日志", padx=5, pady=5)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(frame_log, height=10, font=("Consolas", 9), state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if filename:
            self.excel_path.set(filename)

    def log(self, msg):
        """线程安全地将日志放入队列"""
        self.queue.put(msg)

    def process_queue(self):
        """从队列取出日志并显示"""
        try:
            while True:
                msg = self.queue.get_nowait()
                self.log_text.config(state='normal')
                self.log_text.insert(tk.END, msg + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state='disabled')
        except queue.Empty:
            pass
        finally:
            self.master.after(50, self.process_queue)  # 更频繁刷新

    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

    def start_execution(self):
        if self.running:
            messagebox.showwarning("提示", "已有任务正在执行，请等待。")
            return

        # 获取文件
        excel_file = self.excel_path.get().strip()
        if not excel_file or not os.path.isfile(excel_file):
            messagebox.showerror("错误", "请选择有效的 Excel 文件。")
            return

        # 获取命令，原样保留
        cmd_raw = self.cmd_text.get(1.0, tk.END).strip()
        if not cmd_raw:
            messagebox.showerror("错误", "请输入命令。")
            return
        commands = [line.strip() for line in cmd_raw.splitlines() if line.strip() and not line.strip().startswith('#')]
        # 检查是否包含 quit，给出警告但不强制过滤（用户自己负责）
        if any(cmd.lower() == "quit" for cmd in commands):
            if not messagebox.askyesno("警告", "检测到 'quit' 命令，执行后可能会提前断开连接，导致后续命令失败。\n是否继续？"):
                return

        # 读取Excel
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            messagebox.showerror("错误", f"读取 Excel 失败: {e}")
            return

        required = ['BMC IP', '登录账号', '登录密码']
        for col in required:
            if col not in df.columns:
                messagebox.showerror("错误", f"Excel 缺少列: {col}")
                return

        tasks = [(idx, row) for idx, row in df.iterrows()
                 if not pd.isna(row['BMC IP']) and not pd.isna(row['登录账号']) and not pd.isna(row['登录密码'])]
        if not tasks:
            messagebox.showerror("错误", "Excel 无有效数据。")
            return

        # 立即在日志中显示开始信息（强制刷新）
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, "=" * 60 + "\n")
        self.log_text.insert(tk.END, f"开始执行，设备数 {len(tasks)}，并发 {self.thread_num.get()}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.log_text.update()  # 强制刷新UI

        self.running = True
        threading.Thread(target=self.run_tasks, args=(excel_file, df, tasks, commands), daemon=True).start()

    def run_tasks(self, excel_file, df, tasks, commands):
        max_workers = self.thread_num.get()
        results = []
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_idx = {executor.submit(self.execute_device, idx, row, commands): idx for idx, row in tasks}
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        res = future.result()
                        results.append((idx, res))
                    except Exception as e:
                        row = df.loc[idx]
                        err = f"线程异常: {str(e)}"
                        self.log(f"[{row['BMC IP']}] {err}")
                        results.append((idx, {
                            'BMC IP': row['BMC IP'],
                            '登录账号': row['登录账号'],
                            '登录密码': row['登录密码'],
                            '执行结果': err
                        }))
        except Exception as e:
            self.log(f"全局错误: {e}")
        finally:
            results.sort(key=lambda x: x[0])
            result_df = pd.DataFrame([r[1] for r in results])
            base, ext = os.path.splitext(excel_file)
            out = f"{base}_result{ext}"
            try:
                result_df.to_excel(out, index=False)
                self.log(f"结果已保存: {out}")
            except Exception as e:
                self.log(f"保存失败: {e}")
            self.running = False
            self.log("所有任务执行完毕。")

    def execute_device(self, idx, row, commands):
        ip = row['BMC IP']
        username = row['登录账号']
        password = row['登录密码']
        self.log(f"[{ip}] 开始执行...")
        result = self.ssh_execute(ip, username, password, commands)
        self.log(f"[{ip}] 结果: {result}")
        return {
            'BMC IP': ip,
            '登录账号': username,
            '登录密码': password,
            '执行结果': result
        }

    def ssh_execute(self, ip, username, password, commands):
        client = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username=username, password=password, timeout=10)
            channel = client.invoke_shell()
            time.sleep(2)

            output = ""
            # 处理密码更改提示
            while channel.recv_ready():
                output += channel.recv(65535).decode('utf-8', errors='ignore')
            if "Change now?" in output:
                channel.send("n\n")
                time.sleep(1)
                while channel.recv_ready():
                    output += channel.recv(65535).decode('utf-8', errors='ignore')

            error_msgs = []
            for cmd in commands:
                if cmd.strip().lower() == "save":
                    output, error_msgs = self._handle_save(channel, output, error_msgs)
                    continue

                channel.send(cmd + "\n")
                time.sleep(1)  # 固定间隔1秒
                while channel.recv_ready():
                    output += channel.recv(65535).decode('utf-8', errors='ignore')
                # 检查错误（按关键字）
                if "Error:" in output or "Fail" in output:
                    lines = output.split('\n')
                    for line in lines:
                        if "Error:" in line or "Fail" in line:
                            error_msgs.append(line.strip())

            client.close()

            if error_msgs:
                return "执行出错: " + "; ".join(list(dict.fromkeys(error_msgs))[:5])
            else:
                if "Save the configuration successfully." in output:
                    return "配置执行成功并保存。"
                else:
                    return "配置执行完成（可能未保存）。"
        except paramiko.AuthenticationException:
            return "SSH认证失败，请检查用户名/密码。"
        except paramiko.SSHException as e:
            return f"SSH连接异常: {str(e)}"
        except Exception as e:
            return f"未知异常: {str(e)}"
        finally:
            if client:
                client.close()

    def _handle_save(self, channel, output, error_msgs):
        channel.send("save\n")
        time.sleep(2)
        confirm_sent = False
        save_ok = False
        start = time.time()
        while time.time() - start < 30:
            while channel.recv_ready():
                output += channel.recv(65535).decode('utf-8', errors='ignore')
            if not confirm_sent and re.search(r'continue\?', output, re.IGNORECASE):
                channel.send("y\n")
                confirm_sent = True
                time.sleep(1)
                continue
            if "Save the configuration successfully." in output:
                save_ok = True
                break
            time.sleep(0.5)
        if not save_ok:
            error_msgs.append("未检测到保存确认或保存成功" if not confirm_sent else "已确认但未收到保存成功")
        return output, error_msgs

def main():
    root = tk.Tk()
    app = SSHExecutorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()