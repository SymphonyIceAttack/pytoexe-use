import time, os, smtplib, re
from email.mime.text import MIMEText
from email.header import Header

def load_config():
    return {
        'WATCH_FILE': 'log.txt', # 简化路径
        'SMTP_SERVER': 'smtp.qq.com',
        'SMTP_PORT': '465',
        'SENDER_EMAIL': 'a@b.com',
        'SENDER_PASSWORD': 'pass',
        'RECEIVER_EMAIL': 'c@d.com'
    }

def parse_and_rank(line):
    p = r"预警品种: (\d{6}) (.*?) 预警公式: (.*)"
    m = re.search(p, line)
    if m:
        c, n, f = m.groups()
        s = 5 if "底" in f else 0
        s += 3 if "共振" in f else 0
        return f"【预警】{n}", f"触发{f}"
    return "通知", line

def send_email(line, cfg):
    try:
        msg = MIMEText(line, 'plain', 'utf-8')
        msg['Subject'] = Header("Stock Alert", 'utf-8')
        server = smtplib.SMTP_SSL(cfg['SMTP_SERVER'], 465)
        server.login(cfg['SENDER_EMAIL'], cfg['SENDER_PASSWORD'])
        server.sendmail(cfg['SENDER_EMAIL'], [cfg['RECEIVER_EMAIL']], msg.as_string())
        server.quit()
    except: pass

if __name__ == "__main__":
    print("Monitor Start...")
    while True:
        time.sleep(10) # 极简循环