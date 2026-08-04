import utils.logger as logger
import concurrent.futures
from colorama import init
from pystyle import *
import tls_client
import threading
import colorama
import os, sys
import random
import ctypes
import toml
import time
import json

# Initialize colorama
colorama.init()

# Load configurations
config = toml.load("data/config.toml")
settings = json.loads(open("data/settings.json", "r").read())

# Load tokens and proxies
with open("data/tokens.txt", "r") as f:
    tokens = f.readlines()
with open("data/proxies.txt", "r") as f:
    proxies = f.readlines()

# Remove duplicate tokens
tokens = list(set(tokens))

# Initialize thread lock and counters
LOCK = threading.Lock()
valid, invalid, locked, nitro, non_nitro, flagged, current, total = 0, 0, 0, 0, 0, 0, 0, len(tokens)
done = False

# Clear console
os.system('cls')

# Create output directory with timestamp
output_folder = f"output/{time.strftime('%Y-%m-%d %H-%M-%S')}"
os.makedirs(output_folder, exist_ok=True)

# Start time for performance measurement
start = time.time()

class Checker:
    def __init__(self):
        # Initialize session with TLS client
        self.session = tls_client.Session(client_identifier="chrome_104")
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.update_proxy()
    
    def update_proxy(self):
        if not config["main"]["proxyless"]:
            self.session.proxies = f"http://{random.choice(proxies).strip()}"
    
    def check(self):
        global current, total, valid, locked, nitro, non_nitro, invalid, flagged

        while tokens:
            token = tokens.pop().strip()
            try:
                token_only = token.split(":")[-1]
                self.session.headers["Authorization"] = token_only

                r = self.session.get("https://discord.com/api/v9/users/@me/guilds")
                if r.status_code == 429:
                    logger.err("Rate limited", token=token_only.split(".")[0])
                    self.update_proxy()
                    tokens.append(token)
                    continue

                current += 1

                if r.status_code == 401:
                    invalid += 1
                    logger.err("Invalid", token=token_only.split(".")[0])
                    LOCK.acquire()
                    with open(f"{output_folder}/invalid.txt", "a") as f:
                        f.write(token + "\n")
                    LOCK.release()
                    continue

                if r.status_code == 403:
                    locked += 1
                    logger.err("Locked", token=token_only.split(".")[0])
                    LOCK.acquire()
                    with open(f"{output_folder}/locked.txt", "a") as f:
                        f.write(token + "\n")
                    LOCK.release()
                    continue

                if r.status_code == 200:
                    # Get discord account details
                    r = self.session.get("https://discord.com/api/v9/users/@me")
                    args = {
                        "token": token_only.split(".")[0],
                    }

                    if settings["flagged"]:
                        if r.json().get("flags", 0) & 1048576 == 1048576:
                            flagged += 1
                            logger.err("Flagged", **args)
                            LOCK.acquire()
                            with open(f"{output_folder}/flagged.txt", "a") as f:
                                f.write(token + "\n")
                            LOCK.release()
                            continue

                    if settings["type"]:
                        LOCK.acquire()
                        token_type = "unclaimed"
                        if r.json()["email"] is not None:
                            token_type = "email verified"
                        if r.json()["phone"] is not None:
                            if token_type == "email verified":
                                token_type = "fully verified"
                            else:
                                token_type = "phone verified"
                    else:
                        token_type = "valid"

                    args["type"] = token_type
                    LOCK.release()

                    if settings["age"]:
                        created_at = ((int(r.json()["id"]) >> 22) + 1420070400000) / 1000
                        age = (time.time() - created_at) / 86400 / 30
                        if age > 12:
                            args["age"] = f"{age/12:.0f} years"
                        else:
                            args["age"] = f"{age:.0f} months"

                        age_folder = f"{output_folder}/age/{args['age']}"
                        os.makedirs(age_folder, exist_ok=True)
                        
                        with open(f"{age_folder}/{token_type}.txt", "a") as f:
                            f.write(token + "\n")

                    has_nitro = False
                    if settings["nitro"]:
                        r = self.session.get("https://discord.com/api/v9/users/@me/billing/subscriptions")
                        if r.json():
                            has_nitro = True
                            for sub in r.json():
                                days_left = (time.mktime(time.strptime(sub["current_period_end"], "%Y-%m-%dT%H:%M:%S.%f%z")) - time.time()) / 86400
                                args["nitro"] = f"{days_left:.0f}d"
                                nitro += 1

                                r = self.session.get("https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots")
                                available = sum(1 for sub in r.json() if sub["cooldown_ends_at"] is None)

                                args["boosts"] = available

                                boost_folder = f"{output_folder}/boosts/{days_left:.0f} days"
                                os.makedirs(boost_folder, exist_ok=True)
                                
                                with open(f"{boost_folder}/{available} boosts.txt", "a") as f:
                                    f.write(token + "\n")
                    
                    if not has_nitro:
                        non_nitro += 1
                        LOCK.acquire()
                        with open(f"{output_folder}/non_nitro.txt", "a") as f:
                            f.write(token + "\n")
                        LOCK.release()

                    valid += 1
                    logger.debug("Valid", **args)
                    with open(f"{output_folder}/{token_type}.txt", "a") as f:
                        f.write(token + "\n")
            except Exception as e:
                logger.err("Error", token=token_only.split(".")[0], error=e)
                self.update_proxy()
                tokens.append(token)
                continue

def update_title():
    try:
        while not done:
            time.sleep(0.03)
            cps = current / (time.time() - start)
            cps = round(cps * 60)
            ctypes.windll.kernel32.SetConsoleTitleW(f"Token checker          [Valid - {valid}]          [Invalid - {invalid}]          [Locked - {locked}]          [Remaining - {len(tokens)}]          [Checked - {current/total*100:.2f}%]          [CPM - {cps}]")
    except Exception:
        pass

time.sleep(0.1)
update = threading.Thread(target=update_title)
update.start()

logger.asciiprint()

with concurrent.futures.ThreadPoolExecutor(max_workers=config["main"]["threads"]) as executor:
    for i in range(config["main"]["threads"]):
        executor.submit(Checker().check)
done = True
update.join()

print()
logger.info(f"-", Seconds=time.gmtime(time.time()-start).tm_sec, Minutes=time.gmtime(time.time()-start).tm_min)
logger.info(">", Total     =current)
logger.info(">", Valid     =valid)
logger.info(">", Invalid   =invalid)
logger.info(">", Nitro     =nitro)
logger.info(">", Non_Nitro =non_nitro)
logger.info(">", Locked    = locked)
logger.info(">", Flagged   = flagged)
logger.ext_input()
time.sleep(2)
sys.exit()
