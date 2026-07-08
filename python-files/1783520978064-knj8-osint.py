import urllib.request,urllib.error,json,hashlib,base64,time,os,sys,random,string,ssl
import socket,requests,dns.resolver,dns.query,dns.zone,whois,ftplib
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ==========================================
# KEY SERVER (GitHub Gist - Engelsiz)
# ==========================================
KEY_SERVER = "https://gist.githubusercontent.com/zyresxx997-png/42a974b854542c33ab49754ac5e55216/raw/5fcab3fd2d30c5fa185b28b8d1084c6c2ab93ac0/gistfile1.json"
ADMIN_KEY = "VOID-BERATBABAM"
KEY_FILE = "void_osint.key"
DISCORD_LINK = "https://discord.gg/TvWTXmBsDN"

class Renk:Y='\033[92m';S='\033[93m';K='\033[91m';M='\033[94m';R='\033[0m'

def get_hwid():
    import platform,socket
    raw = f"{platform.system()}{platform.node()}{socket.gethostname()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()

def fetch_keys():
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(KEY_SERVER, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            data = json.loads(r.read())
            print(f"{Renk.Y}[✓]{Renk.R} Key sunucusuna baglanildi.")
            return data
    except Exception as e:
        print(f"{Renk.K}[✗]{Renk.R} Sunucu hatasi: {str(e)[:50]}...")
        return None

def check_key(k):
    print(f"{Renk.S}[*]{Renk.R} Key kontrol ediliyor...")
    
    if k == ADMIN_KEY:
        print(f"{Renk.Y}[✓]{Renk.R} Admin key gecerli. Hos geldin Berat Baba!")
        return True, "ADMIN"
    
    data = fetch_keys()
    if not data:
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE) as f:
                if f.read().strip() == k:
                    print(f"{Renk.Y}[✓]{Renk.R} Offline modda dogrulandi.")
                    return True, "OFFLINE"
        return False, "Sunucuya bağlanılamadı"
    
    keys = data.get("keys", {})
    if k in keys:
        exp = keys[k].get("expires", "2099-12-31")
        try:
            if time.mktime(time.strptime(exp, "%Y-%m-%d")) < time.time():
                return False, "Süresi dolmuş"
        except:
            pass
        print(f"{Renk.Y}[✓]{Renk.R} Key gecerli. Son kullanim: {exp}")
        return True, keys[k]
    
    return False, "Geçersiz key"

def save_key(key):
    with open(KEY_FILE, "w") as f:
        f.write(key)

def login_screen():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"""
{Renk.M}╔══════════════════════════════════════╗
║        [V]OID OSINT v2.0               ║
║        Lisans Sistemi                  ║
║        Discord: {DISCORD_LINK}  ║
╚══════════════════════════════════════╝{Renk.R}
""")
    
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            saved = f.read().strip()
        v, i = check_key(saved)
        if v:
            print(f"{Renk.Y}[✓]{Renk.R} Kayitli lisans gecerli.\n")
            time.sleep(0.5)
            return saved, i
        else:
            os.remove(KEY_FILE)
    
    for _ in range(5):
        k = input("[?] Lisans Key: ").strip().upper()
        if not k:
            continue
        v, i = check_key(k)
        if v:
            print(f"{Renk.Y}[✓]{Renk.R} Key gecerli!\n")
            save_key(k)
            time.sleep(0.5)
            return k, i
        print(f"{Renk.K}[✗]{Renk.R} {i}")
    
    print(f"\n{Renk.K}[✗]{Renk.R} Lisans dogrulanamadi!")
    time.sleep(2)
    sys.exit(0)

# ========== OSINT TOOL ==========
def banner():
    print(f"""
{Renk.M}═══════════════════════════════════════
    V0ID OSINT v2.0
    Domain Security Scanner
═══════════════════════════════════════{Renk.R}
""")

def subdomain_scan(d):
    print(f"\n{Renk.S}[*]{Renk.R} Subdomain enumeration...")
    l=["www","mail","ftp","webmail","smtp","pop","ns1","ns2","webdisk","cpanel","whm","autodiscover","autoconfig","m","imap","test","vpn","secure","dev","api","blog","shop","forum","support","admin","backup","beta","cdn","cloud","dashboard","demo","docs","download","email","files","git","help","home","info","internal","lab","login","media","mobile","my","news","panel","partner","remote","repo","root","server","stage","static","store","tools","upload","video","web","app","auth","backend","chat","client","core","data","db","edge","gateway","global","identity","images","jenkins","kafka","kube","legacy","logs","metrics","monitor","namespace","node","oauth","origin","payment","proxy","public","push","redis","reports","routes","search","signup","status","storage","sync","track","traffic","tunnel","ui","updates","users","vault","version","wiki"]
    o=[]
    for x in l:
        try:
            t=f"{x}.{d}";socket.gethostbyname(t);o.append(t);print(f"  {Renk.Y}[+]{Renk.R} {t}")
        except:pass
    if not o:print(f"  {Renk.K}[-]{Renk.R} None found.")
    return o

def port_scan(d):
    print(f"\n{Renk.S}[*]{Renk.R} Port scanning...")
    try:
        ip=socket.gethostbyname(d);print(f"  IP: {ip}")
    except:
        print(f"  {Renk.K}[-]{Renk.R} Resolution failed.");return []
    q=[21,22,23,25,53,80,110,135,139,143,443,445,993,995,1723,3306,3389,5432,5900,8080,8443,8081,8888,9000,27017,6379,11211,9200,9300,161,514,873,1080,1433,1521,2082,2083,2086,2087,2095,2096,2222,3000,5000,8000,8008,8025,8089,8181,8888,9001,9090,9443]
    o=[]
    for x in q:
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.settimeout(0.4)
            if s.connect_ex((ip,x))==0:o.append(x);print(f"  {Renk.Y}[+]{Renk.R} Port {x} open")
            s.close()
        except:pass
    if not o:print(f"  {Renk.K}[-]{Renk.R} None found.")
    return o

def dns_records(d):
    print(f"\n{Renk.S}[*]{Renk.R} DNS records...")
    t=['A','AAAA','MX','NS','TXT','CNAME','SOA','PTR','SRV']
    for x in t:
        try:
            r=dns.resolver.resolve(d,x)
            for y in r:print(f"  {Renk.M}[+]{Renk.R} {x}: {y}")
        except:pass

def email_enum(d):
    print(f"\n{Renk.S}[*]{Renk.R} Email enumeration...")
    l=["admin","info","support","sales","contact","webmaster","postmaster","hostmaster","abuse","help","service","administrator","office","management","hr","recruitment","jobs","career","press","media","social","security","it","tech","billing","payment","account","root","mailer-daemon","noreply","no-reply","hello","team","work","ceo","founder","owner","partner","legal","complaint","feedback","suggestions","investor","pr","marketing","design","dev","engineer","ops","finance","audit"]
    o=[]
    for x in l:
        m=f"{x}@{d}";o.append(m);print(f"  {Renk.Y}[+]{Renk.R} {m}")
    return o

def http_headers(d):
    print(f"\n{Renk.S}[*]{Renk.R} HTTP headers...")
    try:
        r=requests.get(f"http://{d}",timeout=5,allow_redirects=True)
        print(f"  {Renk.M}[+]{Renk.R} HTTP: {r.status_code} {r.url}")
        for k,v in list(r.headers.items())[:8]:print(f"  {Renk.M}[+]{Renk.R} {k}: {v}")
    except:print(f"  {Renk.K}[-]{Renk.R} HTTP failed.")
    try:
        r=requests.get(f"https://{d}",timeout=5,allow_redirects=True,verify=False)
        print(f"\n  {Renk.M}[+]{Renk.R} HTTPS: {r.status_code} {r.url}")
        for k,v in list(r.headers.items())[:8]:print(f"  {Renk.M}[+]{Renk.R} {k}: {v}")
    except:print(f"  {Renk.K}[-]{Renk.R} HTTPS failed.")

def whois_lookup(d):
    print(f"\n{Renk.S}[*]{Renk.R} WHOIS...")
    try:
        q=whois.whois(d)
        if q.domain_name:print(f"  {Renk.M}[+]{Renk.R} Domain: {q.domain_name}")
        if q.registrar:print(f"  {Renk.M}[+]{Renk.R} Registrar: {q.registrar}")
        if q.creation_date:print(f"  {Renk.M}[+]{Renk.R} Created: {q.creation_date}")
        if q.expiration_date:print(f"  {Renk.M}[+]{Renk.R} Expires: {q.expiration_date}")
        if q.name_servers:print(f"  {Renk.M}[+]{Renk.R} NS: {q.name_servers}")
        if q.org:print(f"  {Renk.M}[+]{Renk.R} Org: {q.org}")
        if q.country:print(f"  {Renk.M}[+]{Renk.R} Country: {q.country}")
    except:print(f"  {Renk.K}[-]{Renk.R} WHOIS failed.")

def security_tests(d):
    print(f"\n{Renk.S}[*]{Renk.R} Security tests...")
    f=z=mysql=False;dirs=[]
    try:
        ftp=ftplib.FTP(d);ftp.login();print(f"  {Renk.K}[!]{Renk.R} FTP anonymous OPEN");f=True;ftp.quit()
    except:print(f"  {Renk.Y}[✓]{Renk.R} FTP anonymous closed")
    try:
        zone=dns.zone.from_xfr(dns.query.xfr(d,d));print(f"  {Renk.K}[!]{Renk.R} DNS zone transfer OPEN");z=True
    except:print(f"  {Renk.Y}[✓]{Renk.R} DNS zone transfer closed")
    try:
        import mysql.connector
        conn=mysql.connector.connect(host=d,user="root",password="",database="mysql",connect_timeout=3)
        print(f"  {Renk.K}[!]{Renk.R} MySQL root empty password OPEN");mysql=True;conn.close()
    except:print(f"  {Renk.Y}[✓]{Renk.R} MySQL secure")
    print(f"\n  {Renk.M}[>]{Renk.R} Directory bruteforce...")
    dl=["admin","login","backup","config","wp-admin","phpmyadmin","mysql","test",".env","backup.zip","cpanel","whm","webmail","roundcube","squirrelmail","old","temp","logs","error_log","debug","hidden","private","secure","secret","internal","api","v1","v2","v3","swagger","docs","git",".git","svn",".svn","hg",".hg","backup.sql","dump.sql","database.sql","wp-config.php","config.php","settings.php",".htaccess","robots.txt","sitemap.xml","crossdomain.xml"]
    for x in dl:
        try:
            r=requests.get(f"https://{d}/{x}",timeout=2,verify=False)
            if r.status_code in [200,403,401]:
                dirs.append((x,r.status_code));print(f"  {Renk.S}[!]{Renk.R} /{x} ({r.status_code})")
        except:pass
    if not dirs:print(f"  {Renk.Y}[✓]{Renk.R} No sensitive directories found")
    print(f"\n  {Renk.M}[>]{Renk.R} Summary:")
    if f:print(f"    {Renk.K}[!]{Renk.R} FTP anonymous")
    if z:print(f"    {Renk.K}[!]{Renk.R} DNS zone transfer")
    if mysql:print(f"    {Renk.K}[!]{Renk.R} MySQL empty root")
    if dirs:print(f"    {Renk.S}[!]{Renk.R} {len(dirs)} sensitive dirs")
    if not any([f,z,mysql])and not dirs:print(f"    {Renk.Y}[✓]{Renk.R} No critical vulnerabilities")
    return{"ftp":f,"dns":z,"mysql":mysql,"dirs":dirs}

def save_report(d,subs,ports,emails,sec):
    print(f"\n{Renk.S}[*]{Renk.R} Saving report...")
    t=datetime.now().strftime("%Y%m%d_%H%M%S")
    f=f"osint_{d}_{t}.txt".replace("/","_").replace(":","_")
    try:
        with open(f,"w",encoding="utf-8")as F:
            F.write(f"V0ID OSINT Report - {d}\n")
            F.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            F.write("="*50+"\n\n")
            F.write("SUBDOMAINS:\n")
            if subs:
                for x in subs:F.write(f"  - {x}\n")
            else:F.write("  - None\n")
            F.write("\nOPEN PORTS:\n")
            if ports:
                for x in ports:F.write(f"  - {x}\n")
            else:F.write("  - None\n")
            F.write("\nEMAILS (possible):\n")
            if emails:
                u=list(dict.fromkeys(emails))
                for x in u[:30]:F.write(f"  - {x}\n")
            else:F.write("  - None\n")
            F.write("\nWHOIS:\n")
            try:
                q=whois.whois(d)
                if q.domain_name:F.write(f"  Domain: {q.domain_name}\n")
                if q.registrar:F.write(f"  Registrar: {q.registrar}\n")
                if q.creation_date:F.write(f"  Created: {q.creation_date}\n")
                if q.expiration_date:F.write(f"  Expires: {q.expiration_date}\n")
                if q.name_servers:F.write(f"  NS: {q.name_servers}\n")
            except:F.write("  - Failed\n")
            F.write("\nSECURITY TESTS:\n")
            F.write("  [✓] FTP anonymous closed\n"if not sec["ftp"]else"  [!] FTP anonymous OPEN\n")
            F.write("  [✓] DNS zone transfer closed\n"if not sec["dns"]else"  [!] DNS zone transfer OPEN\n")
            F.write("  [✓] MySQL root empty password closed\n"if not sec["mysql"]else"  [!] MySQL root empty password OPEN\n")
            if sec["dirs"]:
                F.write(f"  [!] {len(sec['dirs'])} sensitive dirs found:\n")
                for x,c in sec["dirs"]:F.write(f"    - /{x} ({c})\n")
            else:F.write("  [✓] No sensitive directories found\n")
        print(f"  {Renk.Y}[+]{Renk.R} Report saved: {f}")
    except Exception as E:print(f"  {Renk.K}[-]{Renk.R} Save failed: {E}")

def main():
    banner()
    d=input("Target domain (example.com): ").strip()
    if not d:print(f"{Renk.K}[!]{Renk.R} No domain entered.");return
    d=d.replace("https://","").replace("http://","").split("/")[0].split(":")[0].strip().lower()
    print(f"\n{Renk.M}[>]{Renk.R} Target: {d}")
    print(f"{Renk.M}[>]{Renk.R} Started: {datetime.now().strftime('%H:%M:%S')}")
    subs=subdomain_scan(d)
    ports=port_scan(d)
    dns_records(d)
    emails=email_enum(d)
    http_headers(d)
    whois_lookup(d)
    sec=security_tests(d)
    save_report(d,subs,ports,emails,sec)
    print(f"\n{Renk.Y}[✓]{Renk.R} Scan complete.")
    print(f"{Renk.Y}[✓]{Renk.R} Finished: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    key, info = login_screen()
    print(f"\n{Renk.Y}[✓]{Renk.R} Hos geldiniz!")
    print(f"{Renk.M}[*]{Renk.R} HWID: {get_hwid()}")
    print(f"{Renk.M}[*]{Renk.R} Key: {key[:10]}...")
    time.sleep(1)
    main()