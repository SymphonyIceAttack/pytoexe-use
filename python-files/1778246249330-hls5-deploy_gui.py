import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
from pathlib import Path

import paramiko


class DeployThread(threading.Thread):
    def __init__(self, host, port, username, password, domain, service_port,
                 remote_base, local_base, log_queue, stop_event):
        super().__init__(daemon=True) # daemon=True 表示这是一个守护线程——当主程序退出时，这个线程会自动终止，不会阻止程序关闭。
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.domain = domain
        self.service_port = service_port
        self.remote_base = remote_base
        self.local_base = Path(local_base)
        self.log_queue = log_queue
        self.stop_event = stop_event
        self.ssh = None
        self.sftp = None

    def log(self, message, level="INFO"):
        self.log_queue.put((level, message))

    def run(self):
        try:
            if not self.connect_ssh():
                return
            if not self.install_dependencies():
                return
            if not self.upload_files():
                return
            if not self.install_python_deps():
                return
            if not self.setup_systemd():
                return
            if not self.open_firewall():
                return

            self.log(f"访问地址：http://{self.domain}:{self.service_port}", "SUCCESS")
        except Exception as e:
            self.log(f"终止: {str(e)}", "ERROR")
        finally:
            self.close_connections()

    def check_stop(self):
        if self.stop_event.is_set():
            self.log("已取消", "WARN")
            return True
        return False

    def exec_command(self, command):
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command, timeout=60)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='ignore')
            err = stderr.read().decode('utf-8', errors='ignore')
            return out, err, exit_code
        except Exception as e:
            return "", str(e), -1

    def run_step(self, step_name, command, expect_exit=0):
        if self.check_stop():
            return False
        self.log(f"[步骤] {step_name} ...", "INFO")
        out, err, code = self.exec_command(command)
        if out: self.log(out.strip(), "DEBUG")
        if err and code != expect_exit:
            self.log(err.strip(), "ERROR")
        elif err:
            self.log(err.strip(), "WARN")
        if code != expect_exit:
            self.log(f"{step_name} 失败 (返回码 {code})", "ERROR")
            return False
        self.log(f"{step_name} 完成", "SUCCESS")
        return True

    def connect_ssh(self):
        self.log("正在连接 VPS", "INFO")
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, port=self.port, username=self.username,
                             password=self.password, timeout=15)
            self.sftp = self.ssh.open_sftp()
            self.log("SSH 连接成功", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"SSH 连接失败: {str(e)}", "ERROR")
            return False

    def close_connections(self):
        if self.sftp:
            try:
                self.sftp.close()
            except:
                pass
        if self.ssh:
            try:
                self.ssh.close()
            except:
                pass

    def install_dependencies(self):
        if self.check_stop():
            return False
        return self.run_step("安装软件包",
                             "apt-get update -y && apt-get install -y python3 python3-pip")

    def upload_files(self):
        if self.check_stop():
            return False
        self.log("上传文件 ...", "INFO")

        _, _, code = self.exec_command(f"mkdir -p {self.remote_base}")
        if code != 0:
            self.log("创建失败", "ERROR")
            return False

        try:
            self._upload_folder(self.local_base, self.remote_base)
            self.log("上传完成", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"上传出错: {str(e)}", "ERROR")
            return False

    def _upload_folder(self, local_path, remote_path):
        if not local_path.exists():
            raise FileNotFoundError(f"路径不存在: {local_path}")
        try:
            self.sftp.stat(remote_path)
        except FileNotFoundError:
            self.sftp.mkdir(remote_path)

        for item in local_path.iterdir():
            local_item = local_path / item.name
            remote_item = remote_path + "/" + item.name
            if local_item.is_dir():
                self._upload_folder(local_item, remote_item)
            else:
                self.log(f"  上传: {local_item} -> {remote_item}", "DEBUG")
                self.sftp.put(str(local_item), remote_item)
                self.sftp.chmod(remote_item, 0o644)

    def install_python_deps(self):
        if self.check_stop():
            return False
        cmd = f"cd {self.remote_base} && pip3 install -r requirements.txt"
        return self.run_step("安装依赖", cmd)

    def setup_systemd(self):
        # 部署 systemd 服务
        if self.check_stop():
            return False

        service_content = f"""[Unit]
Description=Temp Share Service
After=network.target

[Service]
User={self.username}
WorkingDirectory={self.remote_base}
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port {self.service_port}
Restart=always

[Install]
WantedBy=multi-user.target
"""
        tmp_service = "/tmp/temp_share.service"
        self.sftp.open(tmp_service, 'w').write(service_content)

        cmds = [
            ("设置 systemd 服务",
             f"mv {tmp_service} /etc/systemd/system/temp_share.service && systemctl daemon-reload && systemctl enable temp_share && systemctl restart temp_share",
             0),
        ]
        for step, cmd, expect in cmds:
            if not self.run_step(step, cmd, expect):
                return False
        return True

    def open_firewall(self):
        if self.check_stop():
            return False
        out, _, code = self.exec_command("which ufw")
        if code != 0:
            # self.log("未检测到 ufw，跳过防火墙配置", "INFO")
            return True

        out2, _, code2 = self.exec_command("ufw status | grep -q 'Status: active' && echo ACTIVE || echo INACTIVE")
        if "ACTIVE" not in out2:
            # self.log("ufw 未启用，跳过防火墙配置", "INFO")
            return True

        return self.run_step(f"防火墙放行端口 {self.service_port}",
                             f"ufw allow {self.service_port}/tcp")


class DeployApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("自动部署")
        self.geometry("700x650")
        self.resizable(True, True)

        self.stop_event = threading.Event()
        self.deploy_thread = None
        self.log_queue = queue.Queue()

        self.create_widgets()
        self.poll_log_queue()

    def create_widgets(self):
        title = tk.Label(self, text="自动部署", font=("微软雅黑", 16, "bold"))
        title.pack(pady=10)

        conn_frame = tk.LabelFrame(self, text="VPS连接", padx=10, pady=10)
        conn_frame.pack(fill="x", padx=20, pady=5)

        fields = [
            ("主机 IP:", "host", "91.213.186.86"),
            ("SSH端口:", "ssh_port", "22"),
            ("用户名:", "username", "root"),
            ("密码:", "password", "EbHRdHVw3Hci8TO9"),
            ("域名:", "domain", "chat.minamo.top"),
            ("服务端口:", "service_port", "9090"),
            ("远程项目目录:", "remote_base", "/home/ubuntu/temp_share"),
            ("本地项目文件夹:", "local_base", "./temp_share"),
        ]

        self.inputs = {}
        for i, (label, key, default) in enumerate(fields):
            tk.Label(conn_frame, text=label, anchor="w").grid(row=i, column=0, sticky="w", pady=2)
            entry = tk.Entry(conn_frame, width=40)
            entry.insert(0, default)
            entry.grid(row=i, column=1, sticky="ew", padx=5)
            if key == "password":
                entry.config(show="*")
            self.inputs[key] = entry

        conn_frame.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        self.start_btn = tk.Button(btn_frame, text="开始部署", font=("微软雅黑", 11),
                                   bg="#4CAF50", fg="white", width=15, command=self.start_deploy)
        self.start_btn.pack(side="left", padx=10)
        self.stop_btn = tk.Button(btn_frame, text="取消部署", font=("微软雅黑", 11),
                                  bg="#f44336", fg="white", width=15, command=self.stop_deploy,
                                  state="disabled")
        self.stop_btn.pack(side="left", padx=10)

        self.progress = ttk.Progressbar(self, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill="x", padx=20, pady=5)

        log_frame = tk.LabelFrame(self, text="日志", padx=5, pady=5)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap="word", state="disabled",
                                                  font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)

        self.log_text.tag_config("INFO", foreground="black")
        self.log_text.tag_config("SUCCESS", foreground="green")
        self.log_text.tag_config("WARN", foreground="orange")
        self.log_text.tag_config("ERROR", foreground="red")
        self.log_text.tag_config("DEBUG", foreground="gray")

    def append_log(self, level, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n", level)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def poll_log_queue(self):
        try:
            while True:
                level, msg = self.log_queue.get_nowait()
                self.append_log(level, msg)
        except queue.Empty:
            pass
        self.after(100, self.poll_log_queue)

    def start_deploy(self):
        host = self.inputs["host"].get().strip()
        ssh_port = self.inputs["ssh_port"].get().strip()
        username = self.inputs["username"].get().strip()
        password = self.inputs["password"].get().strip()
        domain = self.inputs["domain"].get().strip()
        service_port = self.inputs["service_port"].get().strip()
        remote_base = self.inputs["remote_base"].get().strip()
        local_base = self.inputs["local_base"].get().strip()

        if not all([host, ssh_port, username, password, domain, service_port, remote_base, local_base]):
            messagebox.showwarning("输入不完整", "请填写所有字段。")
            return
        if not service_port.isdigit():
            messagebox.showerror("端口错误", "服务端口必须是数字。")
            return

        local_path = Path(local_base)
        if not local_path.exists():
            messagebox.showerror("路径错误", f"本地项目文件夹不存在：{local_base}")
            return

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress.start(10)

        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")

        self.stop_event.clear()

        self.deploy_thread = DeployThread(
            host=host,
            port=int(ssh_port),
            username=username,
            password=password,
            domain=domain,
            service_port=int(service_port),
            remote_base=remote_base,
            local_base=local_base,
            log_queue=self.log_queue,
            stop_event=self.stop_event
        )
        self.deploy_thread.start()
        self.monitor_thread()

    def stop_deploy(self):
        if self.deploy_thread and self.deploy_thread.is_alive():
            self.stop_event.set()
            self.append_log("WARN", "正在取消...")
            self.stop_btn.config(state="disabled")

    def monitor_thread(self):
        if self.deploy_thread and self.deploy_thread.is_alive():
            self.after(500, self.monitor_thread)
        else:
            self.progress.stop()
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.deploy_thread = None

    def on_close(self):
        if self.deploy_thread and self.deploy_thread.is_alive():
            self.stop_event.set()
        self.destroy()


if __name__ == "__main__":
    app = DeployApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
