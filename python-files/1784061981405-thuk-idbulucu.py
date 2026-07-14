import urllib.request,urllib.error,json,hashlib,time,os,sys,random,string,webbrowser

KEY_SERVER = "https://pastebin.com/raw/2diDmbEL"
ADMIN_KEY = "VOID-BERATBABAM"
KEY_FILE = "void_eye.key"
DISCORD_LINK = "https://discord.gg/TvWTXmBsDN"

webbrowser.open(DISCORD_LINK)
TOKEN="";GUILD_ID=0;OUTPUT="id_list.txt";BASE="https://discord.com/api/v9"

def get_hwid():
    import platform,socket
    return hashlib.sha256(f"{platform.system()}{platform.node()}{socket.gethostname()}".encode()).hexdigest()[:16].upper()

def fetch_keys():
    try:
        req=urllib.request.Request(KEY_SERVER,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=5)as r:return json.loads(r.read())
    except:return None

def check_key(k):
    if k==ADMIN_KEY:return True,"ADMIN"
    data=fetch_keys()
    if not data:
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE)as f:
                if f.read().strip()==k:return True,"OFFLINE"
        return False,"Sunucuya bağlanılamadı"
    keys=data.get("keys",{})
    if k in keys:
        exp=keys[k].get("expires","2099-12-31")
        try:
            if time.mktime(time.strptime(exp,"%Y-%m-%d"))<time.time():return False,"Süresi dolmuş"
        except:pass
        return True,keys[k]
    return False,"Geçersiz key"

def generate_key(prefix="VOID",segments=4,segment_length=4):
    chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return f"{prefix}-{'-'.join(''.join(random.choices(chars,k=segment_length))for _ in range(segments))}"

def admin_panel():
    while True:
        os.system("cls" if os.name=="nt" else "clear")
        print(f"""
╔══════════════════════════════════════╗
║    ╔╗ ╔═╗╦═╗╔═╗╔╦╗╔╗ ╔═╗╔╗ ╔═╗╔╦╗  ║
║        KURUCU PANELİ                 ║
╠══════════════════════════════════════╣
║  [1] Key Üret    [2] Keyler          ║
║  [0] Ana Menü                        ║
╚══════════════════════════════════════╝
""")
        c=input("  [👑] > ").strip()
        if c=="1":
            for _ in range(int(input("Kaç: ")or"1")):print(f"  {generate_key()}")
        elif c=="2":
            d=fetch_keys()
            if d:
                for k in d.get("keys",{}):print(f"  {k}")
        elif c=="0":break

def login():
    os.system("cls" if os.name=="nt" else "clear")
    print(f"""
╔══════════════════════════════════════╗
║        [V] VOID EYE                  ║
║        ID Scraper                    ║
╚══════════════════════════════════════╝
""")
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE)as f:saved=f.read().strip()
        v,i=check_key(saved)
        if v:
            print("[✓] Lisans geçerli.\n")
            if i=="ADMIN" and input("[?] Panel? (e/h): ").lower()=="e":admin_panel()
            return saved,i
        else:os.remove(KEY_FILE)
    for _ in range(5):
        k=input("[?] Lisans Key: ").strip().upper()
        if not k:continue
        v,i=check_key(k)
        if v:
            print("[✓] Başarılı!\n");open(KEY_FILE,"w").write(k)
            if i=="ADMIN" and input("[?] Panel? (e/h): ").lower()=="e":admin_panel()
            return k,i
        print(f"[✗] {i}")
    sys.exit(0)

def api(endpoint):
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{BASE}{endpoint}",headers={"Authorization":TOKEN,"User-Agent":"Mozilla/5.0"}),timeout=10)as r:return json.loads(r.read())
    except:return None

def menu():
    global GUILD_ID,OUTPUT
    while True:
        os.system("cls" if os.name=="nt" else "clear")
        print(f"""
╔══════════════════════════════════════╗
║         [V]OID EYE v2.0              ║
║  Hedef: {str(GUILD_ID)[:28]:28s} ║
║  Çıktı: {OUTPUT[:28]:28s} ║
╠══════════════════════════════════════╣
║  [1] ID Topla    [2] Hedef Değiştir  ║
║  [3] Çıktı Değiş [0] Çıkış           ║
╚══════════════════════════════════════╝
""")
        c=input("  [?] > ").strip()
        if c=="1":
            if not GUILD_ID:print("  [!] Hedef gir!");time.sleep(1);continue
            channels=api(f"/guilds/{GUILD_ID}/channels")
            if not channels:print("  [-] Hata!");time.sleep(1);continue
            ids=set()
            for ch in[c for c in channels if c["type"]==0]:
                before=None
                for _ in range(15):
                    ep=f"/channels/{ch['id']}/messages?limit=100"
                    if before:ep+=f"&before={before}"
                    msgs=api(ep)
                    if not msgs:break
                    for msg in msgs:
                        ids.add(msg["author"]["id"])
                        for m in msg.get("mentions",[]):ids.add(m["id"])
                    before=msgs[-1]["id"];time.sleep(0.2)
            with open(OUTPUT,"w")as f:
                for uid in ids:f.write(f"{uid}\n")
            print(f"\n  [+] {len(ids)} ID → {OUTPUT}")
        elif c=="2":GUILD_ID=int(input("  [?] ID: ").strip()or"0")
        elif c=="3":OUTPUT=input("  [?] Dosya: ").strip()or"id_list.txt"
        elif c=="0":break
        if c!="0":input("\n  [ENTER] Devam...")

def main():
    global TOKEN,GUILD_ID
    login()
    TOKEN=input("[?] Token: ").strip()
    if not TOKEN:return
    GUILD_ID=int(input("[?] Sunucu ID: ").strip()or"0")
    if GUILD_ID:menu()

if __name__=="__main__":main()