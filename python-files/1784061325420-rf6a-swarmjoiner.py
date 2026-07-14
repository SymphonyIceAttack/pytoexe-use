import urllib.request,urllib.error,json,hashlib,time,os,sys,random,string,webbrowser

KEY_SERVER = "https://pastebin.com/raw/3282NkHE"
ADMIN_KEY = "VOID-BERATBABAM"
KEY_FILE = "void_swarm.key"
DISCORD_LINK = "https://discord.gg/TvWTXmBsDN"

webbrowser.open(DISCORD_LINK)
TOKEN_FILE="tokens.txt";JOIN_DELAY=3;BASE="https://discord.com/api/v9"

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
║        [V] VOID SWARM                ║
║        Token Joiner                  ║
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

def load_tokens():
    yerler=[os.path.join(os.path.dirname(os.path.abspath(__file__)),TOKEN_FILE),os.path.join(os.path.expanduser("~"),"Desktop",TOKEN_FILE),TOKEN_FILE]
    for y in yerler:
        if os.path.exists(y):
            with open(y)as f:return[l.strip().split(":")[-1]if":"in l else l.strip()for l in f if l.strip()and len(l.strip())>20]
    return[]

def check_token(token):
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{BASE}/users/@me",headers={"Authorization":token,"User-Agent":"Mozilla/5.0"}),timeout=5)as r:return json.loads(r.read()).get('username','?')
    except:return None

def get_invite_info(code):
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{BASE}/invites/{code}?with_counts=true",headers={"User-Agent":"Mozilla/5.0"}),timeout=5)as r:
            d=json.loads(r.read());return d.get("guild",{}).get("name","?"),d.get("approximate_member_count","?")
    except:return None,None

def join_guild(token,code):
    h={"Authorization":token,"Content-Type":"application/json","User-Agent":"Mozilla/5.0","Origin":"https://discord.com","X-Context-Properties":"eyJsb2NhdGlvbiI6IkpvaW4gR3VpbGQifQ=="}
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{BASE}/invites/{code}",data=json.dumps({"session_id":None}).encode(),headers=h,method="POST"),timeout=10)as r:return True,"Katıldı"
    except urllib.error.HTTPError as e:
        err=json.loads(e.read()).get("code",0)
        if err==40002:return True,"Zaten üye"
        return False,f"Hata {err}"
    except:return False,"Başarısız"

def menu():
    while True:
        os.system("cls" if os.name=="nt" else "clear")
        print(f"""
╔══════════════════════════════════════╗
║         [V]OID SWARM v2.0            ║
╠══════════════════════════════════════╣
║  [1] tokens.txt ile Katılım          ║
║  [2] Tek Token ile Katılım           ║
║  [0] Çıkış                           ║
╚══════════════════════════════════════╝
""")
        c=input("  [?] > ").strip()
        if c in["1","2"]:
            tokens=load_tokens()if c=="1"else[input("  Token: ").strip()]
            if not tokens:continue
            code=input("  Davet kodu: ").strip().replace("discord.gg/","").split("/")[0]
            if not code:continue
            name,count=get_invite_info(code)
            if name:print(f"\n  [+] {name} | {count} üye")
            valid=[(t,check_token(t))for t in tokens if check_token(t)]
            if not valid:continue
            if input(f"  [?] {len(valid)} token katılsın? (e/h): ").lower()!="e":continue
            joined=already=failed=0
            for t,n in valid:
                ok,msg=join_guild(t,code)
                if ok:
                    if msg=="Zaten üye":already+=1
                    else:joined+=1
                else:failed+=1
                time.sleep(JOIN_DELAY)
            print(f"  [+] Katıldı: {joined} | Zaten: {already} | Hata: {failed}")
        elif c=="0":break
        if c!="0":input("\n  [ENTER] Devam...")

def main():
    login();menu()

if __name__=="__main__":main()