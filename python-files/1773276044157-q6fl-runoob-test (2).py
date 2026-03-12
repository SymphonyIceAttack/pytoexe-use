import time
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

def load_config():
    config = {}
    config_path = "config.txt"
    if not os.path.exists(config_path):
        return None
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()
    return config

def send_email(content, cfg):
    if not content.strip():
        return
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = cfg['SENDER_EMAIL']
    msg['To'] = cfg['RECEIVER_EMAIL']
    msg['Subject'] = Header("新增预警数据", 'utf-8')
    try:
        server = smtplib.SMTP_SSL(cfg['SMTP_SERVER'], int(cfg['SMTP_PORT']))
        server.login(cfg['SENDER_EMAIL'], cfg['SENDER_PASSWORD'])
        server.sendmail(cfg['SENDER_EMAIL'], [cfg['RECEIVER_EMAIL']], msg.as_string())
        server.quit()
        print(f"已发送增量行: {content}")
    except Exception as e:
        print(f"邮件发送失败: {e}")

def start_monitor():
    cfg = load_config()
    if not cfg: return
    target_file = cfg['WATCH_FILE']
    
    # 初始状态：跳转到文件末尾，不发送旧数据
    if os.path.exists(target_file):
        last_pos = os.path.getsize(target_file)
    else:
        last_pos = 0
    
    print(f"开始增量监控: {target_file}")

    while True:
        try:
            if os.path.exists(target_file):
                curr_size = os.path.getsize(target_file)
                
                # 情况1：文件变大了（有新增行）
                if curr_size > last_pos:
                    with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_pos) # 跳过已处理的内容
                        new_content = f.read() # 读取所有新增部分
                        
                        # 按行拆分，确保每一行都发送
                        lines = new_content.splitlines()
                        for line in lines:
                            if line.strip():
                                send_email(line, cfg)
                                time.sleep(0.1) # 略微延迟，避免瞬间请求邮件服务器过快
                        
                        last_pos = curr_size # 更新位置
                
                # 情况2：文件变小了（比如日志被清空或重置）
                elif curr_size < last_pos:
                    last_pos = curr_size
                    
            time.sleep(1) # 轮询间隔改为1秒，更灵敏
        except Exception as e:
            print(f"运行异常: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_monitor()