"""
Futures Arbitrage Scanner — KuCoin · Gate.io · MEXC
Perpetual USDT futures, merged columns, funding filter,
column resize, code editor, settings persistence, proxy support.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import os
import logging
import traceback
import socket
import urllib.request
import urllib.error
from datetime import datetime, timezone
from collections import defaultdict

# ── Logging to console ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("arbitrage")

# ── Config file path ───────────────────────────────────────────────────────────
_SCRIPT_PATH = os.path.abspath(__file__)
_CONFIG_PATH = os.path.join(os.path.dirname(_SCRIPT_PATH), "arbitrage_settings.json")

def load_settings() -> dict:
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(data: dict):
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

# ── Palette ────────────────────────────────────────────────────────────────────
BG_DARK      = "#0d0f18"
BG_CARD      = "#141722"
BG_CARD2     = "#1c2030"
BG_ROW_ALT   = "#181b28"
ACCENT_BLUE  = "#3b82f6"
ACCENT_GREEN = "#22c55e"
ACCENT_RED   = "#ef4444"
ACCENT_AMBER = "#f59e0b"
ACCENT_PURPLE= "#a855f7"
TEXT_PRIMARY = "#e2e8f0"
TEXT_MUTED   = "#4b5563"
TEXT_HEADER  = "#6b7280"
BORDER       = "#232640"

FNT       = ("Segoe UI", 10)
FNT_B     = ("Segoe UI", 10, "bold")
FNT_TITLE = ("Segoe UI", 13, "bold")
FNT_SM    = ("Segoe UI", 9)
FNT_MONO  = ("Consolas", 10)

EXCHANGES = ["KuCoin", "Gate.io", "MEXC"]

# ── Proxy config (module-level, updated by UI) ─────────────────────────────────
_proxy_cfg: dict = {}
_gate_proxy_cfg: dict = {}

def _build_opener(proxy: dict) -> urllib.request.OpenerDirector:
    if not proxy.get("enabled") or not proxy.get("host"):
        return urllib.request.build_opener()

    ptype = proxy.get("type", "http").lower()
    host  = proxy["host"].strip()
    port  = str(proxy.get("port", 1080)).strip()
    user  = proxy.get("user", "").strip()
    pwd   = proxy.get("password", "").strip()

    if ptype == "socks5":
        try:
            import socks
            socks.set_default_proxy(
                socks.SOCKS5,
                host, int(port),
                username=user or None,
                password=pwd  or None,
            )
            socks.wrapmodule(urllib.request)
            log.info("SOCKS5 proxy set: %s:%s", host, port)
            return urllib.request.build_opener()
        except ImportError:
            log.warning("PySocks not installed — falling back to HTTP proxy for SOCKS5 address")
            ptype = "http"

    if user and pwd:
        proxy_url = f"http://{user}:{pwd}@{host}:{port}"
    else:
        proxy_url = f"http://{host}:{port}"

    proxy_handler = urllib.request.ProxyHandler({
        "http":  proxy_url,
        "https": proxy_url,
    })
    log.info("HTTP proxy set: %s:%s", host, port)
    return urllib.request.build_opener(proxy_handler)


# ── Network helper ─────────────────────────────────────────────────────────────

def fetch(url: str, timeout: int = 14,
          extra_headers: dict | None = None,
          proxy: dict | None = None):
    effective_proxy = _proxy_cfg if proxy is None else proxy
    log.debug("GET %s  [proxy=%s]", url,
              effective_proxy.get("host") if effective_proxy.get("enabled") else "direct")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ArbitrageBot/4.0",
            "Accept": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)

        opener = _build_opener(effective_proxy)
        req = urllib.request.Request(url, headers=headers)
        with opener.open(req, timeout=timeout) as r:
            raw = r.read()
            data = json.loads(raw.decode("utf-8", errors="replace"))
            log.debug("OK %s → %s items", url,
                      len(data) if isinstance(data, list) else type(data).__name__)
            return data
    except urllib.error.HTTPError as e:
        log.warning("HTTP %s for %s", e.code, url)
        return {"_fetch_error": f"HTTP {e.code}"}
    except urllib.error.URLError as e:
        log.warning("URLError %s for %s", e.reason, url)
        return {"_fetch_error": str(e.reason)}
    except json.JSONDecodeError as e:
        log.warning("JSON error for %s: %s", url, e)
        return {"_fetch_error": "bad JSON"}
    except Exception as e:
        log.error("fetch error %s: %s", url, e)
        return {"_fetch_error": str(e)}


def _sf(val, default: float = 0.0) -> float:
    try:
        return float(val) if val not in (None, "", "null") else default
    except (TypeError, ValueError):
        return default


def _next_h(ts_raw) -> float:
    """Convert timestamp (ms/s or ISO string) to hours-until.
    Returns -1.0 if unknown or expired, so that caller can use interval."""
    if not ts_raw:
        return -1.0
    try:
        if isinstance(ts_raw, str):
            try:
                dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                ts = dt.timestamp()
            except ValueError:
                ts = float(ts_raw)
        else:
            ts = float(ts_raw)
        if ts > 1e12:
            ts /= 1000
        diff = ts - datetime.now().timestamp()
        return round(diff / 3600, 2) if diff > 0 else -1.0
    except Exception:
        return -1.0


# ── Exchange fetchers ──────────────────────────────────────────────────────────

def get_kucoin_futures() -> tuple[dict[str, dict], str]:
    rename = {"XBT": "BTC"}
    log.info("[KuCoin] Fetching contracts...")
    data = fetch("https://api-futures.kucoin.com/api/v1/contracts/active")
    result: dict[str, dict] = {}
    if not isinstance(data, dict):
        log.error("[KuCoin] No response")
        return result, "нет ответа"
    if data.get("_fetch_error"):
        log.error("[KuCoin] Fetch error: %s", data["_fetch_error"])
        return result, data["_fetch_error"]
    if data.get("code") != "200000":
        log.error("[KuCoin] Bad code: %s", data.get("code"))
        return result, f"код {data.get('code')}"

    for c in data.get("data", []):
        try:
            sym = c.get("symbol", "")
            if not sym.endswith("USDTM"):
                continue
            if c.get("settleCurrency") != "USDT":
                continue
            if c.get("status") != "Open":
                continue
            base = sym.replace("USDTM", "")
            base = rename.get(base, base)
            raw_period = _sf(c.get("fundingFeeSettlePeriod"), 28800)
            interval_h = max(1, int(raw_period) // 3600)
            next_h = _next_h(c.get("nextFundingRateTime"))
            result[base] = {
                "mark":           _sf(c.get("markPrice")),
                "last":           _sf(c.get("lastTradePrice") or c.get("markPrice")),
                "funding":        _sf(c.get("fundingFeeRate")),
                "oi":             _sf(c.get("openInterest")),
                "symbol":         sym,
                "fund_interval":  interval_h,
                "next_funding_h": next_h,
            }
        except Exception as e:
            log.debug("[KuCoin] Parse error for %s: %s", c.get("symbol","?"), e)

    log.info("[KuCoin] Loaded %d contracts", len(result))
    return result, ("" if result else "нет данных")


def get_gate_futures() -> tuple[dict[str, dict], str]:
    result:       dict[str, dict]  = {}
    fund_map:     dict[str, float] = {}
    interval_map: dict[str, int]   = {}
    symbol_map:   dict[str, str]   = {}
    errors: list[str] = []

    gproxy = _gate_proxy_cfg if _gate_proxy_cfg else _proxy_cfg

    log.info("[Gate.io] Fetching tickers...")
    tickers = fetch("https://api.gateio.ws/api/v4/futures/usdt/tickers",
                    timeout=15, proxy=gproxy)
    if isinstance(tickers, dict) and tickers.get("_fetch_error"):
        err_msg = tickers["_fetch_error"]
        log.error("[Gate.io] Tickers error: %s", err_msg)
        errors.append(f"tickers: {err_msg}")
    elif isinstance(tickers, list):
        log.info("[Gate.io] Tickers: %d items", len(tickers))
        for c in tickers:
            try:
                pair = c.get("contract", "")
                if not pair.endswith("_USDT"):
                    continue
                base = pair[:-5]
                next_h = _next_h(c.get("next_funding_time") or c.get("funding_next_apply"))
                result[base] = {
                    "mark":           _sf(c.get("mark_price")),
                    "last":           _sf(c.get("last")),
                    "funding":        _sf(c.get("funding_rate")),
                    "oi":             _sf(c.get("total_size")),
                    "symbol":         pair,
                    "fund_interval":  8,
                    "next_funding_h": next_h,
                }
            except Exception as e:
                log.debug("[Gate.io] Ticker parse error %s: %s", c.get("contract","?"), e)
    else:
        log.error("[Gate.io] Tickers unexpected type: %s, data=%s",
                  type(tickers), str(tickers)[:200])
        errors.append(f"tickers: неожиданный формат ({type(tickers).__name__})")

    log.info("[Gate.io] Fetching contracts (paginated)...")
    page, limit, cap = 1, 500, 20
    total_contracts = 0
    while page <= cap:
        offset = (page - 1) * limit
        url  = f"https://api.gateio.ws/api/v4/futures/usdt/contracts?limit={limit}&offset={offset}"
        data = fetch(url, timeout=15, proxy=gproxy)
        if isinstance(data, dict) and data.get("_fetch_error"):
            err_msg = data["_fetch_error"]
            log.error("[Gate.io] Contracts p%d error: %s", page, err_msg)
            if page == 1:
                errors.append(f"contracts: {err_msg}")
            break
        if not isinstance(data, list):
            log.error("[Gate.io] Contracts p%d unexpected type: %s", page, type(data))
            if page == 1:
                errors.append(f"contracts: неожиданный формат ({type(data).__name__})")
            break
        log.debug("[Gate.io] Contracts page %d: %d items", page, len(data))
        for c in data:
            try:
                name = c.get("name", "")
                if not name.endswith("_USDT"):
                    continue
                base = name[:-5]
                raw_int = _sf(c.get("funding_interval"), 28800)
                fund_map[base]     = _sf(c.get("funding_rate"))
                interval_map[base] = max(1, int(raw_int) // 3600)
                symbol_map[base]   = name
                total_contracts   += 1
            except Exception as e:
                log.debug("[Gate.io] Contract parse error %s: %s", c.get("name","?"), e)
        if len(data) < limit:
            break
        page += 1

    log.info("[Gate.io] Contracts loaded: %d", total_contracts)

    all_bases = set(result) | set(fund_map)
    for base in all_bases:
        fund  = fund_map.get(base)
        inter = interval_map.get(base, 8)
        sym   = symbol_map.get(base)
        if base in result:
            if fund is not None:
                result[base]["funding"]       = fund
            result[base]["fund_interval"] = inter
            if sym:
                result[base]["symbol"] = sym

    before = len(result)
    result = {k: v for k, v in result.items()
              if v.get("mark", 0) > 0 or v.get("last", 0) > 0}
    log.info("[Gate.io] Final: %d pairs", len(result))

    err = "; ".join(errors) if errors else ("нет данных" if not result else "")
    return result, err


def get_mexc_futures() -> tuple[dict[str, dict], str]:
    log.info("[MEXC] Fetching tickers...")
    data = fetch("https://contract.mexc.com/api/v1/contract/ticker", timeout=15)
    result: dict[str, dict] = {}
    if not isinstance(data, dict) and not isinstance(data, list):
        log.error("[MEXC] No response")
        return result, "нет ответа"
    if isinstance(data, dict) and data.get("_fetch_error"):
        log.error("[MEXC] Fetch error: %s", data["_fetch_error"])
        return result, data["_fetch_error"]
    items = data if isinstance(data, list) else data.get("data", [])
    if not isinstance(items, list):
        log.error("[MEXC] Unexpected format: %s", type(data).__name__)
        return result, f"неожиданный формат: {type(data).__name__}"
    skipped = 0
    for c in items:
        try:
            sym = c.get("symbol", "")
            if not sym.endswith("_USDT"):
                skipped += 1
                continue
            base = sym[:-5]
            next_h = _next_h(c.get("nextSettleTime") or c.get("nextFundingTime"))
            result[base] = {
                "mark":           _sf(c.get("indexPrice") or c.get("lastPrice")),
                "last":           _sf(c.get("lastPrice")),
                "funding":        _sf(c.get("fundingRate")),
                "oi":             _sf(c.get("openInterest")),
                "symbol":         sym,
                "fund_interval":  8,
                "next_funding_h": next_h,
            }
        except Exception as e:
            log.debug("[MEXC] Parse error %s: %s", c.get("symbol","?"), e)
            skipped += 1
    log.info("[MEXC] Loaded %d contracts, skipped %d", len(result), skipped)
    return result, ("" if result else "нет данных")


FETCHERS = {
    "KuCoin":  get_kucoin_futures,
    "Gate.io": get_gate_futures,
    "MEXC":    get_mexc_futures,
}

def _fmt_h(h: float) -> str:
    if h < 0:   return "—"
    if h < 1:   return f"{int(h * 60)}м"
    return f"{h:.1f}ч"

# ── Arbitrage engine ───────────────────────────────────────────────────────────

def find_opportunities(
    all_data:      dict[str, dict[str, dict]],
    excluded:      set,
    min_spread:    float,
    min_fund_diff: float,
    use_mark:      bool = True,
) -> list[dict]:
    price_key = "mark" if use_mark else "last"
    coin_map: dict[str, dict[str, dict]] = defaultdict(dict)
    for exchange, coins in all_data.items():
        for coin, info in coins.items():
            if coin.upper() in excluded:
                continue
            p = info.get(price_key, 0)
            if p and p > 0:
                coin_map[coin][exchange] = info

    results = []
    for coin, ex_map in coin_map.items():
        exs = list(ex_map.keys())
        if len(exs) < 2:
            continue
        for i in range(len(exs)):
            for j in range(i + 1, len(exs)):
                ea, eb = exs[i], exs[j]
                pa = ex_map[ea].get(price_key, 0)
                pb = ex_map[eb].get(price_key, 0)
                if pa <= 0 or pb <= 0:
                    continue

                fa = ex_map[ea].get("funding", 0)
                fb = ex_map[eb].get("funding", 0)

                # Направление по фандингу
                if fa > fb:
                    buy_ex, sell_ex = eb, ea
                    buy_price, sell_price = pb, pa
                elif fa < fb:
                    buy_ex, sell_ex = ea, eb
                    buy_price, sell_price = pa, pb
                else:
                    if pa <= pb:
                        buy_ex, sell_ex = ea, eb
                        buy_price, sell_price = pa, pb
                    else:
                        buy_ex, sell_ex = eb, ea
                        buy_price, sell_price = pb, pa

                spread = (sell_price - buy_price) / buy_price * 100
                if abs(spread) < min_spread:
                    continue

                fund_long  = ex_map[buy_ex].get("funding", 0) * 100
                fund_short = ex_map[sell_ex].get("funding", 0) * 100
                fund_diff  = abs(fund_long - fund_short)
                if fund_diff < min_fund_diff:
                    continue

                nfh_buy  = ex_map[buy_ex].get("next_funding_h", -1.0)
                nfh_sell = ex_map[sell_ex].get("next_funding_h", -1.0)
                if nfh_buy < 0:
                    nfh_buy = float(ex_map[buy_ex].get("fund_interval", 8))
                if nfh_sell < 0:
                    nfh_sell = float(ex_map[sell_ex].get("fund_interval", 8))
                next_fund_h = min(nfh_buy, nfh_sell)

                results.append({
                    "coin":          coin,
                    "buy_ex":        buy_ex,
                    "sell_ex":       sell_ex,
                    "buy_price":     buy_price,
                    "sell_price":    sell_price,
                    "buy_symbol":    ex_map[buy_ex].get("symbol", ""),
                    "sell_symbol":   ex_map[sell_ex].get("symbol", ""),
                    "spread":        spread,
                    "profit_est":    spread - 0.10,
                    "fund_long":     fund_long,
                    "fund_short":    fund_short,
                    "fund_diff":     fund_diff,
                    "fund_interval": min(
                        ex_map[buy_ex].get("fund_interval", 8),
                        ex_map[sell_ex].get("fund_interval", 8)
                    ),
                    "next_fund_h":   next_fund_h,
                    "next_fund_h_buy":  nfh_buy,
                    "next_fund_h_sell": nfh_sell,
                    "buy_oi":        ex_map[buy_ex].get("oi", 0),
                    "sell_oi":       ex_map[sell_ex].get("oi", 0),
                })

    results.sort(key=lambda x: x["spread"], reverse=True)
    return results[:300]


def _fmt_price(p: float) -> str:
    if not p:
        return "—"
    if p >= 1000:  return f"{p:,.2f}"
    if p >= 1:     return f"{p:.4f}"
    return f"{p:.6g}"

# ── Application ────────────────────────────────────────────────────────────────

class FuturesArbitrageApp(tk.Tk):

    COL_META = {
        "coin":        ("Монета",            90,  "w"),
        "direction":   ("Лонг(L) / Шорт(S)", 200, "center"),
        "prices":      ("Mark Buy / Sell $",  210, "center"),
        "spread":      ("Спред %",            82,  "e"),
        "funding":     ("Фанд. L% / S%",     185, "center"),
        "fund_diff":   ("Δ Фандинг %",        94,  "e"),
        "next_fund_h": ("До фандинга (L/S)",  95,  "center"),
    }
    DEFAULT_COL_ORDER = ["coin","direction","prices","spread","funding","fund_diff","next_fund_h"]
    _ALL_COLS         = ["coin","direction","prices","spread","funding","fund_diff","next_fund_h"]

    HDR_H       = 30
    RESIZE_ZONE = 6

    def __init__(self):
        super().__init__()
        self.title("Futures Arbitrage Scanner")
        self.geometry("1300x820")
        self.minsize(900, 600)
        self.configure(bg=BG_DARK)

        cfg = load_settings()

        global _proxy_cfg, _gate_proxy_cfg
        _proxy_cfg      = cfg.get("proxy",      {})
        _gate_proxy_cfg = cfg.get("gate_proxy", {})

        self._scan_lock      = threading.Lock()
        self._scan_active    = False
        self._stop_requested = False

        self.all_data:         dict[str, dict[str, dict]] = {}
        self.opportunities:    list[dict] = []
        self.exchange_cnt      = {e: 0 for e in EXCHANGES}
        self._exchange_errors: dict[str, str] = {}
        self._after_id         = None

        self._excluded:    set[str]        = set(cfg.get("excluded_coins", []))
        self._coin_colors: dict[str, str]  = cfg.get("coin_colors", {})

        self.min_spread    = tk.DoubleVar(value=cfg.get("min_spread",    0.5))
        self.min_fund_diff = tk.DoubleVar(value=cfg.get("min_fund_diff", 0.0))
        self.use_mark      = tk.BooleanVar(value=cfg.get("use_mark",    True))
        self.auto_refresh  = tk.BooleanVar(value=False)
        self.refresh_sec   = tk.IntVar(value=cfg.get("refresh_sec",    30))
        self.filter_coin   = tk.StringVar(value=cfg.get("filter_coin", ""))

        valid = set(self.COL_META)
        saved_order = cfg.get("col_order", list(self.DEFAULT_COL_ORDER))
        self._col_order = [c for c in saved_order if c in valid]
        for c in self.DEFAULT_COL_ORDER:
            if c not in self._col_order:
                self._col_order.append(c)

        self._saved_widths: dict[str, int] = {
            k: int(v) for k, v in cfg.get("col_widths", {}).items() if k in valid
        }

        self._sort_col = "spread"
        self._sort_asc = False

        self._drag_col        = None
        self._drag_from_idx   = 0
        self._drag_start      = None
        self._drag_insert_idx = None

        self._is_resizing  = False
        self._resize_col   = None
        self._resize_start = 0
        self._resize_orig  = 0

        self._proxy_win = None
        self._editor_win = None

        self._build_ui()
        self._style_tree()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _collect_settings(self) -> dict:
        widths = {}
        try:
            widths = {c: self.tree.column(c, "width") for c in self.COL_META}
        except Exception:
            pass
        return {
            "min_spread":     self.min_spread.get(),
            "min_fund_diff":  self.min_fund_diff.get(),
            "use_mark":       self.use_mark.get(),
            "refresh_sec":    self.refresh_sec.get(),
            "filter_coin":    self.filter_coin.get(),
            "col_order":      self._col_order,
            "col_widths":     widths,
            "excluded_coins": sorted(self._excluded),
            "coin_colors":    self._coin_colors,
            "proxy":          _proxy_cfg,
            "gate_proxy":     _gate_proxy_cfg,
        }

    def _on_close(self):
        save_settings(self._collect_settings())
        self.destroy()

    def _save_now(self):
        save_settings(self._collect_settings())
        self._prog.set("✓ Сохранено")
        self.after(2000, lambda: self._prog.set(""))

    # ── UI build ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_topbar()
        wrap = tk.Frame(self, bg=BG_DARK)
        wrap.pack(fill="both", expand=True)
        sb = tk.Frame(wrap, bg=BG_CARD, width=252)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        mn = tk.Frame(wrap, bg=BG_DARK)
        mn.pack(side="left", fill="both", expand=True)
        self._build_sidebar(sb)
        self._build_main(mn)

    def _build_topbar(self):
        bar = tk.Frame(self, bg=BG_CARD, height=54)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="⚡  Futures Arbitrage", font=FNT_TITLE,
                 bg=BG_CARD, fg=TEXT_PRIMARY).pack(side="left", padx=20)
        tk.Label(bar, text="Perpetual USDT  ·  KuCoin · Gate.io · MEXC",
                 font=FNT_SM, bg=BG_CARD, fg=TEXT_MUTED).pack(side="left")
        self._dots: dict[str, tk.Label] = {}
        rf = tk.Frame(bar, bg=BG_CARD)
        rf.pack(side="right", padx=20)
        for ex in EXCHANGES:
            f = tk.Frame(rf, bg=BG_CARD)
            f.pack(side="left", padx=8)
            dot = tk.Label(f, text="●", font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_MUTED)
            dot.pack(side="left")
            tk.Label(f, text=ex, font=FNT_SM, bg=BG_CARD, fg=TEXT_MUTED).pack(side="left", padx=2)
            self._dots[ex] = dot

    def _build_sidebar(self, sb):

        def section(txt):
            tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", padx=12, pady=(12, 6))
            tk.Label(sb, text=txt, font=("Segoe UI", 8, "bold"),
                     bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", padx=14, pady=(0, 4))

        tk.Label(sb, text="ПАРАМЕТРЫ", font=("Segoe UI", 8, "bold"),
                 bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", padx=14, pady=(18, 4))

        self._spin(sb, "Мин. спред (%)",     self.min_spread,    -99, 20,   0.1,   "%.1f")
        self._spin(sb, "Мин. Δ Фандинг (%)", self.min_fund_diff,   0, 1.0,  0.001, "%.3f")

        section("ТИП ЦЕНЫ")
        for text, val in [("Mark Price (рекоменд.)", True), ("Last Price", False)]:
            tk.Radiobutton(sb, text=text, variable=self.use_mark, value=val,
                           font=FNT_SM, bg=BG_CARD, fg=TEXT_PRIMARY,
                           activebackground=BG_CARD, activeforeground=TEXT_PRIMARY,
                           selectcolor=BG_CARD2).pack(anchor="w", padx=14, pady=1)

        section("ФИЛЬТР ПО МОНЕТЕ")
        ent = tk.Entry(sb, textvariable=self.filter_coin,
                       font=FNT, bg=BG_CARD2, fg=TEXT_PRIMARY,
                       insertbackground=TEXT_PRIMARY, relief="flat",
                       highlightthickness=1, highlightbackground=BORDER,
                       highlightcolor=ACCENT_BLUE)
        ent.pack(fill="x", padx=14, pady=4)
        ent.bind("<Return>", lambda e: self._apply_filter())

        section("МОНЕТЫ")
        tk.Button(sb, text="⚙  Исключить / Цвет", font=FNT_SM,
                  bg=BG_CARD2, fg=TEXT_PRIMARY, activebackground=BG_CARD,
                  activeforeground=TEXT_PRIMARY, relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=self._open_coin_manager).pack(fill="x", padx=14, pady=4)

        section("АВТООБНОВЛЕНИЕ")
        tk.Checkbutton(sb, text="Включить", variable=self.auto_refresh,
                       font=FNT_SM, bg=BG_CARD, fg=TEXT_PRIMARY,
                       activebackground=BG_CARD, selectcolor=BG_CARD2,
                       command=self._on_auto_toggle).pack(anchor="w", padx=14)
        rf = tk.Frame(sb, bg=BG_CARD)
        rf.pack(fill="x", padx=14, pady=4)
        tk.Label(rf, text="Интервал (сек):", font=FNT_SM,
                 bg=BG_CARD, fg=TEXT_HEADER).pack(side="left")
        tk.Spinbox(rf, from_=10, to=300, increment=5, textvariable=self.refresh_sec,
                   width=5, font=FNT_SM, bg=BG_CARD2, fg=TEXT_PRIMARY,
                   buttonbackground=BG_CARD2, relief="flat").pack(side="left", padx=6)

        section("СТАТИСТИКА")
        self._sv: dict[str, tk.StringVar] = {}
        for key, lbl in [
            ("ku", "KuCoin контрактов"),
            ("ga", "Gate.io контрактов"),
            ("mx", "MEXC контрактов"),
            ("bs", "Лучший спред"),
            ("ba", "Средний спред"),
        ]:
            self._sv[key] = tk.StringVar(value="—")
            r = tk.Frame(sb, bg=BG_CARD)
            r.pack(fill="x", padx=14, pady=1)
            tk.Label(r, text=lbl, font=FNT_SM, bg=BG_CARD, fg=TEXT_MUTED).pack(side="left")
            tk.Label(r, textvariable=self._sv[key], font=FNT_SM,
                     bg=BG_CARD, fg=TEXT_PRIMARY).pack(side="right")

        tk.Frame(sb, bg=BG_CARD).pack(fill="both", expand=True)

        self._err_var = tk.StringVar(value="")
        tk.Label(sb, textvariable=self._err_var, font=("Segoe UI", 8),
                 bg=BG_CARD, fg=ACCENT_RED, wraplength=225,
                 justify="left").pack(anchor="w", padx=14, pady=(4, 0))

        self._ts_var = tk.StringVar(value="Не обновлялось")
        tk.Label(sb, textvariable=self._ts_var, font=FNT_SM,
                 bg=BG_CARD, fg=TEXT_MUTED, wraplength=220).pack(padx=14, pady=10)

    def _spin(self, parent, label, var, from_, to, incr, fmt):
        tk.Label(parent, text=label, font=FNT_SM, bg=BG_CARD,
                 fg=TEXT_HEADER).pack(anchor="w", padx=14, pady=(6, 0))
        tk.Spinbox(parent, from_=from_, to=to, increment=incr,
                   textvariable=var, width=14, font=FNT_SM,
                   bg=BG_CARD2, fg=TEXT_PRIMARY,
                   buttonbackground=BG_CARD2, relief="flat",
                   format=fmt).pack(anchor="w", padx=14, pady=2)

    def _build_main(self, parent):
        # Toolbar
        tb = tk.Frame(parent, bg=BG_DARK, pady=8)
        tb.pack(fill="x", padx=14)

        self._scan_btn = tk.Button(
            tb, text="▶  Сканировать", font=FNT_B,
            bg=ACCENT_BLUE, fg="white", activebackground="#2563eb",
            activeforeground="white", relief="flat", padx=16, pady=6,
            cursor="hand2", command=self._start_scan)
        self._scan_btn.pack(side="left", padx=(0, 4))

        self._stop_btn = tk.Button(
            tb, text="⏹  Стоп", font=FNT_B,
            bg=ACCENT_RED, fg="white", activebackground="#b91c1c",
            activeforeground="white", relief="flat", padx=12, pady=6,
            cursor="hand2", state="disabled", command=self._stop_scan)
        self._stop_btn.pack(side="left", padx=(0, 6))

        for label, cmd, fg, bg_color in [
            ("⟳  Фильтр",             self._apply_filter,    TEXT_PRIMARY, BG_CARD2),
            ("↺  Сброс столбцов",     self._reset_col_order, TEXT_MUTED,   BG_CARD2),
            ("💾  Сохранить",         self._save_now,        TEXT_MUTED,   BG_CARD2),
            ("🔌  Прокси",            self._open_proxy_mgr,  ACCENT_AMBER, "#2a2000"),
            ("</> Редактор кода",     self._open_editor,     ACCENT_BLUE,  "#1e3a5f"),
        ]:
            tk.Button(tb, text=label, font=FNT, bg=bg_color, fg=fg,
                      activebackground=BG_CARD, activeforeground=TEXT_PRIMARY,
                      relief="flat", padx=10, pady=6, cursor="hand2",
                      command=cmd).pack(side="left", padx=4)

        self._prog = tk.StringVar(value="")
        tk.Label(tb, textvariable=self._prog, font=FNT_SM,
                 bg=BG_DARK, fg=TEXT_MUTED).pack(side="left", padx=10)
        tk.Label(tb, text="drag заголовок = переместить  |  граница = resize",
                 font=FNT_SM, bg=BG_DARK, fg=TEXT_MUTED).pack(side="right", padx=8)

        # Metric cards
        mc = tk.Frame(parent, bg=BG_DARK)
        mc.pack(fill="x", padx=14, pady=(0, 6))
        self._mv: dict[str, tk.StringVar] = {}
        for key, lbl, clr in [
            ("best", "Лучший спред",     ACCENT_GREEN),
            ("avg",  "Средний спред",    ACCENT_AMBER),
            ("fund", "Макс. Δ Фандинг", ACCENT_PURPLE),
        ]:
            self._mv[key] = tk.StringVar(value="—")
            c = tk.Frame(mc, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER)
            c.pack(side="left", fill="x", expand=True, padx=3, pady=2)
            tk.Label(c, text=lbl, font=FNT_SM, bg=BG_CARD,
                     fg=TEXT_MUTED).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(c, textvariable=self._mv[key], font=("Segoe UI", 15, "bold"),
                     bg=BG_CARD, fg=clr).pack(anchor="w", padx=10, pady=(2, 8))

        # Table frame
        tf = tk.Frame(parent, bg=BG_DARK)
        tf.pack(fill="both", expand=True, padx=14, pady=(0, 4))

        self._hdr_canvas = tk.Canvas(tf, height=self.HDR_H, bg=BG_CARD2,
                                      highlightthickness=0, bd=0)
        self._hdr_canvas.pack(fill="x", side="top")

        self.tree = ttk.Treeview(tf, columns=tuple(self._ALL_COLS),
                                  show="headings", selectmode="browse")
        for col in self._ALL_COLS:
            _, dw, anc = self.COL_META[col]
            w = self._saved_widths.get(col, dw)
            self.tree.heading(col, text="")
            self.tree.column(col, width=w, anchor=anc, minwidth=30, stretch=False)

        self.tree.configure(displaycolumns=self._col_order)

        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal",  command=self._hscroll)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side="left",   fill="both", expand=True)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")

        self.tree.bind("<Double-1>", self._detail)

        cv = self._hdr_canvas
        cv.bind("<ButtonPress-1>",   self._hdr_press)
        cv.bind("<B1-Motion>",        self._hdr_motion)
        cv.bind("<ButtonRelease-1>",  self._hdr_release)
        cv.bind("<Motion>",           self._hdr_hover)
        cv.bind("<Configure>",        lambda e: self._draw_headers())

        self.after(60, self._draw_headers)

        tk.Label(parent,
                 text="Спред = разница цен. Зелёный ≥2%, серый <0.1%. Не финансовый совет.",
                 font=FNT_SM, bg=BG_DARK, fg=TEXT_MUTED).pack(pady=(0, 6))

    # ── Style ──────────────────────────────────────────────────────────────────
    def _style_tree(self):
        s = ttk.Style(self)
        s.theme_use("default")
        s.configure("Treeview", background=BG_CARD, foreground=TEXT_PRIMARY,
                    rowheight=28, fieldbackground=BG_CARD, borderwidth=0, font=FNT_MONO)
        s.configure("Treeview.Heading", background=BG_CARD2,
                    foreground=TEXT_HEADER, font=FNT_SM, relief="flat")
        s.map("Treeview",
              background=[("selected", BG_CARD2)],
              foreground=[("selected", ACCENT_BLUE)])

    def _hscroll(self, *args):
        self.tree.xview(*args)
        self.after_idle(self._draw_headers)

    # ── Header geometry ────────────────────────────────────────────────────────
    def _vis_widths(self) -> list[int]:
        return [self.tree.column(c, "width") for c in self._col_order]

    def _vis_offsets(self) -> list[int]:
        widths = self._vis_widths()
        total  = sum(widths)
        frac   = self.tree.xview()[0]
        scroll = int(frac * total) if total else 0
        offsets, x = [], -scroll
        for w in widths:
            offsets.append(x)
            x += w
        return offsets

    def _border_at(self, x: int) -> tuple[int | None, str | None]:
        for i, (ox, w) in enumerate(zip(self._vis_offsets(), self._vis_widths())):
            if abs(x - (ox + w)) <= self.RESIZE_ZONE:
                return i, self._col_order[i]
        return None, None

    def _col_at(self, x: int) -> tuple[int | None, str | None]:
        for i, (ox, w) in enumerate(zip(self._vis_offsets(), self._vis_widths())):
            if ox <= x < ox + w:
                return i, self._col_order[i]
        return None, None

    def _insert_at(self, x: int) -> int:
        offsets = self._vis_offsets()
        widths  = self._vis_widths()
        if not offsets:
            return 0
        best_idx, best_d = 0, float("inf")
        edges = [offsets[0]] + [offsets[i] + widths[i] // 2 for i in range(len(offsets))] \
                + [offsets[-1] + widths[-1]]
        for i, ex in enumerate(edges):
            d = abs(x - ex)
            if d < best_d:
                best_d, best_idx = d, i
        return min(best_idx, len(self._col_order))

    # ── Header draw ──────────────────────────────────────────────────────────
    def _draw_headers(self, ghost_col: str | None = None):
        cv = self._hdr_canvas
        cv.delete("all")
        H        = self.HDR_H
        widths   = self._vis_widths()
        offsets  = self._vis_offsets()
        cw       = cv.winfo_width() or 1100

        for i, col in enumerate(self._col_order):
            x0, x1 = offsets[i], offsets[i] + widths[i]
            if x1 < 0 or x0 > cw:
                continue
            label    = self.COL_META[col][0]
            is_sort  = col == self._sort_col
            is_ghost = col == ghost_col
            bg = "#2d3560" if is_ghost else ("#1e2540" if is_sort else BG_CARD2)
            cv.create_rectangle(x0, 0, x1 - 1, H - 1, fill=bg, outline=BORDER, width=1)
            arrow = (" ↑" if self._sort_asc else " ↓") if is_sort else ""
            cv.create_text(x0 + widths[i] // 2, H // 2,
                           text=label + arrow,
                           fill=TEXT_PRIMARY if is_sort else TEXT_HEADER,
                           font=FNT_SM, anchor="center",
                           width=max(widths[i] - 14, 10))
            cv.create_line(x1 - 1, 5, x1 - 1, H - 5, fill="#383d60", width=2)

        if ghost_col is not None and self._drag_insert_idx is not None:
            idx = min(self._drag_insert_idx, len(offsets))
            lx  = offsets[idx] if idx < len(offsets) else (offsets[-1] + widths[-1] if offsets else 0)
            cv.create_line(lx, 0, lx, H, fill=ACCENT_BLUE, width=2)

    # ── Header mouse events ──────────────────────────────────────────────────
    def _hdr_hover(self, event):
        ri, _ = self._border_at(event.x)
        self._hdr_canvas.config(cursor="sb_h_double_arrow" if ri is not None else "")

    def _hdr_press(self, event):
        ri, rcol = self._border_at(event.x)
        if ri is not None:
            self._is_resizing  = True
            self._resize_col   = rcol
            self._resize_start = event.x
            self._resize_orig  = self.tree.column(rcol, "width")
            return
        self._is_resizing = False
        idx, col = self._col_at(event.x)
        if col is None:
            return
        self._drag_col        = col
        self._drag_from_idx   = idx
        self._drag_start      = event.x
        self._drag_insert_idx = idx
        self._hdr_canvas.config(cursor="fleur")

    def _hdr_motion(self, event):
        if self._is_resizing and self._resize_col:
            new_w = max(30, self._resize_orig + (event.x - self._resize_start))
            self.tree.column(self._resize_col, width=new_w)
            self._draw_headers()
            return
        if self._drag_col is None:
            return
        self._drag_insert_idx = self._insert_at(event.x)
        self._draw_headers(ghost_col=self._drag_col)

    def _hdr_release(self, event):
        if self._is_resizing:
            self._is_resizing = False
            self._resize_col  = None
            self._hdr_canvas.config(cursor="")
            self._draw_headers()
            return
        if self._drag_col is None:
            return
        self._hdr_canvas.config(cursor="")
        drag_col = self._drag_col
        from_idx = self._drag_from_idx
        to_idx   = self._drag_insert_idx or from_idx
        self._drag_col = None

        if self._drag_start is not None and abs(event.x - self._drag_start) < 6:
            self._drag_start = None
            self._draw_headers()
            self._sort(drag_col)
            return
        self._drag_start = None

        to_idx = max(0, min(to_idx, len(self._col_order)))
        if to_idx not in (from_idx, from_idx + 1):
            order = list(self._col_order)
            order.pop(from_idx)
            order.insert(to_idx if to_idx <= from_idx else to_idx - 1, drag_col)
            self._col_order = order
            self.tree.configure(displaycolumns=self._col_order)
        self._draw_headers()
        self._refresh_table(self.opportunities)

    def _reset_col_order(self):
        self._col_order = list(self.DEFAULT_COL_ORDER)
        self.tree.configure(displaycolumns=self._col_order)
        for col in self.COL_META:
            self.tree.column(col, width=self.COL_META[col][1])
        self._draw_headers()
        self._refresh_table(self.opportunities)

    # ── Table formatting ─────────────────────────────────────────────────────
    _COL_FMT = {
        "coin":        lambda o: o["coin"],
        "direction":   lambda o: f"{o['buy_ex']}(L)  /  {o['sell_ex']}(S)",
        "prices":      lambda o: f"{_fmt_price(o['buy_price'])}  /  {_fmt_price(o['sell_price'])}",
        "spread":      lambda o: f"{o['spread']:+.3f}%",
        "funding":     lambda o: f"{o['fund_long']:.4f}%  /  {o['fund_short']:.4f}%",
        "fund_diff":   lambda o: f"{o['fund_diff']:.4f}%",
        "next_fund_h": lambda o: f"{_fmt_h(o.get('next_fund_h_buy', -1))} / {_fmt_h(o.get('next_fund_h_sell', -1))}",
    }

    def _refresh_table(self, opps: list[dict]):
        for r in self.tree.get_children():
            self.tree.delete(r)
        flt   = self.filter_coin.get().upper().strip()
        shown = [o for o in opps if flt in o["coin"].upper()] if flt else opps

        used_colors: set[str] = set()
        for o in shown:
            clr = self._coin_colors.get(o["coin"].upper())
            if clr:
                used_colors.add(clr)
        for clr in used_colors:
            self.tree.tag_configure(f"cc_{clr}", foreground=clr)

        for i, o in enumerate(shown):
            sp   = o["spread"]
            coin = o["coin"].upper()
            custom_clr = self._coin_colors.get(coin)

            if custom_clr:
                tag = f"cc_{custom_clr}"
            elif sp >= 2.0:
                tag = "hot"
            elif sp >= 0.5:
                tag = "good"
            else:
                tag = "low"

            values = tuple(self._COL_FMT[c](o) for c in self._ALL_COLS)
            self.tree.insert("", "end", iid=str(i), values=values,
                             tags=(tag, "alt" if i % 2 else ""))

        self.tree.tag_configure("hot",  foreground=ACCENT_GREEN)
        self.tree.tag_configure("good", foreground="#86efac")
        self.tree.tag_configure("low",  foreground="#94a3b8")
        self.tree.tag_configure("alt",  background=BG_ROW_ALT)
        self.after_idle(self._draw_headers)

    def _apply_filter(self):
        self._refresh_table(self.opportunities)

    def _sort(self, col: str):
        self._sort_asc = not self._sort_asc if self._sort_col == col else False
        self._sort_col = col
        num = {"spread", "fund_diff", "fund_long", "fund_short",
               "buy_price", "sell_price", "next_fund_h"}
        self.opportunities.sort(
            key=lambda o: float(o.get(col, 0)) if col in num else str(o.get(col, "")).upper(),
            reverse=not self._sort_asc)
        self._refresh_table(self.opportunities)
        self._draw_headers()

    def _refresh_stats(self):
        opps = self.opportunities
        n    = len(opps)
        self._sv["ku"].set(str(self.exchange_cnt.get("KuCoin",  0)))
        self._sv["ga"].set(str(self.exchange_cnt.get("Gate.io", 0)))
        self._sv["mx"].set(str(self.exchange_cnt.get("MEXC",    0)))
        self._sv["bs"].set(f"{opps[0]['spread']:+.3f}%" if opps else "—")
        avg = sum(o["spread"] for o in opps) / n if n else 0
        self._sv["ba"].set(f"{avg:+.3f}%" if n else "—")
        self._mv["best"].set(f"{opps[0]['spread']:+.3f}%" if opps else "—")
        self._mv["avg"].set(f"{avg:+.3f}%" if n else "—")
        max_fd = max((o["fund_diff"] for o in opps), default=0)
        self._mv["fund"].set(f"{max_fd:.4f}%" if n else "—")
        if self._exchange_errors:
            lines = [f"{ex}: {msg}" for ex, msg in self._exchange_errors.items()]
            self._err_var.set("\n".join(lines))
        else:
            self._err_var.set("")

    # ── Detail popup ─────────────────────────────────────────────────────────
    def _detail(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        idx   = int(sel[0])
        flt   = self.filter_coin.get().upper().strip()
        shown = [o for o in self.opportunities
                 if flt in o["coin"].upper()] if flt else self.opportunities
        if idx >= len(shown):
            return
        o = shown[idx]

        win = tk.Toplevel(self, bg=BG_CARD)
        win.title(f"{o['coin']} USDT Perp — Детали")
        win.geometry("460x450")
        win.resizable(False, False)

        tk.Label(win, text=f"⚡  {o['coin']} / USDT Perpetual",
                 font=("Segoe UI", 15, "bold"), bg=BG_CARD, fg=TEXT_PRIMARY).pack(pady=(20, 2))

        body = tk.Frame(win, bg=BG_CARD2, padx=22, pady=14)
        body.pack(fill="x", padx=22, pady=12)

        for lbl, val, clr in [
            ("Лонг (биржа)",       o["buy_ex"],                         ACCENT_GREEN),
            ("Символ лонга",       o["buy_symbol"],                      TEXT_HEADER),
            ("Mark Price (лонг)",  f"$ {_fmt_price(o['buy_price'])}",    TEXT_PRIMARY),
            ("Фандинг (лонг)",     f"{o['fund_long']:.4f}%",             ACCENT_PURPLE),
            ("", "", ""),
            ("Шорт (биржа)",       o["sell_ex"],                         ACCENT_RED),
            ("Символ шорта",       o["sell_symbol"],                      TEXT_HEADER),
            ("Mark Price (шорт)",  f"$ {_fmt_price(o['sell_price'])}",   TEXT_PRIMARY),
            ("Фандинг (шорт)",     f"{o['fund_short']:.4f}%",            ACCENT_PURPLE),
            ("", "", ""),
            ("Спред",              f"{o['spread']:+.4f}%",                 ACCENT_AMBER),
            ("Δ Фандинг",          f"{o['fund_diff']:.4f}%",              ACCENT_PURPLE),
            ("До фандинга (лонг)", _fmt_h(o.get("next_fund_h_buy", -1.0)),    TEXT_PRIMARY),
            ("До фандинга (шорт)", _fmt_h(o.get("next_fund_h_sell", -1.0)),   TEXT_PRIMARY),
            ("Интервал фандинга",  f"{o.get('fund_interval', 8)}ч",       TEXT_HEADER),
        ]:
            if not lbl:
                tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=4)
                continue
            r = tk.Frame(body, bg=BG_CARD2)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=lbl, font=FNT_SM, bg=BG_CARD2,
                     fg=TEXT_MUTED, width=22, anchor="w").pack(side="left")
            tk.Label(r, text=val, font=FNT_B, bg=BG_CARD2, fg=clr).pack(side="right")

        tk.Label(win, text="Проверяйте глубину стакана и скорость исполнения. Не финансовый совет.",
                 font=FNT_SM, bg=BG_CARD, fg=TEXT_MUTED, wraplength=400).pack(pady=(0, 8))
        tk.Button(win, text="Закрыть", font=FNT, bg=ACCENT_BLUE, fg="white",
                  relief="flat", padx=20, pady=6, cursor="hand2",
                  command=win.destroy).pack(pady=4)

    # ── Proxy manager (single window) ────────────────────────────────────────
    def _open_proxy_mgr(self):
        if self._proxy_win and self._proxy_win.winfo_exists():
            self._proxy_win.lift()
            self._proxy_win.focus_force()
            return

        global _proxy_cfg, _gate_proxy_cfg
        win = tk.Toplevel(self, bg=BG_CARD)
        self._proxy_win = win
        win.title("Настройка прокси")
        win.geometry("500x520")
        win.resizable(False, False)

        def _on_close():
            self._proxy_win.destroy()
            self._proxy_win = None
        win.protocol("WM_DELETE_WINDOW", _on_close)

        tk.Label(win, text="🔌  Настройка прокси", font=FNT_B,
                 bg=BG_CARD, fg=TEXT_PRIMARY).pack(pady=(16, 2))
        tk.Label(win,
                 text="Используйте для доступа к Gate.io без VPN.\n"
                      "Можно задать общий прокси и отдельный только для Gate.io.",
                 font=FNT_SM, bg=BG_CARD, fg=TEXT_MUTED, justify="center").pack(padx=20)

        def _make_proxy_block(parent, title: str, cfg_ref: list) -> dict:
            c = cfg_ref[0]
            tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=(10, 6))
            tk.Label(parent, text=title, font=("Segoe UI", 8, "bold"),
                     bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", padx=14)

            enabled_v = tk.BooleanVar(value=c.get("enabled", False))
            type_v    = tk.StringVar(value=c.get("type", "http"))
            host_v    = tk.StringVar(value=c.get("host", ""))
            port_v    = tk.StringVar(value=str(c.get("port", "1080")))
            user_v    = tk.StringVar(value=c.get("user", ""))
            pwd_v     = tk.StringVar(value=c.get("password", ""))

            tk.Checkbutton(parent, text="Включить", variable=enabled_v,
                           font=FNT_SM, bg=BG_CARD, fg=TEXT_PRIMARY,
                           activebackground=BG_CARD, selectcolor=BG_CARD2).pack(
                               anchor="w", padx=14, pady=2)

            row1 = tk.Frame(parent, bg=BG_CARD)
            row1.pack(fill="x", padx=14, pady=2)
            tk.Label(row1, text="Тип:", font=FNT_SM, bg=BG_CARD,
                     fg=TEXT_HEADER, width=10, anchor="w").pack(side="left")
            for ptype in ("http", "socks5"):
                tk.Radiobutton(row1, text=ptype.upper(), variable=type_v,
                               value=ptype, font=FNT_SM, bg=BG_CARD,
                               fg=TEXT_PRIMARY, activebackground=BG_CARD,
                               selectcolor=BG_CARD2).pack(side="left", padx=6)

            for lbl, var, w, show in [
                ("Хост:", host_v, 22, ""),
                ("Порт:", port_v, 7,  ""),
                ("Логин:", user_v, 18, ""),
                ("Пароль:", pwd_v, 18, "*"),
            ]:
                row = tk.Frame(parent, bg=BG_CARD)
                row.pack(fill="x", padx=14, pady=1)
                tk.Label(row, text=lbl, font=FNT_SM, bg=BG_CARD,
                         fg=TEXT_HEADER, width=10, anchor="w").pack(side="left")
                tk.Entry(row, textvariable=var, width=w, font=FNT_SM,
                         bg=BG_CARD2, fg=TEXT_PRIMARY,
                         insertbackground=TEXT_PRIMARY, show=show,
                         relief="flat", highlightthickness=1,
                         highlightbackground=BORDER,
                         highlightcolor=ACCENT_BLUE).pack(side="left")

            return {"enabled": enabled_v, "type": type_v, "host": host_v,
                    "port": port_v, "user": user_v, "password": pwd_v}

        global_ref = [dict(_proxy_cfg)]
        gate_ref   = [dict(_gate_proxy_cfg)]

        body = tk.Frame(win, bg=BG_CARD)
        body.pack(fill="both", expand=True)

        gv  = _make_proxy_block(body, "ГЛОБАЛЬНЫЙ ПРОКСИ (все биржи)",   global_ref)
        gv2 = _make_proxy_block(body, "ПРОКСИ ТОЛЬКО ДЛЯ GATE.IO",       gate_ref)

        btn_row = tk.Frame(win, bg=BG_CARD)
        btn_row.pack(fill="x", padx=14, pady=10)

        status_v = tk.StringVar(value="")
        tk.Label(btn_row, textvariable=status_v, font=FNT_SM,
                 bg=BG_CARD, fg=ACCENT_GREEN).pack(side="right", padx=8)

        def _extract(v: dict) -> dict:
            try:
                port = int(v["port"].get())
            except ValueError:
                port = 1080
            return {
                "enabled":  v["enabled"].get(),
                "type":     v["type"].get(),
                "host":     v["host"].get().strip(),
                "port":     port,
                "user":     v["user"].get().strip(),
                "password": v["password"].get().strip(),
            }

        def _test_proxy(v: dict):
            cfg = _extract(v)
            if not cfg["enabled"] or not cfg["host"]:
                messagebox.showinfo("Тест", "Прокси не включён или не задан хост.", parent=win)
                return
            status_v.set("Тестирую...")
            win.update()
            def _do_test():
                result = fetch("https://api.gateio.ws/api/v4/futures/usdt/tickers",
                               timeout=10, proxy=cfg)
                if isinstance(result, list):
                    win.after(0, lambda: status_v.set(f"✓ Gate.io: {len(result)} тикеров"))
                else:
                    err = result.get("_fetch_error", "?") if isinstance(result, dict) else str(result)
                    win.after(0, lambda: status_v.set(f"✗ {err}"))
            threading.Thread(target=_do_test, daemon=True).start()

        def _save_proxy():
            global _proxy_cfg, _gate_proxy_cfg
            _proxy_cfg      = _extract(gv)
            _gate_proxy_cfg = _extract(gv2)
            save_settings(self._collect_settings())
            log.info("Proxy saved")
            status_v.set("✓ Сохранено")
            win.after(2500, lambda: status_v.set(""))

        tk.Button(btn_row, text="🔍  Тест Gate.io (глобал.)", font=FNT_SM,
                  bg=BG_CARD2, fg=TEXT_PRIMARY, relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=lambda: _test_proxy(gv)).pack(side="left", padx=4)
        tk.Button(btn_row, text="🔍  Тест Gate.io (gate-прокси)", font=FNT_SM,
                  bg=BG_CARD2, fg=TEXT_PRIMARY, relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=lambda: _test_proxy(gv2)).pack(side="left", padx=4)
        tk.Button(btn_row, text="💾  Сохранить", font=FNT_SM,
                  bg=ACCENT_BLUE, fg="white", relief="flat",
                  padx=12, pady=5, cursor="hand2",
                  command=_save_proxy).pack(side="left", padx=6)

    # ── Coin manager ─────────────────────────────────────────────────────────
    def _open_coin_manager(self):
        win = tk.Toplevel(self, bg=BG_CARD)
        win.title("Управление монетами")
        win.geometry("480x560")
        win.resizable(False, False)

        PRESET_COLORS = [
            ("#ef4444", "Красный"), ("#f59e0b", "Жёлтый"), ("#22c55e", "Зелёный"),
            ("#3b82f6", "Синий"), ("#a855f7", "Фиолетовый"), ("#06b6d4", "Голубой"),
            ("#f97316", "Оранжевый"), ("#ec4899", "Розовый"),
        ]

        tk.Label(win, text="Управление монетами", font=FNT_B,
                 bg=BG_CARD, fg=TEXT_PRIMARY).pack(pady=(16, 4))
        tk.Label(win, text="Введите тикер (BTC, ETH…) и выберите действие.\n"
                           "Исключённые монеты скрыты из результатов.",
                 font=FNT_SM, bg=BG_CARD, fg=TEXT_MUTED).pack(padx=16)

        inp_frm = tk.Frame(win, bg=BG_CARD)
        inp_frm.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(inp_frm, text="Монета:", font=FNT_SM,
                 bg=BG_CARD, fg=TEXT_HEADER).pack(side="left")
        coin_var = tk.StringVar()
        tk.Entry(inp_frm, textvariable=coin_var, width=10,
                 font=FNT, bg=BG_CARD2, fg=TEXT_PRIMARY,
                 insertbackground=TEXT_PRIMARY, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT_BLUE).pack(side="left", padx=8)

        color_var = tk.StringVar(value="")
        clr_frm = tk.Frame(win, bg=BG_CARD)
        clr_frm.pack(fill="x", padx=16, pady=4)
        tk.Label(clr_frm, text="Цвет:", font=FNT_SM,
                 bg=BG_CARD, fg=TEXT_HEADER).pack(side="left")
        for hex_clr, name in PRESET_COLORS:
            b = tk.Radiobutton(clr_frm, text="", variable=color_var, value=hex_clr,
                               bg=BG_CARD, activebackground=BG_CARD,
                               selectcolor=hex_clr,
                               indicatoron=True, relief="flat",
                               cursor="hand2")
            b.pack(side="left", padx=1)
            swatch = tk.Label(clr_frm, text="  ", bg=hex_clr,
                              width=2, relief="flat", cursor="hand2")
            swatch.pack(side="left", padx=1)
            swatch.bind("<Button-1>", lambda e, c=hex_clr: color_var.set(c))

        btn_frm = tk.Frame(win, bg=BG_CARD)
        btn_frm.pack(fill="x", padx=16, pady=8)

        def _add_color():
            coin = coin_var.get().strip().upper()
            clr  = color_var.get().strip()
            if not coin:
                return
            if not clr:
                messagebox.showwarning("Цвет не выбран", "Выберите цвет для монеты.", parent=win)
                return
            self._coin_colors[coin] = clr
            self._excluded.discard(coin)
            coin_var.set("")
            _refresh_list()
            self._refresh_table(self.opportunities)

        def _add_exclude():
            coin = coin_var.get().strip().upper()
            if not coin:
                return
            self._excluded.add(coin)
            self._coin_colors.pop(coin, None)
            coin_var.set("")
            _refresh_list()
            self.opportunities = [o for o in self.opportunities
                                  if o["coin"].upper() != coin]
            self._refresh_table(self.opportunities)

        def _remove_selected():
            sel = listbox.curselection()
            if not sel:
                return
            text = listbox.get(sel[0]).split()[0].upper()
            self._excluded.discard(text)
            self._coin_colors.pop(text, None)
            _refresh_list()
            self._refresh_table(self.opportunities)

        tk.Button(btn_frm, text="🎨 Назначить цвет", font=FNT_SM,
                  bg=BG_CARD2, fg=TEXT_PRIMARY, relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=_add_color).pack(side="left", padx=(0, 6))
        tk.Button(btn_frm, text="🚫 Исключить", font=FNT_SM,
                  bg=BG_CARD2, fg=ACCENT_RED, relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=_add_exclude).pack(side="left", padx=6)
        tk.Button(btn_frm, text="✕ Удалить выбранное", font=FNT_SM,
                  bg=BG_CARD2, fg=TEXT_MUTED, relief="flat",
                  padx=10, pady=5, cursor="hand2",
                  command=_remove_selected).pack(side="left", padx=6)

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))
        tk.Label(win, text="Текущие правила:", font=FNT_SM,
                 bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", padx=16, pady=(6, 2))

        list_frm = tk.Frame(win, bg=BG_CARD2)
        list_frm.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        scrollbar = tk.Scrollbar(list_frm)
        scrollbar.pack(side="right", fill="y")
        listbox = tk.Listbox(list_frm, font=FNT_MONO, bg=BG_CARD2, fg=TEXT_PRIMARY,
                             selectbackground=ACCENT_BLUE, selectforeground="white",
                             relief="flat", borderwidth=0,
                             yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        def _refresh_list():
            listbox.delete(0, "end")
            for coin in sorted(self._excluded):
                listbox.insert("end", f"{coin}   [исключена]")
                listbox.itemconfig("end", foreground=ACCENT_RED)
            for coin, clr in sorted(self._coin_colors.items()):
                listbox.insert("end", f"{coin}   [цвет: {clr}]")
                listbox.itemconfig("end", foreground=clr)

        _refresh_list()

        win.protocol("WM_DELETE_WINDOW", lambda: (
            save_settings(self._collect_settings()), win.destroy()
        ))

    # ── Code editor (single window) ──────────────────────────────────────────
    def _open_editor(self):
        if self._editor_win and self._editor_win.winfo_exists():
            self._editor_win.lift()
            self._editor_win.focus_force()
            return

        win = tk.Toplevel(self, bg=BG_CARD)
        self._editor_win = win
        win.title("Редактор кода — " + os.path.basename(_SCRIPT_PATH))
        win.geometry("920x700")

        def _on_close():
            self._editor_win.destroy()
            self._editor_win = None
        win.protocol("WM_DELETE_WINDOW", _on_close)

        bar = tk.Frame(win, bg=BG_CARD2, pady=6)
        bar.pack(fill="x")

        status_var = tk.StringVar(value="")
        tk.Label(bar, textvariable=status_var, font=FNT_SM,
                 bg=BG_CARD2, fg=ACCENT_GREEN).pack(side="right", padx=12)

        def _validate():
            code = editor.get("1.0", "end-1c")
            try:
                compile(code, _SCRIPT_PATH, "exec")
                return code
            except SyntaxError as e:
                messagebox.showerror("Синтаксическая ошибка", str(e), parent=win)
                return None

        def _save_apply():
            code = _validate()
            if code is None:
                return
            try:
                with open(_SCRIPT_PATH, "w", encoding="utf-8") as f:
                    f.write(code)
            except Exception as e:
                messagebox.showerror("Ошибка записи", str(e), parent=win)
                return
            try:
                exec(compile(code, _SCRIPT_PATH, "exec"), globals())
                status_var.set("✓ Применено (hot-reload)")
                win.after(3000, lambda: status_var.set(""))
                messagebox.showinfo("Hot-reload", "Код сохранён и применён.", parent=win)
            except Exception as e:
                messagebox.showerror("Ошибка выполнения", str(e), parent=win)

        def _save_only():
            code = _validate()
            if code is None:
                return
            try:
                with open(_SCRIPT_PATH, "w", encoding="utf-8") as f:
                    f.write(code)
                status_var.set("✓ Сохранено")
                win.after(3000, lambda: status_var.set(""))
            except Exception as e:
                messagebox.showerror("Ошибка записи", str(e), parent=win)

        def _reload():
            try:
                with open(_SCRIPT_PATH, "r", encoding="utf-8") as f:
                    src = f.read()
                editor.delete("1.0", "end")
                editor.insert("1.0", src)
                status_var.set("↺ Перечитано")
                win.after(2000, lambda: status_var.set(""))
            except Exception as e:
                messagebox.showerror("Ошибка", str(e), parent=win)

        tk.Button(bar, text="💾  Сохранить + применить", font=FNT,
                  bg=ACCENT_BLUE, fg="white", relief="flat", padx=12, pady=4,
                  cursor="hand2", command=_save_apply).pack(side="left", padx=8)
        tk.Button(bar, text="💾  Только сохранить", font=FNT,
                  bg=BG_CARD2, fg=TEXT_MUTED, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=_save_only).pack(side="left", padx=4)
        tk.Button(bar, text="↺  Перечитать", font=FNT,
                  bg=BG_CARD2, fg=TEXT_MUTED, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=_reload).pack(side="left", padx=4)
        tk.Label(bar, text=_SCRIPT_PATH, font=FNT_SM,
                 bg=BG_CARD2, fg=TEXT_MUTED).pack(side="left", padx=10)

        editor = scrolledtext.ScrolledText(
            win, font=("Consolas", 11), bg="#080b12", fg="#d4d4d4",
            insertbackground="#aeafad", wrap="none",
            selectbackground=ACCENT_BLUE, selectforeground="white",
            relief="flat", borderwidth=0, undo=True, maxundo=200)
        editor.pack(fill="both", expand=True)

        def _paste(event=None):
            try:
                text = editor.clipboard_get()
                try:
                    editor.delete("sel.first", "sel.last")
                except tk.TclError:
                    pass
                editor.insert(tk.INSERT, text)
            except tk.TclError:
                pass
            return "break"

        editor.bind("<Control-v>", _paste)
        editor.bind("<Control-V>", _paste)
        editor.bind("<Control-s>", lambda e: (_save_only(), "break")[1])
        editor.bind("<Control-S>", lambda e: (_save_only(), "break")[1])

        try:
            with open(_SCRIPT_PATH, "r", encoding="utf-8") as f:
                editor.insert("1.0", f.read())
        except Exception as e:
            editor.insert("1.0", f"# Ошибка чтения файла: {e}")

    # ── Scan / Auto-refresh ──────────────────────────────────────────────────
    def _start_scan(self):
        with self._scan_lock:
            if self._scan_active:
                log.warning("Scan already running — ignored")
                return
            self._scan_active    = True
            self._stop_requested = False
        self._scan_btn.config(state="disabled", text="⏳ Сканирование...")
        self._stop_btn.config(state="normal")
        self._prog.set("Подключаюсь...")
        log.info("=== Scan started ===")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _stop_scan(self):
        self._stop_requested = True
        self._stop_btn.config(state="disabled")
        self._prog.set("Остановка...")
        log.info("=== Stop requested ===")

    def _scan_worker(self):
        all_data:       dict[str, dict[str, dict]] = {}
        exchange_cnt:   dict[str, int]  = {}
        exchange_errors:dict[str, str]  = {}

        try:
            for ex, fn in FETCHERS.items():
                if self._stop_requested:
                    log.info("Scan stopped before %s", ex)
                    break
                self._set_prog(f"Загружаю {ex}...")
                self._set_dot(ex, "amber")
                try:
                    data, err = fn()
                    all_data[ex]       = data
                    exchange_cnt[ex]   = len(data)
                    if err:
                        exchange_errors[ex] = err
                        log.warning("[%s] Error: %s", ex, err)
                    self._set_dot(ex, "green" if data else "red")
                    log.info("[%s] Done: %d pairs", ex, len(data))
                except Exception as e:
                    all_data[ex]        = {}
                    exchange_cnt[ex]    = 0
                    exchange_errors[ex] = str(e)
                    self._set_dot(ex, "red")
                    log.error("[%s] Exception: %s\n%s", ex, e, traceback.format_exc())

            if not self._stop_requested:
                self._set_prog("Считаю арбитраж...")
                try:    mn_sp = float(self.min_spread.get())
                except: mn_sp = 0.5
                try:    mn_fd = float(self.min_fund_diff.get())
                except: mn_fd = 0.0

                log.info("Finding opportunities (min_spread=%.2f, min_fund_diff=%.4f)", mn_sp, mn_fd)
                opportunities = find_opportunities(
                    all_data, self._excluded, mn_sp, mn_fd,
                    use_mark=self.use_mark.get())
                log.info("Found %d opportunities", len(opportunities))

                self.all_data         = all_data
                self.exchange_cnt     = exchange_cnt
                self._exchange_errors = exchange_errors
                self.opportunities    = opportunities
            else:
                log.info("Scan stopped — skipping arbitrage calculation")

        except Exception as e:
            log.error("Scan worker fatal: %s\n%s", e, traceback.format_exc())
        finally:
            with self._scan_lock:
                self._scan_active = False
            log.info("=== Scan finished ===")

        self.after(0, self._on_scan_done)

    def _on_scan_done(self):
        self._scan_btn.config(state="normal", text="▶  Сканировать")
        self._stop_btn.config(state="disabled")
        self._prog.set("" if not self._stop_requested else "⏹ Остановлено")
        if self._stop_requested:
            self.after(2000, lambda: self._prog.set(""))
            return

        num = {"spread", "fund_diff", "fund_long", "fund_short",
               "buy_price", "sell_price", "next_fund_h"}
        col = self._sort_col
        self.opportunities.sort(
            key=lambda o: float(o.get(col, 0)) if col in num else str(o.get(col, "")).upper(),
            reverse=not self._sort_asc)

        self._refresh_table(self.opportunities)
        self._refresh_stats()
        self._ts_var.set("Обновлено: " + datetime.now().strftime("%H:%M:%S"))

    def _on_auto_toggle(self):
        if self.auto_refresh.get():
            self._sched()
        elif self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

    def _sched(self):
        if not self.auto_refresh.get():
            return
        self._after_id = self.after(max(10, self.refresh_sec.get()) * 1000, self._auto)

    def _auto(self):
        self._start_scan()
        self._sched()

    def _set_prog(self, msg: str):
        self.after(0, lambda: self._prog.set(msg))

    def _set_dot(self, ex: str, color: str):
        c = {"green": ACCENT_GREEN, "red": ACCENT_RED, "amber": ACCENT_AMBER}.get(color, TEXT_MUTED)
        self.after(0, lambda: self._dots[ex].config(fg=c))


if __name__ == "__main__":
    app = FuturesArbitrageApp()
    app.mainloop()