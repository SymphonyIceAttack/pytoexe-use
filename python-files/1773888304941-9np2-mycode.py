import time
import os
import smtplib
import re
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 配置加载 ---
def load_config():
    config = {}
    try:
        # 建议 config.txt 使用 utf-8-sig 编码保存
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

# --- 2. 智能解析与优先级逻辑 (适配 6 字公式名) ---
def parse_and_rank(line):
    # 正则提取：时间、代码、名称、公式名
    # 通达信日志格式示例: 2026-03-19 14:50:00 预警品种: 600036 招商银行 预警公式: 形态超跌共振
    pattern = r"预警品种: (\d{6}) (.*?) 预警公式: (.*)"
    match = re.search(pattern, line)
    
    if match:
        code, name, formula = match.groups()
        score = 0
        
        # 评分规则：底(5分), 共振(3分), 板块(2分)
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
        content = f"时间: {time.strftime('%H:%M:%S')}\n股票: {name} ({code})\n逻辑: {formula}\n评分: {score}\n建议: 信号确立，请检查板块效应及量能配合。"
        return subject, content
    
    return "通达信预警通知", line

# --- 3. 邮件发送函数 ---
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

# --- 4. 日志清理逻辑 (方案 A) ---
def check_and_clear_log(file_path):
    """如果日志文件超过 1MB，则清空文件内容"""
    try:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > 1024 * 1024:  # 1MB 阈值
                with open(file_path, 'w') as f:
                    f.truncate()
                print(f"[{time.strftime('%H:%M:%S')}] 日志文件过大，已自动清理重置。")
                return True
    except Exception as e:
        print(f"清理日志失败: {e}")
    return False

# --- 5. 主监控程序 ---
def start_monitor():
    cfg = load_config()
    if not cfg: return
    
	target_file = cfg['WATCH_FILE']
    target_dir = os.path.dirname(target_file)
    if target_dir and not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir) # 如果路径不存在（如在服务器上），自动创建它
        except:
            pass # 防止权限问题导致打包失败
    # -----------------------
	
	
    file_encoding = cfg.get('FILE_ENCODING', 'GBK')
    
    if os.path.exists(target_file):
        last_pos = os.path.getsize(target_file)
    else:
        last_pos = 0
    
    print(f"智能监控启动 (编码:{file_encoding}): {target_file}")

    while True:
        try:
            if os.path.exists(target_file):
                # 方案 A：定期检查文件大小
                if check_and_clear_log(target_file):
                    last_pos = 0  # 如果文件被清空，指针回到起点
                
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
                                time.sleep(0.5) # 防止发送频率过快
                        
                        last_pos = curr_size
                elif curr_size < last_pos:
                    # 如果文件被手动删除或外部清空
                    last_pos = curr_size
            
            time.sleep(1) # 每秒扫描一次
        except Exception as e:
            print(f"扫描异常: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_monitor()