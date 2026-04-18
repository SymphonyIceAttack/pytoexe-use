from flask import Flask, render_template_string, request, jsonify
import threading
import time
import random
import requests
import webbrowser
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import sys

app = Flask(__name__)

# Gmailnator Class
class Gmailnator:
    BASE_URL = 'https://www.gmailnator.com/'
    HEADERS = {
        'authority': 'www.gmailnator.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.gmailnator.com',
        'referer': 'https://www.gmailnator.com/inbox/',
    }

    def __init__(self):
        self.s = requests.Session()
        self.csrf_token = self.__get_csrf()

    def __get_csrf(self):
        response = self.s.get(self.BASE_URL)
        return response.cookies.get('csrf_gmailnator_cookie')

class GmailnatorGet(Gmailnator):
    def get_email(self):
        payload = {'csrf_gmailnator_token': self.csrf_token, 'action': 'GenerateEmail', 'data[]': [1,2,3]}
        r = self.s.post('https://www.gmailnator.com/index/indexquery', data=payload)
        return r.text.strip()

status = {"running": False, "created": 0, "total": 0, "logs": [], "accounts": []}

def log(msg):
    status["logs"].append(msg)
    print(msg)

def farm_accounts(target_count):
    status["running"] = True
    status["created"] = 0
    status["total"] = target_count
    status["logs"] = []
    status["accounts"] = []

    for i in range(target_count):
        if not status["running"]:
            break
        try:
            log(f"[{i+1}/{target_count}] Creating account...")
            gmail = GmailnatorGet()
            email = gmail.get_email()

            options = uc.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            driver = uc.Chrome(options=options)

            driver.get("https://discord.com/register")
            wait = WebDriverWait(driver, 20)

            wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
            username = f"user{random.randint(10000,99999)}"
            driver.find_element(By.NAME, "username").send_keys(username)
            password = f"Pass{random.randint(100000,999999)}!"
            driver.find_element(By.NAME, "password").send_keys(password)

            driver.find_element(By.NAME, "month").send_keys("6")
            driver.find_element(By.NAME, "day").send_keys("15")
            driver.find_element(By.NAME, "year").send_keys("2003")

            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            time.sleep(8)

            account_line = f"{email}:{password}"
            status["accounts"].append(account_line)
            with open("discord_accounts.txt", "a", encoding="utf-8") as f:
                f.write(account_line + "\n")

            status["created"] += 1
            log(f"[+] Created: {email}:{password}")

        except Exception as e:
            log(f"[-] Error: {str(e)}")
        finally:
            try:
                driver.quit()
            except:
                pass
            time.sleep(random.uniform(15, 40))

    status["running"] = False
    log(f"Finished! {status['created']} accounts saved in discord_accounts.txt")

# Web Routes
@app.route('/')
def index():
    html = """<html><head><title>Discord Farmer</title>
    <style>body{background:#111;color:#0f0;font-family:Arial;text-align:center;}</style>
    </head><body>
    <h1>Discord Account Farmer</h1>
    <input type="number" id="count" value="10" min="1" max="50" style="font-size:18px;padding:8px;">
    <button onclick="start()">Start Farming</button>
    <button onclick="stop()">Stop</button>
    <h3>Status: <span id="status">Idle</span></h3>
    <p>Created: <span id="created">0</span> / <span id="total">0</span></p>
    <pre id="logs" style="background:#000;height:300px;overflow:auto;text-align:left;"></pre>
    <pre id="accounts" style="background:#000;height:200px;overflow:auto;text-align:left;"></pre>
    <script>
        function start(){let c=document.getElementById('count').value;fetch('/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({count:parseInt(c)})});}
        function stop(){fetch('/stop');}
        function update(){fetch('/status').then(r=>r.json()).then(d=>{document.getElementById('status').innerText=d.running?'RUNNING':'Idle';document.getElementById('created').innerText=d.created;document.getElementById('total').innerText=d.total;document.getElementById('logs').innerText=d.logs.join('\\n');document.getElementById('accounts').innerText=d.accounts.join('\\n');});}
        setInterval(update,1500);
    </script>
    </body></html>"""
    return render_template_string(html)

@app.route('/start', methods=['POST'])
def start_farm():
    if not status["running"]:
        count = request.get_json().get("count", 10)
        threading.Thread(target=farm_accounts, args=(count,), daemon=True).start()
    return jsonify({"status": "started"})

@app.route('/stop')
def stop_farm():
    status["running"] = False
    return jsonify({"status": "stopped"})

@app.route('/status')
def get_status():
    return jsonify(status)

if __name__ == "__main__":
    print("Starting Discord Farmer Web App...")
    webbrowser.open("http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)