#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lan/Gen/Utility v0.7  -  Pisciottano Gennaro
Strumento diagnostica rete Windows - operazioni REALI
Avvio: python lan_tester.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess, threading, socket, os, sys, time, platform
import datetime, queue, re, urllib.request, math
import concurrent.futures, struct, ipaddress

# ═══ RILEVAMENTO OS ═══════════════════════════════════════════════
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX   = platform.system() == "Linux"
IS_MAC     = platform.system() == "Darwin"

def _popen_flags():
    """Restituisce creationflags solo su Windows (nasconde la finestra cmd)."""
    if IS_WINDOWS:
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}

def _encoding():
    """Encoding output comandi di sistema."""
    return "cp850" if IS_WINDOWS else "utf-8"

def _ping_cmd(ip, count=1, timeout_ms=1000, size=32, ttl=None, infinite=False):
    """Costruisce il comando ping corretto per l'OS corrente."""
    if IS_WINDOWS:
        cmd = ["ping"]
        if infinite:
            cmd += ["-t"]
        else:
            cmd += ["-n", str(count)]
        cmd += ["-w", str(timeout_ms), "-l", str(size)]
        if ttl:
            cmd += ["-i", str(ttl)]
        cmd += [ip]
    else:
        # Linux / macOS
        cmd = ["ping"]
        if not infinite:
            cmd += ["-c", str(count)]
        cmd += ["-W", str(max(1, timeout_ms // 1000 + 1))]
        cmd += ["-s", str(size)]
        if ttl:
            cmd += ["-t" if IS_MAC else "-t", str(ttl)]
        cmd += [ip]
    return cmd

def _tracert_cmd(dest, max_hops="20", no_dns=True):
    """Costruisce il comando traceroute corretto per l'OS."""
    if IS_WINDOWS:
        cmd = ["tracert", "-h", str(max_hops)]
        if no_dns:
            cmd.append("-d")
        cmd.append(dest)
    else:
        cmd = ["traceroute", "-m", str(max_hops)]
        if no_dns:
            cmd.append("-n")
        cmd.append(dest)
    return cmd

def _arp_cmd(ip=None):
    """Comando ARP per leggere la tabella locale."""
    if IS_WINDOWS:
        return ["arp", "-a"] + ([ip] if ip else [])
    else:
        return ["arp", "-n"] + ([ip] if ip else [])

def _nbtstat_available():
    """NetBIOS/nbtstat disponibile solo su Windows."""
    return IS_WINDOWS

# ═══ COLORI ═══════════════════════════════════════════════════════
BG    = "#080c10"; BG2   = "#0d1117"; BG3   = "#0c1218"
BORDER= "#243040"; FG    = "#c8d8e8"; MUTED = "#8aaccc"
LABEL = "#b8d4ec"; GREEN = "#00ff88"; CYAN  = "#00d4ff"
RED   = "#ff3355"; ORANGE= "#ff8800"; YELLOW= "#ffcc00"
PINK  = "#ff69b4"; WHITE = "#ffffff"; DKRED = "#330800"

# ═══ FONT (+30%) ══════════════════════════════════════════════════
FM  = ("Consolas", 12); FML = ("Consolas", 14)
FMB = ("Consolas", 13, "bold"); FH = ("Segoe UI", 12, "bold")
FHB = ("Segoe UI", 15, "bold"); FT = ("Segoe UI", 20, "bold")
FB  = ("Segoe UI", 14, "bold")

# ═══ FILE TEST DOWNLOAD ═══════════════════════════════════════════
DL_FILES = [
    ("100 MB  - Tele2 CDN (consigliato)",
     "http://speedtest.tele2.net/100MB.zip"),
    ("1 GB    - Tele2 CDN (stress pesante)",
     "http://speedtest.tele2.net/1GB.zip"),
    ("100 MB  - ThinkBroadband UK",
     "http://ipv4.download.thinkbroadband.com/100MB.zip"),
    ("1 GB    - OVH Francia",
     "http://proof.ovh.net/files/1Gb.dat"),
    ("200 MB  - Online.net Francia",
     "http://ping.online.net/200Mo.dat"),
]

Q = queue.Queue()

# ═══ DATABASE OUI MAC — PRODUTTORI ════════════════════════════════
OUI_DB = {
    "00:00:0C":"Cisco","00:00:5E":"Cisco","00:01:42":"Cisco","00:1A:A1":"Cisco",
    "00:50:56":"VMware","00:0C:29":"VMware","00:05:69":"VMware",
    "B8:27:EB":"Raspberry Pi","DC:A6:32":"Raspberry Pi","E4:5F:01":"Raspberry Pi",
    "00:17:F2":"Apple","00:1C:B3":"Apple","00:23:12":"Apple","00:26:BB":"Apple",
    "3C:07:54":"Apple","70:56:81":"Apple","A4:5E:60":"Apple","F0:18:98":"Apple",
    "18:65:90":"Apple","D8:BB:2C":"Apple","F4:F1:5A":"Apple","AC:BC:32":"Apple",
    "00:23:76":"Samsung","00:1D:25":"Samsung","08:D4:0C":"Samsung","50:32:75":"Samsung",
    "B4:3A:28":"Samsung","D8:57:EF":"Samsung","F4:42:8F":"Samsung","78:40:E4":"Samsung",
    "00:15:5D":"Microsoft","28:18:78":"Microsoft","48:70:B3":"Microsoft",
    "54:27:1E":"Microsoft","70:BC:10":"Microsoft",
    "00:13:10":"Linksys","00:18:F8":"Linksys","00:21:29":"Linksys",
    "14:91:82":"TP-Link","50:C7:BF":"TP-Link","54:AF:97":"TP-Link",
    "60:32:B1":"TP-Link","98:DA:C4":"TP-Link","AC:84:C6":"TP-Link",
    "00:90:4C":"ASUS","04:92:26":"ASUS","0C:9D:92":"ASUS","10:7B:44":"ASUS",
    "2C:FD:A1":"ASUS","50:46:5D":"ASUS","74:D0:2B":"ASUS","AC:9E:17":"ASUS",
    "00:1A:2B":"Fujitsu","00:26:55":"Fujitsu",
    "00:0D:3A":"Microsoft Azure","00:22:48":"Microsoft",
    "00:1B:63":"Apple","00:1F:F3":"Apple","00:21:E9":"Apple",
    "28:CF:DA":"Apple","38:C9:86":"Apple","3C:15:C2":"Apple",
    "00:19:E3":"Huawei","00:1E:10":"Huawei","00:25:68":"Huawei",
    "04:F9:38":"Huawei","0C:37:DC":"Huawei","10:1B:54":"Huawei",
    "20:F3:A3":"Huawei","28:6E:D4":"Huawei","48:00:31":"Huawei",
    "4C:8B:EF":"Huawei","54:51:1B":"Huawei","58:2A:F7":"Huawei",
    "00:40:20":"Emulex","00:E0:4C":"Realtek","52:54:00":"QEMU/KVM",
    "00:50:C2":"Teltonika","00:1E:61":"Motorola","00:17:C4":"Motorola",
    "00:22:BD":"Cisco-Linksys","00:1D:7E":"Cisco","00:25:45":"Cisco",
    "F8:1A:67":"TP-Link","A0:F3:C1":"TP-Link","64:70:02":"TP-Link",
    "00:26:5A":"HP","00:17:08":"HP","3C:D9:2B":"HP","9C:8E:99":"HP",
    "AC:E2:D3":"HP","F0:92:1C":"HP","00:80:77":"HP",
    "00:60:B0":"HP","14:58:D0":"HP","70:5A:0F":"HP",
    "00:13:72":"Dell","00:14:22":"Dell","00:18:8B":"Dell","00:21:70":"Dell",
    "00:23:AE":"Dell","14:18:77":"Dell","18:03:73":"Dell","24:B6:FD":"Dell",
    "34:17:EB":"Dell","44:A8:42":"Dell","54:9F:35":"Dell","78:45:C4":"Dell",
    "00:1A:4B":"Netgear","00:1B:2F":"Netgear","00:1E:2A":"Netgear",
    "00:22:3F":"Netgear","00:24:B2":"Netgear","20:4E:7F":"Netgear",
    "28:C6:8E":"Netgear","2C:B0:5D":"Netgear","84:1B:5E":"Netgear",
    "00:1C:4A":"Xiaomi","0C:1D:AF":"Xiaomi","28:6C:07":"Xiaomi",
    "34:80:B3":"Xiaomi","64:09:80":"Xiaomi","68:DF:DD":"Xiaomi",
    "74:51:BA":"Xiaomi","8C:BE:BE":"Xiaomi","A4:50:46":"Xiaomi",
    "B0:E2:35":"Xiaomi","F8:A4:5F":"Xiaomi","FC:64:BA":"Xiaomi",
    "00:04:4B":"Nvidia","04:4B:ED":"Nvidia",
    "00:1A:11":"Google","54:60:09":"Google","F4:F5:D8":"Google",
    "00:17:F2":"Apple TV","00:11:24":"Apple",
    "00:04:E2":"Epson","00:26:AB":"Epson","AC:18:26":"Epson",
    "00:00:48":"Seagate","00:1B:A9":"Brother","00:80:92":"Brother",
    "00:30:05":"Canon","00:1E:8F":"Canon","08:00:37":"Canon",
    "00:00:85":"Sony","00:01:4A":"Sony","00:13:A9":"Sony",
    "00:1D:BA":"Sony","30:17:C8":"Sony","78:84:3C":"Sony",
    "00:1C:A8":"TRENDnet","00:14:D1":"TRENDnet",
    "00:E0:64":"Samsung","00:12:FB":"Samsung","00:15:B9":"Samsung",
    "00:26:37":"Samsung","30:CD:A7":"Samsung","5C:F8:A1":"Samsung",
    "00:17:31":"Gemtek","00:15:61":"Motorola","00:60:52":"Motorola",
    "44:E9:DD":"LG","A8:16:D0":"LG","CC:FA:00":"LG","F8:77:B8":"LG",
    "00:19:99":"Belkin","00:30:BD":"Belkin","94:44:52":"Belkin",
    "00:14:BF":"Linksys","00:16:B6":"Linksys","00:18:39":"Linksys",
}

def oui_lookup(mac: str) -> str:
    """Ritorna il produttore dal MAC address (prefisso 3 ottetti OUI)."""
    if not mac or mac in ("—",""):
        return "Sconosciuto"
    prefix3 = mac.upper()[:8]  # XX:XX:XX
    return OUI_DB.get(prefix3, "Sconosciuto")


class LANTesterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Lan/Gen/Utility v0.10")
        self.root.configure(bg=BG)
        self.root.state("zoomed")
        self.root.resizable(True, True)

        self.running    = False
        self.proc       = None
        self.dl_threads = []
        self.log_buf    = []
        self.ping_vals  = []
        self.bw_vals    = []
        self.dl_speeds  = {}
        self.grafici    = {}

        # ── Smoothing tachigrafi (interpolazione a 60fps) ──────────
        self._dl_tach_target  = 0.0   # valore target tachigrafo download
        self._dl_tach_current = 0.0   # valore interpolato corrente
        self._st_tach_target  = 0.0   # valore target tachigrafo speed test
        self._st_tach_current = 0.0   # valore interpolato corrente

        self._style()
        self._header()
        self._tabs()
        self._statusbar()
        self._poll()
        self._tach_anim_loop()
        threading.Thread(target=self._ip, daemon=True).start()

    # ── AUDIO ──────────────────────────────────────────────────────
    def _beep(self, kind="ok"):
        """Suono breve in thread daemon — non blocca il ping.
        kind='ok'  → beep acuto breve
        kind='err' → doppio tono discendente (alert)
        """
        def _play():
            try:
                if IS_WINDOWS:
                    import winsound
                    if kind == "ok":
                        winsound.Beep(880, 60)
                    else:
                        winsound.Beep(440, 120)
                        winsound.Beep(280, 160)
                elif IS_MAC:
                    if kind == "ok":
                        subprocess.run(["afplay","/System/Library/Sounds/Tink.aiff"],
                                       capture_output=True, timeout=2)
                    else:
                        subprocess.run(["afplay","/System/Library/Sounds/Basso.aiff"],
                                       capture_output=True, timeout=2)
                else:
                    import struct, wave, tempfile, os, math as _m
                    sr = 44100
                    freq, dur_ms, vol = (880,60,0.3) if kind=="ok" else (380,220,0.7)
                    n = int(sr * dur_ms / 1000)
                    samples = b"".join(
                        struct.pack('<h', int(vol*32767*_m.sin(2*_m.pi*freq*i/sr)))
                        for i in range(n))
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                        path = tf.name
                        with wave.open(tf,'w') as wf:
                            wf.setnchannels(1); wf.setsampwidth(2)
                            wf.setframerate(sr); wf.writeframes(samples)
                    for c_ in [["paplay",path],["aplay","-q",path]]:
                        try: subprocess.run(c_, capture_output=True, timeout=2); break
                        except FileNotFoundError: continue
                    try: os.unlink(path)
                    except: pass
            except Exception:
                pass
        threading.Thread(target=_play, daemon=True).start()

    # ── PARSE RTT ─────────────────────────────────────────────────
    @staticmethod
    def _parse_rtt(line: str):
        """
        Estrae il valore RTT in ms da una riga di output ping.
        Copre TUTTE le localizzazioni Windows e Linux/macOS:
          Windows IT:  durata=34ms   durata<1ms   tempo=34ms   tempo<1ms
          Windows EN:  time=34ms     time<1ms
          Linux/macOS: time=1.23 ms  time=34 ms
        Ritorna int(ms) oppure None se non trovato.
        """
        ll = line.lower()
        m = (re.search(r"durata\s*[=<]\s*(\d+(?:\.\d+)?)\s*ms", ll) or
             re.search(r"tempo\s*[=<]\s*(\d+(?:\.\d+)?)\s*ms",  ll) or
             re.search(r"time\s*[=<]\s*(\d+(?:\.\d+)?)\s*ms",   ll))
        if m:
            return int(float(m.group(1)))
        return None

    # ── STILE ─────────────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self.root)
        s.theme_use("default")
        s.configure("TNotebook",     background=BG,  borderwidth=0, tabmargins=0)
        s.configure("TNotebook.Tab", background="#0a0f16", foreground=MUTED,
                    font=FH, padding=[20, 10], borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", BG2), ("active","#162030")],
              foreground=[("selected", WHITE),("active", WHITE)])
        s.configure("TCombobox", fieldbackground=BG3, background=BG3,
                    foreground=GREEN, selectbackground=BG3)

    # ── HEADER ────────────────────────────────────────────────────
    def _header(self):
        h = tk.Frame(self.root, bg=BG, pady=6)
        h.pack(fill="x", padx=12)

        # Sinistra: icona + nome programma
        ic = tk.Canvas(h, width=110, height=60, bg=BG, highlightthickness=0)
        ic.pack(side="left", padx=(0,10))
        self._draw_icon(ic)
        self._led_canvas = ic
        self._led_state  = {}
        self._animate_leds()

        tk.Label(h, text="Lan/Gen/Utility",
                 font=("Segoe UI",26,"bold"), fg=CYAN, bg=BG).pack(side="left")
        tk.Label(h, text=" v0.10", font=("Consolas",13), fg=YELLOW, bg=BG).pack(side="left", pady=8)

        # Destra: autore
        destra = tk.Frame(h, bg=BG)
        destra.pack(side="right", padx=16)
        tk.Label(destra, text="Pisciottano Gennaro",
                 font=("Segoe UI",13,"bold"), fg=WHITE, bg=BG).pack(anchor="e")
        tk.Label(destra, text="powered by Claude AI  -  Anthropic",
                 font=("Segoe UI",9), fg=MUTED, bg=BG).pack(anchor="e")

        # Centro: IP LAN e IP Pubblico
        centro = tk.Frame(h, bg=BG)
        centro.pack(side="right", expand=True, fill="x", padx=20)
        tk.Label(centro, text="— RETE CORRENTE —",
                 font=("Segoe UI",9,"bold"), fg=MUTED, bg=BG).pack()
        self.lbl_lan = tk.Label(centro, text="IL TUO IP È:  ...",
                               font=("Consolas",13,"bold"), fg=WHITE, bg=BG)
        self.lbl_lan.pack()
        self.lbl_pub = tk.Label(centro, text="IP PUBBLICO:  ...",
                               font=("Consolas",11), fg=CYAN, bg=BG)
        self.lbl_pub.pack()

        tk.Frame(self.root, bg=BORDER, height=2).pack(fill="x")

    def _draw_icon(self, c):
        """Disegna: router centrale + 3 PC + cavi + LED."""
        W, H = 110, 60
        # ── Router centrale ──────────────────────────────────────
        rx, ry, rw, rh = 40, 22, 30, 16
        c.create_rectangle(rx, ry, rx+rw, ry+rh,
                           fill="#0d2035", outline=CYAN, width=2, tags="router")
        # Antenna sinistra
        c.create_line(rx+6, ry, rx+4, ry-8, fill=CYAN, width=1)
        c.create_oval(rx+2, ry-11, rx+6, ry-7, fill=CYAN, outline="", tags="led_ant_l")
        # Antenna destra
        c.create_line(rx+rw-6, ry, rx+rw-4, ry-8, fill=CYAN, width=1)
        c.create_oval(rx+rw-6, ry-11, rx+rw-2, ry-7, fill=CYAN, outline="", tags="led_ant_r")
        # LED router (4 punti colorati)
        led_cols = [GREEN, CYAN, YELLOW, GREEN]
        led_tags = ["led_r0","led_r1","led_r2","led_r3"]
        for i,(lc,lt) in enumerate(zip(led_cols, led_tags)):
            lx = rx + 4 + i*6
            c.create_oval(lx, ry+5, lx+4, ry+10,
                          fill=lc, outline="", tags=lt)

        # ── PC sinistro ──────────────────────────────────────────
        # Monitor
        c.create_rectangle(2, 18, 22, 34, fill="#071520", outline=MUTED, width=1)
        c.create_rectangle(4, 20, 20, 32, fill="#0a2540", outline="")
        # Piedistallo
        c.create_line(12, 34, 12, 40, fill=MUTED, width=2)
        c.create_line(8, 40, 16, 40, fill=MUTED, width=2)
        # Tastiera
        c.create_rectangle(4, 42, 20, 46, fill="#0a1825", outline=MUTED, width=1)
        # LED pc sx
        c.create_oval(16, 44, 19, 47, fill=GREEN, outline="", tags="led_pc_l")
        # Cavo router-pc_sx
        c.create_line(22, 28, rx, 30, fill="#3a7aaa", width=2)

        # ── PC destro ────────────────────────────────────────────
        px2 = W - 24
        c.create_rectangle(px2-2, 18, px2+18, 34, fill="#071520", outline=MUTED, width=1)
        c.create_rectangle(px2, 20, px2+16, 32, fill="#0a2540", outline="")
        c.create_line(px2+8, 34, px2+8, 40, fill=MUTED, width=2)
        c.create_line(px2+4, 40, px2+12, 40, fill=MUTED, width=2)
        c.create_rectangle(px2, 42, px2+16, 46, fill="#0a1825", outline=MUTED, width=1)
        # LED pc dx
        c.create_oval(px2+12, 44, px2+15, 47, fill=GREEN, outline="", tags="led_pc_r")
        # Cavo router-pc_dx
        c.create_line(rx+rw, 30, px2-2, 28, fill="#3a7aaa", width=2)

        # ── PC in basso (laptop) ─────────────────────────────────
        bx = W//2 - 14
        c.create_rectangle(bx, 46, bx+28, 56, fill="#071520", outline=MUTED, width=1)
        c.create_rectangle(bx+2, 48, bx+26, 54, fill="#0a2540", outline="")
        c.create_rectangle(bx-2, 56, bx+30, 59, fill="#0a1825", outline=MUTED, width=1)
        # LED laptop
        c.create_oval(bx+22, 57, bx+26, 60, fill=CYAN, outline="", tags="led_lap")
        # Cavo router-laptop
        c.create_line(rx+rw//2, ry+rh, bx+14, 46, fill="#3a7aaa", width=2)

        # Salva riferimenti agli item LED
        self._led_tags = ["led_r0","led_r1","led_r2","led_r3",
                          "led_ant_l","led_ant_r","led_pc_l","led_pc_r","led_lap"]
        self._led_colors = {
            "led_r0": GREEN,  "led_r1": CYAN, "led_r2": YELLOW, "led_r3": GREEN,
            "led_ant_l": CYAN, "led_ant_r": CYAN,
            "led_pc_l": GREEN, "led_pc_r": GREEN, "led_lap": CYAN
        }

    def _animate_leds(self):
        """Fa lampeggiare i LED della rete in modo casuale."""
        import random
        c = self._led_canvas
        for tag in self._led_tags:
            col = self._led_colors[tag]
            # Alterna tra pieno e spento/scuro con probabilità
            if random.random() < 0.35:
                c.itemconfig(tag, fill="#04070a")
            else:
                c.itemconfig(tag, fill=col)
        self.root.after(random.randint(120, 400), self._animate_leds)

    # ── TABS ──────────────────────────────────────────────────────
    def _tabs(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=6, pady=(4,0))
        self._tab_tip_win = None

        TAB_DEFS = [
            ("  🔵 PING",            self._tab_ping,
             "PING\nVerifica raggiungibilità host via ICMP.\nMisura RTT min/med/max e pacchetti persi in tempo reale.\nPing multiplo sui 4 gateway LAN predefiniti.\nAudio beep: tono OK / alert KO."),
            ("  🔍 SCANNER RETE",    self._tab_scanner,
             "SCANNER RETE\nScansiona la subnet alla ricerca di host attivi.\nRileva: IP, MAC, produttore OUI, hostname DNS,\nnome NetBIOS, porte aperte, tipo dispositivo.\nUtile per inventario e sicurezza LAN."),
            ("  ⚡ SPEED TEST",      self._tab_speedtest,
             "SPEED TEST\nMisura velocità reale connessione Internet.\n3 fasi: latenza TCP → download → upload.\nTaghigrafo animato in tempo reale.\nStorico ultimi 10 test nella sidebar."),
            ("  📥 STRESS DOWNLOAD", self._tab_download,
             "STRESS DOWNLOAD\nScarica N file simultanei per saturare la banda.\nTesta stabilità connessione sotto carico massimo\n(fino a 50 download paralleli).\nTaghigrafo velocità totale in tempo reale."),
            ("  🔴 INFO RETE",       self._tab_info,
             "INFO RETE\nInformazioni sulla configurazione di rete locale.\nipconfig/ifconfig, ARP, route, nslookup, netstat.\nUtile per diagnosi e documentazione rete."),
            ("  📊 MONITORAGGIO",    self._tab_monitor,
             "MONITORAGGIO RETE\nMonitoraggio continuo di uno o più host.\nAvvisa se un host va offline (beep + notifica).\nGrafico uptime/downtime e % disponibilità.\nUtile per server e dispositivi critici."),
            ("  🗺 TRACEROUTE",      self._tab_tracert,
             "TRACEROUTE\nMappa ogni router (hop) tra te e la destinazione.\nPer ogni hop: IP e latenza su 3 misurazioni.\nIndividua colli di bottiglia e perdite di pacchetti."),
            ("  ✉ MESSAGGI LAN",     self._tab_messaggi,
             "MESSAGGI LAN\nInvia messaggi agli utenti su range di rete LAN.\nFunzione 'msg' Windows con ricevuta di lettura.\nControllo utenti dominio: cerca per nome/cognome.\n'query user' per utenti connessi ai gateway."),
        ]

        for nm, fn, _ in TAB_DEFS:
            fr = tk.Frame(self.nb, bg=BG)
            self.nb.add(fr, text=nm)
            fn(fr)

        # Tooltip sui tab al passaggio del mouse
        def _on_motion(event):
            try:
                idx = self.nb.index(f"@{event.x},{event.y}")
                txt = TAB_DEFS[idx][2]
            except Exception:
                self._hide_tab_tip(); return
            if self._tab_tip_win and self._tab_tip_win.winfo_exists():
                if getattr(self._tab_tip_win, '_tip_idx', -1) == idx: return
                self._hide_tab_tip()
            win = tk.Toplevel(self.root)
            win.wm_overrideredirect(True)
            win.wm_geometry(f"+{event.x_root+10}+{event.y_root+20}")
            win._tip_idx = idx
            outer = tk.Frame(win, bg=CYAN, padx=1, pady=1); outer.pack()
            inner = tk.Frame(outer, bg="#05101a", padx=12, pady=8); inner.pack()
            for i, line in enumerate(txt.strip().split("\n")):
                col = CYAN if i==0 else FG
                fnt = ("Segoe UI",10,"bold") if i==0 else ("Segoe UI",9)
                tk.Label(inner, text=line, fg=col, bg="#05101a",
                         font=fnt, anchor="w", justify="left").pack(anchor="w")
            self._tab_tip_win = win

        def _on_leave(event):
            self._hide_tab_tip()

        self.nb.bind("<Motion>",   _on_motion)
        self.nb.bind("<Leave>",    _on_leave)
        self.nb.bind("<Button-1>", lambda e: self._hide_tab_tip())

    def _hide_tab_tip(self):
        if self._tab_tip_win:
            try: self._tab_tip_win.destroy()
            except: pass
            self._tab_tip_win = None

    # ── STATUSBAR ─────────────────────────────────────────────────
    def _statusbar(self):
        self.sb = tk.Label(self.root, text="Pronto.", font=FM,
                           fg=MUTED, bg="#050a0f", anchor="w", padx=12, pady=4)
        self.sb.pack(fill="x", side="bottom")

    def _poll(self):
        while not Q.empty():
            try:
                t, line, tag = Q.get_nowait()
                self._w(t, line, tag)
            except queue.Empty:
                break
        self.root.after(40, self._poll)

    def _ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8",80))
            lan = s.getsockname()[0]; s.close()
        except: lan = "N/D"
        try:
            pub = urllib.request.urlopen("https://api.ipify.org",timeout=5).read().decode()
        except: pub = "N/D"
        self.root.after(0, lambda: (
            self.lbl_lan.config(text=f"IL TUO IP È:  {lan}"),
            self.lbl_pub.config(text=f"IP PUBBLICO:  {pub}")
        ))

    # ── HELPER WIDGET ─────────────────────────────────────────────
    def _panel(self, parent, title, col=CYAN, w=None):
        f = tk.Frame(parent, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        if w:
            f.configure(width=w); f.pack_propagate(False)
        f.pack(side="left", fill="y", padx=4, pady=4)
        tk.Label(f, text=title, fg=col, bg=BG2, font=FHB, anchor="w").pack(
            fill="x", padx=10, pady=(8,4))
        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=6)
        body = tk.Frame(f, bg=BG2)
        body.pack(fill="both", expand=True, padx=8, pady=6)
        return body

    def _lbl(self, p, t, col=LABEL):
        tk.Label(p, text=t, fg=col, bg=BG2, font=FH, anchor="w").pack(fill="x", pady=(4,1))

    def _entry(self, p, default=""):
        e = tk.Entry(p, bg=BG3, fg=GREEN, insertbackground=GREEN, font=FML,
                     bd=0, relief="flat",
                     highlightbackground=BORDER, highlightthickness=1,
                     highlightcolor=CYAN)
        e.insert(0, default)
        e.pack(fill="x", pady=(0,4))
        return e

    def _combo(self, p, vals, idx=0):
        cb = ttk.Combobox(p, values=vals, state="readonly", font=FM)
        cb.current(idx); cb.pack(fill="x", pady=(0,4))
        # Forza sfondo scuro sulla listbox del dropdown
        try:
            cb.tk.eval(f"""
                option add *TCombobox*Listbox.background {BG3}
                option add *TCombobox*Listbox.foreground {GREEN}
                option add *TCombobox*Listbox.selectBackground #1a2a3a
                option add *TCombobox*Listbox.selectForeground white
            """)
        except: pass
        return cb

    def _tooltip(self, widget, text):
        """Tooltip: appare su Enter, scompare su Leave/Button."""
        tip = [None]
        def show(e):
            if tip[0] and tip[0].winfo_exists(): return
            t = tk.Toplevel(widget)
            t.wm_overrideredirect(True)
            t.wm_geometry(f"+{e.x_root+14}+{e.y_root+8}")
            outer = tk.Frame(t, bg=CYAN, padx=1, pady=1); outer.pack()
            inner = tk.Frame(outer, bg="#05101a", padx=10, pady=6); inner.pack()
            for i, line in enumerate(text.strip().split("\n")):
                col = CYAN if i == 0 else FG
                fnt = ("Segoe UI",10,"bold") if i==0 else ("Segoe UI",9)
                tk.Label(inner, text=line, fg=col, bg="#05101a",
                         font=fnt, anchor="w", justify="left").pack(anchor="w")
            tip[0] = t
        def hide(e=None):
            if tip[0]:
                try: tip[0].destroy()
                except: pass
                tip[0] = None
        widget.bind("<Enter>",    show, add="+")
        widget.bind("<Leave>",    hide, add="+")
        widget.bind("<Button>",   hide, add="+")
        widget.bind("<FocusOut>", hide, add="+")

    def _btn_tip(self, p, t, cmd, col=GREEN, tip=""):
        """Bottone con tooltip integrato."""
        b = self._btn(p, t, cmd, col)
        if tip:
            self._tooltip(b, tip)
        return b

    def _chk(self, p, t, var, col=CYAN):
        tk.Checkbutton(p, text=t, variable=var, fg=col, bg=BG2,
                       activebackground=BG2, activeforeground=WHITE,
                       selectcolor=BG3, font=FH, anchor="w").pack(fill="x", pady=1)

    def _btn(self, p, t, cmd, col=GREEN):
        b = tk.Button(p, text=t, command=cmd, bg=BG2, fg=col, font=FB,
                      activebackground="#162030", activeforeground=WHITE,
                      bd=2, relief="groove", cursor="hand2",
                      highlightbackground=col, highlightthickness=1, padx=8, pady=7)
        b.bind("<Enter>", lambda e: b.config(bg="#162030", fg=WHITE))
        b.bind("<Leave>", lambda e: b.config(bg=BG2, fg=col))
        b.pack(fill="x", pady=3)
        return b

    def _term(self, p, h=12):
        t = scrolledtext.ScrolledText(p, bg="#04070a", fg=FG, insertbackground=GREEN,
                                       font=FML, bd=0, relief="flat",
                                       highlightbackground=BORDER, highlightthickness=1,
                                       wrap="word", height=h, state="disabled")
        t.tag_config("ok",   foreground=GREEN)
        t.tag_config("err",  foreground=RED)
        t.tag_config("warn", foreground=ORANGE)
        t.tag_config("info", foreground=CYAN)
        t.tag_config("data", foreground=YELLOW)
        t.tag_config("muted",foreground=MUTED)
        t.pack(fill="both", expand=True, pady=(4,0))
        return t

    def _cvs(self, p, h=110):
        c = tk.Canvas(p, bg="#04070a", height=h, highlightthickness=0)
        c.pack(fill="x", pady=(0,4))
        return c

    def _w(self, t, txt, tag=""):
        self.log_buf.append(f"{datetime.datetime.now():%H:%M:%S}  {txt}")
        t.config(state="normal")
        t.insert("end", txt+"\n", tag if tag else ())
        t.see("end"); t.config(state="disabled")

    def _clr(self, t):
        t.config(state="normal"); t.delete("1.0","end"); t.config(state="disabled")

    def _st(self, txt, col=MUTED): self.sb.config(text=txt, fg=col)

    def _salva(self):
        nome = f"lan_log_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Testo","*.txt"),("Tutti","*.*")],
            initialfile=nome, title="Salva log")
        if not path: return
        with open(path,"w",encoding="utf-8") as f:
            f.write(f"Lan/Gen/Utility v0.7 - {datetime.datetime.now():%d/%m/%Y %H:%M:%S}\n")
            f.write("="*60+"\n\n"+"\n".join(self.log_buf))
        messagebox.showinfo("Salvato", f"Log salvato:\n{path}")

    # ── GRAFICI ───────────────────────────────────────────────────
    def _plot_rtt(self, canvas, vals, vmax=None):
        canvas.delete("all")
        # Usa dimensioni fisse se disponibili (evita winfo_width=1 prima del render)
        if hasattr(self, '_ping_rtt_size') and canvas is self.grafici.get("ping"):
            w, h = self._ping_rtt_size
        else:
            canvas.update_idletasks()
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 10: w = 400
            if h < 10: h = 110
        pl, pb = 44, 20
        gw = w - pl - 6; gh = h - pb - 6
        if not vals:
            canvas.create_text(w//2, h//2, text="In attesa dati...", fill=MUTED, font=FM)
            return
        mx = vmax or max((v for v in vals if v is not None), default=100)
        if mx == 0: mx = 100
        for i in range(4):
            y = 6 + gh - int(gh*i/3)
            canvas.create_line(pl, y, w-6, y, fill=BORDER, dash=(2,4))
            canvas.create_text(pl-4, y, text=str(int(mx*i/3)),
                               fill=MUTED, font=("Consolas",9), anchor="e")
        n = len(vals)
        bw = max(2, gw // max(n,1) - 1)
        for i, v in enumerate(vals):
            x = pl + int(i * gw / max(n,1))
            if v is None:
                col = RED; bh = gh
            else:
                bh  = int(gh * min(v, mx) / mx)
                col = RED if v > 200 else ORANGE if v > 50 else GREEN
            y0 = 6 + gh - bh
            canvas.create_rectangle(x, y0, x+bw, 6+gh, fill=col, outline="")

    def _plot_bw(self, canvas, vals, unit="Mb/s"):
        """Grafico stile Speedtest.net: area gradiente + linea velocità + picco."""
        canvas.delete("all")
        canvas.update_idletasks()
        w = canvas.winfo_width() or 500
        h = canvas.winfo_height() or 110
        pl, pr, pt, pb = 52, 10, 8, 22
        gw = w - pl - pr
        gh = h - pt - pb

        if not vals:
            canvas.create_text(w//2, h//2, text="In attesa dati...", fill=MUTED, font=FM)
            return

        # Scala dinamica con arrotondamento
        raw_max = max(vals) or 1
        # Arrotonda il massimo al multiplo "pulito" superiore
        for step in [1,2,5,10,20,50,100,200,500,1000]:
            if raw_max <= step * 4:
                mx = step * 4
                break
        else:
            mx = raw_max * 1.25

        # Griglia e label asse Y
        for i in range(5):
            y = pt + gh - int(gh * i / 4)
            canvas.create_line(pl, y, w-pr, y, fill=BORDER, dash=(2,4))
            val_label = mx * i / 4
            label = f"{int(val_label)}" if val_label == int(val_label) else f"{val_label:.1f}"
            canvas.create_text(pl-4, y, text=label, fill=MUTED,
                               font=("Consolas",9), anchor="e")

        # Label asse X (tempo)
        canvas.create_text(pl, h-4, text="←  tempo  →", fill=MUTED,
                           font=("Consolas",8), anchor="w")
        canvas.create_text(w-pr, h-4, text="ora", fill=CYAN,
                           font=("Consolas",8), anchor="e")

        n = len(vals)
        if n < 2:
            # Solo un punto: disegna barra singola
            v = vals[0]
            bh = int(gh * min(v, mx) / mx)
            x = pl + gw // 2
            canvas.create_rectangle(x-6, pt+gh-bh, x+6, pt+gh,
                                    fill=CYAN, outline="")
        else:
            # Calcola punti della linea
            def px(i): return pl + int(i * gw / (n-1))
            def py(v): return pt + gh - int(gh * min(v, mx) / mx)

            # Area gradiente simulata con bande orizzontali (effetto fill)
            poly_pts = [pl, pt+gh]
            for i, v in enumerate(vals):
                poly_pts += [px(i), py(v)]
            poly_pts += [pl + gw, pt+gh]

            # Disegna sfumatura per bande
            num_bands = 20
            for band in range(num_bands, 0, -1):
                ratio = band / num_bands
                # Colore: da #003366 (fondo) a #00d4ff (top)
                r = int(0x00)
                g = int(0x44 + (0x90 * ratio))
                b = int(0x66 + (0x99 * ratio))
                band_col = f"#{r:02x}{g:02x}{b:02x}"
                # Clip orizzontale: disegna solo la parte sotto la curva
                clip_pts = [pl, pt+gh]
                for i, v in enumerate(vals):
                    cy = py(v)
                    band_y = pt + int(gh * (1 - ratio))
                    clip_y = max(cy, band_y)
                    clip_pts += [px(i), clip_y]
                clip_pts += [pl+gw, pt+gh]
                if len(clip_pts) >= 6:
                    canvas.create_polygon(clip_pts, fill=band_col, outline="", smooth=False)

            # Linea principale (bianca/cyan luminosa)
            line_pts = []
            for i, v in enumerate(vals):
                line_pts += [px(i), py(v)]
            if len(line_pts) >= 4:
                canvas.create_line(line_pts, fill=WHITE, width=2, smooth=True)

            # Linea picco (tratteggiata arancione)
            peak = max(vals)
            peak_y = py(peak)
            canvas.create_line(pl, peak_y, pl+gw, peak_y,
                               fill=ORANGE, width=1, dash=(4,3))
            canvas.create_text(w-pr-2, peak_y-8, text=f"↑{peak:.1f}",
                               fill=ORANGE, font=("Consolas",9), anchor="e")

            # Punto corrente (ultimo valore) con cerchio luminoso
            cur_v = vals[-1]
            cur_x = px(n-1)
            cur_y = py(cur_v)
            canvas.create_oval(cur_x-5, cur_y-5, cur_x+5, cur_y+5,
                               fill=CYAN, outline=WHITE, width=2)
            # Etichetta valore corrente
            col_cur = GREEN if cur_v > mx*0.5 else CYAN if cur_v > mx*0.2 else ORANGE
            canvas.create_text(cur_x, cur_y-16, text=f"{cur_v:.1f}",
                               fill=col_cur, font=("Consolas",10,"bold"), anchor="s")

        # Label unità misura
        canvas.create_text(pl-2, pt, text=unit, fill=MUTED,
                           font=("Consolas",9), anchor="e")

    # ── ESECUZIONE COMANDI ────────────────────────────────────────
    def _run(self, cmd, term, done=None):
        self.running = True
        def _t():
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     text=True, encoding=_encoding(), errors="replace",
                                     **_popen_flags())
                self.proc = p
                for line in p.stdout:
                    line = line.rstrip()
                    if not line: Q.put((term,"","")); continue
                    ll = line.lower()
                    if any(x in ll for x in ["errore","error","scaduta","timeout",
                                              "unreachable","not found","fallito"]):
                        tag = "err"
                    elif any(x in ll for x in ["risposta","reply","bytes="]):
                        tag = "ok"
                    elif "ms" in ll:
                        tag = "data"
                    elif any(x in ll for x in ["server:","address:","name:"]):
                        tag = "info"
                    else:
                        tag = ""
                    Q.put((term, line, tag))
                p.wait()
            except Exception as ex:
                Q.put((term, f"X Errore: {ex}", "err"))
            finally:
                self.proc = None; self.running = False
                if done: self.root.after(0, lambda: done(term))
        threading.Thread(target=_t, daemon=True).start()

    def _ferma(self):
        self.running = False
        if self.proc:
            try: self.proc.terminate()
            except: pass
            self.proc = None
        self._st("Interrotto.", ORANGE)

    def _ferma_ping(self):
        """Interrompe il ping e azzera tutti i contatori e grafici."""
        self._ferma()
        if hasattr(self, 'ps'):
            for key, col in [("mn",GREEN),("av",CYAN),("mx",ORANGE),("lo",RED)]:
                if key in self.ps: self.ps[key].config(text="-", fg=col)
        self.ping_vals = []
        if "ping" in self.grafici:
            self.grafici["ping"].delete("all")
        if hasattr(self, 'ping_pie_canvas'):
            self._draw_ping_pie(0, 0)
        if hasattr(self, 'lbl_pie_ok'):
            self.lbl_pie_ok.config(text="OK: 0")
        if hasattr(self, 'lbl_pie_err'):
            self.lbl_pie_err.config(text="KO: 0")

    # ════ TAB 1 PING ══════════════════════════════════════════════
    def _tab_ping(self, f):
        left = self._panel(f, "PING", CYAN, w=300)
        right = tk.Frame(f, bg=BG); right.pack(side="left", fill="both", expand=True, padx=(0,4), pady=4)

        self._lbl(left, "Indirizzo IP / Hostname")
        self.p_ip = self._entry(left, "10.26.84.1")

        self._lbl(left, "Dimensione pacchetto (byte)")
        dim_frame = tk.Frame(left, bg=BG3, highlightbackground=CYAN, highlightthickness=1)
        dim_frame.pack(fill="x", pady=(0,4))
        self.p_dim = tk.OptionMenu(dim_frame, tk.StringVar(value="32"),
                                   "32", "64", "512", "1024",
                                   "1472 (MTU max)", "65500 (max framm.)")
        self.p_dim.config(bg=BG3, fg=GREEN, activebackground="#1a2a3a",
                          activeforeground=WHITE, font=FM, bd=0,
                          highlightthickness=0, relief="flat",
                          indicatoron=True, width=22)
        self.p_dim["menu"].config(bg=BG3, fg=GREEN, font=FM,
                                  activebackground="#1a2a3a", activeforeground=WHITE)
        self.p_dim_var = self.p_dim["textvariable"] = tk.StringVar(value="32")
        self.p_dim.pack(fill="x")
        self._tooltip(dim_frame,
            "DIMENSIONE PACCHETTO\n"
            "32 byte         → Standard Windows, uso normale\n"
            "64 byte         → Test base, overhead minimo\n"
            "512 byte        → Test intermedio\n"
            "1024 byte       → Simula traffico reale\n"
            "1472 (MTU max)  → MTU massimo Ethernet\n"
            "65500 (max fr.) → Stress test frammentazione")

        self._lbl(left, "TTL")
        self.p_ttl = self._entry(left, "128")
        self._tooltip(self.p_ttl,
            "TTL — Time To Live\n"
            "Numero massimo di router (hop) che il pacchetto\n"
            "può attraversare prima di essere scartato.\n"
            "128 = default Windows  |  64 = default Linux")

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=5)
        self._lbl(left, "Destinazioni rapide", MUTED)
        pg = tk.Frame(left, bg=BG2); pg.pack(fill="x")
        pg.columnconfigure(0, weight=1); pg.columnconfigure(1, weight=1)
        QUICK = [
            ("Gateway LAN",  "10.26.84.1"),
            ("Rete 28/38",   "10.28.38.1"),
            ("Google DNS",   "8.8.8.8"),
            ("Cloudflare",   "1.1.1.1"),
            ("Leonardo CC",  "leonardo.rete.arma.carabinieri.it"),
            ("Quad9",        "9.9.9.9"),
        ]
        for i,(nm,ip) in enumerate(QUICK):
            r,c = divmod(i,2)
            short = ip if len(ip)<=18 else ip[:15]+"…"
            b = tk.Button(pg, text=f"{nm}\n{short}",
                          command=lambda x=ip: (self.p_ip.delete(0,"end"),self.p_ip.insert(0,x)),
                          bg=BG3, fg=FG, font=("Consolas",9),
                          activebackground="#1a2a3a", activeforeground=WHITE,
                          bd=1, relief="groove", cursor="hand2", pady=3, width=14)
            b.bind("<Enter>", lambda e,bt=b: bt.config(bg="#1a2a3a", fg=PINK))
            b.bind("<Leave>", lambda e,bt=b: bt.config(bg=BG3, fg=FG))
            b.grid(row=r, column=c, padx=2, pady=2, sticky="ew")

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=5)
        self._btn_tip(left, "AVVIA PING INFINITO", self._ping_start, GREEN,
            "AVVIA PING INFINITO\n"
            "Invia pacchetti ICMP continui verso l'host scelto.\n"
            "Mostra RTT in ms per ogni risposta.\n"
            "Il grafico si aggiorna in tempo reale ogni pacchetto.")
        self._btn_tip(left, "🖧  PING MULTIPLO LAN", self._ping_multiplo_open, CYAN,
            "PING MULTIPLO LAN\n"
            "Apre una finestra con ping simultaneo verso\n"
            "4 gateway predefiniti della rete:\n"
            "  10.26.84.1   10.28.38.1\n"
            "  10.27.37.1   10.26.36.1\n"
            "LED colorato, RTT, grafico e log per ognuno.")
        self._btn_tip(left, "INTERROMPI", self._ferma_ping, RED,
            "INTERROMPI\nFerma il ping e azzera contatori e grafici.")
        self._btn_tip(left, "SALVA LOG", self._salva, YELLOW,
            "SALVA LOG\nEsporta tutti i risultati in un file .txt con timestamp.")

        # Audio checkbox — abilitato di default
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=4)
        self.ping_audio = tk.BooleanVar(value=True)
        ck = tk.Checkbutton(left, text="  🔊  Audio ping  (beep OK / alert KO)",
                            variable=self.ping_audio,
                            fg=CYAN, bg=BG2, activebackground=BG2,
                            selectcolor=BG3, font=FH, anchor="w", cursor="hand2")
        ck.pack(fill="x", padx=2, pady=(0,4))
        self._tooltip(ck,
            "AUDIO PING\n"
            "✔ Risposta OK  → beep acuto breve (880 Hz, 60 ms)\n"
            "✗ Timeout / KO → doppio tono alert discendente\n"
            "Utile per monitorare senza guardare lo schermo.\n"
            "Funziona su Windows (winsound), macOS, Linux.")

        # Grafico RTT + Torta ping
        gf = tk.Frame(right, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        gf.pack(fill="x", pady=(0,4))
        hdr_f = tk.Frame(gf, bg=BG2); hdr_f.pack(fill="x")
        tk.Label(hdr_f, text="GRAFICO RTT  (ms)",
                 fg=CYAN, bg=BG2, font=FH).pack(side="left", padx=8, pady=(4,2))
        for txt, col in [("< 50ms", GREEN), ("50-200ms", ORANGE), ("> 200ms / PERSO", RED)]:
            tk.Label(hdr_f, text="■", fg=col, bg=BG2, font=FM).pack(side="right", padx=2, pady=4)
            tk.Label(hdr_f, text=txt, fg=MUTED, bg=BG2, font=("Consolas",9)).pack(side="right", pady=4)

        graf_row = tk.Frame(gf, bg=BG2)
        graf_row.pack(fill="x", padx=4, pady=(0,4))

        RTT_W, RTT_H = 420, 120
        rtt_cvs = tk.Canvas(graf_row, bg="#04070a", width=RTT_W, height=RTT_H,
                             highlightthickness=0)
        rtt_cvs.pack(side="left", padx=(0,4))
        self.grafici["ping"] = rtt_cvs
        self._ping_rtt_size = (RTT_W, RTT_H)

        pie_frame = tk.Frame(graf_row, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        pie_frame.pack(side="left", fill="y")
        tk.Label(pie_frame, text="ESITO PING", fg=MUTED, bg=BG2,
                 font=("Consolas",9,"bold")).pack(pady=(4,0))
        self.ping_pie_canvas = tk.Canvas(pie_frame, width=140, height=90,
                                          bg="#04070a", highlightthickness=0)
        self.ping_pie_canvas.pack(padx=6, pady=(0,2))
        leg_f = tk.Frame(pie_frame, bg=BG2); leg_f.pack(pady=(0,2))
        tk.Label(leg_f, text="■ OK",    fg=GREEN, bg=BG2, font=("Consolas",9)).pack(side="left", padx=4)
        tk.Label(leg_f, text="■ PERSO", fg=RED,   bg=BG2, font=("Consolas",9)).pack(side="left", padx=4)
        lbl_pie_f = tk.Frame(pie_frame, bg=BG2); lbl_pie_f.pack(pady=(0,4))
        self.lbl_pie_ok  = tk.Label(lbl_pie_f, text="OK: 0", fg=GREEN, bg=BG2, font=("Consolas",9))
        self.lbl_pie_ok.pack(side="left", padx=3)
        self.lbl_pie_err = tk.Label(lbl_pie_f, text="KO: 0", fg=RED,   bg=BG2, font=("Consolas",9))
        self.lbl_pie_err.pack(side="left", padx=3)

        # Statistiche
        sf = tk.Frame(right, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        sf.pack(fill="x", pady=(0,4))
        self.ps = {}
        for nm,key,col in [("MINIMO ms","mn",GREEN),("MEDIO ms","av",CYAN),
                            ("MASSIMO ms","mx",ORANGE),("PACCHETTI PERSI","lo",RED)]:
            c2 = tk.Frame(sf, bg=BG2); c2.pack(side="left", fill="x", expand=True, padx=6, pady=6)
            lv = tk.Label(c2, text="-", fg=col, bg=BG2, font=("Consolas",18,"bold")); lv.pack()
            tk.Label(c2, text=nm, fg=MUTED, bg=BG2, font=("Consolas",9)).pack()
            self.ps[key] = lv

        tk.Label(right, text="OUTPUT PING", fg=CYAN, bg=BG, font=FHB).pack(anchor="w", padx=4)
        self.t_ping = self._term(right, 9)
        self._w(self.t_ping, "Ping INFINITO — premi AVVIA per iniziare.", "muted")


    def _ping_start(self):
        if self.running: messagebox.showwarning("Occupato","Premi INTERROMPI prima."); return
        ip = self.p_ip.get().strip()
        if not ip: messagebox.showerror("Errore","Inserisci IP."); return
        dim = self.p_dim_var.get().split()[0].replace("(","").replace(")","")
        ttl = self.p_ttl.get().strip() or "128"
        cmd = _ping_cmd(ip, size=int(dim), ttl=ttl, infinite=True)

        self.ping_vals = []; self._clr(self.t_ping)
        self._w(self.t_ping, f"Comando: {' '.join(cmd)}", "info")
        self._w(self.t_ping, "-"*55, "muted")
        self._st(f"Ping infinito -> {ip}", CYAN)
        self.running = True
        persi=[0]; ok_count=[0]; lista=[]

        def _t():
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, encoding=_encoding(), errors="replace",
                                     **_popen_flags())
                self.proc = p
                for line in p.stdout:
                    line = line.rstrip()
                    ll = line.lower()
                    v = self._parse_rtt(line)
                    if v is not None:
                        lista.append(v); self.ping_vals.append(v)
                        ok_count[0] += 1
                        tag = "ok" if v<50 else "warn" if v<200 else "err"
                        validi = [x for x in lista[-60:] if x is not None]
                        if validi:
                            mn_ = min(validi); mx_ = max(validi)
                            av_ = int(sum(validi)/len(validi))
                            d_  = persi[0]; o_ = ok_count[0]; p_ = persi[0]
                            v2  = self.ping_vals[-60:]
                            def _upd_ping(mn=mn_, mx=mx_, av=av_, d=d_, o=o_, pp=p_, vv=v2):
                                self.ps["mn"].config(text=str(mn))
                                self.ps["av"].config(text=str(av))
                                self.ps["mx"].config(text=str(mx))
                                self.ps["lo"].config(text=str(d))
                                self._plot_rtt(self.grafici["ping"], vv)
                                self._draw_ping_pie(o, pp)
                            self.root.after(0, _upd_ping)
                        if self.ping_audio.get():
                            self._beep("ok")
                    elif any(x in ll for x in ["scaduta","timeout","unreachable"]):
                        self.ping_vals.append(None); persi[0]+=1; tag="err"
                        d_ = persi[0]; o_ = ok_count[0]; v2 = self.ping_vals[-60:]
                        def _upd_loss(d=d_, o=o_, pp=d_, vv=v2):
                            self.ps["lo"].config(text=str(d))
                            self._plot_rtt(self.grafici["ping"], vv)
                            self._draw_ping_pie(o, pp)
                        self.root.after(0, _upd_loss)
                        if self.ping_audio.get():
                            self._beep("err")
                    else:
                        tag = "err" if "error" in ll or "errore" in ll else ""
                    if line: Q.put((self.t_ping, line, tag))
                p.wait()
            except Exception as ex:
                Q.put((self.t_ping, f"X {ex}", "err"))
            finally:
                self.proc=None; self.running=False
                Q.put((self.t_ping,"PING TERMINATO.","warn"))
                self.root.after(0, lambda: self._st("Pronto.",MUTED))

        threading.Thread(target=_t, daemon=True).start()


    def _draw_ping_pie(self, ok_count, err_count):
        """Disegna grafico a torta esito ping: verde=ok, rosso=perso."""
        import math as _m
        c = self.ping_pie_canvas
        c.delete("all")
        W, H = 130, 110
        cx, cy = 65, 52
        R = 44
        total = ok_count + err_count
        if total == 0:
            c.create_oval(cx-R, cy-R, cx+R, cy+R, fill="#1a1a1a", outline="#2a3a4a", width=2)
            c.create_text(cx, cy, text="—", fill=MUTED, font=("Consolas",14,"bold"))
            self.lbl_pie_ok.config(text="OK: 0")
            self.lbl_pie_err.config(text="KO: 0")
            return

        frac_ok  = ok_count  / total
        frac_err = err_count / total
        pct_ok   = int(frac_ok  * 100)
        pct_err  = int(frac_err * 100)

        # Sfondo cerchio
        c.create_oval(cx-R, cy-R, cx+R, cy+R, fill="#0a0a0a", outline="#2a3a4a", width=2)

        if err_count == 0:
            # Tutto verde
            c.create_oval(cx-R, cy-R, cx+R, cy+R, fill=GREEN, outline="#2a3a4a", width=2)
        elif ok_count == 0:
            # Tutto rosso
            c.create_oval(cx-R, cy-R, cx+R, cy+R, fill=RED, outline="#2a3a4a", width=2)
        else:
            extent_ok  = frac_ok  * 360
            extent_err = frac_err * 360
            # Fetta verde (ok)
            c.create_arc(cx-R, cy-R, cx+R, cy+R,
                         start=90, extent=-extent_ok,
                         style="pieslice", fill=GREEN, outline="#04070a", width=1)
            # Fetta rossa (err)
            c.create_arc(cx-R, cy-R, cx+R, cy+R,
                         start=90 - extent_ok, extent=-extent_err,
                         style="pieslice", fill=RED, outline="#04070a", width=1)

        # Cerchio interno (effetto ciambella)
        inner_r = R * 0.48
        c.create_oval(cx-inner_r, cy-inner_r, cx+inner_r, cy+inner_r,
                      fill="#04070a", outline="#1a2a3a", width=1)

        # Percentuale centrale
        main_pct = pct_ok if ok_count >= err_count else pct_err
        main_col = GREEN if ok_count >= err_count else RED
        c.create_text(cx, cy-4, text=f"{main_pct}%",
                      fill=main_col, font=("Consolas", 13, "bold"), anchor="center")
        c.create_text(cx, cy+10, text="OK" if ok_count >= err_count else "KO",
                      fill=main_col, font=("Consolas", 8), anchor="center")

        # Totale pacchetti sotto
        c.create_text(cx, cy + R + 14, text=f"Tot: {total}",
                      fill=MUTED, font=("Consolas", 9), anchor="center")

        # Aggiorna label
        self.lbl_pie_ok.config(text=f"OK: {ok_count}")
        self.lbl_pie_err.config(text=f"KO: {err_count}")

    # ════ PING BOMB ════════════════════════════════════════════════
    def _ping_bomb_open(self):
        """Apre finestra PING BOMB con sessioni multiple."""
        win = tk.Toplevel(self.root)
        win.title("💣  PING BOMB")
        win.configure(bg=BG)
        win.geometry("720x620")
        win.resizable(True, True)
        win.grab_set()

        # Header
        hf = tk.Frame(win, bg="#1a0005"); hf.pack(fill="x")
        tk.Label(hf, text="💣  PING BOMB",
                 font=("Segoe UI",18,"bold"), fg=RED, bg="#1a0005").pack(side="left", padx=12, pady=8)
        tk.Label(hf, text="⚠ Usare solo su reti di propria competenza",
                 font=("Segoe UI",9), fg=ORANGE, bg="#1a0005").pack(side="right", padx=12)
        tk.Frame(win, bg=RED, height=2).pack(fill="x")

        # Modalità
        mode_f = tk.Frame(win, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        mode_f.pack(fill="x", padx=8, pady=(8,0))
        tk.Label(mode_f, text="MODALITÀ:", fg=MUTED, bg=BG2, font=FH).pack(side="left", padx=8, pady=6)
        pb_mode = tk.StringVar(value="single")
        for val, lbl in [("single","Stesso IP — N sessioni"),("multi","IP diversi — lista")]:
            tk.Radiobutton(mode_f, text=lbl, variable=pb_mode, value=val,
                           fg=ORANGE, bg=BG2, activebackground=BG2,
                           selectcolor=BG3, font=FH, cursor="hand2").pack(side="left", padx=10)

        # Frame configurazione (cambia in base alla modalità)
        cfg_f = tk.Frame(win, bg=BG); cfg_f.pack(fill="x", padx=8, pady=4)

        # ── Pannello: stesso IP ──────────────────────────────────
        single_f = tk.Frame(cfg_f, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        single_f.pack(fill="x")
        tk.Label(single_f, text="Indirizzo IP / Hostname", fg=LABEL, bg=BG2, font=FH,
                 anchor="w").pack(fill="x", padx=8, pady=(6,2))
        pb_ip_s = tk.Entry(single_f, bg=BG3, fg=GREEN, insertbackground=GREEN,
                           font=FML, bd=0, highlightbackground=BORDER, highlightthickness=1)
        pb_ip_s.insert(0, self.p_ip.get() or "192.168.1.1")
        pb_ip_s.pack(fill="x", padx=8, pady=(0,6))

        tk.Label(single_f, text="Numero sessioni simultanee (1-20)",
                 fg=LABEL, bg=BG2, font=FH, anchor="w").pack(fill="x", padx=8, pady=(2,2))
        sess_f = tk.Frame(single_f, bg=BG2); sess_f.pack(fill="x", padx=8, pady=(0,6))
        pb_sess = tk.IntVar(value=5)
        pb_sess_lbl = tk.Label(sess_f, text="5", fg=ORANGE, bg=BG2,
                               font=("Consolas",20,"bold"), width=3)
        pb_sess_lbl.pack(side="left")
        sc = tk.Scale(sess_f, from_=1, to=20, orient="horizontal",
                      variable=pb_sess, bg=BG2, fg=ORANGE, troughcolor=BG3,
                      highlightthickness=0, sliderrelief="flat", length=300,
                      command=lambda v: pb_sess_lbl.config(text=str(int(float(v)))))
        sc.pack(side="left", padx=8)

        # ── Pannello: IP multipli ────────────────────────────────
        multi_f = tk.Frame(cfg_f, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(multi_f, text="Lista IP (uno per riga, max 20)",
                 fg=LABEL, bg=BG2, font=FH, anchor="w").pack(fill="x", padx=8, pady=(6,2))
        pb_ip_m = scrolledtext.ScrolledText(multi_f, bg=BG3, fg=GREEN,
                                             font=FML, height=5, bd=0,
                                             highlightbackground=BORDER, highlightthickness=1)
        pb_ip_m.insert("end", "192.168.1.1\n8.8.8.8\n1.1.1.1")
        pb_ip_m.pack(fill="x", padx=8, pady=(0,6))

        def switch_mode(*_):
            if pb_mode.get() == "single":
                multi_f.pack_forget()
                single_f.pack(fill="x")
            else:
                single_f.pack_forget()
                multi_f.pack(fill="x")
        pb_mode.trace_add("write", switch_mode)

        # Parametri comuni
        par_f = tk.Frame(win, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        par_f.pack(fill="x", padx=8, pady=(4,0))
        tk.Label(par_f, text="Dimensione pacchetto:",
                 fg=MUTED, bg=BG2, font=FM).grid(row=0, column=0, padx=8, pady=6, sticky="w")
        pb_dim = ttk.Combobox(par_f, values=["32","64","512","1024"], state="readonly", font=FM, width=8)
        pb_dim.current(0); pb_dim.grid(row=0, column=1, padx=4, pady=6, sticky="w")
        tk.Label(par_f, text="Intervallo (ms):",
                 fg=MUTED, bg=BG2, font=FM).grid(row=0, column=2, padx=8, pady=6, sticky="w")
        pb_int = ttk.Combobox(par_f, values=["10","50","100","500","1000"], state="readonly", font=FM, width=7)
        pb_int.current(2); pb_int.grid(row=0, column=3, padx=4, pady=6, sticky="w")

        # Output log
        out_f = tk.Frame(win, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        out_f.pack(fill="both", expand=True, padx=8, pady=(6,0))
        tk.Label(out_f, text="OUTPUT SESSIONI", fg=RED, bg=BG2, font=FH,
                 anchor="w").pack(fill="x", padx=8, pady=(4,2))
        pb_log = scrolledtext.ScrolledText(out_f, bg="#04070a", fg=FG,
                                            font=FM, state="disabled",
                                            highlightbackground=BORDER, highlightthickness=1)
        pb_log.tag_config("ok",   foreground=GREEN)
        pb_log.tag_config("err",  foreground=RED)
        pb_log.tag_config("warn", foreground=ORANGE)
        pb_log.tag_config("info", foreground=CYAN)
        pb_log.tag_config("sess", foreground=YELLOW)
        pb_log.pack(fill="both", expand=True, padx=6, pady=(0,6))

        # Contatori live
        cnt_f = tk.Frame(win, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        cnt_f.pack(fill="x", padx=8, pady=(4,0))
        pb_cnt = {}
        for nm,key,col in [("Sessioni attive","sess",ORANGE),("Totale inviati","sent",CYAN),
                            ("Risposte OK","ok",GREEN),("Timeout","to",RED)]:
            cx = tk.Frame(cnt_f, bg=BG2); cx.pack(side="left", fill="x", expand=True, padx=8, pady=5)
            lv = tk.Label(cx, text="0", fg=col, bg=BG2, font=("Consolas",16,"bold")); lv.pack()
            tk.Label(cx, text=nm, fg=MUTED, bg=BG2, font=FM).pack()
            pb_cnt[key] = lv

        # Stato e proc per PING BOMB
        pb_state = {"running": False, "procs": [], "sent": 0, "ok": 0, "to": 0}

        def pb_log_write(txt, tag=""):
            pb_log.config(state="normal")
            pb_log.insert("end", txt+"\n", tag if tag else ())
            pb_log.see("end"); pb_log.config(state="disabled")

        def pb_update_cnt():
            pb_cnt["sess"].config(text=str(len([p for p in pb_state["procs"] if p.poll() is None])))
            pb_cnt["sent"].config(text=str(pb_state["sent"]))
            pb_cnt["ok"].config(text=str(pb_state["ok"]))
            pb_cnt["to"].config(text=str(pb_state["to"]))

        def pb_session(idx, ip, dim, interval_ms):
            """Thread singola sessione ping."""
            cmd = _ping_cmd(ip, size=dim, timeout_ms=interval_ms, infinite=True)
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, encoding=_encoding(), errors="replace",
                                     **_popen_flags())
                pb_state["procs"].append(p)
                pb_log_write(f"[#{idx:02d}] Avviato → {ip}  dim={dim}b  int={interval_ms}ms", "info")
                for line in p.stdout:
                    if not pb_state["running"]: break
                    line = line.rstrip(); ll = line.lower()
                    if self._parse_rtt(line) is not None:
                        pb_state["sent"] += 1; pb_state["ok"] += 1; tag = "ok"
                    elif any(x in ll for x in ["scaduta","timeout","unreachable"]):
                        pb_state["sent"] += 1; pb_state["to"] += 1; tag = "err"
                    else:
                        tag = ""
                    if line and tag:
                        win.after(0, lambda l=f"[#{idx:02d}] {line}", t=tag: pb_log_write(l, t))
                    win.after(0, pb_update_cnt)
                p.terminate()
            except Exception as ex:
                win.after(0, lambda: pb_log_write(f"[#{idx:02d}] ERRORE: {ex}", "err"))

        def pb_start():
            if pb_state["running"]:
                pb_log_write("Già in esecuzione — premi INTERROMPI prima.", "warn"); return
            pb_state.update({"running": True, "procs": [], "sent": 0, "ok": 0, "to": 0})
            pb_log.config(state="normal"); pb_log.delete("1.0","end"); pb_log.config(state="disabled")

            dim = int(pb_dim.get().split()[0])
            interval_ms = int(pb_int.get())

            if pb_mode.get() == "single":
                ip = pb_ip_s.get().strip()
                if not ip:
                    pb_log_write("Inserisci un IP!", "err"); return
                n = pb_sess.get()
                if n > 15:
                    if not messagebox.askyesno("Attenzione",
                        f"Stai per avviare {n} sessioni simultanee verso {ip}.\n"
                        "Questo può sovraccaricare la rete.\nContinuare?"):
                        pb_state["running"] = False; return
                pb_log_write(f"💣 PING BOMB — {n} sessioni → {ip}", "warn")
                for i in range(1, n+1):
                    threading.Thread(target=pb_session, args=(i, ip, dim, interval_ms),
                                     daemon=True).start()
            else:
                raw = pb_ip_m.get("1.0","end").strip().splitlines()
                ips = [x.strip() for x in raw if x.strip()][:20]
                if not ips:
                    pb_log_write("Inserisci almeno un IP!", "err"); return
                pb_log_write(f"💣 PING BOMB — {len(ips)} IP distinti", "warn")
                for i, ip in enumerate(ips, 1):
                    threading.Thread(target=pb_session, args=(i, ip, dim, interval_ms),
                                     daemon=True).start()
            btn_start.config(state="disabled")
            btn_stop.config(state="normal")

        def pb_stop():
            pb_state["running"] = False
            for p in pb_state["procs"]:
                try: p.terminate()
                except: pass
            pb_state["procs"].clear()
            pb_log_write("⬛ INTERROTTO — tutte le sessioni fermate.", "warn")
            btn_start.config(state="normal")
            btn_stop.config(state="disabled")
            win.after(0, pb_update_cnt)

        win.protocol("WM_DELETE_WINDOW", lambda: (pb_stop(), win.destroy()))

        # Bottoni azione
        act_f = tk.Frame(win, bg=BG); act_f.pack(fill="x", padx=8, pady=6)
        btn_start = tk.Button(act_f, text="💣  AVVIA PING BOMB", command=pb_start,
                              bg="#330010", fg=RED, font=("Segoe UI",13,"bold"),
                              activebackground="#550020", activeforeground=WHITE,
                              bd=2, relief="groove", cursor="hand2", pady=8)
        btn_start.pack(side="left", fill="x", expand=True, padx=(0,4))
        btn_stop = tk.Button(act_f, text="⬛  INTERROMPI TUTTO", command=pb_stop,
                             bg=BG2, fg=ORANGE, font=("Segoe UI",13,"bold"),
                             activebackground="#162030", activeforeground=WHITE,
                             bd=2, relief="groove", cursor="hand2", pady=8,
                             state="disabled")
        btn_stop.pack(side="left", fill="x", expand=True, padx=(4,0))

    # ════ MONITORAGGIO HOST ════════════════════════════════════════
    def _tab_monitor(self, f):
        """Tab monitoraggio continuo host — avvisa se va offline."""
        left = self._panel(f, "MONITORAGGIO HOST", YELLOW, w=310)
        right = tk.Frame(f, bg=BG); right.pack(side="left", fill="both", expand=True, padx=(0,4), pady=4)

        self._lbl(left, "Host da monitorare")
        tk.Label(left, text="(uno per riga, max 10)", fg=MUTED, bg=BG2,
                 font=("Consolas",9), anchor="w").pack(fill="x", padx=2)
        self.mon_hosts_box = scrolledtext.ScrolledText(
            left, bg=BG3, fg=GREEN, font=FML, height=6,
            highlightbackground=BORDER, highlightthickness=1, bd=0)
        self.mon_hosts_box.insert("end", "192.168.1.1\n8.8.8.8\n1.1.1.1")
        self.mon_hosts_box.pack(fill="x", padx=2, pady=(0,6))

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=4)
        self._lbl(left, "Intervallo controllo")
        self.mon_interval = self._combo(left, ["5 secondi","10 secondi","30 secondi","60 secondi"], 1)

        self._lbl(left, "Avviso se offline per più di")
        self.mon_soglia = self._combo(left, ["1 controllo","2 controlli","3 controlli","5 controlli"], 0)

        self.mon_suono = tk.BooleanVar(value=True)
        tk.Checkbutton(left, text="  Suono avviso (beep)", variable=self.mon_suono,
                       fg=YELLOW, bg=BG2, activebackground=BG2, selectcolor=BG3,
                       font=FH, anchor="w").pack(fill="x", pady=2)
        self.mon_popup = tk.BooleanVar(value=True)
        tk.Checkbutton(left, text="  Popup finestra avviso", variable=self.mon_popup,
                       fg=YELLOW, bg=BG2, activebackground=BG2, selectcolor=BG3,
                       font=FH, anchor="w").pack(fill="x", pady=2)

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=6)
        self._btn_tip(left, "▶  AVVIA MONITORAGGIO", self._mon_start, GREEN,
            "AVVIA MONITORAGGIO\n"
            "Controlla periodicamente tutti gli host elencati.\n"
            "Mostra lo stato in tempo reale (ONLINE/OFFLINE).\n"
            "Avvisa immediatamente se un host va offline.")
        self._btn_tip(left, "⬛  FERMA", self._mon_stop, RED,
            "FERMA\nInterrompe il monitoraggio di tutti gli host.")
        self._btn_tip(left, "SALVA LOG", self._salva, YELLOW,
            "SALVA LOG\nEsporta il log eventi in un file .txt.")

        # Tabella stati host
        tk.Label(right, text="STATO HOST IN TEMPO REALE",
                 fg=YELLOW, bg=BG, font=FHB).pack(anchor="w", padx=4)

        tbl_f = tk.Frame(right, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        tbl_f.pack(fill="x", padx=4, pady=(0,4))

        # Header tabella
        hdr = tk.Frame(tbl_f, bg="#0a1520"); hdr.pack(fill="x")
        for txt, w in [("HOST / IP", 22), ("STATO", 12), ("LATENZA", 10),
                       ("ULTIMO OK", 14), ("OFFLINE DA", 12)]:
            tk.Label(hdr, text=txt, fg=CYAN, bg="#0a1520",
                     font=("Consolas",10,"bold"), width=w, anchor="w").pack(side="left", padx=4, pady=3)

        self.mon_rows_f = tk.Frame(tbl_f, bg=BG2); self.mon_rows_f.pack(fill="x")
        self.mon_rows   = {}  # ip -> dict di label

        # Grafico uptime
        gf = tk.Frame(right, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        gf.pack(fill="x", padx=4, pady=(0,4))
        tk.Label(gf, text="LATENZA HOST (ms)", fg=YELLOW, bg=BG2, font=FH).pack(
            anchor="w", padx=8, pady=(4,2))
        self.grafici["mon"] = self._cvs(gf, 100)

        tk.Label(right, text="LOG EVENTI", fg=YELLOW, bg=BG, font=FHB).pack(anchor="w", padx=4)
        self.t_mon = self._term(right, 8)
        self._w(self.t_mon, "Inserisci gli host da monitorare e premi AVVIA.", "muted")

        self.mon_running = False
        self.mon_rtt_vals = {}   # ip -> lista rtt

    def _mon_start(self):
        if self.mon_running:
            messagebox.showwarning("Attivo","Premi FERMA prima."); return
        raw = self.mon_hosts_box.get("1.0","end").strip().splitlines()
        hosts = [h.strip() for h in raw if h.strip()][:10]
        if not hosts:
            messagebox.showerror("Errore","Inserisci almeno un host."); return

        interval = int(self.mon_interval.get().split()[0])
        soglia   = int(self.mon_soglia.get().split()[0])

        # Costruisci righe tabella
        for w in self.mon_rows_f.winfo_children(): w.destroy()
        self.mon_rows.clear(); self.mon_rtt_vals.clear()
        colori = [CYAN, GREEN, YELLOW, ORANGE, PINK, RED, WHITE, MUTED, CYAN, GREEN]
        for i, h in enumerate(hosts):
            row = tk.Frame(self.mon_rows_f, bg=BG2); row.pack(fill="x")
            col = colori[i % len(colori)]
            lbl_h    = tk.Label(row, text=h, fg=col, bg=BG2, font=FM, width=22, anchor="w")
            lbl_stat = tk.Label(row, text="—", fg=MUTED, bg=BG2, font=("Consolas",10,"bold"), width=12, anchor="w")
            lbl_rtt  = tk.Label(row, text="—", fg=MUTED, bg=BG2, font=FM, width=10, anchor="w")
            lbl_ok   = tk.Label(row, text="—", fg=MUTED, bg=BG2, font=FM, width=14, anchor="w")
            lbl_off  = tk.Label(row, text="—", fg=MUTED, bg=BG2, font=FM, width=12, anchor="w")
            for lbl in [lbl_h, lbl_stat, lbl_rtt, lbl_ok, lbl_off]:
                lbl.pack(side="left", padx=4, pady=2)
            self.mon_rows[h] = {
                "stat": lbl_stat, "rtt": lbl_rtt, "ok": lbl_ok, "off": lbl_off,
                "offline_count": 0, "last_ok": "—", "offline_since": None
            }
            self.mon_rtt_vals[h] = []

        self.mon_running = True
        self._clr(self.t_mon)
        self._w(self.t_mon, f"Monitoraggio avviato — {len(hosts)} host — ogni {interval}s", "info")
        self._w(self.t_mon, "-"*55, "muted")
        self._st(f"Monitoraggio {len(hosts)} host attivo", YELLOW)

        def _loop():
            import time as _time
            all_rtt = []
            while self.mon_running:
                for h in hosts:
                    if not self.mon_running: break
                    rtt = self._mon_ping(h)
                    row = self.mon_rows[h]
                    now = datetime.datetime.now().strftime("%H:%M:%S")

                    if rtt is not None:
                        row["offline_count"] = 0
                        row["last_ok"] = now
                        row["offline_since"] = None
                        self.mon_rtt_vals[h].append(rtt)
                        if len(self.mon_rtt_vals[h]) > 60:
                            self.mon_rtt_vals[h] = self.mon_rtt_vals[h][-60:]
                        all_rtt.append(rtt)
                        tag = "ok" if rtt < 50 else "warn" if rtt < 200 else "warn"
                        self.root.after(0, lambda r=row, v=rtt, t=now: (
                            r["stat"].config(text="● ONLINE", fg=GREEN),
                            r["rtt"].config(text=f"{v} ms", fg=GREEN if v<50 else ORANGE),
                            r["ok"].config(text=t, fg=MUTED),
                            r["off"].config(text="—", fg=MUTED)
                        ))
                    else:
                        row["offline_count"] += 1
                        if row["offline_since"] is None:
                            row["offline_since"] = now
                        cnt = row["offline_count"]
                        self.root.after(0, lambda r=row, c=cnt, t=row["offline_since"]: (
                            r["stat"].config(text="✖ OFFLINE", fg=RED),
                            r["rtt"].config(text="—", fg=RED),
                            r["off"].config(text=t, fg=RED)
                        ))
                        if cnt == soglia:
                            msg = f"⚠ HOST OFFLINE: {h}  (alle {row['offline_since']})"
                            Q.put((self.t_mon, msg, "err"))
                            if self.mon_suono.get():
                                self.root.after(0, lambda: self.root.bell())
                            if self.mon_popup.get():
                                self.root.after(0, lambda hh=h: messagebox.showwarning(
                                    "Host Offline!", f"⚠ {hh} non risponde!\nControllare la connessione."))

                # Aggiorna grafico con media RTT di tutti gli host
                if all_rtt:
                    flat = []
                    for v in self.mon_rtt_vals.values():
                        flat.extend(v[-10:])
                    if flat:
                        avg_series = []
                        chunk = max(1, len(flat)//20)
                        for i in range(0, len(flat), chunk):
                            avg_series.append(sum(flat[i:i+chunk])/len(flat[i:i+chunk]))
                        self.root.after(0, lambda v=avg_series: self._plot_rtt(self.grafici["mon"], v))

                _time.sleep(interval)

        threading.Thread(target=_loop, daemon=True).start()

    def _mon_ping(self, host) -> int | None:
        """Ping singolo ICMP reale, ritorna RTT in ms o None se offline."""
        try:
            cmd = _ping_cmd(host, count=1, timeout_ms=2000)
            r = subprocess.run(
                cmd,
                capture_output=True, text=True, encoding=_encoding(),
                errors="replace", timeout=5,
                **_popen_flags())
            v = self._parse_rtt(r.stdout)
            if v is not None:
                return v
        except Exception:
            pass
        return None

    def _mon_stop(self):
        self.mon_running = False
        self._st("Monitoraggio fermato.", MUTED)
        if hasattr(self, "t_mon"):
            self._w(self.t_mon, "Monitoraggio interrotto.", "warn")


    def _tab_tracert(self, f):
        left = self._panel(f, "TRACEROUTE", YELLOW, w=280)
        right = tk.Frame(f, bg=BG); right.pack(side="left", fill="both", expand=True, padx=(0,4), pady=4)

        self._lbl(left, "Destinazione")
        self.tr_ip = self._entry(left, "10.26.84.1")
        self._lbl(left, "Max hop")
        self.tr_hops = self._combo(left,["15","20","30"],1)
        self.v_trdns = tk.BooleanVar(value=False)
        self._chk(left,"  Risolvi DNS (piu lento)",self.v_trdns)
        tk.Frame(left,bg=BORDER,height=1).pack(fill="x",pady=5)
        self._btn_tip(left,"AVVIA TRACEROUTE",self._tracert_start,YELLOW,
            "AVVIA TRACEROUTE\n"
            "Mappa ogni router (hop) tra te e la destinazione.\n"
            "Per ogni hop mostra: IP, latenza (3 misurazioni).\n"
            "Utile per: trovare dove si perdono i pacchetti,\n"
            "individuare colli di bottiglia nella rete.")
        self._btn_tip(left,"INTERROMPI",self._ferma,RED,
            "INTERROMPI\nFerma il traceroute in corso.")
        self._btn_tip(left,"SALVA LOG",self._salva,YELLOW,
            "SALVA LOG\nEsporta il risultato completo in un file .txt.")

        gf = tk.Frame(right,bg=BG2,highlightbackground=BORDER,highlightthickness=1)
        gf.pack(fill="x",pady=(4,4))
        tk.Label(gf,text="LATENZA PER HOP (ms)",fg=YELLOW,bg=BG2,font=FH).pack(anchor="w",padx=8,pady=(4,2))
        self.grafici["tr"] = self._cvs(gf,110)
        tk.Label(right,text="OUTPUT TRACEROUTE",fg=YELLOW,bg=BG,font=FHB).pack(anchor="w",padx=4)
        self.t_tr = self._term(right, 14)
        self._w(self.t_tr,"Mostra ogni router attraversato e la latenza reale.","muted")

    def _tracert_start(self):
        if self.running: messagebox.showwarning("Occupato","Premi INTERROMPI prima."); return
        ip = self.tr_ip.get().strip()
        if not ip: messagebox.showerror("Errore","Inserisci destinazione."); return
        dns = not self.v_trdns.get()
        cmd = _tracert_cmd(ip, max_hops=self.tr_hops.get(), no_dns=dns)
        self._clr(self.t_tr); self.running=True
        hop_rtt=[]
        def _t():
            try:
                p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                   text=True,encoding=_encoding(),errors="replace",
                                   **_popen_flags())
                self.proc=p
                for line in p.stdout:
                    line=line.rstrip(); ll=line.lower()
                    tag=""
                    if "ms" in ll:
                        nums=re.findall(r"(\d+)\s*ms",ll)
                        if nums:
                            hop_rtt.append(int(nums[0]))
                            self.root.after(0,lambda v=hop_rtt[:]:self._plot_rtt(self.grafici["tr"],v))
                        tag="data"
                    elif "*" in line: tag="warn"
                    elif "errore" in ll or "error" in ll: tag="err"
                    if line: Q.put((self.t_tr,line,tag))
                p.wait()
            except Exception as ex: Q.put((self.t_tr,f"X {ex}","err"))
            finally:
                self.proc=None; self.running=False
                Q.put((self.t_tr,"Traceroute completato.","ok"))
                self.root.after(0,lambda:self._st("Pronto.",MUTED))
        Q.put((self.t_tr,f"Comando: {' '.join(cmd)}","info"))
        Q.put((self.t_tr,"-"*55,"muted"))
        self._st(f"Traceroute -> {ip}",YELLOW)
        threading.Thread(target=_t,daemon=True).start()

    # ════ TAB 💣 PING BOMB (tab embed) ════════════════════════════
    def _tab_pingbomb_tab(self, f):
        """Versione tab della finestra PING BOMB."""
        self._ping_bomb_open_in(f)

    def _ping_bomb_open_in(self, parent):
        """Costruisce l'UI PING BOMB dentro il frame del tab."""
        # Stesso contenuto di _ping_bomb_open ma in parent invece di Toplevel
        win = parent   # riusa lo stesso codice, win = frame tab

        hf = tk.Frame(win, bg="#1a0005"); hf.pack(fill="x")
        tk.Label(hf, text="💣  PING BOMB",
                 font=("Segoe UI",16,"bold"), fg=RED, bg="#1a0005").pack(side="left", padx=12, pady=6)
        tk.Label(hf, text="⚠ Usare solo su reti di propria competenza",
                 font=("Segoe UI",9), fg=ORANGE, bg="#1a0005").pack(side="right", padx=12)
        tk.Frame(win, bg=RED, height=2).pack(fill="x")

        body = tk.Frame(win, bg=BG); body.pack(fill="both", expand=True)
        left = self._panel(body, "CONFIGURAZIONE", ORANGE, w=320)
        right = tk.Frame(body, bg=BG); right.pack(side="left", fill="both", expand=True, padx=(0,4), pady=4)

        # Modalità
        tk.Label(left, text="MODALITÀ", fg=MUTED, bg=BG2, font=FH, anchor="w").pack(fill="x", padx=6, pady=(4,2))
        pb_mode = tk.StringVar(value="single")
        mf = tk.Frame(left, bg=BG2); mf.pack(fill="x", padx=4, pady=(0,6))
        for val, lbl in [("single","Stesso IP — N sessioni"),("multi","IP diversi — lista")]:
            tk.Radiobutton(mf, text=lbl, variable=pb_mode, value=val,
                           fg=ORANGE, bg=BG2, activebackground=BG2,
                           selectcolor=BG3, font=FM, cursor="hand2",
                           anchor="w").pack(fill="x", pady=1)

        # Pannello stesso IP
        self._lbl(left, "Indirizzo target")
        pb_ip_s = self._entry(left, self.p_ip.get() or "192.168.1.1")

        tk.Label(left, text="Sessioni simultanee (1 – 20)",
                 fg=LABEL, bg=BG2, font=FH, anchor="w").pack(fill="x", padx=4, pady=(4,2))
        sf2 = tk.Frame(left, bg=BG2); sf2.pack(fill="x", padx=4, pady=(0,6))
        pb_sess = tk.IntVar(value=5)
        pb_sess_lbl = tk.Label(sf2, text="5", fg=ORANGE, bg=BG2,
                               font=("Consolas",18,"bold"), width=3)
        pb_sess_lbl.pack(side="left")
        tk.Scale(sf2, from_=1, to=20, orient="horizontal", variable=pb_sess,
                 bg=BG2, fg=ORANGE, troughcolor=BG3, highlightthickness=0,
                 sliderrelief="flat", length=200,
                 command=lambda v: pb_sess_lbl.config(text=str(int(float(v))))).pack(side="left", padx=6)

        # Pannello IP multipli (nascosto all'inizio)
        multi_outer = tk.Frame(left, bg=BG2); 
        tk.Label(multi_outer, text="Lista IP (uno per riga, max 20)",
                 fg=LABEL, bg=BG2, font=FH, anchor="w").pack(fill="x", padx=4, pady=(4,2))
        pb_ip_m = scrolledtext.ScrolledText(multi_outer, bg=BG3, fg=GREEN,
                                             font=FM, height=5, bd=0,
                                             highlightbackground=BORDER, highlightthickness=1)
        pb_ip_m.insert("end", "192.168.1.1\n8.8.8.8\n1.1.1.1")
        pb_ip_m.pack(fill="x", padx=4, pady=(0,6))

        def switch_mode(*_):
            if pb_mode.get() == "single":
                multi_outer.pack_forget()
                pb_ip_s.pack(fill="x", padx=4, pady=(0,4))  # rimostra
            else:
                try: pb_ip_s.pack_forget()
                except: pass
                multi_outer.pack(fill="x")
        pb_mode.trace_add("write", switch_mode)

        # Parametri
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=4)
        self._lbl(left, "Parametri pacchetto")
        pf = tk.Frame(left, bg=BG2); pf.pack(fill="x", padx=4, pady=(0,4))
        tk.Label(pf, text="Dim:", fg=MUTED, bg=BG2, font=FM).pack(side="left")
        pb_dim = ttk.Combobox(pf, values=["32","64","512","1024"], state="readonly", font=FM, width=6)
        pb_dim.current(0); pb_dim.pack(side="left", padx=(2,10))
        tk.Label(pf, text="Int.(ms):", fg=MUTED, bg=BG2, font=FM).pack(side="left")
        pb_int = ttk.Combobox(pf, values=["10","50","100","500","1000"], state="readonly", font=FM, width=6)
        pb_int.current(2); pb_int.pack(side="left", padx=2)

        # Contatori
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=4)
        cnt_f = tk.Frame(left, bg=BG2); cnt_f.pack(fill="x")
        pb_cnt = {}
        for nm, key, col in [("Sessioni","sess",ORANGE),("Inviati","sent",CYAN),
                              ("OK","ok",GREEN),("Timeout","to",RED)]:
            cx = tk.Frame(cnt_f, bg=BG2); cx.pack(side="left", fill="x", expand=True, pady=4)
            lv = tk.Label(cx, text="0", fg=col, bg=BG2, font=("Consolas",14,"bold")); lv.pack()
            tk.Label(cx, text=nm, fg=MUTED, bg=BG2, font=("Consolas",9)).pack()
            pb_cnt[key] = lv

        # Bottoni
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=4)
        pb_state = {"running": False, "procs": [], "sent": 0, "ok": 0, "to": 0}

        # Output log
        tk.Label(right, text="OUTPUT SESSIONI", fg=RED, bg=BG, font=FHB).pack(anchor="w", padx=4)
        pb_log = scrolledtext.ScrolledText(right, bg="#04070a", fg=FG, font=FM,
                                            state="disabled",
                                            highlightbackground=BORDER, highlightthickness=1)
        pb_log.tag_config("ok",   foreground=GREEN)
        pb_log.tag_config("err",  foreground=RED)
        pb_log.tag_config("warn", foreground=ORANGE)
        pb_log.tag_config("info", foreground=CYAN)
        pb_log.pack(fill="both", expand=True, padx=4, pady=(0,4))

        def pb_log_write(txt, tag=""):
            pb_log.config(state="normal")
            pb_log.insert("end", txt+"\n", tag if tag else ())
            pb_log.see("end"); pb_log.config(state="disabled")

        def pb_update_cnt():
            alive = len([p for p in pb_state["procs"] if p.poll() is None])
            pb_cnt["sess"].config(text=str(alive))
            pb_cnt["sent"].config(text=str(pb_state["sent"]))
            pb_cnt["ok"].config(text=str(pb_state["ok"]))
            pb_cnt["to"].config(text=str(pb_state["to"]))

        def pb_session(idx, ip, dim, interval_ms):
            cmd = _ping_cmd(ip, size=dim, timeout_ms=interval_ms, infinite=True)
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, encoding=_encoding(), errors="replace",
                                     **_popen_flags())
                pb_state["procs"].append(p)
                self.root.after(0, lambda: pb_log_write(f"[#{idx:02d}] → {ip}  dim={dim}b", "info"))
                for line in p.stdout:
                    if not pb_state["running"]: break
                    line = line.rstrip(); ll = line.lower()
                    if self._parse_rtt(line) is not None:
                        pb_state["sent"] += 1; pb_state["ok"] += 1; tag = "ok"
                    elif any(x in ll for x in ["scaduta","timeout","unreachable"]):
                        pb_state["sent"] += 1; pb_state["to"] += 1; tag = "err"
                    else:
                        tag = ""
                    if line and tag:
                        self.root.after(0, lambda l=f"[#{idx:02d}] {line}", t=tag: pb_log_write(l, t))
                    self.root.after(0, pb_update_cnt)
                p.terminate()
            except Exception as ex:
                self.root.after(0, lambda: pb_log_write(f"[#{idx:02d}] ERRORE: {ex}", "err"))

        def pb_start():
            if pb_state["running"]:
                pb_log_write("Già attivo — premi INTERROMPI prima.", "warn"); return
            pb_state.update({"running": True, "procs": [], "sent": 0, "ok": 0, "to": 0})
            pb_log.config(state="normal"); pb_log.delete("1.0","end"); pb_log.config(state="disabled")
            dim = int(pb_dim.get().split()[0])
            interval_ms = int(pb_int.get())
            if pb_mode.get() == "single":
                ip = pb_ip_s.get().strip()
                if not ip: pb_log_write("Inserisci un IP!", "err"); return
                n = pb_sess.get()
                if n > 15:
                    if not messagebox.askyesno("Attenzione",
                        f"Avviare {n} sessioni verso {ip}?\nPuò sovraccaricare la rete."):
                        pb_state["running"] = False; return
                pb_log_write(f"💣 PING BOMB — {n} sessioni → {ip}", "warn")
                for i in range(1, n+1):
                    threading.Thread(target=pb_session, args=(i, ip, dim, interval_ms), daemon=True).start()
            else:
                raw = pb_ip_m.get("1.0","end").strip().splitlines()
                ips = [x.strip() for x in raw if x.strip()][:20]
                if not ips: pb_log_write("Inserisci almeno un IP!", "err"); return
                pb_log_write(f"💣 PING BOMB — {len(ips)} IP distinti", "warn")
                for i, ip in enumerate(ips, 1):
                    threading.Thread(target=pb_session, args=(i, ip, dim, interval_ms), daemon=True).start()
            btn_start.config(state="disabled"); btn_stop.config(state="normal")

        def pb_stop():
            pb_state["running"] = False
            for p in pb_state["procs"]:
                try: p.terminate()
                except: pass
            pb_state["procs"].clear()
            pb_log_write("⬛ INTERROTTO.", "warn")
            btn_start.config(state="normal"); btn_stop.config(state="disabled")
            self.root.after(0, pb_update_cnt)

        btn_f = tk.Frame(left, bg=BG2); btn_f.pack(fill="x", pady=4)
        btn_start = tk.Button(btn_f, text="💣 AVVIA", command=pb_start,
                              bg="#330010", fg=RED, font=FB,
                              activebackground="#550020", activeforeground=WHITE,
                              bd=2, relief="groove", cursor="hand2", pady=7)
        btn_start.pack(side="left", fill="x", expand=True, padx=(0,3))
        btn_stop = tk.Button(btn_f, text="⬛ STOP", command=pb_stop,
                             bg=BG2, fg=ORANGE, font=FB,
                             activebackground="#162030", activeforeground=WHITE,
                             bd=2, relief="groove", cursor="hand2", pady=7,
                             state="disabled")
        btn_stop.pack(side="left", fill="x", expand=True, padx=(3,0))

    # ════ TAB 4 DOWNLOAD ══════════════════════════════════════════
    def _tab_download(self, f):
        left=self._panel(f,"STRESS DOWNLOAD",RED,w=320)
        right=tk.Frame(f,bg=BG); right.pack(side="left",fill="both",expand=True,padx=(0,4),pady=4)

        self._lbl(left,"File sorgente")
        self.dl_v=tk.StringVar(value=DL_FILES[0][0])
        for nm,_ in DL_FILES:
            tk.Radiobutton(left,text=nm,variable=self.dl_v,value=nm,fg=FG,bg=BG2,
                           activebackground=BG2,selectcolor=BG3,font=FM,
                           cursor="hand2",anchor="w").pack(fill="x",pady=1)
        tk.Frame(left,bg=BORDER,height=1).pack(fill="x",pady=5)
        self._lbl(left,"Download simultanei (saturazione banda)")
        nbf=tk.Frame(left,bg=BG2); nbf.pack(fill="x",pady=(0,2))
        self.dl_n=tk.IntVar(value=5)
        row1 = tk.Frame(left, bg=BG2); row1.pack(fill="x", pady=(0,2))
        row2 = tk.Frame(left, bg=BG2); row2.pack(fill="x", pady=(0,5))
        for n,row in [(5,row1),(10,row1),(15,row1),(20,row1),
                      (25,row2),(30,row2),(40,row2),(50,row2)]:
            col = ORANGE if n <= 20 else RED
            b = tk.Radiobutton(row,text=str(n),variable=self.dl_n,value=n,
                           fg=col,bg=BG2,activebackground=BG2,selectcolor=BG3,
                           font=("Consolas",13,"bold"),cursor="hand2")
            b.pack(side="left",padx=5)
        # Avviso per numeri alti
        self.dl_warn_lbl = tk.Label(left,
            text="⚠ 30+ richiede RAM e CPU adeguate",
            fg=ORANGE, bg=BG2, font=("Consolas",9), anchor="w")
        def _aggiorna_warn(*_):
            n = self.dl_n.get()
            if n >= 30:
                self.dl_warn_lbl.config(
                    text=f"⚠ {n} download: rete molto stressata! Pronto.", fg=RED)
            elif n >= 20:
                self.dl_warn_lbl.config(
                    text=f"⚠ {n} download: banda quasi satura.", fg=ORANGE)
            else:
                self.dl_warn_lbl.config(
                    text=f"✓ {n} download: configurazione standard.", fg=GREEN)
        self.dl_n.trace_add("write", _aggiorna_warn)
        self.dl_warn_lbl.pack(fill="x", padx=4, pady=(0,4))

        gb=tk.Button(left,text="AVVIA STRESS DOWNLOAD",command=self._dl_start,
                     bg=DKRED,fg=WHITE,font=("Segoe UI",14,"bold"),
                     activebackground="#550f00",activeforeground=WHITE,
                     bd=2,relief="groove",cursor="hand2",
                     highlightbackground=RED,highlightthickness=2,pady=10)
        gb.pack(fill="x",pady=(4,2))
        gb.bind("<Enter>",lambda e: gb.config(bg="#550f00"))
        gb.bind("<Leave>",lambda e: gb.config(bg=DKRED))
        self._tooltip(gb,
            "AVVIA STRESS DOWNLOAD\n"
            "Scarica N copie simultanee del file selezionato.\n"
            "Satura la banda disponibile per testare la stabilità\n"
            "della connessione sotto carico massimo.\n"
            "I file vengono salvati sul Desktop in una cartella\n"
            "chiamata 'CARTELLA TEST DA CANCELLARE'.\n"
            "⚠ Cancella i file al termine del test!")
        self._btn_tip(left,"INTERROMPI TUTTI",self._dl_ferma,RED,
            "INTERROMPI TUTTI\nFerma tutti i download in corso.\nI file parziali rimangono sul disco.")
        self._btn_tip(left,"SALVA LOG",self._salva,YELLOW,
            "SALVA LOG\nEsporta i risultati dello stress test in .txt.")

        # ── Pannello destro con GRID — tachigrafo sempre visibile in alto ──
        right.grid_rowconfigure(0, weight=0)   # tachigrafo: dimensione fissa
        right.grid_rowconfigure(1, weight=0)   # label progressi: fissa
        right.grid_rowconfigure(2, weight=1)   # barre: si espandono
        right.grid_rowconfigure(3, weight=0)   # log: fissa
        right.grid_columnconfigure(0, weight=1)

        # Riga 0: Tachigrafo — SEMPRE in cima
        tach_row = tk.Frame(right, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        tach_row.grid(row=0, column=0, sticky="ew", padx=4, pady=(4,2))

        sf_left = tk.Frame(tach_row, bg=BG2)
        sf_left.pack(side="left", fill="y", padx=12, pady=8)
        tk.Label(sf_left, text="VELOCITÀ TOTALE", fg=MUTED, bg=BG2, font=FM).pack(anchor="w")
        self.dl_spd_lbl = tk.Label(sf_left, text="0.0  MB/s", fg=RED, bg=BG2,
                                    font=("Consolas",26,"bold"))
        self.dl_spd_lbl.pack(anchor="w")
        tk.Label(sf_left, text="TOTALE SCARICATO", fg=MUTED, bg=BG2, font=FM).pack(anchor="w", pady=(10,0))
        self.dl_tot_lbl = tk.Label(sf_left, text="0  MB", fg=ORANGE, bg=BG2,
                                    font=("Consolas",20,"bold"))
        self.dl_tot_lbl.pack(anchor="w")

        tk.Frame(tach_row, bg=BORDER, width=1).pack(side="left", fill="y", pady=6)
        self.dl_tach = tk.Canvas(tach_row, width=300, height=160,
                                  bg="#04070a", highlightthickness=0)
        self.dl_tach.pack(side="left", padx=8, pady=6)

        # Riga 1: label PROGRESSI
        tk.Label(right, text="PROGRESSI DOWNLOAD", fg=RED, bg=BG,
                 font=FHB).grid(row=1, column=0, sticky="w", padx=4)

        # Riga 2: barre scrollabili
        dl_bf_outer = tk.Frame(right, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        dl_bf_outer.grid(row=2, column=0, sticky="nsew", padx=4, pady=(0,2))
        dl_canvas = tk.Canvas(dl_bf_outer, bg=BG, height=90, highlightthickness=0)
        dl_scroll = ttk.Scrollbar(dl_bf_outer, orient="vertical", command=dl_canvas.yview)
        dl_scroll.pack(side="right", fill="y")
        dl_canvas.pack(side="left", fill="both", expand=True)
        dl_canvas.configure(yscrollcommand=dl_scroll.set)
        self.dl_bf = tk.Frame(dl_canvas, bg=BG)
        dl_canvas.create_window((0,0), window=self.dl_bf, anchor="nw")
        def _on_dlframe_configure(e):
            dl_canvas.configure(scrollregion=dl_canvas.bbox("all"))
        self.dl_bf.bind("<Configure>", _on_dlframe_configure)

        # Riga 3: log (wrapper per compatibilità grid+pack)
        log_wrap = tk.Frame(right, bg=BG)
        log_wrap.grid(row=3, column=0, sticky="ew", padx=4, pady=(0,4))
        self.t_dl = scrolledtext.ScrolledText(log_wrap, bg="#04070a", fg=FG,
                                               insertbackground=GREEN, font=FML,
                                               bd=0, relief="flat",
                                               highlightbackground=BORDER, highlightthickness=1,
                                               wrap="word", height=4, state="disabled")
        self.t_dl.tag_config("ok",   foreground=GREEN)
        self.t_dl.tag_config("err",  foreground=RED)
        self.t_dl.tag_config("warn", foreground=ORANGE)
        self.t_dl.tag_config("info", foreground=CYAN)
        self.t_dl.tag_config("data", foreground=YELLOW)
        self.t_dl.tag_config("muted",foreground=MUTED)
        self.t_dl.pack(fill="x")
        self._w(self.t_dl, "⚠  I file di test vengono CANCELLATI automaticamente al termine.", "warn")
        self.dl_bw={}; self.dl_bf2={}; self.dl_bl={}

    def _dl_start(self):
        if self.running: messagebox.showwarning("Occupato","Premi INTERROMPI prima."); return
        nm=self.dl_v.get(); url=dict(DL_FILES)[nm]
        n=self.dl_n.get(); ext=url.split(".")[-1]
        desk_base = os.path.join(os.path.expanduser("~"),"Desktop")
        desk = os.path.join(desk_base, "CARTELLA TEST DA CANCELLARE")
        os.makedirs(desk, exist_ok=True)
        self._clr(self.t_dl)
        for w in self.dl_bf.winfo_children(): w.destroy()
        self.dl_bw.clear(); self.dl_bf2.clear(); self.dl_bl.clear()
        self.bw_vals=[]; self.dl_speeds={}
        self._dl_tach_target  = 0.0
        self._dl_tach_current = 0.0
        self._w(self.t_dl,f"{n} download simultanei | {nm}","info")
        self._w(self.t_dl,f"URL: {url[:65]}","muted")
        self._w(self.t_dl,f"Cartella: {desk}","muted")
        self._w(self.t_dl,"-"*55,"muted")
        self._st(f"{n} download in corso",RED)
        self.running=True
        for i in range(1,n+1):
            row=tk.Frame(self.dl_bf,bg=BG); row.pack(fill="x",padx=4,pady=1)
            tk.Label(row,text=f"#{i:02d}",fg=ORANGE,bg=BG,font=FMB,width=3).pack(side="left")
            bg_b=tk.Frame(row,bg=BG3,highlightbackground=BORDER,highlightthickness=1,height=16)
            bg_b.pack(side="left",fill="x",expand=True,padx=4)
            fill=tk.Frame(bg_b,bg=RED,height=16); fill.place(x=0,y=0,height=16)
            lbl=tk.Label(row,text="0%",fg=ORANGE,bg=BG,font=FM,width=5); lbl.pack(side="left")
            self.dl_bw[i]=bg_b; self.dl_bf2[i]=fill; self.dl_bl[i]=lbl
            dest=os.path.join(desk,f"CANCELLAMI_QUESTO_E_UN_TEST_{i}.{ext}")
            self.dl_speeds[i]=0.0
            threading.Thread(target=self._scarica,args=(i,url,dest),daemon=True).start()
        threading.Thread(target=self._aggrega,args=(n,),daemon=True).start()

    def _scarica(self,idx,url,dest):
        hdr={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"}
        try:
            Q.put((self.t_dl,f"  #{idx:02d} → {os.path.basename(dest)}","ok"))
            req=urllib.request.Request(url,headers=hdr)
            resp=urllib.request.urlopen(req,timeout=30)
            tot=int(resp.headers.get("Content-Length",0))
            done=0; t0=time.time()
            with open(dest,"wb") as fh:
                while self.running:
                    chunk=resp.read(65536)
                    if not chunk: break
                    fh.write(chunk); done+=len(chunk)
                    el=time.time()-t0
                    if el>0:
                        self.dl_speeds[idx]=done/el/1_000_000
                        # aggiorna target tachigrafo con la somma di tutti i thread
                        self._dl_tach_target = sum(self.dl_speeds.values())
                    pct=done/tot if tot>0 else min(0.99,done/(500*1024*1024))
                    self.root.after(0,lambda p=pct,i=idx:self._upd(i,p))
            if self.running:
                Q.put((self.t_dl,f"  #{idx:02d} COMPLETATO ({done//1024//1024} MB)","ok"))
                self.root.after(0,lambda i=idx:self._upd(i,1.0,True))
            # Auto-cancella il file di test
            try:
                os.remove(dest)
                Q.put((self.t_dl,f"  #{idx:02d} 🗑  File test cancellato automaticamente.","muted"))
            except: pass
            self.dl_speeds[idx]=0.0
        except Exception as ex:
            Q.put((self.t_dl,f"  #{idx:02d} ERRORE: {ex}","err"))
            self.dl_speeds[idx]=0.0

    def _upd(self,idx,pct,done=False):
        try:
            w=self.dl_bw[idx].winfo_width()
            self.dl_bf2[idx].place(width=int(w*pct))
            self.dl_bf2[idx].config(bg=GREEN if done else RED)
            self.dl_bl[idx].config(text=f"{int(pct*100)}%",fg=GREEN if done else ORANGE)
        except: pass

    def _aggrega(self,n):
        total_mb = [0.0]
        while self.running:
            tot = sum(self.dl_speeds.get(i,0) for i in range(1,n+1))
            total_mb[0] += tot * 1.0   # accumula MB ogni secondo
            col = GREEN if tot > 50 else CYAN if tot > 10 else ORANGE if tot > 1 else RED
            self._dl_tach_target = tot   # aggiorna target per il loop animazione
            self.root.after(0, lambda t=tot, c=col, mb=total_mb[0]: (
                self.dl_spd_lbl.config(text=f"{t:.1f}  MB/s", fg=c),
                self.dl_tot_lbl.config(text=f"{mb:.0f}  MB")
            ))
            self._st(f"Velocità: {tot:.1f} MB/s", RED)
            time.sleep(1)
        self._dl_tach_target = 0.0
        self.root.after(0, lambda: self.dl_spd_lbl.config(text="0.0  MB/s", fg=MUTED))

    def _dl_ferma(self):
        self.running=False
        self._dl_tach_target = 0.0
        self._w(self.t_dl,"Interrotto.","warn")
        self._st("Interrotto.",ORANGE)


    # ════ TAB 6 SPEED TEST ════════════════════════════════════════
    def _tab_speedtest(self, f):
        # Server per il test: (label, url_download, dimensione_bytes)
        self.ST_SERVERS = [
            ("Tele2 CDN (Europa)",    "http://speedtest.tele2.net/100MB.zip",    100*1024*1024),
            ("ThinkBroadband UK",     "http://ipv4.download.thinkbroadband.com/100MB.zip", 100*1024*1024),
            ("OVH Francia",           "http://proof.ovh.net/files/100Mb.dat",    100*1024*1024),
            ("Online.net Francia",    "http://ping.online.net/100Mo.dat",        100*1024*1024),
            ("Serverius (NL)",        "http://mirror.serverius.net/files/100mb.zip", 100*1024*1024),
            ("Hetzner Germania",      "http://speed.hetzner.de/100MB.bin",       100*1024*1024),
        ]
        self.st_running  = False
        self.st_dl_mbps  = 0.0
        self.st_ul_mbps  = 0.0
        self.st_ping_ms  = 0
        self.st_history  = []   # lista di dict {dl, ul, ping, ts}

        left  = self._panel(f, "SPEED TEST", CYAN, w=310)
        right = tk.Frame(f, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(0,4), pady=4)

        # ── Pannello sinistro ────────────────────────────────────
        tk.Label(left, text="Misura velocita reale della\nconnessione Internet.\nUpload: cascata proxy-safe\n(speedtest-cli → Cloudflare\n→ httpbin → stima).",
                 fg=MUTED, bg=BG2, font=FM, justify="left").pack(anchor="w", padx=4, pady=(0,6))
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=4)

        self._lbl(left, "Server di test")
        self.st_srv_var = tk.StringVar(value=self.ST_SERVERS[0][0])
        for nm, _, __ in self.ST_SERVERS:
            tk.Radiobutton(left, text=nm, variable=self.st_srv_var, value=nm,
                           fg=FG, bg=BG2, activebackground=BG2, selectcolor=BG3,
                           font=FM, cursor="hand2", anchor="w").pack(fill="x", pady=1)

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=6)

        # Pulsante AVVIA
        self.btn_st = tk.Button(left, text="▶  AVVIA SPEED TEST",
                                command=self._st_start,
                                bg="#001530", fg=CYAN,
                                font=("Segoe UI", 14, "bold"),
                                activebackground="#002a50", activeforeground=WHITE,
                                bd=2, relief="groove", cursor="hand2",
                                highlightbackground=CYAN, highlightthickness=2, pady=10)
        self.btn_st.pack(fill="x", pady=(0,3))
        self.btn_st.bind("<Enter>", lambda e: self.btn_st.config(bg="#002a50"))
        self.btn_st.bind("<Leave>", lambda e: self.btn_st.config(bg="#001530"))
        self._tooltip(self.btn_st,
            "AVVIA SPEED TEST\n"
            "Esegue 3 fasi in sequenza:\n"
            "1. Ping — 5 misurazioni di latenza TCP\n"
            "2. Download — scarica 10 MB dal server scelto\n"
            "3. Upload — cascata proxy-safe:\n"
            "   • speedtest-cli --secure (se installato)\n"
            "   • POST HTTPS → speed.cloudflare.com:443\n"
            "   • POST HTTP → httpbin.org:80\n"
            "   • Stima dal download (se tutto bloccato)")

        self._btn_tip(left, "INTERROMPI", self._st_stop, RED,
            "INTERROMPI\nFerma il test in corso nella fase attuale.")
        self._btn_tip(left, "SALVA LOG",  self._salva, YELLOW,
            "SALVA LOG\nEsporta ping, download, upload e storico in .txt.")

        # Storico test
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=6)
        self._lbl(left, "Storico test", MUTED)
        self.st_hist_box = scrolledtext.ScrolledText(
            left, bg="#04070a", fg=MUTED, font=("Consolas", 10),
            height=7, state="disabled",
            highlightbackground=BORDER, highlightthickness=1)
        self.st_hist_box.pack(fill="x", padx=2, pady=(0,4))

        # ── Pannello destra ─────────────────────────────────────
        # Contatori grandi
        meter_f = tk.Frame(right, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        meter_f.pack(fill="x", pady=(4,4), padx=4)

        for col_f, label, key, unit, color in [
            (meter_f, "PING",     "ping", "ms",   GREEN),
            (meter_f, "DOWNLOAD", "dl",   "Mb/s", CYAN),
            (meter_f, "UPLOAD",   "ul",   "Mb/s", ORANGE),
        ]:
            c = tk.Frame(col_f, bg=BG2)
            c.pack(side="left", fill="x", expand=True, padx=8, pady=10)
            lv = tk.Label(c, text="—", fg=color, bg=BG2,
                          font=("Consolas", 36, "bold"))
            lv.pack()
            tk.Label(c, text=f"{label}  ({unit})", fg=MUTED, bg=BG2, font=FH).pack()
            setattr(self, f"st_lbl_{key}", lv)

        # Barra progressi test
        prog_f = tk.Frame(right, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        prog_f.pack(fill="x", pady=(0,4), padx=4)
        tk.Label(prog_f, text="PROGRESSI TEST", fg=CYAN, bg=BG2,
                 font=FH).pack(anchor="w", padx=8, pady=(5,2))

        # Fase corrente
        self.st_fase_lbl = tk.Label(prog_f, text="In attesa...", fg=MUTED, bg=BG2,
                                     font=FMB, anchor="w")
        self.st_fase_lbl.pack(fill="x", padx=8, pady=(0,4))

        # Barra download
        tk.Label(prog_f, text="Download:", fg=CYAN, bg=BG2, font=FM,
                 anchor="w").pack(fill="x", padx=8)
        dl_bg = tk.Frame(prog_f, bg=BG3, highlightbackground=BORDER,
                          highlightthickness=1, height=20)
        dl_bg.pack(fill="x", padx=8, pady=(0,4))
        self.st_dl_bar = tk.Frame(dl_bg, bg=CYAN, height=20)
        self.st_dl_bar.place(x=0, y=0, height=20, relwidth=0)

        # Barra upload
        tk.Label(prog_f, text="Upload:", fg=ORANGE, bg=BG2, font=FM,
                 anchor="w").pack(fill="x", padx=8)
        ul_bg = tk.Frame(prog_f, bg=BG3, highlightbackground=BORDER,
                          highlightthickness=1, height=20)
        ul_bg.pack(fill="x", padx=8, pady=(0,8))
        self.st_ul_bar = tk.Frame(ul_bg, bg=ORANGE, height=20)
        self.st_ul_bar.place(x=0, y=0, height=20, relwidth=0)

        # ── Tachigrafo centrale grande ─────────────────────────────
        gf = tk.Frame(right, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        gf.pack(fill="x", pady=(0,4), padx=4)
        tk.Label(gf, text="VELOCITÀ IN TEMPO REALE (Mb/s)",
                 fg=CYAN, bg=BG2, font=FH).pack(anchor="w", padx=8, pady=(4,2))
        # Tachigrafo grande centrato — niente grafico a onde
        tach_wrap = tk.Frame(gf, bg=BG2)
        tach_wrap.pack(fill="x", pady=4)
        self.st_tach = tk.Canvas(tach_wrap, width=320, height=260,
                                  bg="#04070a", highlightthickness=0)
        self.st_tach.pack(anchor="center")
        # Canvas dummy per compatibilità con il codice che usa grafici["st"]
        self.grafici["st"] = tk.Canvas(gf, width=1, height=1, bg=BG2, highlightthickness=0)
        self.grafici["st"].pack()

        # Log
        tk.Label(right, text="OUTPUT SPEED TEST", fg=CYAN, bg=BG,
                 font=FHB).pack(anchor="w", padx=4)
        self.t_st = self._term(right, 6)
        self._w(self.t_st, "Seleziona un server e premi AVVIA SPEED TEST.", "muted")
        self._w(self.t_st, "Test di 100MB — download, upload, latenza.", "muted")

    # ── Speed Test Logic ──────────────────────────────────────────
    def _st_stop(self):
        self.st_running = False
        self._st_tach_target = 0.0
        self._st_fase("Interrotto.")
        self._st("Interrotto.", ORANGE)

    def _st_fase(self, testo, col=MUTED):
        self.root.after(0, lambda: self.st_fase_lbl.config(text=testo, fg=col))

    def _st_start(self):
        if self.st_running:
            import tkinter.messagebox as mb
            mb.showwarning("In esecuzione", "Premi INTERROMPI prima.")
            return
        # Trova URL del server selezionato
        srv_name = self.st_srv_var.get()
        srv_entry = next((s for s in self.ST_SERVERS if s[0] == srv_name), self.ST_SERVERS[0])
        url = srv_entry[1]

        self.st_running = True
        self._clr(self.t_st)
        self.st_lbl_ping.config(text="—")
        self.st_lbl_dl.config(text="—")
        self.st_lbl_ul.config(text="—")
        self.st_dl_bar.place(relwidth=0)
        self.st_ul_bar.place(relwidth=0)
        self.st_speed_vals = []
        self._st_tach_target  = 0.0
        self._st_tach_current = 0.0
        self._draw_tachymeter(0)
        self._st(f"Speed test in corso...", CYAN)

        threading.Thread(target=self._st_thread, args=(url,), daemon=True).start()

    def _st_thread(self, url):
        import time, urllib.request, socket

        def log(txt, tag=""):
            Q.put((self.t_st, txt, tag))

        # ── FASE 1: PING ──────────────────────────────────────────
        self._st_fase("⏱  Fase 1/3 — Misurazione latenza (ping)...", CYAN)
        log("── FASE 1: LATENZA ──────────────────────────", "info")

        ping_results = []
        try:
            host = urllib.parse.urlparse(url).netloc if hasattr(urllib, 'parse') else url.split("/")[2]
        except:
            host = "8.8.8.8"

        import urllib.parse
        host = urllib.parse.urlparse(url).netloc

        for i in range(5):
            if not self.st_running: return
            t0 = time.time()
            try:
                s = socket.create_connection((host, 80), timeout=3)
                ms = int((time.time() - t0) * 1000)
                s.close()
                ping_results.append(ms)
                log(f"  Ping #{i+1} -> {host} : {ms} ms",
                    "ok" if ms < 50 else "warn" if ms < 150 else "err")
            except Exception as ex:
                log(f"  Ping #{i+1} ERRORE: {ex}", "err")
            time.sleep(0.2)

        if ping_results:
            avg_ping = int(sum(ping_results) / len(ping_results))
            self.st_ping_ms = avg_ping
            self.root.after(0, lambda v=avg_ping: self.st_lbl_ping.config(
                text=str(v),
                fg=GREEN if v < 50 else ORANGE if v < 150 else RED))
            log(f"  Latenza media: {avg_ping} ms  |  Min: {min(ping_results)} ms  |  Max: {max(ping_results)} ms", "ok")
        else:
            log("  Impossibile misurare il ping.", "err")

        if not self.st_running: return

        # ── FASE 2: DOWNLOAD ──────────────────────────────────────
        self._st_fase("⬇  Fase 2/3 — Test download in corso...", CYAN)
        log("\n── FASE 2: DOWNLOAD ─────────────────────────", "info")
        log(f"  URL: {url}", "muted")

        speed_samples = []
        total_dl = 0
        t_start = time.time()

        try:
            hdr = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"}
            req = urllib.request.Request(url, headers=hdr)
            resp = urllib.request.urlopen(req, timeout=60)
            content_len = int(resp.headers.get("Content-Length", 0))
            t0 = time.time()
            chunk_t0 = t0
            chunk_bytes = 0

            while self.st_running:
                chunk = resp.read(131072)  # 128 KB chunks
                if not chunk:
                    break
                total_dl += len(chunk)
                chunk_bytes += len(chunk)
                elapsed = time.time() - t0
                chunk_elapsed = time.time() - chunk_t0

                if chunk_elapsed >= 0.25:   # refresh ogni 250ms
                    mbps = (chunk_bytes * 8) / chunk_elapsed / 1_000_000
                    speed_samples.append(round(mbps, 2))
                    self.st_speed_vals.append(round(mbps, 2))
                    if len(self.st_speed_vals) > 60:
                        self.st_speed_vals = self.st_speed_vals[-60:]
                    chunk_bytes = 0
                    chunk_t0 = time.time()
                    self._st_tach_target = mbps   # il loop animazione interpola fluido

                    pct = total_dl / content_len if content_len > 0 else min(0.99, total_dl / (100*1024*1024))
                    self.root.after(0, lambda p=pct: self.st_dl_bar.place(relwidth=min(p, 1.0)))
                    self.root.after(0, lambda v=mbps: self.st_lbl_dl.config(
                        text=f"{v:.1f}",
                        fg=GREEN if v > 50 else CYAN if v > 10 else ORANGE))
                    v2 = self.st_speed_vals[:]
                    self.root.after(0, lambda v=v2: self._plot_bw(self.grafici["st"], v, unit="Mb/s"))
                    log(f"  {total_dl//1024//1024} MB scaricati  |  {mbps:.1f} Mb/s  ({elapsed:.1f}s)", "data")

            elapsed_total = time.time() - t_start
            if speed_samples:
                avg_dl = sum(speed_samples) / len(speed_samples)
                peak_dl = max(speed_samples)
                self.st_dl_mbps = avg_dl
                self.root.after(0, lambda v=avg_dl: (
                    self.st_lbl_dl.config(text=f"{v:.1f}",
                        fg=GREEN if v > 50 else CYAN if v > 10 else ORANGE),
                    self.st_dl_bar.place(relwidth=1.0)
                ))
                log(f"  Download completato: {total_dl//1024//1024} MB in {elapsed_total:.1f}s", "ok")
                log(f"  Velocità media: {avg_dl:.1f} Mb/s  |  Peak: {peak_dl:.1f} Mb/s", "ok")
            else:
                log("  Nessun dato download.", "err")

        except Exception as ex:
            log(f"  ERRORE download: {ex}", "err")

        if not self.st_running: return

        # ── PAUSA TRA DOWNLOAD E UPLOAD ───────────────────────────
        self._st_fase("⏸  Pausa 5s tra download e upload...", MUTED)
        log("\n── PAUSA 5 SECONDI ──────────────────────────", "muted")
        self._st_tach_target = 0.0   # lancetta scende a zero
        for i in range(5, 0, -1):
            if not self.st_running: return
            self.root.after(0, lambda s=i: self._st_fase(f"⏸  Pausa tra download e upload...  {s}s", MUTED))
            time.sleep(1)
        if not self.st_running: return

        # ── FASE 3: UPLOAD — cascata proxy-safe ───────────────────
        # Strategia:
        #   1. speedtest-cli --secure  (più preciso, HTTPS/443)
        #   2. POST HTTPS su speed.cloudflare.com (porta 443, proxy friendly)
        #   3. POST HTTP chunked su httpbin.org (porta 80, fallback)
        #   4. Stima dal download se tutto bloccato
        self._st_fase("⬆  Fase 3/3 — Test upload (cascata proxy-safe)...", ORANGE)
        log("\n── FASE 3: UPLOAD ───────────────────────────", "info")

        import http.client, ssl, shutil

        def _ul_update(mbps, pct):
            self._st_tach_target = mbps   # muove la lancetta del tachigrafo
            self.root.after(0, lambda v=mbps: self.st_lbl_ul.config(
                text=f"{v:.1f}",
                fg=GREEN if v > 20 else ORANGE if v > 5 else RED))
            self.root.after(0, lambda p=pct: self.st_ul_bar.place(relwidth=min(p, 1.0)))

        def _ul_done(avg_ul):
            self.st_ul_mbps = avg_ul
            self.root.after(0, lambda v=avg_ul: (
                self.st_lbl_ul.config(text=f"{v:.1f}",
                    fg=GREEN if v > 20 else ORANGE if v > 5 else RED),
                self.st_ul_bar.place(relwidth=1.0)
            ))

        ul_done = False

        # ── TENTATIVO 1: speedtest-cli --secure ───────────────────
        if not ul_done and shutil.which("speedtest-cli"):
            log("  [1/4] Provo speedtest-cli --secure ...", "info")
            try:
                import subprocess as sp
                r = sp.run(
                    ["speedtest-cli", "--secure", "--simple", "--no-pre-allocate"],
                    capture_output=True, text=True, timeout=60,
                    **_popen_flags()
                )
                for line in r.stdout.splitlines():
                    log(f"  {line}", "data")
                    m = re.search(r"Upload:\s+([\d.]+)\s+Mbit/s", line, re.I)
                    if m:
                        avg_ul = float(m.group(1))
                        _ul_done(avg_ul)
                        log(f"  ✔ speedtest-cli: Upload {avg_ul:.1f} Mb/s", "ok")
                        ul_done = True
                        break
                if not ul_done:
                    log("  speedtest-cli non ha restituito dati upload.", "warn")
            except Exception as ex:
                log(f"  speedtest-cli fallito: {ex}", "warn")
        else:
            if not shutil.which("speedtest-cli"):
                log("  [1/4] speedtest-cli non installato — salto.", "muted")
                log("  Suggerimento: pip install speedtest-cli", "muted")

        # ── TENTATIVO 2: HTTPS POST su speed.cloudflare.com (443) ─
        if not ul_done and self.st_running:
            log("  [2/4] Provo upload HTTPS → speed.cloudflare.com:443 ...", "info")
            try:
                ctx = ssl.create_default_context()
                conn2 = http.client.HTTPSConnection("speed.cloudflare.com",
                                                    context=ctx, timeout=15)
                conn2.connect()
                chunk_size = 65536
                buf_size   = 12 * 1024 * 1024   # 12 MB (triplicato)
                payload    = bytes([0x41] * chunk_size)
                sent       = 0
                ul_samples = []
                t_ul = time.time(); chunk_t0 = t_ul; chunk_bytes = 0

                conn2.putrequest("POST", "/__up")
                conn2.putheader("Content-Type", "application/octet-stream")
                conn2.putheader("Content-Length", str(buf_size))
                conn2.endheaders()

                while sent < buf_size and self.st_running:
                    to_send = min(chunk_size, buf_size - sent)
                    conn2.sock.sendall(payload[:to_send])
                    sent += to_send; chunk_bytes += to_send
                    elapsed_c = time.time() - chunk_t0
                    if elapsed_c >= 0.5:
                        mbps = (chunk_bytes * 8) / elapsed_c / 1_000_000
                        ul_samples.append(round(mbps, 2))
                        chunk_bytes = 0; chunk_t0 = time.time()
                        pct = sent / buf_size
                        _ul_update(mbps, pct)
                        log(f"  {sent//1024} KB inviati  |  {mbps:.1f} Mb/s", "data")
                try: conn2.getresponse(); conn2.close()
                except: pass

                if ul_samples:
                    avg_ul = sum(ul_samples) / len(ul_samples)
                    _ul_done(avg_ul)
                    log(f"  ✔ Cloudflare HTTPS: Upload {avg_ul:.1f} Mb/s", "ok")
                    ul_done = True
                else:
                    log("  Nessun campione raccolto.", "warn")
            except Exception as ex:
                log(f"  Cloudflare HTTPS fallito: {ex}", "warn")

        # ── TENTATIVO 3: HTTP POST su httpbin.org (porta 80) ──────
        if not ul_done and self.st_running:
            log("  [3/4] Provo upload HTTP → httpbin.org:80 ...", "info")
            try:
                conn3 = http.client.HTTPConnection("httpbin.org", timeout=15)
                conn3.connect()
                chunk_size = 65536
                buf_size   = 6 * 1024 * 1024   # 6 MB (triplicato)
                payload    = bytes([0x42] * chunk_size)
                sent       = 0
                ul_samples = []
                t_ul = time.time(); chunk_t0 = t_ul; chunk_bytes = 0

                conn3.putrequest("POST", "/post")
                conn3.putheader("Content-Type", "application/octet-stream")
                conn3.putheader("Content-Length", str(buf_size))
                conn3.endheaders()

                while sent < buf_size and self.st_running:
                    to_send = min(chunk_size, buf_size - sent)
                    conn3.sock.sendall(payload[:to_send])
                    sent += to_send; chunk_bytes += to_send
                    elapsed_c = time.time() - chunk_t0
                    if elapsed_c >= 0.5:
                        mbps = (chunk_bytes * 8) / elapsed_c / 1_000_000
                        ul_samples.append(round(mbps, 2))
                        chunk_bytes = 0; chunk_t0 = time.time()
                        pct = sent / buf_size
                        _ul_update(mbps, pct)
                        log(f"  {sent//1024} KB inviati  |  {mbps:.1f} Mb/s", "data")
                try: conn3.getresponse(); conn3.close()
                except: pass

                if ul_samples:
                    avg_ul = sum(ul_samples) / len(ul_samples)
                    _ul_done(avg_ul)
                    log(f"  ✔ httpbin HTTP: Upload {avg_ul:.1f} Mb/s", "ok")
                    ul_done = True
                else:
                    log("  Nessun campione raccolto.", "warn")
            except Exception as ex:
                log(f"  httpbin.org fallito: {ex}", "warn")

        # ── TENTATIVO 4: Stima da download (ultimo fallback) ───────
        if not ul_done:
            log("  [4/4] Tutti i metodi bloccati (proxy aziendale?).", "err")
            log("  Upload non misurabile — stima basata su download.", "warn")
            if self.st_dl_mbps > 0:
                # Upload tipicamente 20-40% del download su ADSL/VDSL
                est = round(self.st_dl_mbps * 0.30, 1)
                self.st_ul_mbps = est
                self.root.after(0, lambda v=est: (
                    self.st_lbl_ul.config(text=f"~{v:.1f}", fg=MUTED),
                    self.st_ul_bar.place(relwidth=0.3)
                ))
                log(f"  Stima upload: ~{est:.1f} Mb/s (30% di {self.st_dl_mbps:.1f} DL)", "warn")
                log("  ⚠ Per upload preciso installa: pip install speedtest-cli", "warn")
            else:
                log("  Upload: N/D", "err")

        if not self.st_running: return

        # ── RISULTATO FINALE ──────────────────────────────────────
        self._st_fase("✔  Test completato!", GREEN)
        log("\n══ RISULTATO FINALE ════════════════════════", "ok")
        log(f"  Ping:     {self.st_ping_ms} ms", "ok")
        log(f"  Download: {self.st_dl_mbps:.1f} Mb/s", "ok")
        log(f"  Upload:   {self.st_ul_mbps:.1f} Mb/s", "ok")

        ts = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {"ping": self.st_ping_ms, "dl": self.st_dl_mbps,
                 "ul": self.st_ul_mbps, "ts": ts}
        self.st_history.append(entry)
        self.log_buf.append(
            f"[SPEED TEST {ts}] Ping:{self.st_ping_ms}ms  DL:{self.st_dl_mbps:.1f}Mb/s  UL:{self.st_ul_mbps:.1f}Mb/s")

        # Aggiorna storico nella sidebar
        self.root.after(0, self._st_update_history)
        self.st_running = False
        # Riporta lancetta a zero dopo breve pausa
        self.root.after(1500, lambda: setattr(self, '_st_tach_target', 0.0))
        self.root.after(0, lambda: self._st("Speed test completato.", GREEN))

    def _st_update_history(self):
        self.st_hist_box.config(state="normal")
        self.st_hist_box.delete("1.0", "end")
        for e in reversed(self.st_history[-10:]):
            line = f"{e['ts']}  ↓{e['dl']:.1f}  ↑{e['ul']:.1f}  P:{e['ping']}ms\n"
            self.st_hist_box.insert("end", line)
        self.st_hist_box.config(state="disabled")

    # ── LOOP ANIMAZIONE TACHIGRAFI (60fps, interpolazione lerp) ──
    def _tach_anim_loop(self):
        """Aggiorna entrambi i tachigrafi a ~60fps con interpolazione fluida."""
        LERP_UP   = 0.03   # salita lenta (più progressiva)
        LERP_DOWN = 0.025  # discesa ancora più lenta (naturale)

        # ── Download tachymeter ───────────────────────────────────
        target_dl  = self._dl_tach_target
        cur_dl     = self._dl_tach_current
        lerp_dl    = LERP_UP if target_dl > cur_dl else LERP_DOWN
        new_dl     = cur_dl + (target_dl - cur_dl) * lerp_dl
        if abs(new_dl - target_dl) < 0.002:
            new_dl = target_dl
        self._dl_tach_current = new_dl

        try:
            self._draw_dl_tachymeter(new_dl, 150)
        except Exception:
            pass

        # ── Speed test tachymeter ─────────────────────────────────
        target_st  = self._st_tach_target
        cur_st     = self._st_tach_current
        lerp_st    = LERP_UP if target_st > cur_st else LERP_DOWN
        new_st     = cur_st + (target_st - cur_st) * lerp_st
        if abs(new_st - target_st) < 0.002:
            new_st = target_st
        self._st_tach_current = new_st

        try:
            self._draw_tachymeter_raw(new_st, 150)
        except Exception:
            pass

        self.root.after(16, self._tach_anim_loop)   # ~60fps

    def _draw_dl_tachymeter(self, val_mbps, max_val=10.0):
        """
        Tachigrafo download: stile identico allo speed test (arco 240°, scala fissa 100).
        """
        import math as _m
        c = self.dl_tach
        c.delete("all")
        W, H = 300, 160
        cx, cy = 150, 148    # centro arco (basso centro)
        R  = 118             # raggio esterno

        # Scala FISSA a 100 MB/s
        max_val = 100.0

        # Angoli: arco da 210° a -30° (totale 240°) — identico allo speed test
        ANG_START = 210
        ANG_RANGE = 240

        def ang(v):
            frac = min(v / max_val, 0.0 if max_val == 0 else min(v / max_val, 1.0))
            frac = min(max(v / max_val, 0.0), 1.0)
            deg  = ANG_START - frac * ANG_RANGE
            return _m.radians(deg)

        # Sfondo arco (grigio scuro)
        c.create_arc(cx-R, cy-R, cx+R, cy+R,
                     start=-30, extent=240,
                     style="arc", outline="#1a2a3a", width=14)

        # Sfondo segmenti colorati (sempre visibili)
        seg_data = [
            (0.00, 0.33, "#1a0000"),
            (0.33, 0.66, "#1a1a00"),
            (0.66, 1.00, "#001a08"),
        ]
        for fs, fe, col in seg_data:
            deg_s = ANG_START - fs * ANG_RANGE
            ext   = (fs - fe) * ANG_RANGE
            c.create_arc(cx-R+4, cy-R+4, cx+R-4, cy+R-4,
                         start=deg_s + ext, extent=-ext,
                         style="arc", outline=col, width=8)

        # Arco valore corrente (colore rosso→giallo→verde)
        if val_mbps > 0:
            frac = min(val_mbps / max_val, 1.0)
            if frac < 0.33:
                arc_col = RED
            elif frac < 0.66:
                t = (frac - 0.33) / 0.33
                r = 0xff; g = int(0xff * t); b = 0
                arc_col = f"#{r:02x}{g:02x}{b:02x}"
            else:
                t = (frac - 0.66) / 0.34
                r = int(0xff * (1-t)); g = 0xff; b = 0
                arc_col = f"#{r:02x}{g:02x}{b:02x}"
            extent = frac * ANG_RANGE
            c.create_arc(cx-R, cy-R, cx+R, cy+R,
                         start=210 - extent, extent=extent,
                         style="arc", outline=arc_col, width=12)

        # Tacche
        num_major = 5
        for i in range(num_major + 1):
            frac_t = i / num_major
            v_t    = max_val * frac_t
            a      = ang(v_t)
            x1 = cx + (R-2)  * _m.cos(a);  y1 = cy - (R-2)  * _m.sin(a)
            x2 = cx + (R-14) * _m.cos(a);  y2 = cy - (R-14) * _m.sin(a)
            c.create_line(x1, y1, x2, y2, fill=MUTED, width=2)
            xn = cx + (R-28) * _m.cos(a);  yn = cy - (R-28) * _m.sin(a)
            lbl = str(int(v_t))
            c.create_text(xn, yn, text=lbl, fill=MUTED,
                          font=("Consolas", 9), anchor="center")
        num_minor = num_major * 4
        for i in range(num_minor + 1):
            if i % 4 == 0: continue
            frac_t = i / num_minor
            a      = ang(max_val * frac_t)
            x1 = cx + (R-2)  * _m.cos(a);  y1 = cy - (R-2)  * _m.sin(a)
            x2 = cx + (R-8)  * _m.cos(a);  y2 = cy - (R-8)  * _m.sin(a)
            c.create_line(x1, y1, x2, y2, fill="#2a3a4a", width=1)

        # Ago (triangolo sottile, stile voltmetro)
        na = ang(val_mbps)
        tip_r  = R - 4
        base_r = 14
        perp = na + _m.pi / 2
        bx1 = cx + base_r * 0.35 * _m.cos(perp)
        by1 = cy - base_r * 0.35 * _m.sin(perp)
        bx2 = cx - base_r * 0.35 * _m.cos(perp)
        by2 = cy + base_r * 0.35 * _m.sin(perp)
        tx  = cx + tip_r * _m.cos(na)
        ty  = cy - tip_r * _m.sin(na)
        # ombra
        c.create_polygon(bx1+2, by1+2, bx2+2, by2+2, tx+2, ty+2,
                         fill="#000000", outline="")
        # colore ago rosso→giallo→verde
        frac_n = min(val_mbps / max_val, 1.0)
        if frac_n < 0.33:
            col_n = RED
        elif frac_n < 0.66:
            t = (frac_n - 0.33) / 0.33
            r = 0xff; g = int(0xff * t); b = 0
            col_n = f"#{r:02x}{g:02x}{b:02x}"
        else:
            t = (frac_n - 0.66) / 0.34
            r = int(0xff * (1-t)); g = 0xff; b = 0
            col_n = f"#{r:02x}{g:02x}{b:02x}"
        c.create_polygon(bx1, by1, bx2, by2, tx, ty,
                         fill=col_n, outline=WHITE, width=1)
        # coda ago
        tail_r = 18
        txb = cx - tail_r * _m.cos(na)
        tyb = cy + tail_r * _m.sin(na)
        c.create_line(cx, cy, txb, tyb, fill="#445566", width=3)
        # cerniera
        c.create_oval(cx-8, cy-8, cx+8, cy+8, fill="#0d1a26", outline=CYAN, width=2)
        c.create_oval(cx-3, cy-3, cx+3, cy+3, fill=CYAN, outline="")

        # Linea base
        c.create_line(cx-R, cy, cx+R, cy, fill="#1a2a3a", width=1)

        # Valore digitale
        c.create_text(cx, cy - 30, text=f"{val_mbps:.2f}",
                      fill=WHITE, font=("Consolas", 20, "bold"), anchor="center")
        c.create_text(cx, cy - 10, text="MB/s",
                      fill=MUTED, font=("Consolas", 10), anchor="center")
        c.create_text(cx - R + 4, cy + 14, text="0",
                      fill=MUTED, font=("Consolas", 9), anchor="w")
        c.create_text(cx + R - 4, cy + 14, text="100",
                      fill=MUTED, font=("Consolas", 9), anchor="e")

    def _draw_tachymeter(self, val_mbps, max_val=None):
        """Setter target speedtest tachymeter — il loop di animazione fa il rendering."""
        self._st_tach_target = val_mbps

    def _draw_tachymeter_raw(self, val_mbps, max_val=None):
        """Disegna un tachigrafo analogico stile cruscotto sul canvas st_tach."""
        import math as _math
        c = self.st_tach
        c.delete("all")
        W, H = 320, 260
        cx, cy = 160, 165   # centro arco
        R = 120             # raggio esterno (grande)

        # Scala FISSA a 120 Mb/s
        max_val = 120

        # Angoli: arco da 210° a -30° (totale 240°)
        ANG_START = 210   # gradi (sinistra)
        ANG_END   = -30   # gradi (destra)
        ANG_RANGE = 240

        def ang(v):
            """Converte valore in angolo radianti."""
            frac = min(v / max_val, 1.0)
            deg  = ANG_START - frac * ANG_RANGE
            return _math.radians(deg)

        # Sfondo arco (grigio scuro)
        c.create_arc(cx-R, cy-R, cx+R, cy+R,
                     start=-30, extent=240,
                     style="arc", outline="#1a2a3a", width=18)

        # Arco colorato a segmenti: rosso→giallo→verde (da sinistra=lento a destra=veloce)
        # Disegniamo prima i segmenti di colore fissi (sempre visibili come sfondo)
        seg_data = [
            (0.00, 0.33, "#1a0000"),   # zona rossa scura
            (0.33, 0.66, "#1a1a00"),   # zona gialla scura
            (0.66, 1.00, "#001a08"),   # zona verde scura
        ]
        for fs, fe, col in seg_data:
            deg_s = ANG_START - fs * ANG_RANGE
            ext   = (fs - fe) * ANG_RANGE
            c.create_arc(cx-R+4, cy-R+4, cx+R-4, cy+R-4,
                         start=deg_s + ext, extent=-ext,
                         style="arc", outline=col, width=10)

        # Arco valore corrente (colorato in base alla velocità)
        if val_mbps > 0:
            frac = min(val_mbps / max_val, 1.0)
            if frac < 0.33:
                arc_col = RED
            elif frac < 0.66:
                # interpolazione rosso → giallo
                t = (frac - 0.33) / 0.33
                r = int(0xff); g = int(0xff * t); b = 0
                arc_col = f"#{r:02x}{g:02x}{b:02x}"
            else:
                # interpolazione giallo → verde
                t = (frac - 0.66) / 0.34
                r = int(0xff * (1-t)); g = 0xff; b = 0
                arc_col = f"#{r:02x}{g:02x}{b:02x}"
            extent = frac * 240
            c.create_arc(cx-R, cy-R, cx+R, cy+R,
                         start=210 - extent, extent=extent,
                         style="arc", outline=arc_col, width=16)

        # Tacche e numeri
        num_ticks = 6
        for i in range(num_ticks + 1):
            frac_t = i / num_ticks
            tick_val = max_val * frac_t
            a = ang(tick_val)
            # Tacca lunga
            x1 = cx + (R-6)  * _math.cos(a)
            y1 = cy - (R-6)  * _math.sin(a)
            x2 = cx + (R-22) * _math.cos(a)
            y2 = cy - (R-22) * _math.sin(a)
            c.create_line(x1, y1, x2, y2, fill=MUTED, width=3)
            # Numero
            xn = cx + (R-42) * _math.cos(a)
            yn = cy - (R-42) * _math.sin(a)
            lbl = str(int(tick_val)) if tick_val < 100 else f"{int(tick_val/10)*10}"
            c.create_text(xn, yn, text=lbl, fill=MUTED,
                          font=("Consolas", 13), anchor="center")

        # Tacche piccole intermedie
        for i in range(num_ticks * 4):
            if i % 4 == 0: continue
            frac_t = i / (num_ticks * 4)
            a = ang(max_val * frac_t)
            x1 = cx + (R-6)  * _math.cos(a)
            y1 = cy - (R-6)  * _math.sin(a)
            x2 = cx + (R-16) * _math.cos(a)
            y2 = cy - (R-16) * _math.sin(a)
            c.create_line(x1, y1, x2, y2, fill="#2a3a4a", width=1)

        # Ago
        needle_ang = ang(val_mbps)
        nx = cx + (R-10) * _math.cos(needle_ang)
        ny = cy - (R-10) * _math.sin(needle_ang)
        # Ombra ago
        c.create_line(cx+2, cy+2, nx+2, ny+2, fill="#000000", width=5)
        # Ago principale — colore da rosso (lento) a verde (veloce)
        frac_n = min(val_mbps / max_val, 1.0)
        if frac_n < 0.33:
            col_needle = RED
        elif frac_n < 0.66:
            t = (frac_n - 0.33) / 0.33
            r = int(0xff); g = int(0xff * t); b = 0
            col_needle = f"#{r:02x}{g:02x}{b:02x}"
        else:
            t = (frac_n - 0.66) / 0.34
            r = int(0xff * (1-t)); g = 0xff; b = 0
            col_needle = f"#{r:02x}{g:02x}{b:02x}"
        c.create_line(cx, cy, nx, ny, fill=col_needle, width=4, capstyle="round")
        # Cerniera ago
        c.create_oval(cx-10, cy-10, cx+10, cy+10, fill="#1a2a3a", outline=CYAN, width=2)

        # Valore digitale al centro
        v_str = f"{val_mbps:.1f}"
        c.create_text(cx, cy+28, text=v_str, fill=WHITE,
                      font=("Consolas", 28, "bold"), anchor="center")
        c.create_text(cx, cy+58, text="Mb/s", fill=MUTED,
                      font=("Consolas", 14), anchor="center")

    # ════ TAB 7 INFO RETE ═════════════════════════════════════════
    def _tab_info(self, f):
        left=self._panel(f,"INFO RETE",RED,w=280)
        right=tk.Frame(f,bg=BG); right.pack(side="left",fill="both",expand=True,padx=(0,4),pady=4)

        INFO_TIPS = {
            "ipconfig /all": (
                "IPCONFIG /ALL\n"
                "Mostra la configurazione completa di tutte le\n"
                "interfacce di rete: IP, MAC, gateway, DNS,\n"
                "DHCP, subnet mask, lease time.\n"
                "È il primo comando da eseguire per diagnosticare\n"
                "qualsiasi problema di rete."
            ),
            "route print": (
                "ROUTE PRINT\n"
                "Mostra la tabella di routing di Windows.\n"
                "Indica come il PC decide dove inviare i pacchetti\n"
                "per ogni destinazione IP.\n"
                "Utile per: VPN, reti multiple, problemi di routing."
            ),
            "arp -a": (
                "ARP -A — Tabella ARP\n"
                "Mostra la cache ARP: la corrispondenza tra\n"
                "indirizzi IP e MAC address della rete locale.\n"
                "Utile per: trovare device nascosti, rilevare\n"
                "ARP spoofing, identificare dispositivi per MAC."
            ),
            "netstat -an": (
                "NETSTAT -AN — Connessioni attive\n"
                "Elenca tutte le connessioni TCP/UDP aperte.\n"
                "Mostra: porta locale, IP remoto, stato.\n"
                "LISTEN = in attesa  |  ESTABLISHED = attiva\n"
                "TIME_WAIT = in chiusura\n"
                "Utile per trovare porte aperte o connessioni sospette."
            ),
            "netstat -e": (
                "NETSTAT -E — Statistiche interfacce\n"
                "Contatori hardware dell'adattatore di rete:\n"
                "bytes TX/RX, errori, pacchetti scartati.\n"
                "Errori alti = problema hardware o cavo."
            ),
            "ping 8.8.8.8": (
                "PING 8.8.8.8 — Test connettività Google\n"
                "Invia 4 ping ai DNS pubblici di Google.\n"
                "Test rapido per verificare se Internet è\n"
                "raggiungibile dal PC.\n"
                "Se fallisce: problema gateway o ISP."
            ),
        }
        # Comandi adattati all'OS corrente
        if IS_WINDOWS:
            info_cmds = [
                ("ipconfig /all\nConfigurazione interfacce", ["ipconfig","/all"],     GREEN),
                ("route print\nTabella di routing",          ["route","print"],        CYAN),
                ("arp -a\nTabella ARP  IP <-> MAC",          ["arp","-a"],             YELLOW),
                ("netstat -an\nConnessioni attive",           ["netstat","-an"],        ORANGE),
                ("netstat -e\nStatistiche interfacce",        ["netstat","-e"],         FG),
                ("ping 8.8.8.8 -n 4\nTest connettivita Google", ["ping","8.8.8.8","-n","4"], GREEN),
            ]
        else:
            info_cmds = [
                ("ip addr\nConfigurazione interfacce",        ["ip","addr"],            GREEN),
                ("ip route\nTabella di routing",              ["ip","route"],           CYAN),
                ("arp -n\nTabella ARP  IP <-> MAC",           ["arp","-n"],             YELLOW),
                ("netstat -an\nConnessioni attive",           ["netstat","-an"],        ORANGE),
                ("netstat -s\nStatistiche interfacce",        ["netstat","-s"],         FG),
                ("ping -c 4 8.8.8.8\nTest connettivita Google", ["ping","-c","4","8.8.8.8"], GREEN),
            ]
        for title,cmd,col in info_cmds:
            tip_key = title.split("\n")[0].replace(" -n 4","")
            b=tk.Button(left,text=title,command=lambda c=cmd:self._info_run(c),
                        bg=BG3,fg=col,font=FM,activebackground="#1a2a3a",
                        activeforeground=WHITE,bd=1,relief="groove",cursor="hand2",
                        pady=5,anchor="w",justify="left")
            b.pack(fill="x",pady=2)
            b.bind("<Enter>",lambda e,bt=b,c=col:bt.config(bg="#1a2a3a",fg=WHITE))
            b.bind("<Leave>",lambda e,bt=b,c=col:bt.config(bg=BG3,fg=c))
            if tip_key in INFO_TIPS:
                self._tooltip(b, INFO_TIPS[tip_key])
        tk.Frame(left,bg=BORDER,height=1).pack(fill="x",pady=5)
        self._btn_tip(left,"INTERROMPI",self._ferma,RED,
            "INTERROMPI\nFerma il comando in corso.")
        self._btn_tip(left,"SALVA LOG",self._salva,YELLOW,
            "SALVA LOG\nEsporta l'output del comando in un file .txt.")

        tk.Label(right,text="OUTPUT",fg=RED,bg=BG,font=FHB).pack(anchor="w",padx=4)
        self.t_info=self._term(right,22)
        self._w(self.t_info,"Clicca un comando per eseguirlo.","muted")


    # ════ TAB SCANNER RETE ═══════════════════════════════════════
    def _tab_scanner(self, f):
        left = self._panel(f, "SCANNER RETE", PINK, w=310)
        right = tk.Frame(f, bg=BG); right.pack(side="left", fill="both", expand=True, padx=(0,4), pady=4)

        self._lbl(left, "Range IP da scansionare")
        rf = tk.Frame(left, bg=BG2); rf.pack(fill="x", pady=(0,6))
        # DA
        row_da = tk.Frame(rf, bg=BG2); row_da.pack(fill="x", pady=1)
        tk.Label(row_da, text="  Da:", fg=MUTED, bg=BG2, font=FM, width=5, anchor="w").pack(side="left")
        self.sc_from = self._entry_inline(row_da, "192.168.1.1", 18)
        # A
        row_a = tk.Frame(rf, bg=BG2); row_a.pack(fill="x", pady=1)
        tk.Label(row_a, text="  A: ", fg=MUTED, bg=BG2, font=FM, width=5, anchor="w").pack(side="left")
        self.sc_to   = self._entry_inline(row_a, "192.168.1.254", 18)

        self._lbl(left, "Thread paralleli (velocita)")
        self.sc_threads = self._combo(left, ["20 - lento (reti lente)","50 - bilanciato","100 - veloce","200 - massimo"], 1)
        self._tooltip(self.sc_threads,
            "THREAD PARALLELI\n"
            "Numero di IP testati simultaneamente.\n"
            "20  → Reti lente o proxy, minimo carico\n"
            "50  → Bilanciato, uso normale\n"
            "100 → Veloce, reti stabili\n"
            "200 → Massimo, può sovraccaricare switch vecchi")

        self._lbl(left, "Timeout ping (ms)")
        self.sc_timeout = self._combo(left, ["200 ms","500 ms","1000 ms"], 0)
        self._tooltip(self.sc_timeout,
            "TIMEOUT PING\n"
            "Tempo massimo di attesa per ogni ping.\n"
            "200ms → Rete locale veloce (LAN Gigabit)\n"
            "500ms → Rete normale o Wi-Fi\n"
            "1000ms → Rete lenta, VPN o link WAN")

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=5)
        self._lbl(left, "Cosa scansionare", MUTED)

        self.v_sc_ping  = tk.BooleanVar(value=True)
        self.v_sc_arp   = tk.BooleanVar(value=True)
        self.v_sc_dns   = tk.BooleanVar(value=True)
        self.v_sc_nbt   = tk.BooleanVar(value=True)
        self.v_sc_ports = tk.BooleanVar(value=True)
        self.v_sc_banner= tk.BooleanVar(value=True)

        SC_CHECKS = [
            ("  Ping sweep (rilevamento host)",    self.v_sc_ping,   GREEN,
             "PING SWEEP\nInvia un ping ICMP a ogni IP del range.\nSolo gli IP che rispondono vengono analizzati.\nDisattiva per reti che bloccano ICMP."),
            ("  ARP table + identificazione MAC",  self.v_sc_arp,    CYAN,
             "ARP + MAC\nLegge la tabella ARP di Windows per ottenere\ni MAC address dei dispositivi trovati.\nIdentifica il produttore dal prefisso OUI del MAC."),
            ("  Risoluzione DNS inversa",          self.v_sc_dns,    YELLOW,
             "DNS INVERSO\nPer ogni IP trovato, esegue una query PTR\nper trovare il nome host associato.\nRichiede server DNS configurato correttamente."),
            ("  NetBIOS / nbtstat (nomi Windows)", self.v_sc_nbt,    ORANGE,
             "NBTSTAT — Nome NetBIOS\nInterroga ogni host per il nome NetBIOS (Windows).\nPermette di identificare PC Windows per nome.\n⚠ Rallenta la scansione (~3s per host attivo)."),
            ("  Scansione porte principali",       self.v_sc_ports,  PINK,
             "PORT SCAN\nTesta 20 porte comuni su ogni host attivo:\nFTP(21), SSH(22), HTTP(80), RDP(3389), SMB(445)...\nTimeout 300ms per porta — veloce ma non esaustivo."),
            ("  Banner grabbing (servizi)",        self.v_sc_banner, RED,
             "BANNER GRABBING\nSe una porta è aperta, invia una richiesta\ne cattura i primi 80 byte di risposta.\nPermette di identificare il software in ascolto\n(es: 'Apache 2.4', 'OpenSSH 8.0', 'IIS/10.0')."),
        ]
        for txt, var, col, tip in SC_CHECKS:
            chk = tk.Checkbutton(left, text=txt, variable=var, fg=col, bg=BG2,
                                 activebackground=BG2, activeforeground=WHITE,
                                 selectcolor=BG3, font=FH, anchor="w")
            chk.pack(fill="x", pady=1)
            self._tooltip(chk, tip)

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=5)

        # Pulsante scan
        self.btn_scan = tk.Button(left, text="AVVIA SCANSIONE",
                                  command=self._scan_start,
                                  bg="#001a0a", fg=PINK,
                                  font=("Segoe UI", 14, "bold"),
                                  activebackground="#002a14", activeforeground=WHITE,
                                  bd=2, relief="groove", cursor="hand2",
                                  highlightbackground=PINK, highlightthickness=2, pady=10)
        self.btn_scan.pack(fill="x", pady=(0,3))
        self.btn_scan.bind("<Enter>", lambda e: self.btn_scan.config(bg="#002a14"))
        self.btn_scan.bind("<Leave>", lambda e: self.btn_scan.config(bg="#001a0a"))
        self._tooltip(self.btn_scan,
            "AVVIA SCANSIONE\n"
            "Scansiona il range IP specificato in parallelo.\n"
            "Fasi: ARP preload → Ping sweep → MAC/DNS/\n"
            "NetBIOS/Porte/Banner per ogni host attivo.\n"
            "I risultati appaiono in tempo reale nella tabella.")

        self._btn_tip(left, "INTERROMPI", self._scan_stop, RED,
            "INTERROMPI\nFerma la scansione. I risultati già trovati\nrimangono visibili nella tabella.")
        self._btn_tip(left, "SALVA REPORT", self._scan_salva, YELLOW,
            "SALVA REPORT\nEsporta la tabella completa in .txt o .csv\ncon tutti i dettagli di ogni dispositivo trovato.")

        # Progress bar
        pb_f = tk.Frame(left, bg=BG2); pb_f.pack(fill="x", pady=(6,0))
        self._lbl(pb_f, "Progresso scansione")
        self.sc_prog_var = tk.DoubleVar(value=0)
        pb_bg = tk.Frame(pb_f, bg=BG3, highlightbackground=BORDER,
                         highlightthickness=1, height=18)
        pb_bg.pack(fill="x", pady=(0,4))
        self.sc_prog_fill = tk.Frame(pb_bg, bg=PINK, height=18)
        self.sc_prog_fill.place(x=0, y=0, height=18, relwidth=0)
        self.sc_prog_lbl = tk.Label(pb_f, text="0 / 0   0 attivi",
                                    fg=MUTED, bg=BG2, font=("Consolas",10),
                                    wraplength=270, anchor="w", justify="left")
        self.sc_prog_lbl.pack(anchor="w", fill="x")

        # ── Destra: tabella risultati ────────────────────────────
        tk.Label(right, text="DISPOSITIVI TROVATI", fg=PINK, bg=BG,
                 font=FHB).pack(anchor="w", padx=4)

        # Treeview per i risultati
        cols = ("ip","mac","produttore","hostname","netbios","porte","tipo")
        self.sc_tree = ttk.Treeview(right, columns=cols, show="headings",
                                     height=14, selectmode="browse")
        headers = [("ip","IP Address",120),("mac","MAC Address",145),
                   ("produttore","Produttore",130),("hostname","Hostname DNS",140),
                   ("netbios","Nome NetBIOS",130),("porte","Porte Aperte",160),
                   ("tipo","Tipo rilevato",140)]
        for col, txt, w in headers:
            self.sc_tree.heading(col, text=txt, anchor="w")
            self.sc_tree.column(col, width=w, minwidth=60)

        # Stile treeview
        sv = ttk.Style(self.root)
        sv.configure("Treeview", background=BG2, foreground=FG,
                      fieldbackground=BG2, font=FM, rowheight=24)
        sv.configure("Treeview.Heading", background="#0a0f16",
                      foreground=CYAN, font=FH)
        sv.map("Treeview", background=[("selected","#162030")],
               foreground=[("selected", WHITE)])

        # Scrollbar treeview
        sc_scroll = ttk.Scrollbar(right, orient="vertical",
                                   command=self.sc_tree.yview)
        self.sc_tree.configure(yscrollcommand=sc_scroll.set)
        sc_scroll.pack(side="right", fill="y")
        self.sc_tree.pack(fill="both", expand=True, padx=(4,0))

        # Click su riga → dettaglio
        self.sc_tree.bind("<<TreeviewSelect>>", self._scan_dettaglio)

        # Dettaglio dispositivo
        dk = tk.Frame(right, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        dk.pack(fill="x", pady=(4,0), padx=4)
        tk.Label(dk, text="DETTAGLIO DISPOSITIVO SELEZIONATO",
                 fg=PINK, bg=BG2, font=FH).pack(anchor="w", padx=8, pady=(5,2))
        self.sc_detail = scrolledtext.ScrolledText(dk, bg="#04070a", fg=FG,
                                                    font=FM, height=5, state="disabled",
                                                    highlightbackground=BORDER,
                                                    highlightthickness=1)
        self.sc_detail.tag_config("ok",   foreground=GREEN)
        self.sc_detail.tag_config("info", foreground=CYAN)
        self.sc_detail.tag_config("warn", foreground=ORANGE)
        self.sc_detail.tag_config("muted",foreground=MUTED)
        self.sc_detail.pack(fill="x", padx=6, pady=(0,6))

        # Contatori
        cf = tk.Frame(right, bg=BG2, highlightbackground=BORDER, highlightthickness=1)
        cf.pack(fill="x", padx=4, pady=(4,0))
        self.sc_count = {}
        for nm, key, col in [
            ("Host attivi","attivi",GREEN), ("Porte aperte","porte",PINK),
            ("Windows","windows",CYAN), ("Durata","durata",YELLOW)
        ]:
            c2 = tk.Frame(cf, bg=BG2); c2.pack(side="left", fill="x", expand=True, padx=8, pady=5)
            lv = tk.Label(c2, text="—", fg=col, bg=BG2, font=("Consolas",17,"bold")); lv.pack()
            tk.Label(c2, text=nm, fg=MUTED, bg=BG2, font=FM).pack()
            self.sc_count[key] = lv

        # Dati scanner
        self.sc_running    = False
        self.sc_risultati  = []
        self.sc_t0         = 0

    def _entry_inline(self, parent, default, w):
        e = tk.Entry(parent, bg=BG3, fg=GREEN, insertbackground=GREEN, font=FML,
                     bd=0, relief="flat",
                     highlightbackground=BORDER, highlightthickness=1,
                     highlightcolor=CYAN, width=w)
        e.insert(0, default); e.pack(side="left")
        return e

    def _scan_stop(self):
        self.sc_running = False
        self._st("Scansione interrotta.", ORANGE)

    def _scan_salva(self):
        if not self.sc_risultati:
            messagebox.showinfo("Nessun dato", "Esegui prima una scansione.")
            return
        nome = f"scanner_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Testo","*.txt"),("CSV","*.csv"),("Tutti","*.*")],
            initialfile=nome, title="Salva report scanner")
        if not path: return
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Lan/Gen/Utility v0.7 - Report Scanner Rete\n")
            f.write(f"Data: {datetime.datetime.now():%d/%m/%Y %H:%M:%S}\n")
            f.write("="*80 + "\n\n")
            for r in self.sc_risultati:
                f.write(f"IP:          {r.get('ip','—')}\n")
                f.write(f"MAC:         {r.get('mac','—')}\n")
                f.write(f"Produttore:  {r.get('produttore','—')}\n")
                f.write(f"Hostname:    {r.get('hostname','—')}\n")
                f.write(f"NetBIOS:     {r.get('netbios','—')}\n")
                f.write(f"Porte:       {r.get('porte','—')}\n")
                f.write(f"Banner:      {r.get('banner','—')}\n")
                f.write(f"Tipo:        {r.get('tipo','—')}\n")
                f.write("-"*60 + "\n")
        messagebox.showinfo("Salvato", f"Report salvato:\n{path}")

    def _scan_start(self):
        if self.sc_running:
            messagebox.showwarning("In esecuzione","Premi INTERROMPI prima.")
            return

        ip_from = self.sc_from.get().strip()
        ip_to   = self.sc_to.get().strip()

        try:
            start = list(map(int, ip_from.split(".")))
            end   = list(map(int, ip_to.split(".")))
            base  = ".".join(map(str, start[:3]))
            n_from= start[3]; n_to= end[3]
            if n_to < n_from: n_from, n_to = n_to, n_from
            ip_list = [f"{base}.{i}" for i in range(n_from, n_to+1)]
        except:
            messagebox.showerror("Errore", "Range IP non valido. Usa formato: 192.168.1.1")
            return

        n_threads = int(self.sc_threads.get().split()[0])
        timeout_ms= int(self.sc_timeout.get().split()[0])

        # Pulizia UI
        for item in self.sc_tree.get_children():
            self.sc_tree.delete(item)
        self.sc_risultati = []
        self.sc_running   = True
        self.sc_t0        = time.time()

        for k in self.sc_count:
            self.sc_count[k].config(text="—")
        self.sc_prog_fill.place(relwidth=0)
        self.sc_prog_lbl.config(text=f"0 / {len(ip_list)}  0 attivi")
        self._st(f"Scansione {ip_list[0]} - {ip_list[-1]} ({len(ip_list)} IP)...", PINK)

        threading.Thread(target=self._scan_thread,
                         args=(ip_list, n_threads, timeout_ms),
                         daemon=True).start()

    def _scan_thread(self, ip_list, n_threads, timeout_ms):
        totale  = len(ip_list)
        attivi  = 0
        done    = 0
        windows_count = 0
        porte_tot = 0
        lock    = threading.Lock()

        # ── FASE 1: Leggi ARP table (istantaneo) ──────────────────
        arp_map = {}  # ip -> mac
        if self.v_sc_arp.get():
            try:
                out = subprocess.check_output(_arp_cmd(), encoding=_encoding(),
                                              errors="replace",
                                              **_popen_flags())
                for line in out.splitlines():
                    if IS_WINDOWS:
                        # Formato Windows: 192.168.1.1   b8-27-eb-xx-xx-xx  dinamico
                        m = re.match(r"\s*(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})\s+", line)
                        if m:
                            ip  = m.group(1)
                            mac = m.group(2).replace("-",":").upper()
                            arp_map[ip] = mac
                    else:
                        # Formato Linux: 192.168.1.1 ether b8:27:eb:xx:xx:xx C eth0
                        m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+\S+\s+([0-9a-fA-F:]{17})", line)
                        if m:
                            ip  = m.group(1)
                            mac = m.group(2).upper()
                            arp_map[ip] = mac
            except: pass

        def scan_ip(ip):
            nonlocal done, attivi, windows_count, porte_tot
            if not self.sc_running: return

            risultato = {"ip": ip, "mac":"—","produttore":"—",
                         "hostname":"—","netbios":"—",
                         "porte":"—","banner":"—","tipo":"—"}

            # ── PING ──────────────────────────────────────────────
            alive = False
            if self.v_sc_ping.get():
                try:
                    cmd_ping = _ping_cmd(ip, count=1, timeout_ms=timeout_ms)
                    r = subprocess.run(
                        cmd_ping,
                        capture_output=True, text=True,
                        encoding=_encoding(), errors="replace",
                        timeout=timeout_ms/1000 + 1,
                        **_popen_flags())
                    alive = "TTL=" in r.stdout or "ttl=" in r.stdout.lower()
                except: pass
            else:
                # Se ping disabilitato, prova porta 80 per vedere se host vivo
                try:
                    s = socket.socket(); s.settimeout(0.3)
                    alive = s.connect_ex((ip, 80)) == 0
                    s.close()
                except: pass

            if not alive:
                with lock: done += 1
                self.root.after(0, lambda d=done: self._scan_update_progress(d, totale, attivi))
                return

            with lock: attivi += 1

            # ── MAC + PRODUTTORE ───────────────────────────────────
            mac = arp_map.get(ip, "—")
            if mac == "—":
                # Forza ARP con ping se non in tabella
                try:
                    subprocess.run(_ping_cmd(ip, count=1, timeout_ms=200),
                                   capture_output=True,
                                   timeout=1,
                                   **_popen_flags())
                    out2 = subprocess.check_output(_arp_cmd(ip),
                                                   encoding=_encoding(), errors="replace",
                                                   **_popen_flags())
                    m2 = re.search(r"([0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}", out2)
                    if m2:
                        mac = m2.group(0).replace("-",":").upper()
                except: pass

            risultato["mac"] = mac
            if mac != "—":
                risultato["produttore"] = oui_lookup(mac)

            # ── DNS INVERSO ───────────────────────────────────────
            if self.v_sc_dns.get():
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                    risultato["hostname"] = hostname
                except: pass

            # ── NBTSTAT ───────────────────────────────────────────
            if self.v_sc_nbt.get() and _nbtstat_available():
                try:
                    nb = subprocess.run(
                        ["nbtstat","-A",ip],
                        capture_output=True, text=True,
                        encoding=_encoding(), errors="replace",
                        timeout=3,
                        **_popen_flags())
                    nbt_out = nb.stdout
                    # Cerca nome NetBIOS (primo nome <00>)
                    m3 = re.search(r"([A-Z0-9_-]{1,15})\s+<00>\s+UNIQUE", nbt_out)
                    if m3:
                        risultato["netbios"] = m3.group(1).strip()
                        with lock: windows_count += 1
                except: pass
            elif self.v_sc_nbt.get() and not _nbtstat_available():
                # Su Linux proviamo nmblookup se disponibile
                try:
                    import shutil
                    if shutil.which("nmblookup"):
                        nb = subprocess.run(["nmblookup","-A",ip],
                                            capture_output=True, text=True,
                                            encoding="utf-8", errors="replace", timeout=3)
                        m3 = re.search(r"<00>\s+-\s+<GROUP>\s+\S+\s+(\S+)", nb.stdout)
                        if not m3:
                            m3 = re.search(r"(\S+)\s+<00>", nb.stdout)
                        if m3:
                            risultato["netbios"] = m3.group(1).strip()
                except: pass

            # ── PORTE ─────────────────────────────────────────────
            PORTE_TARGET = [
                (21,"FTP"),(22,"SSH"),(23,"Telnet"),(25,"SMTP"),
                (53,"DNS"),(80,"HTTP"),(110,"POP3"),(135,"RPC"),
                (139,"NetBIOS"),(143,"IMAP"),(443,"HTTPS"),
                (445,"SMB"),(554,"RTSP/Cam"),(3306,"MySQL"),
                (3389,"RDP"),(5000,"UPnP"),(5900,"VNC"),
                (8080,"HTTP-Alt"),(8443,"HTTPS-Alt"),(9100,"Stampa"),
            ]
            porte_aperte = []
            banner_info  = []

            if self.v_sc_ports.get():
                for porta, nome in PORTE_TARGET:
                    if not self.sc_running: break
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(0.3)
                        if s.connect_ex((ip, porta)) == 0:
                            porte_aperte.append(f"{porta}/{nome}")
                            with lock: porte_tot += 1
                            # Banner grab
                            if self.v_sc_banner.get():
                                try:
                                    if porta in [80, 8080, 8443]:
                                        s.send(b"GET / HTTP/1.0\r\nHost: "+ip.encode()+b"\r\n\r\n")
                                    elif porta == 21:
                                        pass  # FTP invia banner automaticamente
                                    elif porta == 22:
                                        pass  # SSH invia banner automaticamente
                                    s.settimeout(0.5)
                                    raw = s.recv(512)
                                    banner = raw.decode("utf-8","ignore").strip()[:80]
                                    banner = banner.replace("\n"," ").replace("\r","")
                                    if banner:
                                        banner_info.append(f"{porta}: {banner}")
                                except: pass
                        s.close()
                    except: pass

            if porte_aperte:
                risultato["porte"] = ", ".join(porte_aperte)
            if banner_info:
                risultato["banner"] = " | ".join(banner_info[:3])

            # ── TIPO STIMATO ──────────────────────────────────────
            tipo = self._stima_tipo(risultato)
            risultato["tipo"] = tipo

            self.sc_risultati.append(risultato)

            # Aggiorna UI nel thread principale
            self.root.after(0, lambda r=dict(risultato): self._scan_add_row(r))

            with lock:
                done += 1
            self.root.after(0, lambda d=done, a=attivi: self._scan_update_progress(d, totale, a))

        # Esegui con pool di thread
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as pool:
            futures = [pool.submit(scan_ip, ip) for ip in ip_list
                       if self.sc_running]
            concurrent.futures.wait(futures)

        if self.sc_running:
            elapsed = time.time() - self.sc_t0
            self.root.after(0, lambda a=attivi, pt=porte_tot, wc=windows_count, el=elapsed:
                            self._scan_done(a, pt, wc, el))
        self.sc_running = False

    def _stima_tipo(self, r):
        """Stima il tipo di dispositivo dai dati raccolti — logica prioritaria robusta."""
        prod     = r.get("produttore","").lower()
        hostname = r.get("hostname","").lower()
        netbios  = r.get("netbios","").lower()
        porte    = r.get("porte","")
        banner   = r.get("banner","").lower()
        ip       = r.get("ip","")

        # Estrai lista porte numeriche
        porte_nums = set()
        for p in porte.split(", "):
            num = p.split("/")[0].strip()
            if num.isdigit():
                porte_nums.add(num)

        # ── REGOLA 1: Banner SSH Dropbear → apparato embedded (router/NAS/cam) ──
        # Dropbear è usato quasi esclusivamente su Linux embedded (router, cam, NAS)
        if "dropbear" in banner:
            if "53" in porte_nums or "80" in porte_nums:
                return "Router / Gateway (Linux embedded)"
            return "Dispositivo Linux embedded (Dropbear SSH)"

        # ── REGOLA 2: Combinazione SSH + DNS + HTTP senza SMB/RDP → router/gateway ──
        # Nessun PC Windows ha DNS (53) aperto normalmente
        if "53" in porte_nums and "22" in porte_nums:
            if "445" not in porte_nums and "3389" not in porte_nums:
                if "80" in porte_nums or "443" in porte_nums:
                    return "Router / Gateway"
                return "Server DNS / Apparato di rete"

        # ── REGOLA 3: Solo Telnet + HTTP (no SMB/RDP) → apparato di rete ──
        if "23" in porte_nums and "80" in porte_nums:
            if "445" not in porte_nums and "3389" not in porte_nums and not netbios:
                return "Router / Switch (con web UI)"

        # ── REGOLA 4: Produttori SOLO di apparati di rete ─────────────────────
        ROUTER_VENDORS = ["cisco","netgear","tp-link","tplink","linksys","belkin",
                          "zyxel","mikrotik","ubiquiti","draytek","fritz","dlink",
                          "d-link","juniper","fortinet","openwrt","teltonika"]
        if any(v in prod for v in ROUTER_VENDORS):
            non_router = {"445","3389","5900","9100","25","110","143"}
            if not any(p in non_router for p in porte_nums):
                return "Router / Switch"

        # ── REGOLA 5: IP gateway tipici (.1 / .254) senza SMB/RDP e senza NetBIOS ──
        last_octet = ip.split(".")[-1] if ip else ""
        if last_octet in ("1","254","253") and "445" not in porte_nums and "3389" not in porte_nums:
            if not netbios:
                return "Router / Gateway"

        # ── REGOLA 6: Keyword hostname ──────────────────────────────────────────
        if any(x in hostname for x in ["router","gateway","fritz","modem","ap-","wap-",
                                        "switch","firewall","fortigate","pfsense","mikrotik"]):
            return "Router / Firewall"

        # ── REGOLA 7: Stampanti ─────────────────────────────────────────────────
        if "9100" in porte_nums:
            return "Stampante di rete"
        if any(x in prod for x in ["hp","epson","canon","brother","lexmark","xerox","ricoh","kyocera"]):
            if "9100" in porte_nums or "631" in porte_nums:
                return "Stampante / Periferica"

        # ── REGOLA 8: Telecamere IP ─────────────────────────────────────────────
        if "554" in porte_nums or "rtsp" in banner:
            return "Telecamera IP"
        if any(x in hostname for x in ["cam","ipcam","dvr","nvr","hikvision","dahua"]):
            return "Telecamera / DVR"

        # ── REGOLA 9: PC Windows — richiede almeno SMB/RDP o NetBIOS ───────────
        if "3389" in porte_nums:
            return "PC Windows (RDP attivo)"
        if "445" in porte_nums and netbios:
            return "PC / Server Windows"
        if netbios and "445" in porte_nums:
            return "PC / Server Windows"
        if netbios:
            return "PC Windows"
        # MAC da produttori Windows-only ma SOLO se ha anche SMB o RDP
        if any(x in prod for x in ["microsoft","dell","lenovo","intel","realtek","emulex"]):
            if "445" in porte_nums or "3389" in porte_nums:
                return "PC / Server Windows"

        # ── REGOLA 10: Server Linux / NAS ───────────────────────────────────────
        if "22" in porte_nums and ("80" in porte_nums or "443" in porte_nums):
            if "445" not in porte_nums:
                return "Server Linux / NAS"
        if "22" in porte_nums or "ssh" in banner:
            return "Server Linux / SSH"

        # ── REGOLA 11: Dispositivi specifici ───────────────────────────────────
        if "5900" in porte_nums:
            return "Dispositivo VNC"
        if "raspberry" in prod:
            return "Raspberry Pi"
        if "apple" in prod:
            return "Apple (Mac / iPhone / iPad)"
        if "samsung" in prod:
            if "9100" in porte_nums: return "Stampante Samsung"
            if "80" in porte_nums or "443" in porte_nums: return "SmartTV / Samsung"
            return "Smartphone Samsung"
        if any(x in prod for x in ["xiaomi","huawei","oppo","vivo","oneplus"]):
            return "Smartphone Android"
        if "google" in prod:
            return "Google Home / Chromecast"
        if any(x in prod for x in ["amazon","ring"]):
            return "Amazon Echo / Ring"
        if any(x in prod for x in ["vmware","qemu"]):
            return "Macchina Virtuale"

        # ── REGOLA 12: Fallback intelligente ────────────────────────────────────
        if "80" in porte_nums and "443" in porte_nums and "22" not in porte_nums:
            return "NAS / Server Web"
        if "80" in porte_nums and not netbios and "445" not in porte_nums:
            return "Dispositivo con web UI"
        if porte_nums:
            return "Dispositivo di rete attivo"
        return "Host attivo"


    def _scan_add_row(self, r):
        """Aggiunge riga nella treeview"""
        ip   = r["ip"]
        mac  = r["mac"]
        prod = r["produttore"]
        host = r["hostname"]
        nbt  = r["netbios"]
        port = r["porte"]
        tipo = r["tipo"]

        # Colore riga in base al tipo
        tag = "generic"
        if "Windows" in tipo or "PC" in tipo:  tag = "windows"
        elif "Router" in tipo:                  tag = "router"
        elif "Telecamera" in tipo:              tag = "camera"
        elif "Apple" in tipo:                   tag = "apple"
        elif "Server" in tipo or "Linux" in tipo: tag = "server"

        iid = self.sc_tree.insert("", "end",
            values=(ip, mac, prod, host if host!="—" else "",
                    nbt if nbt!="—" else "",
                    port if port!="—" else "",
                    tipo), tags=(tag,))

        # Colori per tipo
        self.sc_tree.tag_configure("windows", foreground=CYAN)
        self.sc_tree.tag_configure("router",  foreground=YELLOW)
        self.sc_tree.tag_configure("camera",  foreground=RED)
        self.sc_tree.tag_configure("apple",   foreground=PINK)
        self.sc_tree.tag_configure("server",  foreground=GREEN)
        self.sc_tree.tag_configure("generic", foreground=FG)

    def _scan_update_progress(self, done, totale, attivi):
        pct = done / totale if totale > 0 else 0
        self.sc_prog_fill.place(relwidth=pct)
        self.sc_prog_lbl.config(
            text=f"{done}/{totale}  {attivi} attivi")
        elapsed = time.time() - self.sc_t0
        self.sc_count["attivi"].config(text=str(attivi))
        self.sc_count["durata"].config(text=f"{elapsed:.0f}s")

    def _scan_done(self, attivi, porte_tot, windows, elapsed):
        self.sc_count["attivi"].config(text=str(attivi))
        self.sc_count["porte"].config(text=str(porte_tot))
        self.sc_count["windows"].config(text=str(windows))
        self.sc_count["durata"].config(text=f"{elapsed:.0f}s")
        self.sc_prog_fill.place(relwidth=1.0)
        self._st(f"Scansione completata: {attivi} host attivi in {elapsed:.0f} secondi.", GREEN)

    def _scan_dettaglio(self, event):
        sel = self.sc_tree.selection()
        if not sel: return
        vals = self.sc_tree.item(sel[0], "values")
        if not vals: return
        ip = vals[0]
        # Trova il risultato completo
        r = next((x for x in self.sc_risultati if x.get("ip")==ip), None)
        if not r: return

        self.sc_detail.config(state="normal")
        self.sc_detail.delete("1.0","end")

        def ins(t, txt, tag=""):
            self.sc_detail.insert("end", t, "info")
            self.sc_detail.insert("end", f"{txt}\n", tag if tag else ())

        ins("IP Indirizzo:   ", r.get("ip","—"), "ok")
        ins("MAC Address:    ", r.get("mac","—"), "warn")
        ins("Produttore:     ", r.get("produttore","—"), "warn")
        ins("Hostname DNS:   ", r.get("hostname","—"))
        ins("Nome NetBIOS:   ", r.get("netbios","—"), "ok" if r.get("netbios","—")!="—" else "muted")
        ins("Porte Aperte:   ", r.get("porte","—"), "ok" if r.get("porte","—")!="—" else "muted")
        ins("Banner servizi: ", r.get("banner","—"), "warn" if r.get("banner","—")!="—" else "muted")

        self.sc_detail.config(state="disabled")

    def _info_run(self,cmd):
        if self.running: messagebox.showwarning("Occupato","Premi INTERROMPI prima."); return
        self._clr(self.t_info)
        Q.put((self.t_info,f"Comando: {' '.join(cmd)}","info"))
        Q.put((self.t_info,f"  {datetime.datetime.now():%H:%M:%S}","muted"))
        Q.put((self.t_info,"-"*55,"muted"))
        self._st(f"{' '.join(cmd)}",CYAN)
        self._run(cmd,self.t_info,lambda t:(self._w(t,"Completato.","ok"),self._st("Pronto.",MUTED)))


    # ════ PING MULTIPLO LAN ═══════════════════════════════════════
    def _ping_multiplo_open(self):
        """Finestra con ping simultaneo verso 4 gateway LAN predefiniti."""
        HOSTS = [
            ("10.26.84.1", "Rete 26/84"),
            ("10.28.38.1", "Rete 28/38"),
            ("10.27.37.1", "Rete 27/37"),
            ("10.26.36.1", "Rete 26/36"),
        ]
        win = tk.Toplevel(self.root)
        win.title("🖧  Ping Multiplo LAN")
        win.configure(bg=BG)
        win.geometry("800x560")
        win.resizable(True, True)

        hf = tk.Frame(win, bg="#001830"); hf.pack(fill="x")
        tk.Label(hf, text="🖧  PING MULTIPLO LAN",
                 font=("Segoe UI",16,"bold"), fg=CYAN, bg="#001830").pack(side="left", padx=14, pady=8)
        tk.Label(hf, text="Ping simultaneo ai 4 gateway di rete  —  Audio: " +
                 ("ON" if self.ping_audio.get() else "OFF"),
                 font=("Segoe UI",9), fg=MUTED, bg="#001830").pack(side="left", padx=4)
        tk.Frame(win, bg=CYAN, height=2).pack(fill="x")

        state = {ip: {"running": False, "proc": None,
                      "ok": 0, "persi": 0, "mn": None, "mx": None, "somma": 0, "vals": []}
                 for ip,_ in HOSTS}

        grid = tk.Frame(win, bg=BG); grid.pack(fill="both", expand=True, padx=8, pady=8)
        grid.columnconfigure(0, weight=1); grid.columnconfigure(1, weight=1)
        grid.rowconfigure(0, weight=1);    grid.rowconfigure(1, weight=1)
        cards = {}

        for idx, (ip, label) in enumerate(HOSTS):
            row, col = divmod(idx, 2)
            card = tk.Frame(grid, bg=BG2, highlightbackground=BORDER, highlightthickness=2)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            hdr = tk.Frame(card, bg="#000d1a"); hdr.pack(fill="x")
            led = tk.Label(hdr, text="●", fg=MUTED, bg="#000d1a", font=("Consolas",14))
            led.pack(side="left", padx=8, pady=4)
            tk.Label(hdr, text=label, fg=WHITE, bg="#000d1a",
                     font=("Segoe UI",11,"bold")).pack(side="left")
            tk.Label(hdr, text=ip, fg=MUTED, bg="#000d1a",
                     font=("Consolas",10)).pack(side="left", padx=8)
            stato_lbl = tk.Label(hdr, text="—", fg=MUTED, bg="#000d1a",
                                 font=("Segoe UI",10,"bold"))
            stato_lbl.pack(side="right", padx=10)

            cnt_f = tk.Frame(card, bg=BG2); cnt_f.pack(fill="x", padx=8, pady=6)
            lbls = {}
            for nm, key, c_ in [("MIN","mn",GREEN),("MED","av",CYAN),
                                  ("MAX","mx",ORANGE),("PERSI","lo",RED)]:
                cell = tk.Frame(cnt_f, bg=BG3); cell.pack(side="left", fill="x", expand=True, padx=2)
                tk.Label(cell, text=nm, fg=MUTED, bg=BG3, font=("Consolas",8)).pack(pady=(3,0))
                lv = tk.Label(cell, text="—", fg=c_, bg=BG3, font=("Consolas",16,"bold")); lv.pack()
                tk.Label(cell, text="ms" if key!="lo" else "pkt", fg=MUTED, bg=BG3,
                         font=("Consolas",7)).pack(pady=(0,3))
                lbls[key] = lv

            cvs = tk.Canvas(card, bg="#04070a", height=70, highlightthickness=0)
            cvs.pack(fill="x", padx=6, pady=(0,6))

            log = scrolledtext.ScrolledText(card, bg="#04070a", fg=FG, font=("Consolas",9),
                                             height=4, state="disabled",
                                             highlightbackground=BORDER, highlightthickness=1)
            log.tag_config("ok",  foreground=GREEN)
            log.tag_config("err", foreground=RED)
            log.tag_config("warn",foreground=ORANGE)
            log.pack(fill="both", expand=True, padx=6, pady=(0,6))
            cards[ip] = {"led": led, "stato": stato_lbl, "lbls": lbls,
                          "cvs": cvs, "log": log, "card": card}

        def _log_w(ip, txt, tag=""):
            w = cards[ip]["log"]
            w.config(state="normal")
            w.insert("end", txt+"\n", tag if tag else ())
            w.see("end"); w.config(state="disabled")

        def _upd_card(ip):
            s = state[ip]; c = cards[ip]
            ok_ = s["ok"]; ps_ = s["persi"]
            mn_ = s["mn"]; mx_ = s["mx"]
            av_ = (s["somma"]//ok_) if ok_>0 else None
            def _col(v):
                if v is None: return MUTED
                return GREEN if v<50 else (ORANGE if v<200 else RED)
            c["lbls"]["mn"].config(text=(str(mn_) if mn_ is not None else "—"), fg=_col(mn_))
            c["lbls"]["av"].config(text=(str(av_) if av_ is not None else "—"), fg=_col(av_))
            c["lbls"]["mx"].config(text=(str(mx_) if mx_ is not None else "—"), fg=_col(mx_))
            c["lbls"]["lo"].config(text=str(ps_),
                                   fg=(GREEN if ps_==0 else (ORANGE if ps_<3 else RED)))
            tot_ = ok_+ps_; pct_ = int(ps_/tot_*100) if tot_>0 else 0
            if ps_==0 and ok_>0:
                c["led"].config(fg=GREEN)
                c["stato"].config(text=f"OK  ({pct_}% persi)", fg=GREEN)
                c["card"].config(highlightbackground=GREEN)
            elif ok_>0:
                c["led"].config(fg=ORANGE)
                c["stato"].config(text=f"⚠ {pct_}% persi", fg=ORANGE)
                c["card"].config(highlightbackground=ORANGE)
            else:
                c["led"].config(fg=RED)
                c["stato"].config(text="KO", fg=RED)
                c["card"].config(highlightbackground=RED)
            self._plot_rtt(c["cvs"], s["vals"][-40:])

        def _ping_thr(ip):
            cmd = _ping_cmd(ip, infinite=True)
            s   = state[ip]
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, encoding=_encoding(), errors="replace",
                                     **_popen_flags())
                s["proc"] = p
                for raw in p.stdout:
                    if not s["running"]: break
                    line = raw.rstrip()
                    if not line: continue
                    ll = line.lower()
                    v = self._parse_rtt(line)
                    if v is not None:
                        s["ok"]+=1; s["somma"]+=v
                        s["mn"] = v if s["mn"] is None else min(s["mn"],v)
                        s["mx"] = v if s["mx"] is None else max(s["mx"],v)
                        s["vals"].append(v)
                        t_ = "ok" if v<50 else ("warn" if v<200 else "err")
                        win.after(0, lambda _ip=ip: _upd_card(_ip))
                        win.after(0, lambda l=f"RTT {v}ms", t=t_, _ip=ip: _log_w(_ip,l,t))
                        if self.ping_audio.get(): self._beep("ok")
                    elif any(x in ll for x in ["scaduta","timeout","unreachable","timed out"]):
                        s["persi"]+=1; s["vals"].append(None)
                        win.after(0, lambda _ip=ip: _upd_card(_ip))
                        win.after(0, lambda _ip=ip: _log_w(_ip,"TIMEOUT","err"))
                        if self.ping_audio.get(): self._beep("err")
                p.wait()
            except Exception as ex:
                win.after(0, lambda: _log_w(ip, f"ERRORE: {ex}", "err"))
            finally:
                s["proc"]=None; s["running"]=False

        def start_all():
            for ip,_ in HOSTS:
                s = state[ip]
                if s["running"]: continue
                s.update({"running":True,"ok":0,"persi":0,"mn":None,"mx":None,"somma":0,"vals":[]})
                cards[ip]["led"].config(fg=CYAN)
                cards[ip]["stato"].config(text="In corso…", fg=CYAN)
                cards[ip]["card"].config(highlightbackground=CYAN)
                for k in ("mn","av","mx","lo"): cards[ip]["lbls"][k].config(text="—")
                threading.Thread(target=_ping_thr, args=(ip,), daemon=True).start()
            btn_s.config(state="disabled"); btn_stop.config(state="normal")

        def stop_all():
            for ip,_ in HOSTS:
                s = state[ip]; s["running"]=False
                if s["proc"]:
                    try: s["proc"].terminate()
                    except: pass
            btn_s.config(state="normal"); btn_stop.config(state="disabled")

        win.protocol("WM_DELETE_WINDOW", lambda: (stop_all(), win.destroy()))

        bf = tk.Frame(win, bg=BG); bf.pack(fill="x", padx=8, pady=(0,8))
        btn_s = tk.Button(bf, text="▶  AVVIA TUTTI", command=start_all,
                          bg="#001530", fg=CYAN, font=("Segoe UI",13,"bold"),
                          activebackground="#002a50", activeforeground=WHITE,
                          bd=2, relief="groove", cursor="hand2", pady=8)
        btn_s.pack(side="left", fill="x", expand=True, padx=(0,4))
        btn_stop = tk.Button(bf, text="⬛  INTERROMPI TUTTI", command=stop_all,
                             bg=BG2, fg=RED, font=("Segoe UI",13,"bold"),
                             activebackground="#162030", activeforeground=WHITE,
                             bd=2, relief="groove", cursor="hand2", pady=8, state="disabled")
        btn_stop.pack(side="left", fill="x", expand=True, padx=(4,0))
        win.after(300, start_all)


    # ════ TAB MESSAGGI LAN ════════════════════════════════════════
    def _tab_messaggi(self, f):
        left  = self._panel(f, "MESSAGGI LAN", CYAN, w=310)
        right = tk.Frame(f, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(0,4), pady=4)

        # ── Modalità destinazione ─────────────────────────────────
        self._lbl(left, "Modalità destinazione")
        self.msg_mode = tk.StringVar(value="single")
        for val, lbl in [("single","IP singolo / hostname"),
                          ("range",  "Range IP  (es: 10.28.38.2–255)"),
                          ("broadcast","Broadcast subnet")]:
            tk.Radiobutton(left, text=lbl, variable=self.msg_mode, value=val,
                           fg=CYAN, bg=BG2, activebackground=BG2,
                           selectcolor=BG3, font=FM, cursor="hand2",
                           anchor="w", command=self._msg_mode_switch).pack(fill="x", pady=1)

        self.msg_single_frame = tk.Frame(left, bg=BG2)
        self.msg_single_frame.pack(fill="x")
        self._lbl(self.msg_single_frame, "IP / hostname destinatario")
        self.msg_ip = self._entry(self.msg_single_frame, "10.28.38.2")
        self._tooltip(self.msg_ip,
            "IP DESTINATARIO\nEs: 10.28.38.15  oppure  NOMEUTENTE\n"
            "Il servizio Messenger / Terminal Services\ndeve essere attivo sul PC di destinazione.")

        self.msg_range_frame = tk.Frame(left, bg=BG2)
        rf = tk.Frame(self.msg_range_frame, bg=BG2); rf.pack(fill="x", padx=4)
        tk.Label(rf, text="Da IP:", fg=LABEL, bg=BG2, font=FH).grid(row=0,column=0,sticky="w",pady=2)
        self.msg_range_start = tk.Entry(rf, bg=BG3, fg=GREEN, insertbackground=GREEN,
                                         font=FM, highlightbackground=BORDER, highlightthickness=1)
        self.msg_range_start.insert(0,"10.28.38.2")
        self.msg_range_start.grid(row=0,column=1,sticky="ew",padx=(6,0),pady=2)
        tk.Label(rf, text="A IP:", fg=LABEL, bg=BG2, font=FH).grid(row=1,column=0,sticky="w",pady=2)
        self.msg_range_end = tk.Entry(rf, bg=BG3, fg=GREEN, insertbackground=GREEN,
                                       font=FM, highlightbackground=BORDER, highlightthickness=1)
        self.msg_range_end.insert(0,"10.28.38.26")
        self.msg_range_end.grid(row=1,column=1,sticky="ew",padx=(6,0),pady=2)
        rf.columnconfigure(1, weight=1)
        self._tooltip(rf,"RANGE IP\nMax 25 destinatari per invio.\nEs: da 10.28.38.2 a 10.28.38.26")

        self.msg_bc_frame = tk.Frame(left, bg=BG2)
        self._lbl(self.msg_bc_frame, "Indirizzo broadcast subnet")
        self.msg_bc_ip = self._entry(self.msg_bc_frame, "10.28.38.255")

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=5)
        self._lbl(left, "Testo del messaggio")
        self.msg_text = scrolledtext.ScrolledText(
            left, bg=BG3, fg=GREEN, insertbackground=GREEN,
            font=FM, height=4, bd=0,
            highlightbackground=CYAN, highlightthickness=1, wrap="word")
        self.msg_text.pack(fill="x", padx=4, pady=(0,4))
        self.msg_text.insert("end","Avviso: la rete sarà temporaneamente interrotta per manutenzione.")

        # Messaggi rapidi
        tk.Label(left, text="Messaggi rapidi", fg=MUTED, bg=BG2, font=("Consolas",9)).pack(anchor="w",padx=4)
        for lbl_txt, testo in [
            ("🔧 Manutenzione", "Avviso: la rete sarà temporaneamente interrotta per manutenzione programmata. Salvare il lavoro."),
            ("🔴 Riavvio",      "ATTENZIONE: il sistema verrà riavviato tra 5 minuti. Salvare immediatamente tutti i file aperti."),
            ("✅ Ripristino",   "La rete è stata ripristinata. Tutti i servizi sono nuovamente disponibili."),
            ("📢 Comunicazione","Comunicazione di servizio: si prega di contattare il supporto tecnico. Grazie."),
        ]:
            b = tk.Button(left, text=lbl_txt, font=("Consolas",10),
                          bg=BG3, fg=FG, activebackground="#1a2a3a", activeforeground=WHITE,
                          bd=1, relief="groove", cursor="hand2", anchor="w",
                          command=lambda t=testo: (self.msg_text.delete("1.0","end"),
                                                   self.msg_text.insert("end",t)))
            b.pack(fill="x", padx=4, pady=1)
            b.bind("<Enter>", lambda e,bt=b: bt.config(bg="#1a2a3a",fg=CYAN))
            b.bind("<Leave>", lambda e,bt=b: bt.config(bg=BG3,fg=FG))

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=4)
        self.msg_ricevuta = tk.BooleanVar(value=True)
        tk.Checkbutton(left, text="  Richiedi ricevuta di lettura  (/v)",
                       variable=self.msg_ricevuta,
                       fg=CYAN, bg=BG2, activebackground=BG2,
                       selectcolor=BG3, font=FH, anchor="w").pack(fill="x", padx=4, pady=2)

        df = tk.Frame(left, bg=BG2); df.pack(fill="x", padx=4, pady=(0,2))
        tk.Label(df, text="Ritardo tra invii (ms):", fg=MUTED, bg=BG2, font=FM).pack(side="left")
        self.msg_delay = tk.IntVar(value=500)
        delay_lbl = tk.Label(df, text="500", fg=ORANGE, bg=BG2, font=FMB); delay_lbl.pack(side="right")
        tk.Scale(left, from_=100, to=3000, orient="horizontal",
                 variable=self.msg_delay, bg=BG2, fg=ORANGE, troughcolor=BG3,
                 highlightthickness=0, sliderrelief="flat", length=240,
                 command=lambda v: delay_lbl.config(text=str(int(float(v))))).pack(fill="x",padx=4,pady=(0,4))

        self._btn_tip(left, "📤  INVIA MESSAGGIO", self._msg_invia, GREEN,
            "INVIA MESSAGGIO\n"
            "Invia via 'msg' di Windows.\n"
            "Range: max 25 IP simultanei.\n"
            "Richiede Messenger / Terminal Services attivo.")
        self._btn_tip(left, "⬛  INTERROMPI INVIO", self._msg_ferma, RED,
            "INTERROMPI\nFerma l'invio in corso.")

        # ── Pannello destra: dominio + log ────────────────────────
        dh = tk.Frame(right, bg=BG2, highlightbackground=CYAN, highlightthickness=1)
        dh.pack(fill="x", pady=(0,4))
        tk.Label(dh, text="👤  CONTROLLO UTENTI DI DOMINIO",
                 fg=CYAN, bg=BG2, font=FHB).pack(anchor="w", padx=10, pady=(8,2))
        tk.Label(dh, text="Cerca utente per nome, cognome o username di dominio.",
                 fg=MUTED, bg=BG2, font=FM).pack(anchor="w", padx=10, pady=(0,4))

        sf2 = tk.Frame(dh, bg=BG2); sf2.pack(fill="x", padx=10, pady=(0,6))
        sf2.columnconfigure(1, weight=1); sf2.columnconfigure(3, weight=1)
        tk.Label(sf2, text="Nome:", fg=LABEL, bg=BG2, font=FH).grid(row=0,column=0,sticky="w",pady=2)
        self.dom_nome = tk.Entry(sf2, bg=BG3, fg=GREEN, insertbackground=GREEN,
                                  font=FML, highlightbackground=BORDER, highlightthickness=1)
        self.dom_nome.grid(row=0,column=1,sticky="ew",padx=(6,16),pady=2)
        tk.Label(sf2, text="Cognome:", fg=LABEL, bg=BG2, font=FH).grid(row=0,column=2,sticky="w",pady=2)
        self.dom_cognome = tk.Entry(sf2, bg=BG3, fg=GREEN, insertbackground=GREEN,
                                     font=FML, highlightbackground=BORDER, highlightthickness=1)
        self.dom_cognome.grid(row=0,column=3,sticky="ew",padx=(6,0),pady=2)
        tk.Label(sf2, text="Username:", fg=LABEL, bg=BG2, font=FH).grid(row=1,column=0,sticky="w",pady=2)
        self.dom_user = tk.Entry(sf2, bg=BG3, fg=GREEN, insertbackground=GREEN,
                                  font=FML, highlightbackground=BORDER, highlightthickness=1)
        self.dom_user.grid(row=1,column=1,sticky="ew",padx=(6,16),pady=2)
        tk.Label(sf2, text="Dominio:", fg=LABEL, bg=BG2, font=FH).grid(row=1,column=2,sticky="w",pady=2)
        self.dom_dominio = tk.Entry(sf2, bg=BG3, fg=GREEN, insertbackground=GREEN,
                                     font=FML, highlightbackground=BORDER, highlightthickness=1)
        self.dom_dominio.insert(0,"ARMACC")
        self.dom_dominio.grid(row=1,column=3,sticky="ew",padx=(6,0),pady=2)

        bf2 = tk.Frame(dh, bg=BG2); bf2.pack(fill="x", padx=10, pady=(0,8))
        tk.Button(bf2, text="🔍  CERCA UTENTE", command=self._dom_cerca,
                  bg="#001530", fg=CYAN, font=("Segoe UI",12,"bold"),
                  activebackground="#002a50", activeforeground=WHITE,
                  bd=2, relief="groove", cursor="hand2", pady=6).pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(bf2, text="👤  UTENTI CONNESSI", command=self._dom_connessi,
                  bg=BG2, fg=GREEN, font=("Segoe UI",12,"bold"),
                  activebackground="#162030", activeforeground=WHITE,
                  bd=2, relief="groove", cursor="hand2", pady=6).pack(side="left", fill="x", expand=True, padx=(4,0))

        tk.Label(right, text="LOG INVIO MESSAGGI", fg=CYAN, bg=BG, font=FHB).pack(anchor="w", padx=4)
        self.msg_log = scrolledtext.ScrolledText(
            right, bg="#04070a", fg=FG, font=FML, bd=0, relief="flat",
            highlightbackground=BORDER, highlightthickness=1,
            wrap="word", height=8, state="disabled")
        for t_,c_ in [("ok",GREEN),("err",RED),("warn",ORANGE),("info",CYAN),("muted",MUTED)]:
            self.msg_log.tag_config(t_, foreground=c_)
        self.msg_log.pack(fill="both", expand=True, padx=4, pady=(0,4))
        self._msg_log("Pronto. Configura e premi INVIA.", "muted")

        tk.Label(right, text="RISULTATI DOMINIO", fg=CYAN, bg=BG, font=FHB).pack(anchor="w", padx=4)
        self.dom_log = scrolledtext.ScrolledText(
            right, bg="#04070a", fg=FG, font=FM, bd=0, relief="flat",
            highlightbackground=BORDER, highlightthickness=1,
            wrap="word", height=6, state="disabled")
        for t_,c_ in [("ok",GREEN),("err",RED),("warn",ORANGE),("info",CYAN),("muted",MUTED)]:
            self.dom_log.tag_config(t_, foreground=c_)
        self.dom_log.pack(fill="both", expand=True, padx=4, pady=(0,4))
        self._dom_log("Inserisci nome/cognome o username e premi CERCA UTENTE.", "muted")

        self._msg_running = False
        self._msg_proc    = None

    def _msg_mode_switch(self):
        mode = self.msg_mode.get()
        for fr in [self.msg_single_frame, self.msg_range_frame, self.msg_bc_frame]:
            fr.pack_forget()
        if mode == "single":    self.msg_single_frame.pack(fill="x")
        elif mode == "range":   self.msg_range_frame.pack(fill="x")
        else:                   self.msg_bc_frame.pack(fill="x")

    def _msg_log(self, txt, tag=""):
        w = self.msg_log; w.config(state="normal")
        w.insert("end", f"{datetime.datetime.now():%H:%M:%S}  {txt}\n", tag if tag else ())
        w.see("end"); w.config(state="disabled")

    def _dom_log(self, txt, tag=""):
        w = self.dom_log; w.config(state="normal")
        w.insert("end", txt+"\n", tag if tag else ())
        w.see("end"); w.config(state="disabled")

    def _msg_ferma(self):
        self._msg_running = False
        if self._msg_proc:
            try: self._msg_proc.terminate()
            except: pass
            self._msg_proc = None
        self._msg_log("Invio interrotto.", "warn")

    def _msg_invia(self):
        if self._msg_running:
            messagebox.showwarning("Occupato","Invio già in corso."); return
        if not IS_WINDOWS:
            messagebox.showerror("Non supportato","Il comando 'msg' è disponibile solo su Windows."); return
        testo = self.msg_text.get("1.0","end").strip()
        if not testo:
            messagebox.showerror("Errore","Inserisci il testo del messaggio."); return
        mode = self.msg_mode.get(); verbose = self.msg_ricevuta.get(); delay = self.msg_delay.get()
        targets = []
        if mode == "single":
            ip = self.msg_ip.get().strip()
            if not ip: messagebox.showerror("Errore","Inserisci IP o hostname."); return
            targets = [ip]
        elif mode == "range":
            try:
                start = ipaddress.IPv4Address(self.msg_range_start.get().strip())
                end   = ipaddress.IPv4Address(self.msg_range_end.get().strip())
                if start > end: messagebox.showerror("Errore","IP iniziale > IP finale."); return
                targets = [str(ipaddress.IPv4Address(i)) for i in range(int(start),int(end)+1)]
                if len(targets) > 25:
                    if not messagebox.askyesno("Attenzione",
                        f"Stai per inviare a {len(targets)} destinatari. Continuare?"):
                        return
            except Exception as ex:
                messagebox.showerror("Errore IP", str(ex)); return
        else:
            bc = self.msg_bc_ip.get().strip()
            if not bc: messagebox.showerror("Errore","Inserisci broadcast."); return
            targets = [bc]
        self._msg_running = True
        self._msg_log(f"Invio a {len(targets)} destinatari  delay={delay}ms  verbose={verbose}", "info")
        self._msg_log(f"Testo: «{testo[:80]}{'…' if len(testo)>80 else ''}»", "muted")
        self._msg_log("─"*50, "muted")
        def _thr():
            ok_c = 0; err_c = 0
            for ip in targets:
                if not self._msg_running: break
                cmd = ["msg","*",f"/server:{ip}"] + (["/v"] if verbose else []) + [testo]
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True,
                                       encoding=_encoding(), errors="replace",
                                       timeout=8, **_popen_flags())
                    out = (r.stdout+r.stderr).strip()
                    if r.returncode == 0:
                        ok_c += 1; tag_ = "ok"
                        esito = f"✔  {ip}  — Inviato" + (f"  [{out[:60]}]" if out and verbose else "")
                    else:
                        err_c += 1; tag_ = "err"
                        esito = f"✗  {ip}  — {out[:80] if out else 'Host non raggiungibile'}"
                except subprocess.TimeoutExpired:
                    err_c+=1; tag_="err"; esito=f"✗  {ip}  — Timeout"
                except Exception as ex:
                    err_c+=1; tag_="err"; esito=f"✗  {ip}  — {ex}"
                self.root.after(0, lambda e=esito,t=tag_: self._msg_log(e,t))
                time.sleep(delay/1000.0)
            def _fine():
                self._msg_log("─"*50,"muted")
                self._msg_log(f"COMPLETATO — OK:{ok_c}  Errori:{err_c}","ok" if err_c==0 else "warn")
                self._msg_running = False
            self.root.after(0, _fine)
        threading.Thread(target=_thr, daemon=True).start()

    def _dom_cerca(self):
        nome=self.dom_nome.get().strip(); cognome=self.dom_cognome.get().strip()
        username=self.dom_user.get().strip()
        if not nome and not cognome and not username:
            messagebox.showwarning("Attenzione","Inserisci almeno uno tra Nome, Cognome o Username."); return
        self.dom_log.config(state="normal"); self.dom_log.delete("1.0","end"); self.dom_log.config(state="disabled")
        self._dom_log(f"Ricerca: nome='{nome}'  cognome='{cognome}'  user='{username}'","info")
        self._dom_log("─"*50,"muted")
        def _thr():
            res = []
            if username:
                cmd = ["net","user",username,"/domain"] if IS_WINDOWS else ["id",username]
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True,
                                       encoding=_encoding(), errors="replace",
                                       timeout=15, **_popen_flags())
                    res.append(("ok",f"Risultato per '{username}':"))
                    for l in (r.stdout+r.stderr).splitlines():
                        if l.strip(): res.append(("","  "+l))
                except Exception as ex:
                    res.append(("err",f"Errore: {ex}"))
            elif IS_WINDOWS and (nome or cognome):
                parts = []
                if nome:    parts.append(f"(givenName={nome}*)")
                if cognome: parts.append(f"(sn={cognome}*)")
                filt = "(&"+"".join(parts)+")" if len(parts)>1 else parts[0]
                try:
                    r = subprocess.run(["dsquery","user","-filter",filt,"-limit","25"],
                                       capture_output=True, text=True,
                                       encoding=_encoding(), errors="replace",
                                       timeout=20, **_popen_flags())
                    out = r.stdout.strip()
                    if out:
                        res.append(("ok",f"Account trovati:"))
                        for dn in out.splitlines():
                            if dn.strip(): res.append(("info","  "+dn.strip().strip('"')))
                    else:
                        res.append(("warn","Nessun utente trovato."))
                except FileNotFoundError:
                    res.append(("warn","dsquery non disponibile — uso 'net user /domain':"))
                    try:
                        r = subprocess.run(["net","user","/domain"], capture_output=True,
                                           text=True, encoding=_encoding(), errors="replace",
                                           timeout=20, **_popen_flags())
                        cerca = (nome+" "+cognome).lower().strip()
                        trovati = [l for l in r.stdout.splitlines()
                                   if any(p in l.lower() for p in cerca.split() if p)]
                        if trovati:
                            for t in trovati: res.append(("info","  "+t.strip()))
                        else:
                            res.append(("warn","Nessuna corrispondenza."))
                    except Exception as ex2:
                        res.append(("err",f"Errore: {ex2}"))
                except Exception as ex:
                    res.append(("err",f"Errore: {ex}"))
            else:
                res.append(("warn","Inserisci username per ricerca su sistemi non Windows."))
            def _show():
                for tag_,txt in res: self._dom_log(txt,tag_)
                self._dom_log("─"*50,"muted")
            self.root.after(0, _show)
        threading.Thread(target=_thr, daemon=True).start()

    def _dom_connessi(self):
        self.dom_log.config(state="normal"); self.dom_log.delete("1.0","end"); self.dom_log.config(state="disabled")
        self._dom_log("Ricerca utenti connessi in rete…","info"); self._dom_log("─"*50,"muted")
        def _thr():
            res = []
            if IS_WINDOWS:
                for ip in ["10.26.84.1","10.28.38.1","10.27.37.1","10.26.36.1"]:
                    try:
                        r = subprocess.run(["query","user",f"/server:{ip}"],
                                           capture_output=True, text=True,
                                           encoding=_encoding(), errors="replace",
                                           timeout=8, **_popen_flags())
                        out = r.stdout.strip()
                        if out and r.returncode==0:
                            res.append(("ok",f"Host {ip}:"))
                            for l in out.splitlines():
                                if l.strip(): res.append(("info","  "+l))
                        else:
                            res.append(("muted",f"Host {ip}: nessun utente o non raggiungibile."))
                    except Exception as ex:
                        res.append(("err",f"Host {ip}: {ex}"))
            else:
                try:
                    r = subprocess.run(["who"], capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", timeout=5)
                    res.append(("ok","Utenti locali (who):"))
                    for l in r.stdout.splitlines():
                        if l.strip(): res.append(("info","  "+l))
                except Exception as ex:
                    res.append(("err",f"Errore: {ex}"))
            def _show():
                for tag_,txt in res: self._dom_log(txt,tag_)
                self._dom_log("─"*50,"muted")
            self.root.after(0,_show)
        threading.Thread(target=_thr, daemon=True).start()


if __name__ == "__main__":
    try:
        app = LANTesterApp()
        app.root.mainloop()
    except Exception as e:
        # Mostra l'errore in una finestra invece di chiudersi silenziosamente
        import traceback
        err = traceback.format_exc()
        try:
            root = tk.Tk()
            root.title("Errore avvio LAN Tester")
            root.configure(bg="#1a0010")
            root.geometry("700x400")
            tk.Label(root, text="ERRORE ALL'AVVIO", font=("Consolas",16,"bold"),
                     fg="#ff3355", bg="#1a0010").pack(pady=10)
            t = scrolledtext.ScrolledText(root, bg="#04070a", fg="#ff8888",
                                           font=("Consolas",11), wrap="word")
            t.pack(fill="both", expand=True, padx=10, pady=(0,10))
            t.insert("end", err)
            t.config(state="disabled")
            tk.Button(root, text="CHIUDI", command=root.destroy,
                      bg="#330000", fg="white", font=("Segoe UI",12,"bold"),
                      cursor="hand2", padx=20, pady=8).pack(pady=8)
            root.mainloop()
        except:
            # Fallback: scrivi su file
            with open("lan_tester_errore.txt", "w") as f:
                f.write(err)
            input(f"ERRORE: {e}\nDettagli salvati in lan_tester_errore.txt\nPremi INVIO per chiudere...")
