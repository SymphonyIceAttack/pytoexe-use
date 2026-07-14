import urllib.request,urllib.error,json,hashlib,base64,time,os,sys,threading,random,string,webbrowser

KEY_SERVER = "https://pastebin.com/raw/vmLRqjyA"
ADMIN_KEY = "VOID-BERATBABAM"
KEY_FILE = "void_whisper.key"
DISCORD_LINK = "https://discord.gg/TvWTXmBsDN"

webbrowser.open(DISCORD_LINK)
TOKEN="";DELAY=1.5;THREADS=3
BASE="https://discord.com/api/v9"

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
║         [V] VOID WHISPER             ║
║         Toplu DM Aracı               ║
╚══════════════════════════════════════╝
    Discord: {DISCORD_LINK}
""")
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE)as f:saved=f.read().strip()
        v,i=check_key(saved)
        if v:
            print("[✓] Lisans geçerli.\n")
            if i=="ADMIN" and input("[?] Kurucu paneli? (e/h): ").lower()=="e":admin_panel()
            return saved,i
        else:os.remove(KEY_FILE)
    for _ in range(5):
        k=input("[?] Lisans Key: ").strip().upper()
        if not k:continue
        v,i=check_key(k)
        if v:
            print("[✓] Başarılı!\n");open(KEY_FILE,"w").write(k)
            if i=="ADMIN" and input("[?] Kurucu paneli? (e/h): ").lower()=="e":admin_panel()
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

def get_members(gid):
    members=[];after=None
    while True:
        ep=f"/guilds/{gid}/members?limit=1000"
        if after:ep+=f"&after={after}"
        s,b=api("GET",ep)
        if s!=200:break
        chunk=json.loads(b)
        if not chunk:break
        members.extend(chunk)
        if len(chunk)<1000:break
        after=chunk[-1]["user"]["id"];time.sleep(0.5)
    return members

def get_guilds():
    s,b=api("GET","/users/@me/guilds")
    return json.loads(b)if s==200 else[]

def send_dm(uid,msg):
    for _ in range(3):
        try:
            s,b=api("POST","/users/@me/channels",{"recipient_id":uid})
            if s==200:
                did=json.loads(b)["id"]
                s2,_=api("POST",f"/channels/{did}/messages",{"content":msg})
                if s2==200:return True
            time.sleep(2)
        except:time.sleep(2)
    return False

def run_mass_dm(gid,msg):
    print("\n[*] Üyeler çekiliyor...")
    members=get_members(gid)
    if not members:print("[-] Başarısız!");time.sleep(1);return
    filtered=[m for m in members if not m["user"].get("bot")]
    print(f"[+] {len(filtered)} üye. Süre: ~{len(filtered)*DELAY/60:.0f}dk")
    if input("[?] Devam? (e/h): ").lower()!="e":return
    sent=[0];failed=[0];lock=threading.Lock()
    def worker(chunk):
        for m in chunk:
            u=m["user"]
            pmsg=msg.replace("{user}",u.get("username","?"))
            ok=send_dm(u["id"],pmsg)
            with lock:
                if ok:sent[0]+=1;print(f"  [✓] {u['username']} ({sent[0]}/{len(filtered)})")
                else:failed[0]+=1
            time.sleep(DELAY+random.uniform(0,1))
    cs=max(1,len(filtered)//THREADS)
    tl=[threading.Thread(target=worker,args=(filtered[i:i+cs],))for i in range(0,len(filtered),cs)]
    for t in tl:t.start();time.sleep(0.3)
    for t in tl:t.join()
    print(f"\n[+] Gönderilen: {sent[0]} | Başarısız: {failed[0]}")

def run_dm_from_file(ids,msg):
    print(f"\n[+] {len(ids)} ID. Süre: ~{len(ids)*DELAY/60:.0f}dk")
    if input("[?] Devam? (e/h): ").lower()!="e":return
    sent=[0];lock=threading.Lock()
    def worker(chunk):
        for uid in chunk:
            ok=send_dm(uid,msg)
            with lock:
                if ok:sent[0]+=1;print(f"  [✓] {uid} ({sent[0]}/{len(ids)})")
            time.sleep(DELAY+random.uniform(0,1))
    cs=max(1,len(ids)//THREADS)
    tl=[threading.Thread(target=worker,args=(ids[i:i+cs],))for i in range(0,len(ids),cs)]
    for t in tl:t.start();time.sleep(0.3)
    for t in tl:t.join()
    print(f"\n[+] Gönderilen: {sent[0]}")

def menu():
    while True:
        os.system("cls" if os.name=="nt" else "clear")
        print(f"""
╔══════════════════════════════════════╗
║         [V]OID WHISPER v2.0          ║
╠══════════════════════════════════════╣
║  [1] Sunucudaki Herkese DM At        ║
║  [2] Sunucu ID ile DM At             ║
║  [3] Dosyadan ID Listesi ile DM      ║
║  [0] Çıkış                           ║
╚══════════════════════════════════════╝
""")
        c=input("  [?] > ").strip()
        if c=="1":
            guilds=get_guilds()
            if not guilds:print("\n  [-] Hiç sunucuda değilsin!");time.sleep(1.5);continue
            for i,g in enumerate(guilds):print(f"  [{i+1:2d}] {g['name'][:40]:40s} | {g['id']}")
            try:
                idx=int(input("\n  [?] Sunucu No > "))-1
                if 0<=idx<len(guilds):
                    msg=input("  [?] Mesaj > ").strip()
                    if msg:run_mass_dm(guilds[idx]["id"],msg)
            except:print("  [-] Geçersiz!");time.sleep(1)
        elif c=="2":
            gid=input("  [?] Sunucu ID > ").strip()
            msg=input("  [?] Mesaj > ").strip()
            if gid and msg:run_mass_dm(gid,msg)
        elif c=="3":
            fn=input("  [?] Dosya (id_list.txt) > ").strip()or"id_list.txt"
            if not os.path.exists(fn):print(f"  [-] {fn} yok!");time.sleep(1.5);continue
            with open(fn)as f:ids=[l.strip()for l in f if l.strip()]
            if not ids:print("  [-] Boş!");time.sleep(1.5);continue
            print(f"  [+] {len(ids)} ID.")
            msg=input("  [?] Mesaj > ").strip()
            if msg:run_dm_from_file(ids,msg)
        elif c=="0":print("\n  [V] Sinyal kesildi.");time.sleep(1);break
        else:print("  [-] Geçersiz!");time.sleep(0.5)
        if c!="0":input("\n  [ENTER] Devam...")

def main():
    global TOKEN
    login()
    TOKEN=input("[?] Discord Token: ").strip()
    if not TOKEN:print("[-] Token gerekli!");input();return
    menu()

if __name__=="__main__":main()