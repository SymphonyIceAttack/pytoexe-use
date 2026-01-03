import webbrowser
import time
import random

def weiter():
    URL = input("URL: ")
    print("Verarbeite...")
    time.sleep(1)
    print("DNS Server connect...")
    time.sleep(0.4)
    print("Completed")

    random_2 = random.randint(15588, 6546584654)
    print(f"DNS Port: {random_2}")
    print(f"Connecting to {URL} ...")
    time.sleep(2)
    print("Connect")
    print("Opening...")
    webbrowser.open(URL)

def geht_nicht():
    print("Connecting to Program File is not good.")
    print("Please go to new or old version.")
    time.sleep(1)

# -------------------------
# COMMAND SYSTEM
# -------------------------

commands = {
    "weiter": weiter,
    "geht_nicht": geht_nicht
}

print("Please wait.")
time.sleep(0.8)
print("...")

random_1 = random.randint(0, 1)

if random_1 == 1:
    cmd = "weiter"
elif random_1 == 0:
    cmd = "geht_nicht"
else:
    print("Program is not compatible.")
    print("Please go to new or old version.")
    time.sleep(2)
    exit()

# Funktion ausführen
commands[cmd]()
