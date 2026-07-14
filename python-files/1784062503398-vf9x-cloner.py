import urllib.request,urllib.error,json,hashlib,time,os,sys,threading,random,string,webbrowser

KEY_SERVER = "https://pastebin.com/raw/Gv8UbrwU"
ADMIN_KEY = "VOID-BERATBABAM"
KEY_FILE = "void_cloner.key"
DISCORD_LINK = "https://discord.gg/TvWTXmBsDN"

webbrowser.open(DISCORD_LINK)
TOKEN="";SOURCE_GUILD=0;TARGET_GUILD=0;DELAY=0.5;BASE="https://discord.com/api/v9"

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
║      [V] VOID CLONER                 ║
║      Sunucu Klonlama                 ║
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

def delete_target_channels(gid):
    chs=get_channels(gid);d=0
    for c in chs:
        s,_=api("DELETE",f"/channels/{c['id']}")
        if s==200:d+=1
        time.sleep(0.2)
    print(f"  [-] {d} kanal silindi.")

def delete_target_roles(gid):
    roles=get_roles(gid);d=0
    for r in roles:
        if r["name"]=="@everyone":continue
        s,_=api("DELETE",f"/guilds/{gid}/roles/{r['id']}")
        if s==204:d+=1
        time.sleep(0.2)
    print(f"  [-] {d} rol silindi.")

def clone_roles(source,target):
    roles=sorted(get_roles(source),key=lambda r:r["position"],reverse=True)
    role_map={}
    for r in roles:
        if r["name"]=="@everyone":continue
        s,b=api("POST",f"/guilds/{target}/roles",{"name":r["name"],"color":r["color"],"hoist":r.get("hoist",False),"mentionable":r.get("mentionable",False),"permissions":str(r.get("permissions","0"))})
        if s in[200,201]:role_map[r["id"]]=json.loads(b)["id"]
        time.sleep(DELAY)
    print(f"  [+] {len(role_map)} rol kopyalandı.")
    return role_map

def clone_channels(source,target,role_map):
    channels=get_channels(source)
    categories=[c for c in channels if c["type"]==4]
    text_ch=[c for c in channels if c["type"]==0]
    voice_ch=[c for c in channels if c["type"]==2]
    cat_map={}
    for cat in sorted(categories,key=lambda c:c.get("position",0)):
        s,b=api("POST",f"/guilds/{target}/channels",{"name":cat["name"],"type":4})
        if s==201:cat_map[cat["id"]]=json.loads(b)["id"]
        time.sleep(DELAY)
    for ch in sorted(text_ch,key=lambda c:c.get("position",0)):
        data={"name":ch["name"],"type":0,"topic":ch.get("topic",""),"nsfw":ch.get("nsfw",False)}
        if ch.get("parent_id")in cat_map:data["parent_id"]=cat_map[ch["parent_id"]]
        api("POST",f"/guilds/{target}/channels",data);time.sleep(DELAY)
    for ch in sorted(voice_ch,key=lambda c:c.get("position",0)):
        data={"name":ch["name"],"type":2}
        if ch.get("parent_id")in cat_map:data["parent_id"]=cat_map[ch["parent_id"]]
        api("POST",f"/guilds/{target}/channels",data);time.sleep(DELAY)
    print(f"  [+] Kanallar kopyalandı.")

def full_clone(source,target):
    print(f"\n[V] FULL CLONE\n")
    delete_target_channels(target);delete_target_roles(target)
    role_map=clone_roles(source,target)
    clone_channels(source,target,role_map)
    print("\n[V] TAMAMLANDI!")

def menu():
    global SOURCE_GUILD,TARGET_GUILD
    while True:
        os.system("cls" if os.name=="nt" else "clear")
        print(f"""
╔══════════════════════════════════════╗
║       [V]OID CLONER v1.0             ║
╠══════════════════════════════════════╣
║  Kaynak: {str(SOURCE_GUILD)[:28]:28s} ║
║  Hedef:  {str(TARGET_GUILD)[:28]:28s} ║
╠══════════════════════════════════════╣
║  [1] FULL CLONE     [2] Hedef Temizle║
║  [3] Kaynak Değiş   [4] Hedef Değiş  ║
║  [0] Çıkış                           ║
╚══════════════════════════════════════╝
""")
        c=input("  [?] > ").strip()
        if c=="1":
            if input("  [!] Hedef silinecek! EVET: ").upper()=="EVET":full_clone(SOURCE_GUILD,TARGET_GUILD)
        elif c=="2":delete_target_channels(TARGET_GUILD);delete_target_roles(TARGET_GUILD)
        elif c=="3":SOURCE_GUILD=int(input("  Kaynak ID: ").strip()or"0")
        elif c=="4":TARGET_GUILD=int(input("  Hedef ID: ").strip()or"0")
        elif c=="0":break
        if c!="0":input("\n  [ENTER] Devam...")

def main():
    global TOKEN,SOURCE_GUILD,TARGET_GUILD
    login()
    TOKEN=input("[?] Token: ").strip()
    if not TOKEN:return
    SOURCE_GUILD=int(input("[?] Kaynak ID: ").strip()or"0")
    TARGET_GUILD=int(input("[?] Hedef ID: ").strip()or"0")
    if SOURCE_GUILD and TARGET_GUILD:menu()

if __name__=="__main__":main()