import os
import time
import random
import re


# =========================
# COLORS
# =========================

RESET = "\033[0m"
BOLD = "\033[1m"

RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
WHITE = "\033[97m"
GRAY = "\033[90m"
MAGENTA = "\033[95m"


# =========================
# SYSTEM
# =========================

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input(f"\n{GRAY}Press ENTER to continue...{RESET}")


def loading(text, duration=1.2):
    print(f"{CYAN}{text}{RESET}", end="", flush=True)

    steps = max(1, int(duration / 0.15))

    for _ in range(steps):
        print(".", end="", flush=True)
        time.sleep(0.15)

    print(f" {GREEN}OK{RESET}")


def fake_progress():
    actions = [
        "Initializing module",
        "Loading virtual database",
        "Preparing search engine",
        "Analyzing input",
        "Generating demo results"
    ]

    for action in actions:
        loading(action, random.uniform(0.5, 1.0))


# =========================
# TELEGRAM INPUT
# =========================

def get_telegram_target():

    while True:

        target = input(
            f"{WHITE}Enter Telegram username "
            f"{GRAY}>> {RESET}"
        ).strip()

        # Проверка: username обязательно начинается с @
        if not target.startswith("@"):

            print(
                f"{RED}[!] Username must start with @.{RESET}"
            )

            time.sleep(1)

            continue

        # Убираем @ для проверки
        username = target[1:]

        # Проверка на пустой username
        if not username:

            print(
                f"{RED}[!] Enter a username after @.{RESET}"
            )

            time.sleep(1)

            continue

        # Разрешены только английские буквы, цифры и _
        if not re.fullmatch(
            r"[A-Za-z0-9_]+",
            username
        ):

            print(
                f"{RED}[!] Only English letters, numbers and _ are allowed.{RESET}"
            )

            time.sleep(1)

            continue

        # Минимальная длина
        if len(username) < 3:

            print(
                f"{RED}[!] Username must contain at least 3 characters.{RESET}"
            )

            time.sleep(1)

            continue

        return username


# =========================
# AI DEMO IDENTITY
# =========================

def translit_to_ru(text):

    table = {
        "shch": "щ",
        "sch": "щ",
        "zh": "ж",
        "kh": "х",
        "ts": "ц",
        "ch": "ч",
        "sh": "ш",
        "yu": "ю",
        "ya": "я",
        "yo": "ё",

        "a": "а",
        "b": "б",
        "v": "в",
        "g": "г",
        "d": "д",
        "e": "е",
        "z": "з",
        "i": "и",
        "j": "й",
        "k": "к",
        "l": "л",
        "m": "м",
        "n": "н",
        "o": "о",
        "p": "п",
        "r": "р",
        "s": "с",
        "t": "т",
        "u": "у",
        "f": "ф",
        "h": "х",
        "c": "к",
        "y": "ы",
        "w": "в",
        "q": "к",
        "x": "кс"
    }

    result = text.lower()

    combinations = [
        "shch", "sch",
        "zh", "kh", "ts",
        "ch", "sh",
        "yu", "ya", "yo"
    ]

    for latin in combinations:
        result = result.replace(latin, table[latin])

    final = ""

    for char in result:
        final += table.get(char, char)

    return final


def clean_target(target):

    target = target.lower().strip()
    target = target.replace("@", "")

    target = re.sub(
        r"[^a-zа-яё]",
        "",
        target
    )

    return target


def split_target(target):

    if len(target) < 4:
        return target, target

    middle = len(target) // 2

    shift = random.choice([
        -1, 0, 0, 1
    ])

    split_point = max(
        2,
        min(
            len(target) - 2,
            middle + shift
        )
    )

    first = target[:split_point]
    second = target[split_point:]

    return first, second


def generate_demo_identity(target):

    original = target
    target = clean_target(target)

    if not target:
        target = "unknown"

    first_part, second_part = split_target(target)

    known_names = {
        "demi": ["Деми", "Демид", "Демьян"],
        "dem": ["Деми", "Демид"],
        "alex": ["Алекс", "Алексей"],
        "kirill": ["Кирилл"],
        "kir": ["Кирилл", "Кир"],
        "ivan": ["Иван", "Ваня"],
        "max": ["Макс", "Максим"],
        "maks": ["Макс", "Максим"],
        "dan": ["Даня", "Данил"],
        "art": ["Артём", "Артур"],
        "nik": ["Ник", "Никита"],
        "serg": ["Сергей"],
        "vlad": ["Влад", "Владислав"],
        "roma": ["Рома", "Роман"],
        "misha": ["Миша", "Михаил"],
        "egor": ["Егор"],
        "den": ["Денис", "Ден"]
    }

    name = None

    for key, variants in known_names.items():

        if target.startswith(key):

            name = random.choice(variants)

            remainder = target[len(key):]

            if remainder:
                second_part = remainder

            break

    if not name:

        ru_name = translit_to_ru(first_part)

        if len(ru_name) < 3:
            ru_name = translit_to_ru(
                target[:5]
            )

        name = ru_name.capitalize()

    surname_base = translit_to_ru(
        second_part
    )

    if len(surname_base) < 3:
        surname_base = translit_to_ru(
            target[-5:]
        )

    surname_base = surname_base.capitalize()

    endings = [
        "ов",
        "ев",
        "ин",
        "ский",
        "кин",
        "енко"
    ]

    funny_endings = [
        "улькин",
        "ыч",
        "ычев",
        "озавров",
        "ович"
    ]

    if random.randint(1, 100) <= 30:

        surname = (
            surname_base
            + random.choice(funny_endings)
        )

    else:

        surname = (
            surname_base
            + random.choice(endings)
        )

    full_name = f"{name} {surname}"

    aliases = [
        full_name,
        f"{name} {surname_base}",
        f"{surname_base} {name}",
        f"{name} {surname_base}ыч"
    ]

    alias = random.choice(aliases)

    return {
        "input": original,
        "name": name,
        "surname": surname,
        "full_name": full_name,
        "alias": alias
    }


# =========================
# RANDOM GEOINT DATA
# =========================

def generate_random_address():

    streets = [
        "Колотушкина",
        "Пельменная",
        "Сосисочная",
        "Кирпичная",
        "Арбузная",
        "Компьютерная",
        "Котлетная",
        "Банановая",
        "Шаурмичная",
        "Мемная",
        "Пиксельная",
        "Картофельная",
        "Котиковая",
        "Тапочная",
        "Гречневая"
    ]

    street_types = [
        "ул.",
        "пр-т",
        "пер.",
        "наб.",
        "бул."
    ]

    cities = [
        "Котоград",
        "Мембург",
        "Пельменск",
        "Криптоград",
        "Пиксельбург",
        "Арбузово",
        "Байтоград",
        "Шаурминск",
        "Кодинск",
        "Котолеск",
        "Лагоград",
        "Рофлянск"
    ]

    return {
        "street": (
            f"{random.choice(street_types)} "
            f"{random.choice(streets)}"
        ),

        "house": random.randint(1, 250),

        "apartment": random.randint(1, 500),

        "city": random.choice(cities)
    }


def generate_random_coordinates():

    latitude = round(
        random.uniform(-80, 80),
        4
    )

    longitude = round(
        random.uniform(-170, 170),
        4
    )

    return latitude, longitude


def generate_demo_country():

    countries = [
        "Демостания",
        "Рофляндия",
        "Пиксельная Республика",
        "Виртуляндия",
        "Котостан",
        "Байтландия",
        "Мемороссия",
        "Симуляция"
    ]

    return random.choice(countries)


# =========================
# RANDOM NETWORK DATA
# =========================

def generate_random_ip():

    return ".".join(
        str(random.randint(1, 254))
        for _ in range(4)
    )


# =========================
# BANNER
# =========================

def banner():

    print(f"""{RED}{BOLD}
 ██████╗ ███████╗███╗   ██╗███████╗██╗██╗  ██╗
██╔════╝ ██╔════╝████╗  ██║██╔════╝██║██║  ██║
██║  ███╗█████╗  ██╔██╗ ██║█████╗  ██║███████║
██║   ██║██╔══╝  ██║╚██╗██║██╔══╝  ██║██╔══██║
╚██████╔╝███████╗██║ ╚████║███████╗██║██║  ██║
 ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝╚═╝  ╚═╝
{RESET}
{GRAY}              VISUAL INTELLIGENCE TOOLKIT{RESET}
{GRAY}                    VERSION 1.3{RESET}

""")


# =========================
# OSINT DEMO
# =========================

def osint_demo():

    clear()

    print(f"{BLUE}{BOLD}")
    print("╔════════════════════════════════════════════╗")
    print("║                 OSINT MODULE               ║")
    print("╚════════════════════════════════════════════╝")
    print(f"{RESET}")

    print(f"{GRAY}")
    print("Open Source Intelligence")
    print("DEMO MODE — generated results only.")
    print(f"{RESET}\n")

    target = get_telegram_target()

    if not target:
        return

    print()

    fake_progress()

    identity = generate_demo_identity(target)

    print()

    print(f"{GREEN}[+] Target accepted{RESET}")
    print(f"{GRAY}Telegram : @{target}{RESET}")

    time.sleep(0.8)

    print(f"""
{CYAN}╔════════════════════════════════════════════╗
║              OSINT DEMO REPORT             ║
╠════════════════════════════════════════════╣
║ Telegram     : @{target[:24]:<24} ║
║ Status       : DEMO                        ║
╠════════════════════════════════════════════╣
║ AI Name      : {identity["name"][:25]:<25} ║
║ AI Surname   : {identity["surname"][:25]:<25} ║
║ AI Identity  : {identity["full_name"][:25]:<25} ║
║ Alias        : {identity["alias"][:25]:<25} ║
║ Source       : GENERATED                   ║
╚════════════════════════════════════════════╝
{RESET}
""")

    print(
        f"{YELLOW}"
        "[!] All identity information is AI-generated demo data."
        f"{RESET}"
    )

    pause()


# =========================
# DOX DEMO
# =========================

def dox_demo():

    clear()

    print(f"{RED}{BOLD}")
    print("╔════════════════════════════════════════════╗")
    print("║                  DOX MODULE                ║")
    print("╚════════════════════════════════════════════╝")
    print(f"{RESET}")

    print(f"{YELLOW}")
    print("WARNING: VISUAL DEMONSTRATION ONLY")
    print("No real personal information is collected,")
    print("searched, stored or displayed.")
    print(f"{RESET}\n")

    target = get_telegram_target()

    if not target:
        return

    print()

    fake_progress()

    identity = generate_demo_identity(target)

    print()

    print(f"{RED}{BOLD}")
    print("╔════════════════════════════════════════════╗")
    print("║                DEMO REPORT                 ║")
    print("╠════════════════════════════════════════════╣")
    print(f"║ Telegram     : @{target[:24]:<24} ║")
    print("╠════════════════════════════════════════════╣")
    print(f"║ Full name    : {identity['full_name'][:25]:<25} ║")
    print(f"║ Alias        : {identity['alias'][:25]:<25} ║")
    print("║ Phone        : [SIMULATED]                 ║")
    print("║ Address      : [SIMULATED]                 ║")
    print("║ Email        : [SIMULATED]                 ║")
    print("║ Leaks        : [NOT CHECKED]               ║")
    print("╚════════════════════════════════════════════╝")
    print(f"{RESET}")

    print(
        f"{GRAY}"
        "This report is generated for visual purposes only."
        f"{RESET}"
    )

    pause()


# =========================
# GEOINT DEMO
# =========================

def geoint_demo():

    clear()

    print(f"{GREEN}{BOLD}")
    print("╔════════════════════════════════════════════╗")
    print("║                 GEOINT MODULE              ║")
    print("╚════════════════════════════════════════════╝")
    print(f"{RESET}")

    print(f"{GRAY}")
    print("Geographic Intelligence — visual simulation.")
    print(f"{RESET}\n")

    location = input(
        "Enter location for demo: "
    ).strip()

    if not location:
        return

    print()

    fake_progress()

    address = generate_random_address()

    latitude, longitude = (
        generate_random_coordinates()
    )

    country = generate_demo_country()

    coordinates = f"{latitude}, {longitude}"

    print(f"""
{GREEN}╔════════════════════════════════════════════╗
║              GEOINT DEMO RESULT            ║
╠════════════════════════════════════════════╣
║ Query        : {location[:25]:<25} ║
║ Country      : {country[:25]:<25} ║
║ City         : {address["city"][:25]:<25} ║
║ Street       : {address["street"][:25]:<25} ║
║ House        : {str(address["house"]):<25} ║
║ Apartment    : {str(address["apartment"]):<25} ║
║ Coordinates  : {coordinates[:25]:<25} ║
║ Map data     : [SIMULATED]                 ║
╚════════════════════════════════════════════╝
{RESET}
""")

    print(
        f"{YELLOW}"
        "[SIM] Address and coordinates are randomly generated."
        f"{RESET}"
    )

    pause()


# =========================
# NETWORK DEMO
# =========================

def network_demo():

    clear()

    print(f"{MAGENTA}{BOLD}")
    print("╔════════════════════════════════════════════╗")
    print("║               NETWORK MODULE               ║")
    print("╚════════════════════════════════════════════╝")
    print(f"{RESET}\n")

    target = input(
        "Enter demo host/IP: "
    ).strip()

    if not target:
        return

    print()

    fake_progress()

    print(
        f"\n{CYAN}Simulated network nodes:{RESET}\n"
    )

    random_ips = []

    for _ in range(
        random.randint(3, 7)
    ):

        ip = generate_random_ip()

        while ip in random_ips:
            ip = generate_random_ip()

        random_ips.append(ip)

    for ip in random_ips:

        status = random.choice([
            "ONLINE",
            "OFFLINE",
            "FILTERED"
        ])

        if status == "ONLINE":
            color = GREEN

        elif status == "FILTERED":
            color = YELLOW

        else:
            color = RED

        print(
            f"  {CYAN}{ip:<16}{RESET}"
            f"{color}{status}{RESET}"
        )

        time.sleep(
            random.uniform(0.15, 0.4)
        )

    ports = [
        22,
        53,
        80,
        443,
        8080
    ]

    print(
        f"\n{CYAN}Simulated ports:{RESET}\n"
    )

    for port in ports:

        status = random.choice([
            "OPEN",
            "CLOSED",
            "FILTERED"
        ])

        if status == "OPEN":
            color = GREEN

        elif status == "FILTERED":
            color = YELLOW

        else:
            color = RED

        print(
            f"  Port {port:<5} "
            f"{color}{status}{RESET}"
        )

        time.sleep(0.25)

    print()

    print(
        f"{GRAY}"
        "[SIM] Random IP addresses and port statuses "
        "are generated locally."
        f"{RESET}"
    )

    pause()


# =========================
# SCANNER DEMO
# =========================

def scanner_demo():

    clear()

    print(f"{YELLOW}{BOLD}")
    print("╔════════════════════════════════════════════╗")
    print("║                SCANNER MODULE              ║")
    print("╚════════════════════════════════════════════╝")
    print(f"{RESET}\n")

    target = input(
        "Enter demo target: "
    ).strip()

    if not target:
        return

    print()

    for i in range(0, 101, 10):

        bar_length = 30

        filled = int(
            bar_length * i / 100
        )

        bar = (
            f"{GREEN}"
            + "█" * filled
            + f"{GRAY}"
            + "░" * (bar_length - filled)
            + f"{RESET}"
        )

        print(
            f"\r[{bar}] {i}%",
            end="",
            flush=True
        )

        time.sleep(0.12)

    print("\n")

    print(f"{GREEN}[+] Scan completed.{RESET}")
    print(f"{GRAY}[SIM] No actual scanning performed.{RESET}")

    pause()


# =========================
# ABOUT
# =========================

def about():

    clear()

    print(f"{CYAN}{BOLD}")
    print("╔════════════════════════════════════════════╗")
    print("║                   ABOUT                    ║")
    print("╚════════════════════════════════════════════╝")
    print(f"{RESET}")

    print("""
Visual Intelligence Toolkit

Version : 1.3
Mode    : DEMONSTRATION

Modules:
  • GEOINT
  • OSINT
  • DOX
  • NETWORK
  • SCANNER

Features:
  • Telegram username input
  • AI-generated fictional identities
  • Random fictional addresses
  • Random simulated IP addresses
  • Simulated ports and scan results

No real personal information is searched,
collected, stored or exposed.
""")

    input(
        f"\n{GRAY}Press ENTER to return to menu...{RESET}"
    )


# =========================
# MAIN MENU
# =========================

def main():

    while True:

        clear()
        banner()

        print(f"{CYAN}┌──────────────────────────────────────────────┐{RESET}")

        print(
            f"{CYAN}│{RESET}  {WHITE}[1]{RESET}  "
            f"{GREEN}GEOINT{RESET}     "
            f"{GRAY}Geographic intelligence{RESET}"
        )

        print(
            f"{CYAN}│{RESET}  {WHITE}[2]{RESET}  "
            f"{BLUE}OSINT{RESET}      "
            f"{GRAY}Telegram intelligence demo{RESET}"
        )

        print(
            f"{CYAN}│{RESET}  {WHITE}[3]{RESET}  "
            f"{RED}DOX{RESET}        "
            f"{GRAY}Investigation demo{RESET}"
        )

        print(
            f"{CYAN}│{RESET}  {WHITE}[4]{RESET}  "
            f"{MAGENTA}NETWORK{RESET}    "
            f"{GRAY}Network simulation{RESET}"
        )

        print(
            f"{CYAN}│{RESET}  {WHITE}[5]{RESET}  "
            f"{YELLOW}SCANNER{RESET}    "
            f"{GRAY}Scanner simulation{RESET}"
        )

        print(
            f"{CYAN}│{RESET}  {WHITE}[6]{RESET}  "
            f"{WHITE}ABOUT{RESET}      "
            f"{GRAY}Information{RESET}"
        )

        print(
            f"{CYAN}│{RESET}  {WHITE}[0]{RESET}  "
            f"{RED}EXIT{RESET}"
        )

        print(f"{CYAN}└──────────────────────────────────────────────┘{RESET}")

        choice = input(
            f"\n{WHITE}root@toolkit{RESET} "
            f"{GRAY}>> {RESET}"
        ).strip()

        if choice == "1":

            geoint_demo()

        elif choice == "2":

            osint_demo()

        elif choice == "3":

            dox_demo()

        elif choice == "4":

            network_demo()

        elif choice == "5":

            scanner_demo()

        elif choice == "6":

            about()

        elif choice == "0":

            clear()

            print(f"""
{RED}{BOLD}
╔════════════════════════════════════════════╗
║              SESSION CLOSED                ║
╚════════════════════════════════════════════╝
{RESET}
""")

            break

        else:

            print(
                f"\n{RED}[!] Unknown command.{RESET}"
            )

            time.sleep(1)


# =========================
# START
# =========================

if __name__ == "__main__":
    main()