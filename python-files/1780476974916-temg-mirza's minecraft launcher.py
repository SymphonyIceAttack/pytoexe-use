import requests
import urllib3
import os
import time
import json

# Disable ALL SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== CONFIGURATION =====
BOT_TOKEN = '8654403666:AAEaRN-i0xb4P9CUAkPuo904lXrcJeSni2Y'
USER_ID = 8904949827  # Your user ID
# =========================

# API URL
API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/'

def send_message(chat_id, text):
    """Send a message via Telegram API without SSL verification"""
    url = API_URL + 'sendMessage'
    data = {'chat_id': chat_id, 'text': text}
    try:
        requests.post(url, json=data, verify=False, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def get_updates(offset=None):
    """Get updates from Telegram without SSL verification"""
    url = API_URL + 'getUpdates'
    params = {'timeout': 30, 'offset': offset}
    try:
        response = requests.get(url, params=params, verify=False, timeout=35)
        return response.json()
    except Exception as e:
        print(f"Error getting updates: {e}")
        return None

def execute_command(command):
    """Execute system commands"""
    if command == '/status':
        try:
            cpu = os.popen('wmic cpu get loadpercentage').read().strip().split('\n')[1]
            return f"📊 CPU Usage: {cpu}%"
        except:
            return "⚠️ Could not get CPU status"
    elif command == '/shutdown':
        os.system('shutdown /s /t 10')
        return "⚠️ Shutting down in 10 seconds! Send /cancel to stop."
    elif command == '/cancel':
        os.system('shutdown /a')
        return "✅ Shutdown cancelled."
    elif command == '/lock':
        os.system('rundll32.exe user32.dll,LockWorkStation')
        return "🔒 Screen locked."
    elif command == '/sleep':
        os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
        return "💤 Going to sleep..."
    elif command == '/help':
        return """Commands:
/status - Check CPU usage
/shutdown - Shutdown laptop (10 sec delay)
/cancel - Cancel shutdown
/lock - Lock screen
/sleep - Put laptop to sleep"""
    elif command == '/start':
        return "✅ Bot is connected and running!\nSend /help for commands."
    else:
        return None

print("🤖 Bot starting with NO SSL verification...")
print(f"Bot token: {BOT_TOKEN[:10]}...")
print(f"Authorized user: {USER_ID}")
print("Waiting for commands on Telegram...")
print("")

# Send startup confirmation
send_message(USER_ID, "✅ Bot has started! Send /help for commands.")

# Main polling loop
last_update_id = 0

while True:
    try:
        updates = get_updates(offset=last_update_id + 1 if last_update_id else None)
        
        if updates and updates.get('ok'):
            for result in updates.get('result', []):
                update_id = result.get('update_id')
                if update_id:
                    last_update_id = update_id
                
                message = result.get('message', {})
                chat_id = message.get('chat', {}).get('id')
                text = message.get('text', '')
                
                # Only respond to authorized user
                if chat_id == USER_ID and text:
                    print(f"Received command: {text}")
                    response = execute_command(text)
                    if response:
                        send_message(chat_id, response)
        
        time.sleep(1)
        
    except Exception as e:
        print(f"Error in main loop: {e}")
        time.sleep(5)