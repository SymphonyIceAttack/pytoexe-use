import keyboard
import time
import threading
from colorama import Fore, Style, init

init(autoreset=True)

APP_NAME = "CVV — ULTIMATE SPAM ENGINE"

SPAM_KEY = 'f'
TOGGLE_KEY = 'e'
EXIT_KEY = 'esc'

SPEED_MODES = {
    'precision': 40,
    'balanced': 120,
    'aggressive': 200,
    'blitz': 300,
    'overdrive': 380,
    'forcefield_spam': 500,
    'slash_fury': 600,
    'ultra_blitz': 800,
    'hyper_speed': 1000
}

CURRENT_MODE = 'hyper_speed'
RUNNING = False
SHOW_OUTPUT = True
LAST_UPDATE_TIME = 0
UPDATE_INTERVAL = 0.5

def get_delay(mode):
    return 1 / SPEED_MODES[mode]

def spam_worker():
    while True:
        if RUNNING:
            delay = get_delay(CURRENT_MODE)
            keyboard.press(SPAM_KEY)
            keyboard.release(SPAM_KEY)
            time.sleep(max(delay, 0.00001))
        else:
            time.sleep(0.00001)

def update_display():
    global LAST_UPDATE_TIME
    current_time = time.time()

    if SHOW_OUTPUT and (current_time - LAST_UPDATE_TIME >= UPDATE_INTERVAL):
        LAST_UPDATE_TIME = current_time
        print(f"\033[2J\033[H")
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'='*65}")
        print(f"       ⚡ {APP_NAME} ⚡")
        print(f"{Fore.MAGENTA}{'='*65}")
        print(f"{Fore.YELLOW}   🔧 SYSTEM STATUS: {Fore.GREEN}MAXIMUM SPAM")
        print(f"{Fore.YELLOW}   🎮 GAME: {Fore.CYAN}Blade Ball (Roblox)")
        print(f"{Fore.YELLOW}   ⚡ CURRENT MODE: {Fore.RED}{CURRENT_MODE.upper()}")
        print(f"{Fore.MAGENTA}\n   🛡️  SPAM MODES:")

        modes = [
            ('Precision Mode', 'precision', 40),
            ('Balanced Mode', 'balanced', 120),
            ('Aggressive Mode', 'aggressive', 200),
            ('Blitz Mode', 'blitz', 300),
            ('Overdrive Mode', 'overdrive', 380),
            ('ForceField Spam', 'forcefield_spam', 500),
            ('Slash of Fury', 'slash_fury', 600),
            ('Ultra Blitz', 'ultra_blitz', 800),
            ('Hyper Speed', 'hyper_speed', 1000)
        ]

        for i, (display_name, mode_key, cps) in enumerate(modes, 1):
            status = f"{Fore.GREEN}✓" if CURRENT_MODE == mode_key else f"{Fore.WHITE}"
            mode_color = Fore.RED if CURRENT_MODE == mode_key else Fore.CYAN
            description = (
                '— Perfect parry' if mode_key == 'precision' else
                '— All-round' if mode_key == 'balanced' else
                '— Offensive spam' if mode_key == 'aggressive' else
                '— Lightning fast' if mode_key == 'blitz' else
                '— MAXIMUM' if mode_key == 'overdrive' else
                '— Counter ability' if mode_key == 'forcefield_spam' else
                '— Instant activation' if mode_key == 'slash_fury' else
                '— Ultra fast' if mode_key == 'ultra_blitz' else
                '— Hyper speed' if mode_key == 'hyper_speed' else ''
            )
            print(f"{status}   {i}. {Fore.WHITE}[{i}] {mode_color}{display_name} {Fore.WHITE}({cps} CPS) {description}")

        print(f"{Fore.MAGENTA}\n   🎛️  CONTROLS:")
        status_indicator = f"{Fore.GREEN}ACTIVE" if RUNNING else f"{Fore.RED}INACTIVE"
        print(f"{Fore.YELLOW}   [{TOGGLE_KEY.upper()}] {Fore.WHITE}Hold to spam ({status_indicator})")
        print(f"{Fore.RED}   [{EXIT_KEY.upper()}] {Fore.WHITE}Emergency shutdown")
        print(f"{Fore.MAGENTA}{'-'*65}")

def toggle_spam(event=None):
    global RUNNING
    RUNNING = keyboard.is_pressed(TOGGLE_KEY)

def set_mode(mode_name):
    global CURRENT_MODE
    CURRENT_MODE = mode_name
    update_display()

def check_trigger():
    keyboard.on_press_key(TOGGLE_KEY, toggle_spam)
    keyboard.on_release_key(TOGGLE_KEY, toggle_spam)

    keyboard.add_hotkey('1', lambda: set_mode('precision'))
    keyboard.add_hotkey('2', lambda: set_mode('balanced'))
    keyboard.add_hotkey('3', lambda: set_mode('aggressive'))
    keyboard.add_hotkey('4', lambda: set_mode('blitz'))
    keyboard.add_hotkey('5', lambda: set_mode('overdrive'))
    keyboard.add_hotkey('6', lambda: set_mode('forcefield_spam'))
    keyboard.add_hotkey('7', lambda: set_mode('slash_fury'))
    keyboard.add_hotkey('8', lambda: set_mode('ultra_blitz'))
    keyboard.add_hotkey('9', lambda: set_mode('hyper_speed'))

    update_display()
    print(f"{Fore.GREEN}✅ Макрос CVV готов к работе! Зажмите [{TOGGLE_KEY.upper()}] для спама.")

    try:
        while True:
            if keyboard.is_pressed(EXIT_KEY):
                break
            time.sleep(0.00001)
    except KeyboardInterrupt:
        pass
    finally:
        print(f"{Fore.YELLOW}🛑 {Fore.WHITE}Shutting down... Goodbye!")
        keyboard.unhook_all()

spam_thread = threading.Thread(target=spam_worker, daemon=True)
spam_thread.start()

check_trigger()
