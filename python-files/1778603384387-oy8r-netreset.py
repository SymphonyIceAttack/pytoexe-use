#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetReset v2.0 — Modern Windows Network Tool
GUI: CustomTkinter | Theme: Catppuccin Mocha (Dark)

Компиляция в .exe (без консоли):
    pip install customtkinter pyinstaller
    pyinstaller --onefile --noconsole --name "NetReset" netreset.py
"""

import subprocess
import sys
import ctypes
import re
import threading
import time
from dataclasses import dataclass, field
from typing import List, Tuple
from datetime import datetime


# ── Авто-установка ────────────────────────────────────────────────────────────
def _ensure_deps():
    for pkg in ["customtkinter"]:
        try:
            __import__(pkg)
        except ImportError:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg, "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

_ensure_deps()

import customtkinter as ctk


# ── Palette: Catppuccin Mocha ─────────────────────────────────────────────────
BG       = "#1e1e2e"
MANTLE   = "#181825"
CRUST    = "#11111b"
S0       = "#313244"   # surface0  – card bg
S1       = "#45475a"   # surface1  – border / separator
S2       = "#585b70"   # surface2  – hover
TEXT     = "#cdd6f4"
SUB1     = "#bac2de"
SUB0     = "#a6adc8"
OV2      = "#9399b2"
OV1      = "#7f849c"
OV0      = "#6c7086"
BLUE     = "#89b4fa"
GREEN    = "#a6e3a1"
YELLOW   = "#f9e2af"
RED      = "#f38ba8"
ORANGE   = "#fab387"
MAUVE    = "#cba6f7"
TEAL     = "#94e2d5"
SKY      = "#89dceb"

VERSION = "2.0.0"


# ── Данные адаптера ───────────────────────────────────────────────────────────
@dataclass
class Adapter:
    name: str
    description: str = ""
    status: str = "Unknown"
    mac: str = ""
    dhcp_v4: bool = True
    dhcp_v6: bool = True
    ipv4: List[str] = field(default_factory=list)
    ipv6: List[str] = field(default_factory=list)
    gateway_v4: List[str] = field(default_factory=list)
    dns_v4: List[str] = field(default_factory=list)
    dns_v6: List[str] = field(default_factory=list)
    is_vpn: bool = False
    issues: List[str] = field(default_factory=list)


# ── Сетевая логика ────────────────────────────────────────────────────────────
VPN_KW = [
    "vpn","tap","tun","tunnel","wireguard","wg","openvpn","nordvpn",
    "expressvpn","protonvpn","mullvad","surfshark","cisco","anyconnect",
    "pulse","globalprotect","fortinet","forti","hamachi","zerotier",
    "tailscale","radmin","pptp","l2tp","sstp","ikev2","softet",
    "outline","shadowsocks","clash","v2ray","xray",
]

KNOWN_DNS = {
    "8.8.8.8":         ("Google DNS",  GREEN),
    "8.8.4.4":         ("Google DNS",  GREEN),
    "1.1.1.1":         ("Cloudflare",  GREEN),
    "1.0.0.1":         ("Cloudflare",  GREEN),
    "9.9.9.9":         ("Quad9",       GREEN),
    "149.112.112.112": ("Quad9",       GREEN),
    "208.67.222.222":  ("OpenDNS",     YELLOW),
    "208.67.220.220":  ("OpenDNS",     YELLOW),
    "77.88.8.8":       ("Yandex DNS",  YELLOW),
    "77.88.8.1":       ("Yandex DNS",  YELLOW),
    "94.140.14.14":    ("AdGuard",     YELLOW),
    "94.140.15.15":    ("AdGuard",     YELLOW),
}

PS_COLLECT = r"""
$ErrorActionPreference = 'SilentlyContinue'
$adapters = Get-NetAdapter -IncludeHidden | Where-Object { $_.InterfaceType -ne 24 }
foreach ($a in $adapters) {
    $idx   = $a.InterfaceIndex
    $ipCfg = Get-NetIPConfiguration -InterfaceIndex $idx -All
    $dns4  = Get-DnsClientServerAddress -InterfaceIndex $idx -AddressFamily IPv4
    $dns6  = Get-DnsClientServerAddress -InterfaceIndex $idx -AddressFamily IPv6
    $if4   = Get-NetIPInterface -InterfaceIndex $idx -AddressFamily IPv4
    $if6   = Get-NetIPInterface -InterfaceIndex $idx -AddressFamily IPv6
    $ipv4  = ($ipCfg.IPv4Address  | ForEach-Object { $_.IPAddress }) -join "|"
    $ipv6g = ($ipCfg.IPv6Address  | Where-Object { $_.IPAddress -notlike 'fe80*' } | ForEach-Object { $_.IPAddress }) -join "|"
    $gw4   = ($ipCfg.IPv4DefaultGateway | ForEach-Object { $_.NextHop }) -join "|"
    $d4    = ($dns4.ServerAddresses) -join "|"
    $d6    = ($dns6.ServerAddresses) -join "|"
    $dh4   = if ($if4) { $if4.Dhcp } else { 'Unknown' }
    $dh6   = if ($if6) { $if6.Dhcp } else { 'Unknown' }
    Write-Output ">>>START<<<"
    Write-Output "NAME:$($a.Name)"
    Write-Output "DESC:$($a.InterfaceDescription)"
    Write-Output "STATUS:$($a.Status)"
    Write-Output "MAC:$($a.MacAddress)"
    Write-Output "DHCP4:$dh4"
    Write-Output "DHCP6:$dh6"
    Write-Output "IPV4:$ipv4"
    Write-Output "IPV6G:$ipv6g"
    Write-Output "GW4:$gw4"
    Write-Output "DNS4:$d4"
    Write-Output "DNS6:$d6"
    Write-Output ">>>END<<<"
}
"""


def run_cmd(cmd: str, timeout: int = 30) -> Tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True,
            timeout=timeout, encoding="cp866", errors="replace",
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return -1, str(e)


def run_ps(script: str, timeout: int = 25) -> str:
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        return (r.stdout or "").strip()
    except Exception:
        return ""


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def request_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable,
        " ".join(f'"{a}"' for a in sys.argv), None, 1,
    )
    sys.exit(0)


def detect_issues(a: Adapter) -> List[str]:
    if a.status not in ("Up", "Connected"):
        return []
    issues = []
    for ip in a.dns_v4:
        if ip not in KNOWN_DNS:
            if not re.match(r"^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)", ip):
                if not ip.startswith("127.") and ":" not in ip:
                    issues.append(f"Неизвестный DNS: {ip}")
    if not a.dhcp_v4 and a.ipv4:
        issues.append("Статический IPv4")
    if not a.dhcp_v6 and a.ipv6:
        issues.append("Статический IPv6")
    if a.ipv4 and not a.gateway_v4 and not a.is_vpn:
        issues.append("Нет шлюза по умолчанию")
    if not a.dns_v4 and a.ipv4 and not a.is_vpn:
        issues.append("DNS не настроен")
    return issues


def get_adapters() -> List[Adapter]:
    out = run_ps(PS_COLLECT)
    adapters: List[Adapter] = []
    cur: dict = {}
    for raw in out.splitlines():
        line = raw.strip()
        if line == ">>>START<<<":
            cur = {}
        elif line == ">>>END<<<":
            if "NAME" not in cur:
                continue
            def sf(k):
                return [x for x in cur.get(k, "").split("|") if x.strip()]
            n, d = cur.get("NAME", ""), cur.get("DESC", "")
            a = Adapter(
                name=n, description=d,
                status=cur.get("STATUS", "Unknown"),
                mac=cur.get("MAC", ""),
                dhcp_v4=cur.get("DHCP4", "Disabled") == "Enabled",
                dhcp_v6=cur.get("DHCP6", "Disabled") == "Enabled",
                ipv4=sf("IPV4"), ipv6=sf("IPV6G"),
                gateway_v4=sf("GW4"), dns_v4=sf("DNS4"), dns_v6=sf("DNS6"),
                is_vpn=any(kw in (n + " " + d).lower() for kw in VPN_KW),
            )
            a.issues = detect_issues(a)
            adapters.append(a)
        elif ":" in line:
            k, _, v = line.partition(":")
            cur[k.strip()] = v.strip()
    return adapters


def dns_info(ip: str) -> Tuple[str, str]:
    if ip in KNOWN_DNS:
        return KNOWN_DNS[ip]
    if re.match(r"^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)", ip):
        return "Роутер/LAN", TEAL
    if ip.startswith("127."):
        return "Loopback", TEAL
    if ":" in ip:
        return "IPv6", SKY
    return "Неизвестный!", RED


# ═══════════════════════════════════════════════════════════════════════════════
#  GUI
# ═══════════════════════════════════════════════════════════════════════════════

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def _font(size=13, weight="normal") -> ctk.CTkFont:
    return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)


def _label(parent, text, size=13, color=TEXT, weight="normal",
           anchor="w", wraplength=0, **kw) -> ctk.CTkLabel:
    kw.setdefault("fg_color", "transparent")
    return ctk.CTkLabel(
        parent, text=text,
        font=_font(size, weight),
        text_color=color,
        anchor=anchor,
        wraplength=wraplength,
        **kw,
    )


def _hsep(parent) -> ctk.CTkFrame:
    return ctk.CTkFrame(parent, height=1, fg_color=S1)


# ─── Боковая панель ───────────────────────────────────────────────────────────
class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate, **kw):
        super().__init__(master, fg_color=MANTLE, corner_radius=0, width=210, **kw)
        self.on_navigate = on_navigate
        self._buttons: dict = {}
        self._build()

    def _build(self):
        self.grid_propagate(False)
        self.pack_propagate(False)

        # Logo
        logo = ctk.CTkFrame(self, fg_color="transparent", height=80)
        logo.pack(fill="x", padx=16, pady=(20, 8))
        logo.pack_propagate(False)
        _label(logo, "NetReset", size=22, color=BLUE,
               weight="bold", anchor="center").pack(expand=True)
        _label(logo, f"v{VERSION}", size=11, color=OV0,
               anchor="center").pack()

        _hsep(self).pack(fill="x", padx=12, pady=(8, 16))

        nav_items = [
            ("adapters", "Адаптеры",    "🖥"),
            ("reset",    "Сброс сети",  "🔄"),
            ("about",    "О программе", "ℹ"),
        ]
        for key, label, icon in nav_items:
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}   {label}",
                anchor="w",
                fg_color="transparent",
                text_color=SUB1,
                hover_color=S1,
                font=_font(13),
                height=42,
                corner_radius=8,
                command=lambda k=key: self.on_navigate(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._buttons[key] = btn

        # Footer
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=12, pady=16)
        _hsep(footer).pack(fill="x", pady=(0, 10))
        ac = GREEN if is_admin() else RED
        at = "● Администратор" if is_admin() else "● Нет прав адм."
        _label(footer, at, size=11, color=ac, anchor="center").pack()

    def set_active(self, key: str):
        for k, btn in self._buttons.items():
            btn.configure(
                fg_color=S0 if k == key else "transparent",
                text_color=TEXT if k == key else SUB1,
            )


# ─── Карточка адаптера ────────────────────────────────────────────────────────
class AdapterCard(ctk.CTkFrame):
    def __init__(self, master, adapter: Adapter, **kw):
        super().__init__(master, fg_color=S0, corner_radius=12, **kw)
        self.adapter = adapter
        self._build()

    def _accent(self) -> str:
        a = self.adapter
        if a.status not in ("Up", "Connected"):
            return OV0
        if a.is_vpn:
            return ORANGE
        if any("Неизвестный" in i or "Статичес" in i for i in a.issues):
            return RED
        if a.issues:
            return YELLOW
        return GREEN

    def _badge(self, parent, text: str, color: str):
        f = ctk.CTkFrame(parent, fg_color=color + "33", corner_radius=5)
        f.pack(side="right", padx=(4, 0))
        _label(f, text, size=10, color=color, weight="bold",
               anchor="center").pack(padx=8, pady=2)

    def _info_row(self, parent, label: str, value: str, color: str = SUB1):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=1)
        _label(f, label, size=11, color=OV0).pack(side="left", padx=(0, 5))
        _label(f, value or "—", size=12, color=color).pack(side="left")

    def _build(self):
        a = self.adapter
        accent = self._accent()

        # Left accent strip
        ctk.CTkFrame(self, width=4, fg_color=accent, corner_radius=2).pack(
            side="left", fill="y", padx=(6, 0), pady=8,
        )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=(12, 14), pady=10)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(body, fg_color="transparent")
        hdr.pack(fill="x")

        dot_col = GREEN if a.status in ("Up", "Connected") else OV0
        _label(hdr, "●", size=11, color=dot_col).pack(side="left", padx=(0, 5))
        _label(hdr, a.name, size=14, color=TEXT, weight="bold").pack(side="left")

        badges = ctk.CTkFrame(hdr, fg_color="transparent")
        badges.pack(side="right")
        if a.is_vpn:
            self._badge(badges, "VPN", ORANGE)
        status_color = GREEN if a.status in ("Up", "Connected") else OV0
        self._badge(badges, a.status or "Unknown", status_color)

        desc = a.description[:70] + ("…" if len(a.description) > 70 else "")
        _label(body, desc, size=11, color=OV0).pack(fill="x", pady=(3, 8))

        _hsep(body).pack(fill="x", pady=(0, 8))

        # ── Info grid (2 columns) ─────────────────────────────────────────────
        grid = ctk.CTkFrame(body, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1)

        left  = ctk.CTkFrame(grid, fg_color="transparent")
        right = ctk.CTkFrame(grid, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nw")
        right.grid(row=0, column=1, sticky="nw", padx=(16, 0))

        # Left: network addresses
        self._info_row(left, "IPv4:", ", ".join(a.ipv4) if a.ipv4 else None)
        self._info_row(left, "IPv6:", ", ".join(a.ipv6) if a.ipv6 else None, SUB0)
        self._info_row(left, "Шлюз:", ", ".join(a.gateway_v4) if a.gateway_v4 else None, SUB0)
        self._info_row(left, "MAC: ", a.mac if a.mac else None, OV1)

        # Right: DNS + DHCP
        dhcp4_str   = "✔ Авто" if a.dhcp_v4 else "✘ Статика"
        dhcp4_color = GREEN if a.dhcp_v4 else RED
        self._info_row(right, "DHCP v4:", dhcp4_str, dhcp4_color)

        dhcp6_str   = "✔ Авто" if a.dhcp_v6 else "✘ Статика"
        dhcp6_color = GREEN if a.dhcp_v6 else YELLOW
        self._info_row(right, "DHCP v6:", dhcp6_str, dhcp6_color)

        if a.dns_v4:
            for i, ip in enumerate(a.dns_v4[:3]):
                name, color = dns_info(ip)
                prefix = "DNS:   " if i == 0 else "       "
                self._info_row(right, prefix, f"{ip}  [{name}]", color)
        else:
            self._info_row(right, "DNS:   ", "Авто (DHCP)", TEAL)

        # ── Issues ────────────────────────────────────────────────────────────
        _hsep(body).pack(fill="x", pady=(8, 6))
        iss_f = ctk.CTkFrame(body, fg_color="transparent")
        iss_f.pack(fill="x")

        real_issues = [i for i in a.issues if "VPN" not in i]
        if a.is_vpn:
            _label(iss_f, "⚡  VPN адаптер активен", size=11, color=ORANGE).pack(anchor="w")
        if real_issues:
            for iss in real_issues:
                c = RED if ("Неизвестный" in iss or "Статичес" in iss) else YELLOW
                _label(iss_f, f"⚠  {iss}", size=11, color=c).pack(anchor="w")
        elif not a.is_vpn:
            _label(iss_f, "✔  Проблем не обнаружено", size=11, color=GREEN).pack(anchor="w")


# ─── Страница Адаптеры ────────────────────────────────────────────────────────
class AdaptersPage(ctk.CTkFrame):
    def __init__(self, master, app_ref, **kw):
        super().__init__(master, fg_color=BG, corner_radius=0, **kw)
        self.app_ref = app_ref
        self._build()

    def _build(self):
        topbar = ctk.CTkFrame(self, fg_color=MANTLE, height=54, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        _label(topbar, "Сетевые адаптеры", size=17, color=TEXT,
               weight="bold").pack(side="left", padx=20)

        self.status_lbl = _label(topbar, "", size=12, color=OV0)
        self.status_lbl.pack(side="right", padx=14)

        self.refresh_btn = ctk.CTkButton(
            topbar, text="⟳  Обновить",
            font=_font(12), fg_color=BLUE + "22",
            text_color=BLUE, hover_color=S1,
            width=115, height=32, corner_radius=8,
            command=self.app_ref.refresh_adapters,
        )
        self.refresh_btn.pack(side="right", padx=(0, 8), pady=10)

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG, corner_radius=0,
            scrollbar_button_color=S2,
            scrollbar_button_hover_color=S1,
        )
        self.scroll.pack(fill="both", expand=True)

    def set_loading(self, loading: bool):
        self.refresh_btn.configure(state="disabled" if loading else "normal")
        self.status_lbl.configure(
            text="Загрузка…" if loading else "",
            text_color=BLUE if loading else OV0,
        )

    def render_adapters(self, adapters: List[Adapter]):
        for w in self.scroll.winfo_children():
            w.destroy()

        if not adapters:
            _label(self.scroll, "Адаптеры не найдены.", size=13,
                   color=OV0, anchor="center").pack(pady=60)
            return

        def section(title: str, items: List[Adapter], accent: str):
            if not items:
                return
            hdr = ctk.CTkFrame(self.scroll, fg_color="transparent")
            hdr.pack(fill="x", padx=20, pady=(16, 4))
            ctk.CTkFrame(hdr, height=1, fg_color=accent + "66",
                         corner_radius=1).pack(fill="x", side="left", expand=True)
            _label(hdr, f"  {title}  ", size=10, color=accent,
                   weight="bold").pack(side="left")
            ctk.CTkFrame(hdr, height=1, fg_color=accent + "66",
                         corner_radius=1).pack(fill="x", side="left", expand=True)
            for a in items:
                AdapterCard(self.scroll, a).pack(fill="x", padx=20, pady=(0, 8))

        section("VPN-АДАПТЕРЫ",
                [a for a in adapters if a.is_vpn and a.status in ("Up", "Connected")],
                ORANGE)
        section("АКТИВНЫЕ",
                [a for a in adapters if not a.is_vpn and a.status in ("Up", "Connected")],
                GREEN)
        section("НЕАКТИВНЫЕ",
                [a for a in adapters if a.status not in ("Up", "Connected")],
                OV0)

        issues_n = sum(
            len([i for i in a.issues if "VPN" not in i])
            for a in adapters if a.status in ("Up", "Connected")
        )
        ts = datetime.now().strftime("%H:%M:%S")
        if issues_n:
            self.status_lbl.configure(
                text=f"⚠  Проблем: {issues_n}  ·  {ts}", text_color=YELLOW,
            )
        else:
            self.status_lbl.configure(
                text=f"✔  Всё в порядке  ·  {ts}", text_color=GREEN,
            )


# ─── Страница Сброс ───────────────────────────────────────────────────────────
class ResetPage(ctk.CTkFrame):
    def __init__(self, master, app_ref, **kw):
        super().__init__(master, fg_color=BG, corner_radius=0, **kw)
        self.app_ref = app_ref
        self._busy = False
        self._op_buttons: List[ctk.CTkButton] = []
        self._build()

    def _build(self):
        topbar = ctk.CTkFrame(self, fg_color=MANTLE, height=54, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        _label(topbar, "Сброс сети", size=17, color=TEXT,
               weight="bold").pack(side="left", padx=20)

        content = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        content.pack(fill="both", expand=True)

        # ── Op cards ─────────────────────────────────────────────────────────
        grid = ctk.CTkFrame(content, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(16, 6))
        grid.columnconfigure((0, 1), weight=1)

        ops = [
            ("DNS → Авто", "🌐",
             "Сбрасывает DNS на всех адаптерах на\nавтоматическое получение (DHCP).\nОчищает DNS-кэш системы.",
             BLUE, self._op_dns),
            ("IP → DHCP", "📡",
             "Возвращает IP-адреса на DHCP\nдля всех не-VPN адаптеров.\nVPN адаптеры остаются нетронутыми.",
             TEAL, self._op_ip),
            ("Полный сброс", "⚡",
             "IP стек + IPv6 + Winsock + Firewall\n+ DNS на всех адаптерах.\nТребует перезагрузки.",
             RED, self._op_full),
            ("Один адаптер", "🔌",
             "Выбери нужный адаптер из списка\nи сбрось его настройки\nотдельно от остальных.",
             MAUVE, self._op_single),
        ]

        for i, (title, icon, desc, color, cmd) in enumerate(ops):
            card = ctk.CTkFrame(grid, fg_color=S0, corner_radius=12)
            col  = i % 2
            row  = i // 2
            pad_l = 0 if col == 0 else 6
            pad_r = 6 if col == 0 else 0
            card.grid(row=row, column=col, padx=(pad_l, pad_r),
                      pady=6, sticky="nsew")
            grid.rowconfigure(row, weight=1)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=18, pady=14)

            top = ctk.CTkFrame(inner, fg_color="transparent")
            top.pack(fill="x", pady=(0, 8))
            _label(top, icon, size=20, color=color).pack(side="left", padx=(0, 10))
            _label(top, title, size=15, color=TEXT, weight="bold").pack(side="left")

            _label(inner, desc, size=12, color=SUB0, wraplength=260,
                   anchor="w").pack(fill="x", pady=(0, 12))

            btn = ctk.CTkButton(
                inner, text="Выполнить", font=_font(12, "bold"),
                fg_color=color + "22", text_color=color, hover_color=color + "44",
                height=34, corner_radius=8, command=cmd,
            )
            btn.pack(fill="x")
            self._op_buttons.append(btn)

        # ── Log ───────────────────────────────────────────────────────────────
        log_hdr = ctk.CTkFrame(content, fg_color="transparent")
        log_hdr.pack(fill="x", padx=20, pady=(10, 4))
        _label(log_hdr, "Журнал операций", size=13, color=OV2,
               weight="bold").pack(side="left")
        ctk.CTkButton(
            log_hdr, text="Очистить", font=_font(11),
            fg_color="transparent", text_color=OV0, hover_color=S1,
            width=70, height=24, corner_radius=6,
            command=self._clear_log,
        ).pack(side="right")

        self.log_box = ctk.CTkTextbox(
            content,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=CRUST, text_color=SUB0,
            corner_radius=10, height=200,
            activate_scrollbars=True, wrap="word",
        )
        self.log_box.pack(fill="x", padx=20, pady=(0, 8))
        self.log_box.configure(state="disabled")

        self.prog_lbl = _label(content, "", size=12, color=OV0, anchor="center")
        self.prog_lbl.pack()

        self.progress = ctk.CTkProgressBar(
            content, fg_color=S1, progress_color=BLUE, height=4, corner_radius=2,
        )
        self.progress.pack(fill="x", padx=20, pady=(4, 20))
        self.progress.set(0)

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{ts}]  {msg}\n")
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        for btn in self._op_buttons:
            btn.configure(state=state)
        if not busy:
            self.progress.set(0)
            self.prog_lbl.configure(text="")

    def _run_commands(self, cmds: List[Tuple[str, str]], done_msg: str = "Завершено."):
        if self._busy:
            return
        self._set_busy(True)
        total = len(cmds)

        def worker():
            self.after(0, lambda: self._log(f"▶  Начало ({total} операций)"))
            for i, (cmd, desc) in enumerate(cmds, 1):
                self.after(0, lambda d=desc, n=i: (
                    self.prog_lbl.configure(text=f"[{n}/{total}]  {d}"),
                    self.progress.set(n / total),
                ))
                code, _ = run_cmd(cmd, timeout=30)
                sym = "✔" if code in (0, 1) else "✘"
                self.after(0, lambda s=sym, d=desc: self._log(f"{s}  {d}"))
                time.sleep(0.1)
            self.after(0, lambda: (
                self._log(f"━━  {done_msg}"),
                self._set_busy(False),
                self.app_ref.refresh_adapters(),
            ))

        threading.Thread(target=worker, daemon=True).start()

    # ── Operations ────────────────────────────────────────────────────────────
    def _op_dns(self):
        adps = self.app_ref.adapters
        if not adps:
            self._log("⚠  Нет данных. Обновите страницу Адаптеры.")
            return
        cmds = []
        for a in adps:
            cmds += [
                (f'netsh interface ip set dns "{a.name}" dhcp',
                 f"DNS IPv4 → авто [{a.name}]"),
                (f'netsh interface ipv6 set dnsservers "{a.name}" source=dhcp',
                 f"DNS IPv6 → авто [{a.name}]"),
            ]
        cmds.append(("ipconfig /flushdns", "Очистка DNS-кэша"))
        self._run_commands(cmds, "DNS сброшен на всех адаптерах.")

    def _op_ip(self):
        adps = self.app_ref.adapters
        if not adps:
            self._log("⚠  Нет данных. Обновите страницу Адаптеры.")
            return
        cmds = []
        for a in adps:
            if a.is_vpn:
                continue
            cmds += [
                (f'netsh interface ip set address "{a.name}" dhcp',
                 f"IPv4 → DHCP [{a.name}]"),
                (f'netsh interface ip set dns "{a.name}" dhcp',
                 f"DNS → авто  [{a.name}]"),
            ]
        self._run_commands(cmds, "IP-адреса сброшены на DHCP.")

    def _op_full(self):
        dlg = ConfirmDialog(
            self.app_ref,
            title="Полный сброс сети",
            message=(
                "Будет выполнен полный сброс сетевого стека:\n\n"
                "  • netsh int ip reset\n"
                "  • netsh int ipv6 reset\n"
                "  • netsh winsock reset\n"
                "  • netsh advfirewall reset\n"
                "  • ipconfig /flushdns + /release + /renew\n"
                "  • DNS → авто на всех адаптерах\n\n"
                "Интернет прервётся на время операции.\n"
                "После завершения необходима перезагрузка."
            ),
            color=RED,
        )
        if not dlg.confirmed:
            return
        adps = self.app_ref.adapters or []
        cmds = [
            ("ipconfig /release",            "Освобождение DHCP-аренды"),
            ("netsh int ip reset",           "Сброс IPv4 стека"),
            ("netsh int ipv6 reset",         "Сброс IPv6 стека"),
            ("netsh winsock reset catalog",  "Сброс Winsock-каталога"),
            ("netsh int tcp reset",          "Сброс TCP-параметров"),
            ("netsh advfirewall reset",      "Сброс файрвола"),
            ("ipconfig /flushdns",           "Очистка DNS-кэша"),
            ("netsh int ip delete arpcache", "Очистка ARP-кэша"),
        ]
        for a in adps:
            cmds += [
                (f'netsh interface ip set dns "{a.name}" dhcp',
                 f"DNS IPv4 → авто [{a.name}]"),
                (f'netsh interface ipv6 set dnsservers "{a.name}" source=dhcp',
                 f"DNS IPv6 → авто [{a.name}]"),
            ]
        cmds.append(("ipconfig /renew", "Обновление DHCP-аренды"))
        self._run_commands(cmds, "Полный сброс завершён. Перезагрузи компьютер!")

    def _op_single(self):
        adps = [a for a in (self.app_ref.adapters or [])
                if a.status in ("Up", "Connected")]
        if not adps:
            self._log("⚠  Нет активных адаптеров.")
            return
        dlg = AdapterPickDialog(self.app_ref, adps)
        if dlg.chosen is None:
            return
        n = dlg.chosen.name
        cmds = [
            (f'netsh interface ip set address "{n}" dhcp', "IPv4 → DHCP"),
            (f'netsh interface ip set dns "{n}" dhcp',     "DNS IPv4 → авто"),
            (f'netsh interface ipv6 set dnsservers "{n}" source=dhcp', "DNS IPv6 → авто"),
            (f'ipconfig /release "{n}"',                   "Освобождение аренды"),
            (f'ipconfig /renew "{n}"',                     "Обновление аренды"),
            ("ipconfig /flushdns",                         "Очистка DNS-кэша"),
        ]
        self._run_commands(cmds, f"Адаптер «{n}» сброшен.")


# ─── Страница "О программе" ───────────────────────────────────────────────────
class AboutPage(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG, corner_radius=0, **kw)
        self._build()

    def _build(self):
        topbar = ctk.CTkFrame(self, fg_color=MANTLE, height=54, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        _label(topbar, "О программе", size=17, color=TEXT,
               weight="bold").pack(side="left", padx=20)

        scroll = ctk.CTkScrollableFrame(self, fg_color=BG, corner_radius=0)
        scroll.pack(fill="both", expand=True)

        _label(scroll, "NetReset", size=38, color=BLUE,
               weight="bold", anchor="center").pack(pady=(44, 4))
        _label(scroll, f"версия {VERSION}", size=13, color=OV0,
               anchor="center").pack()
        _label(scroll, "Windows Network Diagnostics & Reset",
               size=13, color=SUB0, anchor="center").pack(pady=(4, 32))

        blocks = [
            ("🖥  Адаптеры", BLUE,
             "Отображает все адаптеры: физические, виртуальные, VPN.\n"
             "Автодетект VPN по имени/описанию (WireGuard, TAP, NordVPN, Tailscale и др.).\n"
             "Показывает IPv4, IPv6, DNS с метками, шлюз, статус DHCP v4/v6."),
            ("⚠  Диагностика", YELLOW,
             "Проверяет каждый активный адаптер:\n"
             "  • Неизвестные / подозрительные DNS-серверы\n"
             "  • Статический IP (DHCP отключён)\n"
             "  • Отсутствие шлюза или DNS"),
            ("🔄  Операции сброса", GREEN,
             "DNS → Авто: netsh interface ip/ipv6 set dns dhcp + ipconfig /flushdns\n"
             "IP → DHCP: netsh interface ip set address dhcp (VPN пропускаются)\n"
             "Полный сброс: IP стек + IPv6 + Winsock + Firewall + DNS\n"
             "Один адаптер: выбор из списка активных"),
        ]
        for title, color, text in blocks:
            card = ctk.CTkFrame(scroll, fg_color=S0, corner_radius=12)
            card.pack(fill="x", padx=50, pady=6)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", padx=20, pady=14)
            _label(inner, title, size=14, color=color,
                   weight="bold").pack(anchor="w", pady=(0, 6))
            _label(inner, text, size=12, color=SUB0,
                   wraplength=640, anchor="w").pack(anchor="w")

        # Build hint
        hint_card = ctk.CTkFrame(scroll, fg_color=CRUST, corner_radius=10)
        hint_card.pack(fill="x", padx=50, pady=(12, 6))
        hint_inner = ctk.CTkFrame(hint_card, fg_color="transparent")
        hint_inner.pack(padx=20, pady=14, fill="x")
        _label(hint_inner, "Компиляция в .exe", size=12, color=OV2,
               weight="bold").pack(anchor="w", pady=(0, 6))
        tb = ctk.CTkTextbox(
            hint_inner,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=S0, text_color=TEAL,
            height=50, corner_radius=6, activate_scrollbars=False,
        )
        tb.pack(fill="x")
        tb.insert("1.0",
                  "pip install customtkinter pyinstaller\n"
                  'pyinstaller --onefile --noconsole --name "NetReset" netreset.py')
        tb.configure(state="disabled")

        _label(scroll, "Требуются права администратора для выполнения сброса.",
               size=11, color=OV0, anchor="center").pack(pady=(12, 50))


# ─── Диалоги ──────────────────────────────────────────────────────────────────
class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, message: str, color: str = BLUE):
        super().__init__(parent)
        self.confirmed = False
        self.title(title)
        self.geometry("490x340")
        self.resizable(False, False)
        self.configure(fg_color=MANTLE)
        self.grab_set()
        self.lift()
        self.focus_force()
        self._center(parent)

        ctk.CTkFrame(self, height=4, fg_color=color, corner_radius=0).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=20)

        _label(body, title, size=16, color=TEXT, weight="bold").pack(anchor="w")
        _label(body, message, size=12, color=SUB0,
               wraplength=430, anchor="w").pack(anchor="w", pady=(10, 20))

        btns = ctk.CTkFrame(body, fg_color="transparent")
        btns.pack(side="bottom", fill="x")
        ctk.CTkButton(
            btns, text="Отмена", font=_font(12),
            fg_color=S1, text_color=SUB1, hover_color=S2,
            width=110, height=36, corner_radius=8,
            command=self.destroy,
        ).pack(side="right", padx=(6, 0))
        ctk.CTkButton(
            btns, text="Подтвердить", font=_font(12, "bold"),
            fg_color=color + "33", text_color=color, hover_color=color + "55",
            width=140, height=36, corner_radius=8,
            command=self._ok,
        ).pack(side="right")
        self.wait_window()

    def _ok(self):
        self.confirmed = True
        self.destroy()

    def _center(self, parent):
        parent.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() // 2 - 245
        y = parent.winfo_y() + parent.winfo_height() // 2 - 170
        self.geometry(f"+{x}+{y}")


class AdapterPickDialog(ctk.CTkToplevel):
    def __init__(self, parent, adapters: List[Adapter]):
        super().__init__(parent)
        self.chosen: Adapter = None
        self.title("Выбор адаптера")
        self.geometry("420x360")
        self.resizable(False, False)
        self.configure(fg_color=MANTLE)
        self.grab_set()
        self.lift()
        self.focus_force()
        self._center(parent)

        ctk.CTkFrame(self, height=4, fg_color=MAUVE, corner_radius=0).pack(fill="x")
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        _label(body, "Выбери адаптер:", size=14, color=TEXT,
               weight="bold").pack(anchor="w", pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(body, fg_color=BG, corner_radius=8, height=230)
        scroll.pack(fill="both", expand=True)

        for a in adapters:
            tag = "  [VPN]" if a.is_vpn else ""
            note = f"  ·  {len(a.issues)} пробл." if a.issues else ""
            c = ORANGE if a.is_vpn else (YELLOW if a.issues else TEXT)
            ctk.CTkButton(
                scroll, text=f"  {a.name}{tag}{note}",
                anchor="w", font=_font(13),
                fg_color=S0, text_color=c, hover_color=S1,
                height=38, corner_radius=8,
                command=lambda x=a: self._pick(x),
            ).pack(fill="x", pady=2)

        self.wait_window()

    def _pick(self, a: Adapter):
        self.chosen = a
        self.destroy()

    def _center(self, parent):
        parent.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() // 2 - 210
        y = parent.winfo_y() + parent.winfo_height() // 2 - 180
        self.geometry(f"+{x}+{y}")


# ─── Главное окно ─────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.adapters: List[Adapter] = []
        self._loading = False

        self.title("NetReset")
        self.geometry("1120x700")
        self.minsize(900, 580)
        self.configure(fg_color=BG)
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"1120x700+{(sw-1120)//2}+{(sh-700)//2}")

        self._build()
        self.after(200, self.refresh_adapters)

    def _build(self):
        self.sidebar = Sidebar(self, on_navigate=self._navigate)
        self.sidebar.pack(side="left", fill="y")

        self.content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        self.pages = {
            "adapters": AdaptersPage(self.content, app_ref=self),
            "reset":    ResetPage(self.content, app_ref=self),
            "about":    AboutPage(self.content),
        }
        self._navigate("adapters")

    def _navigate(self, key: str):
        for name, page in self.pages.items():
            (page.pack if name == key else page.pack_forget)(
                **({"fill": "both", "expand": True} if name == key else {})
            )
        self.sidebar.set_active(key)

    def refresh_adapters(self):
        if self._loading:
            return
        self._loading = True
        self.pages["adapters"].set_loading(True)

        def worker():
            data = get_adapters()
            self.after(0, lambda: self._loaded(data))

        threading.Thread(target=worker, daemon=True).start()

    def _loaded(self, data: List[Adapter]):
        self.adapters = data
        self._loading = False
        self.pages["adapters"].set_loading(False)
        self.pages["adapters"].render_adapters(data)


# ── Точка входа ───────────────────────────────────────────────────────────────
def main():
    if not is_admin():
        import tkinter.messagebox as mb
        root = ctk.CTk()
        root.withdraw()
        ans = mb.askyesno(
            "NetReset — Права администратора",
            "Для сброса сетевых настроек нужны права администратора.\n\n"
            "Перезапустить с правами администратора (UAC)?",
        )
        root.destroy()
        if ans:
            request_admin()

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
