import time
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- 配置解析 ---
def load_config():
    config = {}
    with open("config.txt", "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                config[k] = v
    return config

# --- 邮件发送函数 ---
def send_email(content, cfg):
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = cfg['SENDER_EMAIL']
    msg['To'] = cfg['RECEIVER_EMAIL']
    msg['Subject'] = Header("文件更新通知", 'utf-8')

    try:
        # 使用 SSL 连接
        server = smtplib.SMTP_SSL(cfg['SMTP_SERVER'], int(cfg['SMTP_PORT']))
        server.login(cfg['SENDER_EMAIL'], cfg['SENDER_PASSWORD'])
        server.sendmail(cfg['SENDER_EMAIL'], [cfg['RECEIVER_EMAIL']], msg.as_string())
        server.quit()
        print(f"邮件已发送: {content}")
    except Exception as e:
        print(f"发送失败: {e}")

# --- 文件监控逻辑 ---
class FileMonitorHandler(FileSystemEventHandler):
    def __init__(self, file_path, cfg):
        self.file_path = os.path.abspath(file_path)
        self.cfg = cfg
        self.last_size = os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0

    def on_modified(self, event):
        # 排除文件夹变动，只关注目标文件
        if os.path.abspath(event.src_path) == self.file_path:
            time.sleep(0.5)  # 稍微等待，防止文件正被其他进程写入锁死
            try:
                with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        if last_line:
                            send_email(last_line, self.cfg)
            except Exception as e:
                print(f"读取文件出错: {e}")

# --- 主程序 ---
if __name__ == "__main__":
    config = load_config()
    target_file = config['WATCH_FILE']
    
    # 监控目标文件所在的文件夹
    folder_to_watch = os.path.dirname(os.path.abspath(target_file))
    
    event_handler = FileMonitorHandler(target_file, config)
    observer = Observer()
    observer.schedule(event_handler, folder_to_watch, recursive=False)
    
    print(f"正在监控文件: {target_file}")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()