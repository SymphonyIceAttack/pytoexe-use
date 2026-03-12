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
    # 增加 encoding='utf-8-sig' 以处理某些 Windows 记事本带 BOM 的情况
    with open(config_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()
    return config

def send_email(content, cfg):
    # 这里的 content 就是文件里的一整行原始数据
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
        # 仅在本地控制台提示，不会发到邮件里
        print(f">>> 邮件发送成功: {content[:20]}...") 
    except Exception as e:
        print(f"邮件发送失败: {e}")

def start_monitor():
    cfg = load_config()
    if not cfg: 
        print("错误：无法读取配置文件！")
        return
    
    target_file = cfg['WATCH_FILE']
    
    # 初始化：跳到末尾
    if os.path.exists(target_file):
        last_pos = os.path.getsize(target_file)
    else:
        last_pos = 0
    
    print(f"正在监控中: {target_file}")

    while True:
        try:
            if os.path.exists(target_file):
                curr_size = os.path.getsize(target_file)
                
                if curr_size > last_pos:
                    # 使用 'rb' 模式（二进制）读取，再手动解码，能更好保留原始字符
                    with open(target_file, 'rb') as f:
                        f.seek(last_pos)
                        new_data = f.read()
                        
                        # 将二进制解码为文本，忽略无法解析的坏字符
                        new_text = new_data.decode('utf-8', errors='ignore')
                        
                        if new_text:
                            # 按照换行符拆分
                            lines = new_text.replace('\r', '').split('\n')
                            for line in lines:
                                if line.strip():
                                    # 直接发送原始行内容
                                    send_email(line, cfg)
                                    time.sleep(0.5) 
                        
                        last_pos = curr_size
                
                elif curr_size < last_pos:
                    print("检测到文件被重置/缩小，更新指针...")
                    last_pos = curr_size
            
            time.sleep(1)
        except Exception as e:
            print(f"程序运行异常: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_monitor()