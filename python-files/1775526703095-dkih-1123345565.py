import os
import time
from tkinter import filedialog, Tk

# ------------------ BANNER ------------------
def show_banner():
    print(r"""
 ███████╗██╗  ██╗██╗   ██╗███████╗
 ██╔════╝██║ ██╔╝╚██╗ ██╔╝╚══███╔╝
 ███████╗█████╔╝  ╚████╔╝   ███╔╝ 
 ╚════██║██╔═██╗   ╚██╔╝   ███╔╝  
 ███████║██║  ██╗   ██║   ███████╗
 ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
       S K Y Z  ANTI REMOVER

""")

# ------------------ Keywords (FULL) ------------------
ANTI_CHEAT_KEYWORDS = [
   b"FieldCheatDetector", b"ADetector'1", b"PersistentSingleton1",
    b"Entitlementcheck", b"AstreiodsGameManager", b"BanOnStart",
    b"CheckIfInUnity", b"DeleteData", b"ZzYyXx", b"QuestLink",
    b"HorrorAi", b"KSHRAnti", b"SaveManager", b"TeleportToBan",
    b"VersionChecker", b"KeyPadEnter", b"AppEntitlementCheck",
    b"SignatureCheck", b"ProtectedUIInt32", b"AsteroidSpawner",
    b"ProtectedInt16", b"Bullet", b"ProtectedVector4", b"ProtectedFloat",
    b"ProtectedQuaternionPref", b"ProtectedVector3Int",
    b"ProtectedVector2Pref", b"ProtectedString", b"Asteroid",
    b"CheatingDetectionStatus", b"AntiCheatMonitor", b"ProtectedUInt64",
    b"QuestSentailProtect", b"DllChecker", b"assembliesToCheck",
    b"AstreiodsGame", b"AntiCheatManager", b"DllSigmaThing",
    b"WallHackDetector", b"SpeedHackDetector", b"ModTool", b"GOOBEREER",
    b"GlitchMonke", b"IgottaremanethisitwasmadebyK_S_H_R",
    b"Kidsthesedays", b"veryfyyey", b"ApkChecker", b"Antimodders",
    b"Code.Stages.Anticheats", b"AppDeeplinkUI", b"ChangeCosmetic",
    b"coinsScripts", b"PublicZone", b"SampleUI",
    b"LoginHandle.IsClientLoggedIn", b"ConntrastStretch",
    b"CollisionSounds", b"Donut", b"WifiCheck", b"PlayerMovement01",
    b"HydrasPrivAntiCheat", b"imposter", b"AntiCheat", b"Funnymods",
    b"BloxianAnti", b"KokoAntiSkid", b"checkere", b"particallagreducer",
    b"timmyfixer", b"antidll", b"anti-dll", b"anti-hack", b"anti-cheat",
    b"anticheat", b"ModsFolderChecker", b"FolderVerifer",
    b"LemonFolderChecker", b"Melonloaderchecker", b"AntiCheats",
    b"Sgima", b"bustanut", b"coke", b"yummy", b"yummymelons",
    b"yummylemons", b"AntiModFolders", b"BadBilly", b"DisableOnEnable",
    b"QuitGame", b"DisableOnStart", b"AntiCheat2byXler",
    b"AntiCheatByXler", b"AntiModders", b"QuitOnCollision",
    b"DisableOnJoin", b"getBanReason", b"BanManager",
    b"SnowAntiRuntime", b"noscrippyforyou", b"UnitysAntiCheat",
    b"DestroyBOTrigger", b"PastebinLoader", b"byeeeeeeeeee",
    b"handscantbeextremelyfarapart", b"EnableObjectAfterDelay",
    b"PhotonTrigger", b"NetworkRig", b"NoLemonScript", b"BasilsAuth",
    b"sigma", b"GorillaQuitBox", b"spoopy", b"kick",
    b"DiscordWebhookTrigger", b"VoidGuard", b"SuspiciousBehaviourChecker",
    b"owner", b"DeviceCheck", b"LevelManager", b"GorillaManagerV2",
    b"AntiUABEA", b"FroggysAntiSkid", b"MeshEnable", b"tpiffail",
    b"chilloutitsjustagamelol", b"VentOpenPro", b"CumDoorButtonD",
    b"SigmaFPS", b"SharksAndMinnowsManager", b"BoxMove2", b"lnit",
    b"ResetToStart", b"FPSDisplayFR", b"FunMonkeyGONE", b"JumpScareN",
    b"SHRplayfabauth1", b"CheckSkuOwnership", b"SHRplayfabauth",
    b"objectsarecool", b"ownsmodcosmetics", b"AntiModder",
    b"KickIfBanned", b"QuestScript", b"kickp", b"rizz", b"DLLChecker",
    b"MeNoLoaderchecker", b"AntiKickTest", b"KickProtection",
    b"NoNameDetector", b"AIBooster", b"StoreMesh",
    b"hidemyshitsonofabitch", b"gameobj", b"gaymonster", b"moveon",
    b"NewBehaviourScript", b"CokesAnticheat", b"youcantgetwomenever",
    b"youbroketherules", b"IsCorrect", b"yabadabadooo", b"workrrr",
    b"WHYYYYY", b"WAAAAAA", b"Treeheehehe", b"byebye", b"byebyeee",
    b"rotatething", b"settingsyoo", b"thinghehe", b"treeman",
    b"heydonthaveeverything", b"whyareyoufrozen", b"nametag", b"Checkn",
    b"blablabla", b"EditorOnlyStuff", b"somethingtolurethem",
    b"NameDetector", b"ModFolderChecker", b"NoPublic", b"NoPublic125",
    b"sigcheck", b"Questlink", b"Modders", b"Modder", b"sigchecker",
    b"Signature Check", b"MelonLoader", b"uwumod", b"amongus",
    b"OculusByteCheck", b"HydrasBasicAntiCheat", b"ByteCheck",
]

# ------------------ State ------------------
filepath = None
modified_data = None


# ------------------ Core Logic ------------------
def load_file():
    global filepath
    root = Tk()
    root.withdraw()

    f = filedialog.askopenfilename(filetypes=[("Unity3D Files", "*.unity3d")])
    if not f:
        print("No file selected.")
        return

    filepath = f
    print(f"Loaded: {os.path.basename(f)}")


def remove_anticheat():
    global modified_data

    if not filepath:
        print("Load a file first.")
        return

    print("Processing...")

    try:
        with open(filepath, "rb") as f:
            data = bytearray(f.read())
    except Exception as e:
        print("Error:", e)
        return

    removed = []

    for kw in ANTI_CHEAT_KEYWORDS:
        count = data.count(kw)
        if count == 0:
            continue

        removed.append(f"{kw.decode(errors='ignore')} x{count}")

        while kw in data:
            i = data.find(kw)
            data[i:i+len(kw)] = b"\x00" * len(kw)

    modified_data = bytes(data)

    print("Done.\n")

    if removed:
        print("Removed:")
        for r in removed:
            print("-", r)
    else:
        print("Nothing found.")


def save_file():
    if modified_data is None:
        print("Nothing to save.")
        return

    root = Tk()
    root.withdraw()

    path = filedialog.asksaveasfilename(defaultextension=".unity3d")
    if not path:
        return

    with open(path, "wb") as f:
        f.write(modified_data)

    print("Saved.")


# ------------------ Menu (MAIN.PY STYLE) ------------------
def main():
    os.system('cls' if os.name == 'nt' else 'clear')

    show_banner()  # <-- THIS IS YOUR BIG TEXT

    print("=== SKYZ ANTI REMOVER ===\n")
    print("[1] Load File")
    print("[2] Remove Anti")
    print("[3] Save File")
    print("[i] Info")
    print("[x] Exit\n")

    choice = input("Select option: ").lower()

    if choice == "1":
        load_file()
    elif choice == "2":
        remove_anticheat()
    elif choice == "3":
        save_file()
    elif choice == "i":
        print("\nSimple anti-cheat remover tool.")
    elif choice == "x":
        print("Exiting...")
        time.sleep(1)
        exit()
    else:
        print("Invalid.")

    input("\nPress Enter to continue...")
    main()


# ------------------ Run ------------------
if __name__ == "__main__":
    main()