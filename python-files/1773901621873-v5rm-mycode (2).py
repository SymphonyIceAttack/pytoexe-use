import time
import os
import smtplib
import re
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置加载（增强版：兼容在线打包环境） ---
def load_config():
    # 默认配置：作为保底，防止在线编译器因找不到文件而报错
    config = {
        'WATCH_FILE': r'C:\data\log.txt',
        'SMTP_SERVER': 'smtp.qq.com',
        'SMTP_PORT': '465',
        'SENDER_EMAIL': 'your_email@qq.com',
        'SENDER_PASSWORD': 'your_auth_code',
        'RECEIVER_EMAIL': 'target_email@example.com',
        'FILE_ENCODING': 'GBK'
    }
    try:
        # 优先读取本地同级目录下的 config.txt
        config_path = "config.txt"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        config[k.strip()] = v.strip()
            print(f"[{time.strftime('%H:%M:%S')}] 成功加载本地 config.txt 配置")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] 未找到 config.txt，使用代码内置默认值（仅用于打包/测试）")
    except Exception as e:
        print(f"读取配置异常: {e}")
    return config

# --- 2. 智能解析与优先级逻辑（适配 6 字公式名） ---
def parse_and_rank(line):
    # 正则提取：代码、名称、公式名
    pattern = r"预警品种: (\d{6}) (.*?) 预警公式: (.*)"
    match = re.search(pattern, line)
    
    if match:
        code, name, formula = match.groups()
        score = 0
        
        # 核心关键词评分逻辑
        if "底" in formula: score += 5
        if "共振" in formula: score += 3
        if "板块" in formula: score += 2
        
        # 等级判定
        if score >= 8: 
            level = "【★特级关注★】"
        elif score >= 5: 
            level = "【优先观察】"
        else:
            level = "【普通预警】"
            
        subject = f"{level} {name}({code}) {formula}"
        content = (f"时间: {time.strftime('%H:%M:%S')}\n"
                   f"股票: {name} ({code})\n"
                   f"逻辑: {formula}\n"
                   f"评分: {score}\n"
                   f"建议: 信号已触发，请检查尾盘量能及板块强度。")
        return subject, content
    
    return "通达信预警通知", line

# --- 3. 邮件发送模块 ---
def send_email(line, cfg):
    if not line.strip():
        return
    
    subject_text, body_content = parse_and_rank(line)
    
    msg = MIMEText(body_content, 'plain', 'utf-8')
    msg['From'] = cfg['SENDER_EMAIL']
    msg['To'] = cfg['RECEIVER_EMAIL']
    msg['Subject'] = Header(subject_text, 'utf-8')
    
    try:
        server = smtplib.SMTP_SSL(cfg['SMTP_SERVER'], int(cfg['SMTP_PORT']))
        server.login(cfg['SENDER_EMAIL'], cfg['SENDER_PASSWORD'])
        server.sendmail(cfg['SENDER_EMAIL'], [cfg['RECEIVER_EMAIL']], msg.as_string())
        server.quit()
        print(f"[{time.strftime('%H:%M:%S')}] {subject_text} 发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")

# --- 4. 日志文件自动清理（方案 A） ---
def check_and_clear_log(file_path):
    try:
        if os.path.exists(file_path):
            # 如果文件超过 1MB，清空内容以保持运行效率
            if os.path.getsize(file_path) > 1024 * 1024:
                with open(file_path, 'w') as f:
                    f.truncate()
                print(f"[{time.strftime('%H:%M:%S')}] 日志文件过大，已自动清理重置。")
                return True
    except Exception as e:
        print(f"清理日志失败: {e}")
    return False

# --- 5. 主监控循环 ---
def start_monitor():
    cfg = load_config()
    target_file = cfg['WATCH_FILE']
    file_encoding = cfg.get('FILE_ENCODING', 'GBK')
    
    # 路径防护：如果 C:\data 不存在，尝试创建（防止打包环境报错）
    target_dir = os.path.dirname(target_file)
    if target_dir and not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
        except:
            pass

    if os.path.exists(target_file):
        last_pos = os.path.getsize(target_file)
    else:
        last_pos = 0
    
    print(f"监控启动中... 目标文件: {target_file}")

    while True:
        try:
            if os.path.exists(target_file):
                # 检查并清理大文件
                if check_and_clear_log(target_file):
                    last_pos = 0
                
                curr_size = os.path.getsize(target_file)
                if curr_size > last_pos:
                    with open(target_file, 'rb') as f:
                        f.seek(last_pos)
                        raw_data = f.read()
                        
                        try:
                            text_data = raw_data.decode(file_encoding)
                        except UnicodeDecodeError:
                            text_data = raw_data.decode(file_encoding, errors='ignore')
                        
                        lines = text_data.splitlines()
                        for line in lines:
                            if line.strip():
                                send_email(line, cfg)
                                time.sleep(0.5) 
                        
                        last_pos = curr_size
                elif curr_size < last_pos:
                    last_pos = curr_size
            
            time.sleep(1) 
        except Exception as e:
            print(f"监控异常: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_monitor()