import time
import os
import webbrowser

os.system("cls")

print("Initializing GhostAbi Security System...")
time.sleep(1)

print("[+] Connecting...")
time.sleep(1)

print("[+] Access granted")
time.sleep(1)

print()
print("██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗")
print("██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝")
print("██║  ███╗███████║██║   ██║███████╗   ██║")
print("██║   ██║██╔══██║██║   ██║╚════██║   ██║")
print("╚██████╔╝██║  ██║╚██████╔╝███████║   ██║")
print(" ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝")

print()
print("HACKED BY GhostAbi DU HURENSHON")
time.sleep(2)

links = [
    "https://www.partydeko.de/kostuem-pimmel-paul-2-tlg.html",
    "https://www.youtube.com/watch?v=qsJkFb7UW_g",
    "https://de.pornhub.org/view_video.php?viewkey=6947ab4411dde#1"

    ]

print()
print("Opening connection windows...")

for link in links:
    webbrowser.open(link)
    time.sleep(1)

    for i in range(1, 11):
    dateiname = f"GhostAbi_Hack_{i}.txt"

    with open(dateiname, "w", encoding="utf-8") as datei:
        datei.write("HACKED BY GhostAbi\n")
        datei.write("HACK SCREEN\n")

    os.startfile(dateiname)
    time.sleep(0.5)

print("Dateien geöffnet.")