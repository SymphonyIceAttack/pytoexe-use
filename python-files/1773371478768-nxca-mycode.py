import time
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

def load_config():
    config = {}
    try:
        # 读取配置文件本身建议用 utf-8-sig
        with open("config.txt", "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()
        return config
    except Exception as e:
        print(f"读取配置失败: {e}")
        return None

def send_email(content, cfg):
    if not content.strip():
        return
    
    # 构造邮件正文
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = cfg['SENDER_EMAIL']
    msg['To'] = cfg['RECEIVER_EMAIL']
    msg['Subject'] = Header("通达信预警通知", 'utf-8')
    
    try:
        server = smtplib.SMTP_SSL(cfg['SMTP_SERVER'], int(cfg['SMTP_PORT']))
        server.login(cfg['SENDER_EMAIL'], cfg['SENDER_PASSWORD'])
        server.sendmail(cfg['SENDER_EMAIL'], [cfg['RECEIVER_EMAIL']], msg.as_string())
        server.quit()
        print(f"[{time.strftime('%H:%M:%S')}] 发送成功: {content}")
    except Exception as e:
        print(f"邮件发送失败: {e}")

def start_monitor():
    cfg = load_config()
    if not cfg: return
    
    target_file = cfg['WATCH_FILE']
    # 从配置获取编码，如果没有设置则默认 GBK (金融软件最常用)
    file_encoding = cfg.get('FILE_ENCODING', 'GBK')
    
    if os.path.exists(target_file):
        last_pos = os.path.getsize(target_file)
    else:
        last_pos = 0
    
    print(f"正在监控(编码:{file_encoding}): {target_file}")

    while True:
        try:
            if os.path.exists(target_file):
                curr_size = os.path.getsize(target_file)
                
                if curr_size > last_pos:
                    with open(target_file, 'rb') as f:
                        f.seek(last_pos)
                        raw_data = f.read()
                        
                        # 使用配置指定的编码解码
                        try:
                            text_data = raw_data.decode(file_encoding)
                        except UnicodeDecodeError:
                            # 如果指定编码失败，回退到自动忽略错误模式
                            text_data = raw_data.decode(file_encoding, errors='ignore')
                        
                        lines = text_data.splitlines()
                        for line in lines:
                            if line.strip():
                                send_email(line, cfg)
                                time.sleep(0.3)
                        
                        last_pos = curr_size
                elif curr_size < last_pos:
                    last_pos = curr_size
            
            time.sleep(1)
        except Exception as e:
            print(f"异常: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_monitor()