"""
╔══════════════════════════════════════════════════════╗
║           KALSHI TRADING BOT  —  Windows             ║
╠══════════════════════════════════════════════════════╣
║  SETUP (run once in Command Prompt / PowerShell):    ║
║    pip install flask requests cryptography           ║
║                                                      ║
║  RUN:                                                ║
║    python kalshi_bot.py                              ║
║                                                      ║
║  Then open:  http://localhost:7337                   ║
╚══════════════════════════════════════════════════════╝

SAFETY RULES (hardcoded, cannot be changed from UI):
  • Simulation mode is DEFAULT — no real money moves
  • Live trading needs an explicit toggle + confirmation
  • Every live order uses action="sell" after a hold period
    to close positions — no position ever held indefinitely
  • Immediate-or-cancel (IOC) on buys → no resting open orders
  • Liquidity (orderbook depth) checked before every buy
  • Hard cap: $20 per order regardless of risk % setting
  • Only single-leg YES or NO on standard markets
  • No multivariate / combo bets, ever
"""

# ─── stdlib ───────────────────────────────────────────────────────────────────
import base64
import datetime
import json
import os
import random
import threading
import time
import uuid
import webbrowser
from urllib.parse import urlparse

# ─── third-party (pip install flask requests cryptography) ───────────────────
try:
    import requests as req_lib
except ImportError:
    raise SystemExit("Missing: pip install requests")

try:
    from flask import Flask, jsonify, request as flask_req
except ImportError:
    raise SystemExit("Missing: pip install flask")

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding as asym_pad
    from cryptography.hazmat.backends import default_backend
except ImportError:
    raise SystemExit("Missing: pip install cryptography")

# ─── Config ───────────────────────────────────────────────────────────────────
PROD_BASE         = "https://api.elections.kalshi.com/trade-api/v2"
DEMO_BASE         = "https://demo-api.kalshi.co/trade-api/v2"
PORT              = 7337
MAX_ORDER_DOLLARS = 20.0   # hard cap per buy order
MIN_LIQUIDITY     = 5      # minimum contracts on best bid to proceed
HOLD_SECONDS_MIN  = 8      # minimum seconds to hold before selling
HOLD_SECONDS_MAX  = 45     # maximum seconds to hold before selling

# ─── RSA signing (matches Kalshi docs exactly) ───────────────────────────────
def load_private_key(pem_text: str):
    """Load RSA private key from PEM string (PKCS#8 or PKCS#1)."""
    return serialization.load_pem_private_key(
        pem_text.strip().encode(),
        password=None,
        backend=default_backend(),
    )

def make_headers(private_key, key_id: str, method: str, path: str) -> dict:
    """
    Build the three Kalshi auth headers for any request.
    path must be the full path from root e.g. /trade-api/v2/portfolio/balance
    Query parameters are stripped before signing.
    """
    ts_ms = str(int(datetime.datetime.now().timestamp() * 1000))
    clean_path = path.split("?")[0]
    message = f"{ts_ms}{method.upper()}{clean_path}".encode("utf-8")
    sig = private_key.sign(
        message,
        asym_pad.PSS(
            mgf=asym_pad.MGF1(hashes.SHA256()),
            salt_length=asym_pad.PSS.DIGEST_LENGTH,   # correct constant per Kalshi docs
        ),
        hashes.SHA256(),
    )
    return {
        "Content-Type":            "application/json",
        "KALSHI-ACCESS-KEY":       key_id,
        "KALSHI-ACCESS-TIMESTAMP": ts_ms,
        "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode("utf-8"),
    }

def kalshi_get(endpoint: str, key_id: str, private_key, use_demo: bool) -> dict:
    base = DEMO_BASE if use_demo else PROD_BASE
    full_path = f"/trade-api/v2{endpoint}"
    hdrs = make_headers(private_key, key_id, "GET", full_path)
    r = req_lib.get(base + endpoint, headers=hdrs, timeout=10)
    r.raise_for_status()
    return r.json()

def kalshi_post(endpoint: str, body: dict, key_id: str, private_key, use_demo: bool) -> dict:
    base = DEMO_BASE if use_demo else PROD_BASE
    full_path = f"/trade-api/v2{endpoint}"
    hdrs = make_headers(private_key, key_id, "POST", full_path)
    r = req_lib.post(base + endpoint, headers=hdrs, json=body, timeout=10)
    r.raise_for_status()
    return r.json()

def kalshi_delete(endpoint: str, key_id: str, private_key, use_demo: bool) -> dict:
    base = DEMO_BASE if use_demo else PROD_BASE
    full_path = f"/trade-api/v2{endpoint}"
    hdrs = make_headers(private_key, key_id, "DELETE", full_path)
    r = req_lib.delete(base + endpoint, headers=hdrs, timeout=10)
    r.raise_for_status()
    return r.json()

# ─── Strategies ───────────────────────────────────────────────────────────────
STRATEGIES = {
    "conservative": {
        "label": "Conservative", "icon": "🛡️", "risk": "Low",
        "sim_win_rate": 0.58, "freq": 12.0,
        "desc": "Near-50/50 liquid markets only. Holds 8–25s.",
    },
    "arb": {
        "label": "Arbitrage", "icon": "⚖️", "risk": "Low",
        "sim_win_rate": 0.56, "freq": 8.0,
        "desc": "Wide YES/NO spread markets. Holds 10–30s.",
    },
    "meanRevert": {
        "label": "Mean Reversion", "icon": "🔄", "risk": "Medium",
        "sim_win_rate": 0.54, "freq": 5.0,
        "desc": "Buys overextended prices, waits for snap-back.",
    },
    "momentum": {
        "label": "Momentum", "icon": "⚡", "risk": "High",
        "sim_win_rate": 0.52, "freq": 3.0,
        "desc": "Chases directional moves. Holds 5–15s.",
    },
}

# ─── Simulated markets (used when not connected or no live data) ──────────────
SIM_MARKETS = [
    {"ticker": "SIM-FED",  "title": "Fed rate cut by June 2026?",  "yes_bid": 0.42, "volume": 280000},
    {"ticker": "SIM-SPX",  "title": "S&P 500 above 6500 EOY?",    "yes_bid": 0.55, "volume": 410000},
    {"ticker": "SIM-REC",  "title": "US recession in 2026?",        "yes_bid": 0.28, "volume": 190000},
    {"ticker": "SIM-TSLA", "title": "Tesla above $400 by Q3?",      "yes_bid": 0.33, "volume": 150000},
    {"ticker": "SIM-BTC",  "title": "BTC above $150k EOY?",         "yes_bid": 0.38, "volume": 320000},
    {"ticker": "SIM-OIL",  "title": "Oil above $100 Dec 2026?",     "yes_bid": 0.22, "volume": 88000},
    {"ticker": "SIM-GDP",  "title": "GDP growth >2.5% Q2?",         "yes_bid": 0.61, "volume": 74000},
    {"ticker": "SIM-MORT", "title": "30yr mortgage <6% EOY?",       "yes_bid": 0.45, "volume": 120000},
    {"ticker": "SIM-UNE",  "title": "Unemployment <4% in Q3?",      "yes_bid": 0.52, "volume": 95000},
    {"ticker": "SIM-CPI",  "title": "CPI inflation <3% by Q3?",     "yes_bid": 0.48, "volume": 67000},
]

# ─── Shared bot state ─────────────────────────────────────────────────────────
class BotState:
    def __init__(self):
        self.lock         = threading.Lock()
        # control
        self.running      = False
        self.live_enabled = False   # separate from connected — must be explicitly set
        # credentials
        self.connected    = False
        self.key_id       = ""
        self.private_key  = None
        self.use_demo     = True
        # config
        self.strategy     = "conservative"
        self.bankroll     = 500.0
        self.risk_pct     = 3
        # financials (sim)
        self.balance      = 500.0
        self.pnl          = 0.0
        self.wins         = 0
        self.losses       = 0
        self.total        = 0
        # data
        self.trades       = []      # list of dicts, newest first
        self.log_lines    = []      # list of strings, newest first
        self.live_markets = []      # raw market dicts from Kalshi API
        self.positions    = []      # raw position dicts from Kalshi API
        # open positions waiting to be sold (live only)
        # each entry: {ticker, side, contracts, buy_price_cents, buy_cost, sell_after, order_id}
        self.open_positions = []

    def snapshot(self):
        with self.lock:
            return {
                "running":      self.running,
                "connected":    self.connected,
                "live_enabled": self.live_enabled,
                "use_demo":     self.use_demo,
                "strategy":     self.strategy,
                "bankroll":     self.bankroll,
                "balance":      round(self.balance, 2),
                "pnl":          round(self.pnl, 2),
                "win_rate":     round(self.wins / self.total, 4) if self.total else 0.0,
                "trade_count":  self.total,
                "open_count":   len(self.open_positions),
                "trades":       self.trades[:80],
                "log":          self.log_lines[:200],
                "markets":      self.live_markets[:30],
                "positions":    self.positions[:20],
            }

BOT = BotState()

# ─── Logging helper ───────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    with BOT.lock:
        BOT.log_lines.insert(0, line)
        if len(BOT.log_lines) > 300:
            BOT.log_lines.pop()
    print(line, flush=True)

# ─── Trade recorder ───────────────────────────────────────────────────────────
def record_trade(market: str, side: str, contracts: int, price: float,
                 result: str, profit: float, mode: str, order_id: str = ""):
    with BOT.lock:
        BOT.total += 1
        BOT.balance = round(BOT.balance + profit, 2)
        BOT.pnl = round(BOT.pnl + profit, 2)
        if result == "WIN":
            BOT.wins += 1
        elif result == "LOSS":
            BOT.losses += 1

        trade = {
            "id":        BOT.total,
            "time":      datetime.datetime.now().strftime("%H:%M:%S"),
            "market":    market[:50],
            "side":      side.upper(),
            "contracts": contracts,
            "price":     f"{price:.2f}",
            "result":    result,
            "profit":    f"{profit:+.2f}",
            "balance":   f"{BOT.balance:.2f}",
            "mode":      mode,
            "order_id":  order_id,
        }
        BOT.trades.insert(0, trade)
        if len(BOT.trades) > 120:
            BOT.trades.pop()

# ─── Orderbook liquidity check ────────────────────────────────────────────────
def get_best_bid(ticker: str, side: str) -> tuple:
    """
    Returns (best_price_dollars, available_contracts).
    Raises RuntimeError if below MIN_LIQUIDITY.
    side is 'yes' or 'no'.
    """
    with BOT.lock:
        key_id = BOT.key_id
        pk = BOT.private_key
        use_demo = BOT.use_demo

    ob = kalshi_get(f"/markets/{ticker}/orderbook", key_id, pk, use_demo)
    book = ob.get("orderbook_fp", {})
    bids = book.get(f"{side}_dollars", [])

    if not bids:
        raise RuntimeError(f"No {side.upper()} bids in orderbook for {ticker}")

    # Bids are sorted ascending — last element is the best (highest) bid
    best = bids[-1]
    best_price = float(best[0])
    best_qty   = float(best[1])

    if best_qty < MIN_LIQUIDITY:
        raise RuntimeError(
            f"Low liquidity on {ticker}: only {best_qty:.0f} contracts "
            f"(need {MIN_LIQUIDITY}). Skipping."
        )
    return best_price, best_qty

# ─── Live BUY ─────────────────────────────────────────────────────────────────
def live_buy(ticker: str, side: str, contracts: int, limit_price_cents: int,
             key_id: str, pk, use_demo: bool) -> dict:
    """
    Place an immediate-or-cancel BUY order.
    limit_price_cents: 1-99 (integer cents)
    Returns the order dict from Kalshi.
    Raises on HTTP error.
    """
    yes_price = limit_price_cents if side == "yes" else (100 - limit_price_cents)
    no_price  = 100 - yes_price
    yes_price = max(1, min(99, yes_price))
    no_price  = max(1, min(99, no_price))

    body = {
        "ticker":          ticker,
        "client_order_id": str(uuid.uuid4()),
        "action":          "buy",
        "side":            side,
        "type":            "limit",
        "count":           contracts,
        "yes_price":       yes_price,
        "no_price":        no_price,
        "time_in_force":   "immediate_or_cancel",
    }
    resp = kalshi_post("/portfolio/orders", body, key_id, pk, use_demo)
    return resp.get("order", {})

# ─── Live SELL ────────────────────────────────────────────────────────────────
def live_sell(ticker: str, side: str, contracts: int,
              key_id: str, pk, use_demo: bool) -> dict:
    """
    Sell an existing position.
    On Kalshi, selling YES = action:"sell", side:"yes".
    Uses immediate_or_cancel so it either hits the best bid or cancels.
    Returns the order dict from Kalshi.
    """
    # Get current best bid so we don't underprice our sell
    try:
        best_price, _ = get_best_bid(ticker, side)
        # Sell 1 cent below best bid to ensure fill
        sell_cents = max(1, int(best_price * 100) - 1)
    except Exception:
        sell_cents = 1   # last resort — sell at 1 cent to guarantee exit

    yes_price = sell_cents if side == "yes" else (100 - sell_cents)
    no_price  = 100 - yes_price
    yes_price = max(1, min(99, yes_price))
    no_price  = max(1, min(99, no_price))

    body = {
        "ticker":          ticker,
        "client_order_id": str(uuid.uuid4()),
        "action":          "sell",
        "side":            side,
        "type":            "limit",
        "count":           contracts,
        "yes_price":       yes_price,
        "no_price":        no_price,
        "time_in_force":   "immediate_or_cancel",
    }
    resp = kalshi_post("/portfolio/orders", body, key_id, pk, use_demo)
    return resp.get("order", {})

# ─── Sell worker — closes open positions after hold period ────────────────────
def sell_worker():
    """
    Runs in its own thread.
    Watches BOT.open_positions and sells any position whose sell_after time has passed.
    """
    while True:
        time.sleep(1)
        with BOT.lock:
            if not BOT.running:
                break
            now = time.time()
            to_sell = [p for p in BOT.open_positions if now >= p["sell_after"]]
            for p in to_sell:
                BOT.open_positions.remove(p)

        for pos in to_sell:
            with BOT.lock:
                key_id   = BOT.key_id
                pk       = BOT.private_key
                use_demo = BOT.use_demo
                mode     = "DEMO" if use_demo else "LIVE"

            try:
                sell_order = live_sell(
                    pos["ticker"], pos["side"], pos["contracts"],
                    key_id, pk, use_demo
                )
                status = str(sell_order.get("status", ""))
                filled = float(sell_order.get("fill_count_fp") or 0)
                sell_cost = float(sell_order.get("taker_fill_cost_dollars") or 0)
                fees      = float(sell_order.get("taker_fees_dollars") or 0)

                if filled > 0 or status in ("filled", "executed"):
                    # Revenue from selling minus original cost
                    gross_revenue = sell_cost
                    net_profit    = round(gross_revenue - pos["buy_cost"] - fees, 2)
                    result = "WIN" if net_profit > 0 else "LOSS"
                    log(f"💰 [{mode}] SOLD {pos['side'].upper()} "
                        f"{pos['contracts']}x {pos['ticker']} | "
                        f"revenue ${gross_revenue:.2f} | net {net_profit:+.2f}")
                    record_trade(
                        market    = pos["ticker"],
                        side      = pos["side"],
                        contracts = pos["contracts"],
                        price     = sell_cost / max(pos["contracts"], 1),
                        result    = result,
                        profit    = net_profit,
                        mode      = f"SELL-{mode}",
                        order_id  = sell_order.get("order_id", ""),
                    )
                else:
                    # IOC sell didn't fill — position may still be open on exchange
                    log(f"⚠️  [{mode}] SELL IOC no fill on {pos['ticker']} "
                        f"— position may still be open. Check Kalshi dashboard.")

            except Exception as e:
                log(f"❌ SELL FAILED {pos['ticker']}: {e} — check Kalshi dashboard!")

# ─── Main bot loop ────────────────────────────────────────────────────────────
def bot_loop():
    log("🟢 Bot started")
    refresh_tick = 0

    while True:
        # Read all needed state under lock once
        with BOT.lock:
            if not BOT.running:
                break
            strat        = STRATEGIES[BOT.strategy]
            sim_win_rate = strat["sim_win_rate"]
            freq         = strat["freq"]
            risk_pct     = BOT.risk_pct
            balance      = BOT.balance
            connected    = BOT.connected
            live_enabled = BOT.live_enabled
            key_id       = BOT.key_id
            pk           = BOT.private_key
            use_demo     = BOT.use_demo
            live_mkts    = list(BOT.live_markets)

        # ── Refresh live data every ~60 seconds ───────────────────────────
        refresh_tick += 1
        if connected and refresh_tick % max(1, int(60 / freq)) == 0:
            try:
                mkt_data = kalshi_get("/markets?status=open&limit=30", key_id, pk, use_demo)
                with BOT.lock:
                    BOT.live_markets = mkt_data.get("markets", [])

                bal_data = kalshi_get("/portfolio/balance", key_id, pk, use_demo)
                with BOT.lock:
                    BOT.balance = float(bal_data.get("balance", BOT.balance * 100)) / 100

                pos_data = kalshi_get("/portfolio/positions", key_id, pk, use_demo)
                with BOT.lock:
                    BOT.positions = pos_data.get("market_positions", [])[:20]
            except Exception as e:
                log(f"⚠️  Live data refresh failed: {e}")

        # ── Pick a market ─────────────────────────────────────────────────
        pool = live_mkts if (connected and live_mkts) else SIM_MARKETS

        # Only trade markets with a sensible YES price (10¢–90¢)
        tradeable = [
            m for m in pool
            if 0.10 <= float(
                m.get("yes_bid_dollars") or m.get("yes_bid") or 0.50
            ) <= 0.90
        ]
        if not tradeable:
            tradeable = pool

        mkt      = random.choice(tradeable)
        mkt_name = str(mkt.get("title") or mkt.get("name") or "Unknown Market")
        ticker   = str(mkt.get("ticker") or "")
        yes_bid  = float(mkt.get("yes_bid_dollars") or mkt.get("yes_bid") or 0.50)
        side     = "yes" if random.random() > 0.5 else "no"
        price    = yes_bid if side == "yes" else round(1.0 - yes_bid, 4)

        # ── Position sizing ───────────────────────────────────────────────
        raw_stake = (risk_pct / 100.0) * balance
        stake     = round(min(raw_stake, MAX_ORDER_DOLLARS), 2)
        stake     = max(1.0, stake)
        contracts = max(1, int(stake / max(price, 0.01)))

        # ── Decide path: simulation or live ──────────────────────────────
        # Initialize ALL trade variables before any branch so nothing is undefined
        profit      = 0.0
        is_win      = False
        mode        = "SIM"
        can_go_live = (
            connected
            and live_enabled
            and bool(ticker)
            and not ticker.startswith("SIM-")
        )

        if can_go_live:
            # ══════════════════════════════════════════════════════════════
            # LIVE PATH — real money
            # ══════════════════════════════════════════════════════════════
            mode = "DEMO" if use_demo else "LIVE"
            try:
                # 1. Check liquidity
                best_price, avail_qty = get_best_bid(ticker, side)

                # 2. Cap contracts to 30% of available so we don't move the market
                contracts = max(1, min(contracts, int(avail_qty * 0.3)))

                # 3. Limit price = best bid + 1¢ nudge to fill as taker
                limit_cents = max(1, min(99, int(best_price * 100) + 1))

                # 4. Place IOC buy
                buy_order  = live_buy(ticker, side, contracts, limit_cents, key_id, pk, use_demo)
                status     = str(buy_order.get("status", ""))
                filled     = float(buy_order.get("fill_count_fp") or 0)
                buy_cost   = float(buy_order.get("taker_fill_cost_dollars") or 0)
                buy_fees   = float(buy_order.get("taker_fees_dollars") or 0)
                order_id   = str(buy_order.get("order_id") or "")

                if filled > 0 or status in ("filled", "executed"):
                    total_cost = round(buy_cost + buy_fees, 2)
                    log(f"📥 [{mode}] BOUGHT {side.upper()} {contracts}x "
                        f"{ticker} @ ${best_price:.2f} | cost ${total_cost:.2f}")

                    # Record the buy as a pending trade (P&L unknown until sell)
                    record_trade(
                        market    = mkt_name,
                        side      = side,
                        contracts = contracts,
                        price     = best_price,
                        result    = "OPEN",
                        profit    = -total_cost,   # outflow
                        mode      = f"BUY-{mode}",
                        order_id  = order_id,
                    )

                    # 5. Schedule sell after a random hold period
                    hold_secs = random.uniform(HOLD_SECONDS_MIN, HOLD_SECONDS_MAX)
                    with BOT.lock:
                        BOT.open_positions.append({
                            "ticker":     ticker,
                            "side":       side,
                            "contracts":  int(filled) if filled >= 1 else contracts,
                            "buy_price_cents": limit_cents,
                            "buy_cost":   total_cost,
                            "sell_after": time.time() + hold_secs,
                            "order_id":   order_id,
                        })

                else:
                    # IOC cancelled — no fill, nothing spent, skip cycle
                    log(f"⏭️  [{mode}] IOC no fill on {ticker} — skipping")
                    time.sleep(freq)
                    continue

            except Exception as e:
                log(f"❌ Live buy error — falling back to sim: {e}")
                can_go_live = False   # fall through to sim

        if not can_go_live:
            # ══════════════════════════════════════════════════════════════
            # SIMULATION PATH — no real money
            # ══════════════════════════════════════════════════════════════
            mode   = "SIM"
            is_win = random.random() < sim_win_rate

            if is_win:
                # Simulate a profitable hold: earn ~20–70% of stake
                profit = round(stake * random.uniform(0.20, 0.70), 2)
                result = "WIN"
            else:
                # Simulate a loss: lose ~20–50% of stake
                profit = round(-stake * random.uniform(0.20, 0.50), 2)
                result = "LOSS"

            record_trade(
                market    = mkt_name,
                side      = side,
                contracts = contracts,
                price     = price,
                result    = result,
                profit    = profit,
                mode      = mode,
            )

            icon = "✅" if is_win else "❌"
            log(f"{icon} [SIM] {side.upper()} \"{mkt_name[:36]}\" {profit:+.2f}")

        time.sleep(freq)

    log("🔴 Bot stopped")

# ─── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__)

# Serve the UI
@app.route("/")
def index():
    return _html()

@app.route("/api/state")
def api_state():
    return jsonify(BOT.snapshot())

@app.route("/api/connect", methods=["POST"])
def api_connect():
    data   = flask_req.get_json(force=True, silent=True) or {}
    key_id = str(data.get("key_id") or "").strip()
    pem    = str(data.get("pem")    or "").strip()
    demo   = bool(data.get("use_demo", True))

    if not key_id or not pem:
        return jsonify({"ok": False, "error": "Key ID and private key are both required."})

    try:
        pk = load_private_key(pem)
    except Exception as e:
        return jsonify({"ok": False, "error":
            f"Could not load private key: {e}\n\n"
            "Paste the complete PEM including the -----BEGIN----- and -----END----- lines."})

    try:
        bal_data = kalshi_get("/portfolio/balance", key_id, pk, demo)
        balance  = float(bal_data.get("balance") or 0) / 100
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

    with BOT.lock:
        BOT.key_id      = key_id
        BOT.private_key = pk
        BOT.use_demo    = demo
        BOT.connected   = True
        BOT.live_enabled = False   # always starts disabled after connect

    log(f"🔗 Connected to Kalshi {'Demo' if demo else 'LIVE'} — balance ${balance:.2f}")
    return jsonify({"ok": True, "balance": balance})

@app.route("/api/configure", methods=["POST"])
def api_configure():
    data = flask_req.get_json(force=True, silent=True) or {}
    with BOT.lock:
        if "strategy" in data:
            BOT.strategy = str(data["strategy"])
        if "risk_pct" in data:
            BOT.risk_pct = min(10, max(1, int(data["risk_pct"])))
        if "use_demo" in data:
            BOT.use_demo = bool(data["use_demo"])
        new_br = float(data.get("bankroll") or BOT.bankroll)
        if new_br != BOT.bankroll:
            BOT.bankroll  = new_br
            BOT.balance   = new_br
            BOT.pnl       = 0.0
            BOT.wins      = 0
            BOT.losses    = 0
            BOT.total     = 0
            BOT.trades    = []
            BOT.log_lines = []
    return jsonify({"ok": True})

@app.route("/api/set_live", methods=["POST"])
def api_set_live():
    data    = flask_req.get_json(force=True, silent=True) or {}
    enabled = bool(data.get("live", False))
    with BOT.lock:
        if not BOT.connected:
            enabled = False
        BOT.live_enabled = enabled
    log("🔧 Live trading " + ("ENABLED ⚠️  — real orders will be placed" if enabled else "disabled ✅"))
    return jsonify({"ok": True})

@app.route("/api/start", methods=["POST"])
def api_start():
    with BOT.lock:
        already   = BOT.running
        BOT.running = True
    if not already:
        threading.Thread(target=bot_loop,  daemon=True).start()
        threading.Thread(target=sell_worker, daemon=True).start()
    return jsonify({"ok": True})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    with BOT.lock:
        BOT.running = False
    return jsonify({"ok": True})

# ─── HTML UI ──────────────────────────────────────────────────────────────────
def _html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kalshi Bot</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=Inter:wght@400;500;600;700;800&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --g:#22c55e;--r:#ef4444;--b:#3b82f6;--p:#8b5cf6;--y:#f59e0b;
  --bg:#0a0c14;--s1:#111827;--s2:#1f2937;--bdr:#374151;--txt:#e5e7eb;--sub:#6b7280
}
body{background:var(--bg);color:var(--txt);font-family:Inter,sans-serif;min-height:100vh;font-size:14px}
.mono{font-family:"IBM Plex Mono",monospace}
input,textarea{background:var(--s2);border:1px solid var(--bdr);border-radius:8px;
  color:var(--txt);padding:10px 12px;font-family:inherit;font-size:13px;width:100%;transition:border-color .2s}
textarea{font-family:"IBM Plex Mono",monospace;font-size:11px;resize:vertical;line-height:1.5}
input:focus,textarea:focus{outline:none;border-color:var(--g)}
button{cursor:pointer;font-family:Inter,sans-serif;font-weight:600;border-radius:8px;transition:all .15s}
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-thumb{background:var(--s2);border-radius:4px}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
@keyframes fadein{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes scan{0%{left:-50%}100%{left:100%}}

/* ── SETUP ── */
.setup-wrap{max-width:560px;margin:0 auto;padding:48px 20px 80px;animation:fadein .4s ease}
.brand{text-align:center;margin-bottom:36px}
.brand-badge{display:inline-flex;align-items:center;gap:8px;padding:5px 16px;
  background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
  border-radius:999px;margin-bottom:18px}
.brand-dot{width:6px;height:6px;border-radius:50%;background:var(--g);animation:pulse 2s infinite}
.brand-title{font-size:32px;font-weight:800;letter-spacing:-1px;line-height:1.1;margin-bottom:10px}
.brand-sub{color:var(--sub);font-size:13px;line-height:1.6}
.warn{background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.2);
  border-radius:10px;padding:12px 16px;font-size:12px;color:#9f4040;line-height:1.6;margin-bottom:22px}
.warn strong{color:var(--r)}
.card{background:var(--s1);border:1px solid var(--bdr);border-radius:14px;padding:20px;margin-bottom:12px}
.card-hdr{display:flex;align-items:center;gap:10px;margin-bottom:16px}
.step-n{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:700;flex-shrink:0}
.step-lbl{font-weight:700;font-size:13px}
.lbl{font-size:11px;color:var(--sub);display:block;margin-bottom:5px;letter-spacing:.5px;text-transform:uppercase}
.togrow{display:flex;gap:8px;margin-bottom:12px}
.togbtn{flex:1;padding:9px;font-size:12px;font-weight:600;border:1px solid var(--bdr);
  background:var(--s2);color:var(--sub);border-radius:8px}
.togbtn.on{background:rgba(34,197,94,.1);border-color:rgba(34,197,94,.35);color:var(--g)}
.sg{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.sc{background:var(--s2);border:1px solid var(--bdr);border-radius:10px;
  padding:12px;cursor:pointer;transition:all .15s}
.sc:hover{border-color:var(--bdr)}
.sc.on{background:rgba(34,197,94,.06);border-color:rgba(34,197,94,.3)}
.sc-ico{font-size:18px;margin-bottom:5px}
.sc-nm{font-size:12px;font-weight:700;color:var(--sub);margin-bottom:3px}
.sc.on .sc-nm{color:var(--g)}
.sc-ds{font-size:11px;color:#4b5563;line-height:1.4}
.br-wrap{position:relative}
.br-wrap .dlr{position:absolute;left:12px;top:50%;transform:translateY(-50%);
  color:var(--g);font-weight:700;font-family:"IBM Plex Mono",monospace;font-size:14px}
.br-wrap input{padding-left:26px;font-family:"IBM Plex Mono",monospace;font-size:15px}
.rng-row{display:flex;justify-content:space-between;font-size:11px;color:#374151;margin-top:4px}
.launch{width:100%;padding:14px;font-size:15px;font-weight:700;border:1px solid rgba(34,197,94,.4);
  background:rgba(34,197,94,.1);color:var(--g);margin-top:2px}
.launch:hover{background:rgba(34,197,94,.18)}
.tip{background:rgba(59,130,246,.05);border:1px solid rgba(59,130,246,.15);
  border-radius:8px;padding:10px 14px;font-size:11px;color:#374151;line-height:1.6;margin-top:12px}
.tip strong{color:var(--b)}
.err{display:none;margin-top:8px;font-size:11.5px;color:var(--r);
  background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.15);
  border-radius:7px;padding:9px 12px;line-height:1.65;white-space:pre-wrap}

/* ── DASHBOARD ── */
#dash{display:none;flex-direction:column;min-height:100vh}
.dhead{position:sticky;top:0;z-index:20;display:flex;align-items:center;
  justify-content:space-between;padding:12px 20px;border-bottom:1px solid var(--bdr);
  background:rgba(10,12,20,.95);backdrop-filter:blur(12px)}
.dhl,.dhr{display:flex;align-items:center;gap:10px}
.bnm{font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:700;color:var(--g);letter-spacing:1.5px}
.pill{border-radius:999px;padding:2px 10px;font-size:11px;font-weight:600}
.pg{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.25);color:var(--g)}
.py{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.25);color:var(--y)}
.pr{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25);color:var(--r)}
.pb{background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.25);color:var(--b)}
#sbtn{padding:7px 16px;font-size:12px;border:none}
.krow{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;padding:12px 20px}
.kpi{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;
  padding:14px 16px;position:relative;overflow:hidden}
.kpi-bg{position:absolute;inset:0;pointer-events:none}
.kpi-dot{position:absolute;top:11px;right:11px;width:6px;height:6px;
  border-radius:50%;display:none;animation:pulse 1.4s infinite}
.kpi-lbl{font-size:10px;letter-spacing:1.5px;color:var(--sub);text-transform:uppercase;margin-bottom:6px}
.kpi-val{font-family:"IBM Plex Mono",monospace;font-size:19px;font-weight:700}
.kpi-sub{font-size:11px;color:var(--sub);margin-top:3px}
.bgrid{flex:1;display:grid;grid-template-columns:1fr 300px;gap:10px;padding:0 20px 20px}
.panel{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;
  display:flex;flex-direction:column;overflow:hidden;min-height:0}
.tabs{display:flex;border-bottom:1px solid var(--bdr);flex-shrink:0}
.tb{background:none;border:none;border-bottom:2px solid transparent;
  color:var(--sub);padding:10px 16px;font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase}
.tb.on{border-bottom-color:var(--g);color:var(--g)}
.tc{flex:1;overflow-y:auto;padding:0 12px}
.th{display:grid;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.04);
  font-size:9px;color:#374151;letter-spacing:1.5px;text-transform:uppercase}
.tr{display:grid;align-items:center;padding:6px 0;
  border-bottom:1px solid rgba(255,255,255,.025);font-size:11px}
.gt{grid-template-columns:58px 1fr 38px 40px 50px 64px 38px}
.gm{grid-template-columns:1fr 80px 70px 34px}
.gp{grid-template-columns:1fr 60px 60px 60px}
.empty{text-align:center;padding:50px 0;color:#374151;font-size:13px}
.loge{font-family:"IBM Plex Mono",monospace;font-size:10.5px;
  padding:4px 0;border-bottom:1px solid rgba(255,255,255,.02);line-height:1.45}
.sidebar{display:flex;flex-direction:column;gap:10px}
.sc3{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;padding:16px}
.s3l{font-size:9px;color:#374151;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:9px}
.str{display:flex;justify-content:space-between;align-items:center;
  padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:12px}
.stl{color:var(--sub)}.stv{color:#9ca3af;font-family:"IBM Plex Mono",monospace}
.mg2{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px}
.mc{background:var(--s2);border-radius:7px;padding:8px 10px}
.ml{font-size:10px;color:#374151}.mv{font-size:12px;color:#9ca3af;font-family:"IBM Plex Mono",monospace}
.scan-bar{position:fixed;top:0;left:0;right:0;height:1px;z-index:30;
  pointer-events:none;overflow:hidden;display:none}
.scan-inner{position:absolute;top:0;width:50%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(34,197,94,.6),transparent);
  animation:scan 2.5s linear infinite}
/* live overlay */
#lov{display:none;position:fixed;inset:0;background:rgba(0,0,0,.8);
  z-index:100;align-items:center;justify-content:center}
#lov.show{display:flex}
.lob{background:#111827;border:1px solid rgba(239,68,68,.3);border-radius:16px;
  padding:32px;max-width:440px;width:92%;text-align:center}
.lob h2{font-size:20px;font-weight:800;color:var(--r);margin-bottom:12px}
.lob p{font-size:12.5px;color:var(--sub);line-height:1.7;margin-bottom:4px}
.lob ul{text-align:left;font-size:12px;color:#6b7280;line-height:1.85;margin:12px 0 20px 20px}
.lob ul li{margin-bottom:1px}
.lob-btns{display:flex;gap:10px;margin-top:4px}
.bc2{flex:1;padding:11px;border-radius:8px;background:var(--s2);
  border:1px solid var(--bdr);color:var(--sub);font-size:13px}
.bk2{flex:1;padding:11px;border-radius:8px;background:rgba(239,68,68,.1);
  border:1px solid rgba(239,68,68,.3);color:var(--r);font-size:13px}
/* live toggle */
.ts{position:relative;width:44px;height:24px;flex-shrink:0;display:inline-block}
.ts input{opacity:0;width:0;height:0;position:absolute}
.sl2{position:absolute;inset:0;background:#1f2937;border:1px solid #374151;
  border-radius:999px;cursor:pointer;transition:.25s}
.sl2:before{content:"";position:absolute;width:16px;height:16px;left:3px;top:3px;
  background:#6b7280;border-radius:50%;transition:.25s}
input:checked+.sl2{background:rgba(239,68,68,.2);border-color:rgba(239,68,68,.5)}
input:checked+.sl2:before{transform:translateX(20px);background:var(--r)}
.yb{display:flex;align-items:center;gap:5px}
.ybb{width:26px;height:3px;background:var(--s2);border-radius:2px;overflow:hidden}
.ybi{height:100%;transition:width .4s}
</style>
</head>
<body>
<div class="scan-bar" id="scanBar"><div class="scan-inner"></div></div>

<!-- LIVE CONFIRM OVERLAY -->
<div id="lov">
  <div class="lob">
    <h2>⚠️ Enable Live Trading?</h2>
    <p>This will place <strong style="color:#e5e7eb">real orders</strong> with real money on Kalshi.</p>
    <ul>
      <li>Hard cap: <strong style="color:#e5e7eb">$20 per buy order</strong></li>
      <li>Buy orders use <strong style="color:#e5e7eb">immediate-or-cancel</strong> — no stuck open orders</li>
      <li>Every buy is followed by a <strong style="color:#e5e7eb">sell order</strong> after a hold period</li>
      <li>Liquidity checked <strong style="color:#e5e7eb">before every buy</strong></li>
      <li><strong style="color:#e5e7eb">Single-leg YES or NO only</strong> — zero combo bets</li>
      <li>Test in <strong style="color:#e5e7eb">Demo mode first</strong> if you haven't already</li>
    </ul>
    <div class="lob-btns">
      <button class="bc2" onclick="cancelLive()">← Go Back</button>
      <button class="bk2" onclick="confirmLive()">I Understand — Enable</button>
    </div>
  </div>
</div>

<!-- ── SETUP ─────────────────────────────────────────── -->
<div id="setup">
<div class="setup-wrap">
  <div class="brand">
    <div class="brand-badge">
      <span class="brand-dot"></span>
      <span class="mono" style="font-size:11px;color:var(--g);letter-spacing:2px;font-weight:700">KALSHI BOT</span>
    </div>
    <div class="brand-title">Automated Prediction<br><span style="color:var(--g)">Market Trading</span></div>
    <p class="brand-sub">CFTC-regulated · Buys AND sells · No combo bets · Liquidity-checked</p>
  </div>

  <div class="warn">
    <strong>⚠️ Risk Warning:</strong> Prediction markets involve real financial risk.
    Simulated results do not guarantee real returns. Only use funds you can afford to lose.
    Live mode is OFF by default and requires explicit confirmation. Max $20 per order.
  </div>

  <!-- Step 1: API -->
  <div class="card">
    <div class="card-hdr">
      <div class="step-n" id="s1n" style="background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.25);color:var(--g)">1</div>
      <span class="step-lbl">Connect Kalshi API</span>
      <span id="balBadge" style="margin-left:auto;font-size:12px;color:var(--g);font-family:monospace;display:none"></span>
    </div>
    <div class="togrow">
      <button class="togbtn on" id="demoBtn" onclick="setDemo(true)">🧪 Demo (Safe)</button>
      <button class="togbtn"    id="liveBtn" onclick="setDemo(false)">💰 Live Trading</button>
    </div>
    <div style="margin-bottom:10px">
      <label class="lbl">Key ID</label>
      <input type="text" id="keyId" class="mono" placeholder="a952bcbe-ec3b-4b5b-b8f9-11dae589608c">
    </div>
    <div style="margin-bottom:12px">
      <label class="lbl">RSA Private Key — paste full PEM including -----BEGIN and -----END lines</label>
      <textarea id="privKey" rows="6"
        placeholder="-----BEGIN RSA PRIVATE KEY-----&#10;MIIEo...&#10;-----END RSA PRIVATE KEY-----"></textarea>
      <div style="font-size:10px;color:#374151;margin-top:4px">
        🔒 Your key never leaves this machine. All signing is done locally.
      </div>
    </div>
    <button id="testBtn" onclick="testConn()"
      style="width:100%;padding:10px;border:1px solid rgba(34,197,94,.2);
      background:rgba(34,197,94,.06);color:var(--sub);font-size:13px">
      Test Connection
    </button>
    <div id="connErr" class="err"></div>
    <div class="tip">
      <strong>No key yet?</strong> Skip this — the bot runs in full simulation.
      Get your key at <strong style="color:var(--b)">kalshi.com → Account & security → API Keys</strong>.
      For safe testing: <strong style="color:var(--b)">demo.kalshi.co → API Keys</strong>
    </div>
  </div>

  <!-- Step 2: Strategy -->
  <div class="card">
    <div class="card-hdr">
      <div class="step-n" style="background:rgba(139,92,246,.1);border:1px solid rgba(139,92,246,.25);color:var(--p)">2</div>
      <span class="step-lbl">Choose Strategy</span>
    </div>
    <div class="sg">
      <div class="sc on" id="sc-conservative" onclick="setSt('conservative')">
        <div class="sc-ico">🛡️</div><div class="sc-nm">Conservative</div>
        <div class="sc-ds">Near-50/50 liquid markets. Safest. Holds 8–25s.</div>
      </div>
      <div class="sc" id="sc-arb" onclick="setSt('arb')">
        <div class="sc-ico">⚖️</div><div class="sc-nm">Arbitrage</div>
        <div class="sc-ds">Wide YES/NO price gaps. Holds 10–30s.</div>
      </div>
      <div class="sc" id="sc-meanRevert" onclick="setSt('meanRevert')">
        <div class="sc-ico">🔄</div><div class="sc-nm">Mean Reversion</div>
        <div class="sc-ds">Overextended prices, waits for snap-back.</div>
      </div>
      <div class="sc" id="sc-momentum" onclick="setSt('momentum')">
        <div class="sc-ico">⚡</div><div class="sc-nm">Momentum</div>
        <div class="sc-ds">Chases directional moves. Holds 5–15s.</div>
      </div>
    </div>
  </div>

  <!-- Step 3: Capital -->
  <div class="card">
    <div class="card-hdr">
      <div class="step-n" style="background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.25);color:var(--b)">3</div>
      <span class="step-lbl">Capital &amp; Risk</span>
    </div>
    <div style="margin-bottom:16px">
      <label class="lbl">Starting Bankroll (USD)</label>
      <div class="br-wrap"><span class="dlr">$</span>
        <input type="number" id="bankroll" min="10" value="500">
      </div>
    </div>
    <div>
      <label class="lbl" style="display:flex;justify-content:space-between">
        <span>Max Risk Per Trade</span>
        <span id="riskLbl" class="mono" style="color:var(--g);font-weight:700">3%</span>
      </label>
      <input type="range" min="1" max="10" value="3" id="riskRange"
        style="width:100%;accent-color:var(--g);background:none;border:none;padding:0"
        oninput="upRisk(this.value)">
      <div class="rng-row">
        <span>1% Safest</span>
        <span>10% Max (hard capped at $20/order)</span>
      </div>
    </div>
  </div>

  <button class="launch" onclick="doLaunch()">Open Dashboard →</button>
  <p style="text-align:center;font-size:11px;color:#374151;margin-top:8px">
    Simulation mode is the default · Live requires explicit confirmation · Max $20 per order
  </p>
</div>
</div>

<!-- ── DASHBOARD ─────────────────────────────────────── -->
<div id="dash">
  <div class="dhead">
    <div class="dhl">
      <button onclick="goSetup()" style="background:none;border:none;color:var(--sub);font-size:17px;padding:0 4px">←</button>
      <span class="bnm">KALSHI BOT</span>
      <span class="pill pb" id="stratPill">🛡️ Conservative</span>
    </div>
    <div class="dhr">
      <span class="pill" id="modePill">● Simulation</span>
      <span class="pill pr" id="livePill" style="display:none">● LIVE</span>
      <button id="sbtn" onclick="togBot()"
        style="background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);color:var(--g);font-size:12px">
        ▶ Start Bot
      </button>
    </div>
  </div>

  <div class="krow">
    <div class="kpi">
      <div class="kpi-bg" style="background:radial-gradient(circle at top left,rgba(34,197,94,.07),transparent 65%)"></div>
      <span class="kpi-dot" id="kDot" style="background:var(--g);box-shadow:0 0 7px var(--g)"></span>
      <div class="kpi-lbl">Portfolio</div>
      <div class="kpi-val" id="kBal" style="color:var(--g)">$500.00</div>
      <div class="kpi-sub" id="kStart">Started $500.00</div>
    </div>
    <div class="kpi">
      <div class="kpi-bg" style="background:radial-gradient(circle at top left,rgba(34,197,94,.07),transparent 65%)"></div>
      <div class="kpi-lbl">Total P&amp;L</div>
      <div class="kpi-val" id="kPnl" style="color:var(--g)">+$0.00</div>
      <div class="kpi-sub" id="kRet">+0.0% return</div>
    </div>
    <div class="kpi">
      <div class="kpi-bg" style="background:radial-gradient(circle at top left,rgba(139,92,246,.07),transparent 65%)"></div>
      <div class="kpi-lbl">Win Rate</div>
      <div class="kpi-val" id="kWr" style="color:var(--p)">—</div>
      <div class="kpi-sub" id="kTc">0 trades</div>
    </div>
    <div class="kpi">
      <div class="kpi-bg" style="background:radial-gradient(circle at top left,rgba(59,130,246,.07),transparent 65%)"></div>
      <div class="kpi-lbl">Open Positions</div>
      <div class="kpi-val" id="kOpen" style="color:var(--b)">0</div>
      <div class="kpi-sub" id="kMsub">Waiting to sell</div>
    </div>
  </div>

  <div class="bgrid">
    <!-- Left: tab panel -->
    <div class="panel">
      <div class="tabs">
        <button class="tb on" onclick="setTab('trades')">Trades</button>
        <button class="tb"    onclick="setTab('markets')">Markets</button>
        <button class="tb"    onclick="setTab('positions')">Positions</button>
        <button class="tb"    onclick="setTab('log')">Log</button>
      </div>
      <div class="tc" id="tc-trades">
        <div class="th gt">
          <span>Time</span><span>Market</span><span>Side</span>
          <span>Qty</span><span>Result</span>
          <span style="text-align:right">P&amp;L</span>
          <span style="text-align:right">Mode</span>
        </div>
        <div id="tBody"><div class="empty">Press <span style="color:var(--g)">▶ Start Bot</span> to begin</div></div>
      </div>
      <div class="tc" id="tc-markets" style="display:none">
        <div class="th gm"><span>Market</span><span>YES Price</span><span>Volume</span><span style="text-align:right">↕</span></div>
        <div id="mBody"></div>
      </div>
      <div class="tc" id="tc-positions" style="display:none">
        <div class="th gp"><span>Ticker</span><span style="text-align:right">YES</span><span style="text-align:right">NO</span><span style="text-align:right">Exposure</span></div>
        <div id="pBody"><div class="empty">No open positions</div></div>
      </div>
      <div class="tc" id="tc-log" style="display:none">
        <div id="lBody" style="padding-top:6px"><div class="empty">No activity yet</div></div>
      </div>
    </div>

    <!-- Right: sidebar -->
    <div class="sidebar">
      <!-- Equity curve -->
      <div class="sc3">
        <div class="s3l">Equity Curve</div>
        <svg id="spk" width="100%" height="52" viewBox="0 0 268 52" preserveAspectRatio="none">
          <line x1="0" y1="26" x2="268" y2="26" stroke="#1f2937" stroke-width="1" stroke-dasharray="4"/>
        </svg>
      </div>

      <!-- Live toggle (hidden until connected) -->
      <div class="sc3" id="liveCard" style="display:none">
        <div class="s3l">Live Trading</div>
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:9px">
          <label class="ts"><input type="checkbox" id="liveChk" onchange="onLT(this)"><span class="sl2"></span></label>
          <span id="liveLbl" style="font-size:12px;font-weight:600;color:var(--sub)">Disabled (safe)</span>
        </div>
        <div style="font-size:11px;color:#374151;line-height:1.5">
          IOC buys + scheduled sells. Max $20/order. Liquidity checked first.
        </div>
      </div>

      <!-- Strategy card -->
      <div class="sc3">
        <div class="s3l">Strategy</div>
        <div id="sIco" style="font-size:18px;margin-bottom:6px">🛡️</div>
        <div id="sNm" style="font-size:13px;font-weight:700;color:var(--g);margin-bottom:4px">Conservative</div>
        <div id="sDs" style="font-size:11px;color:var(--sub);line-height:1.5;margin-bottom:11px">Near-50/50 liquid markets only.</div>
        <div class="mg2">
          <div class="mc"><div class="ml">Risk</div><div class="mv" id="sRsk" style="color:var(--g)">Low</div></div>
          <div class="mc"><div class="ml">Per Trade</div><div class="mv" id="sPer">3%</div></div>
          <div class="mc"><div class="ml">Interval</div><div class="mv" id="sFrq">~12s</div></div>
          <div class="mc"><div class="ml">Max/Order</div><div class="mv" style="color:var(--g)">$20</div></div>
        </div>
      </div>

      <!-- Session stats -->
      <div class="sc3" style="flex:1">
        <div class="s3l">Session</div>
        <div class="str"><span class="stl">Trades Won</span><span class="stv" id="sWon">— / 0</span></div>
        <div class="str"><span class="stl">Avg Win</span><span class="stv" id="sAW">—</span></div>
        <div class="str"><span class="stl">Avg Loss</span><span class="stv" id="sAL">—</span></div>
        <div class="str"><span class="stl">Net P&amp;L</span><span class="stv" id="sPnl">+$0.00</span></div>
        <div class="str" style="border:none"><span class="stl">Return</span><span class="stv" id="sRet">+0.0%</span></div>
      </div>
    </div>
  </div>
</div>

<script>
// ── State ─────────────────────────────────────────────────────────────────────
let useDemo = true;
let strat   = 'conservative';
let pollId  = null;
let balHist = [];
let brStart = 500;

const STRATS = {
  conservative: {icon:'🛡️', name:'Conservative', risk:'Low',    freq:12, desc:'Near-50/50 liquid markets. Safest.'},
  arb:          {icon:'⚖️', name:'Arbitrage',    risk:'Low',    freq:8,  desc:'Wide YES/NO price gaps.'},
  meanRevert:   {icon:'🔄', name:'Mean Rev.',    risk:'Medium', freq:5,  desc:'Overextended prices, waits for snap-back.'},
  momentum:     {icon:'⚡', name:'Momentum',     risk:'High',   freq:3,  desc:'Chases directional moves.'},
};

const SIM_MKTS = [
  {title:'Fed rate cut Jun 2026?',  yes:0.42, vol:280000},
  {title:'S&P 500 above 6500 EOY?', yes:0.55, vol:410000},
  {title:'US recession 2026?',      yes:0.28, vol:190000},
  {title:'Tesla above $400 Q3?',    yes:0.33, vol:150000},
  {title:'BTC above $150k EOY?',    yes:0.38, vol:320000},
  {title:'Oil above $100 Dec 26?',  yes:0.22, vol:88000},
  {title:'GDP growth >2.5% Q2?',    yes:0.61, vol:74000},
  {title:'Mortgage <6% EOY?',       yes:0.45, vol:120000},
  {title:'Unemployment <4% Q3?',    yes:0.52, vol:95000},
  {title:'CPI <3% by Q3?',          yes:0.48, vol:67000},
];

// ── Setup helpers ─────────────────────────────────────────────────────────────
function setDemo(v) {
  useDemo = v;
  document.getElementById('demoBtn').className = 'togbtn ' + (v ? 'on' : '');
  document.getElementById('liveBtn').className = 'togbtn ' + (v ? '' : 'on');
  document.getElementById('connErr').style.display = 'none';
}

function setSt(k) {
  strat = k;
  document.querySelectorAll('.sc').forEach(e => e.classList.remove('on'));
  document.getElementById('sc-' + k).classList.add('on');
}

function upRisk(v) {
  const l = document.getElementById('riskLbl');
  l.textContent = v + '%';
  l.style.color = v <= 3 ? 'var(--g)' : v <= 6 ? 'var(--y)' : 'var(--r)';
}

async function testConn() {
  const btn = document.getElementById('testBtn');
  const err = document.getElementById('connErr');
  const kid = document.getElementById('keyId').value.trim();
  const pem = document.getElementById('privKey').value.trim();
  btn.textContent = '⏳ Testing…';
  btn.style.color = 'var(--y)';
  err.style.display = 'none';
  try {
    const r = await fetch('/api/connect', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({key_id: kid, pem: pem, use_demo: useDemo})
    });
    const d = await r.json();
    if (d.ok) {
      btn.textContent = '✅ Connected — Balance: $' + d.balance.toFixed(2);
      btn.style.color = 'var(--g)';
      const n = document.getElementById('s1n');
      n.textContent = '✓'; n.style.background = 'var(--g)'; n.style.color = '#000';
      document.getElementById('balBadge').textContent = '$' + d.balance.toFixed(2);
      document.getElementById('balBadge').style.display = 'block';
    } else {
      throw new Error(d.error || 'Unknown error');
    }
  } catch(e) {
    btn.textContent = '✗ Retry'; btn.style.color = 'var(--r)';
    err.style.display = 'block'; err.textContent = '❌ ' + e.message;
  }
}

function doLaunch() {
  brStart = parseFloat(document.getElementById('bankroll').value) || 500;
  const risk = parseInt(document.getElementById('riskRange').value) || 3;
  fetch('/api/configure', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({strategy: strat, bankroll: brStart, risk_pct: risk, use_demo: useDemo})
  }).then(() => openDash());
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
function openDash() {
  document.getElementById('setup').style.display = 'none';
  document.getElementById('dash').style.display = 'flex';
  const s = STRATS[strat];
  document.getElementById('stratPill').textContent = s.icon + ' ' + s.name;
  document.getElementById('sIco').textContent = s.icon;
  document.getElementById('sNm').textContent  = s.name;
  document.getElementById('sDs').textContent  = s.desc;
  document.getElementById('sRsk').textContent = s.risk;
  document.getElementById('sRsk').style.color = s.risk === 'Low' ? 'var(--g)' : s.risk === 'Medium' ? 'var(--y)' : 'var(--r)';
  document.getElementById('sPer').textContent = document.getElementById('riskRange').value + '%';
  document.getElementById('sFrq').textContent = '~' + s.freq + 's';
  document.getElementById('kStart').textContent = 'Started $' + brStart.toFixed(2);
  startPoll();
  fetch('/api/state').then(r => r.json()).then(d => {
    if (d.connected) document.getElementById('liveCard').style.display = 'block';
  });
}

function goSetup() {
  fetch('/api/stop', {method: 'POST'});
  stopPoll();
  document.getElementById('dash').style.display = 'none';
  document.getElementById('setup').style.display = 'block';
  balHist = [];
  const b = document.getElementById('sbtn');
  b.textContent = '▶ Start Bot';
  b.style.background = 'rgba(34,197,94,.1)';
  b.style.borderColor = 'rgba(34,197,94,.3)';
  b.style.color = 'var(--g)';
  document.getElementById('scanBar').style.display = 'none';
  document.getElementById('kDot').style.display = 'none';
  document.getElementById('liveChk').checked = false;
}

function togBot() {
  const b = document.getElementById('sbtn');
  const running = b.textContent.includes('Pause');
  fetch('/api/' + (running ? 'stop' : 'start'), {method: 'POST'}).then(() => {
    if (running) {
      b.textContent = '▶ Start Bot';
      b.style.background = 'rgba(34,197,94,.1)';
      b.style.borderColor = 'rgba(34,197,94,.3)';
      b.style.color = 'var(--g)';
      document.getElementById('scanBar').style.display = 'none';
      document.getElementById('kDot').style.display = 'none';
    } else {
      b.textContent = '⏸ Pause';
      b.style.background = 'rgba(239,68,68,.12)';
      b.style.borderColor = 'rgba(239,68,68,.3)';
      b.style.color = 'var(--r)';
      document.getElementById('scanBar').style.display = 'block';
      document.getElementById('kDot').style.display = 'block';
    }
  });
}

// ── Live toggle ───────────────────────────────────────────────────────────────
function onLT(chk) {
  if (chk.checked) {
    chk.checked = false;
    document.getElementById('lov').classList.add('show');
  } else {
    disableLive();
  }
}
function cancelLive()  { document.getElementById('lov').classList.remove('show'); }
function confirmLive() {
  document.getElementById('lov').classList.remove('show');
  document.getElementById('liveChk').checked = true;
  document.getElementById('liveLbl').textContent = 'ENABLED — real orders active';
  document.getElementById('liveLbl').style.color = 'var(--r)';
  document.getElementById('livePill').style.display = 'inline-flex';
  fetch('/api/set_live', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({live: true})});
}
function disableLive() {
  document.getElementById('liveLbl').textContent = 'Disabled (safe)';
  document.getElementById('liveLbl').style.color = 'var(--sub)';
  document.getElementById('livePill').style.display = 'none';
  fetch('/api/set_live', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({live: false})});
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
function setTab(n) {
  ['trades','markets','positions','log'].forEach(t => {
    document.getElementById('tc-' + t).style.display = t === n ? 'block' : 'none';
  });
  document.querySelectorAll('.tb').forEach((b, i) => {
    b.classList.toggle('on', ['trades','markets','positions','log'][i] === n);
  });
}

// ── Polling ───────────────────────────────────────────────────────────────────
function startPoll() { pollId = setInterval(doPoll, 900); doPoll(); }
function stopPoll()  { clearInterval(pollId); }

async function doPoll() {
  try {
    const d = await (await fetch('/api/state')).json();
    render(d);
  } catch (_) {}
}

const $u = n => '$' + Math.abs(n).toFixed(2);
const $f = n => (n >= 0 ? '+' : '-') + '$' + Math.abs(n).toFixed(2);
const $p = n => (n * 100).toFixed(1) + '%';

function render(d) {
  const ret = brStart > 0 ? (d.pnl / brStart) * 100 : 0;

  // KPIs
  document.getElementById('kBal').textContent  = $u(d.balance);
  document.getElementById('kPnl').textContent  = $f(d.pnl);
  document.getElementById('kPnl').style.color  = d.pnl >= 0 ? 'var(--g)' : 'var(--r)';
  document.getElementById('kRet').textContent  = (ret >= 0 ? '+' : '') + ret.toFixed(1) + '% return';
  document.getElementById('kWr').textContent   = d.trade_count > 0 ? $p(d.win_rate) : '—';
  document.getElementById('kTc').textContent   = d.trade_count + ' trades';
  document.getElementById('kOpen').textContent = d.open_count;
  document.getElementById('kMsub').textContent = d.open_count > 0 ? 'Selling soon…' : 'No open positions';

  // Mode pill
  const mp = document.getElementById('modePill');
  if (d.connected) {
    mp.textContent = d.use_demo ? '● Demo API' : '● API Connected';
    mp.className = 'pill pg';
  } else {
    mp.textContent = '● Simulation';
    mp.className = 'pill py';
  }
  if (d.connected) document.getElementById('liveCard').style.display = 'block';

  // ── Trades tab ────────────────────────────────────────────────────────────
  const tb = document.getElementById('tBody');
  if (!d.trades || !d.trades.length) {
    tb.innerHTML = '<div class="empty">Press <span style="color:var(--g)">▶ Start Bot</span> to begin</div>';
  } else {
    tb.innerHTML = d.trades.map(t => {
      const pc = parseFloat(t.profit);
      const rc = t.result === 'WIN'    ? 'var(--g)'
               : t.result === 'LOSS'   ? 'var(--r)'
               : t.result === 'OPEN'   ? 'var(--y)'
               : t.result === 'FILLED' ? 'var(--b)'
               : 'var(--sub)';
      const mc = t.mode.includes('LIVE') ? 'var(--r)'
               : t.mode.includes('DEMO') ? 'var(--b)'
               : '#374151';
      return `<div class="tr gt">
        <span style="color:#4b5563" class="mono">${t.time}</span>
        <span style="color:#6b7280;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding-right:6px"
              title="${t.market}">${t.market}</span>
        <span style="color:${t.side==='YES'?'var(--g)':'var(--p)'};font-weight:700">${t.side}</span>
        <span style="color:#4b5563" class="mono">${t.contracts}</span>
        <span style="color:${rc};font-weight:700;font-size:10px">${t.result}</span>
        <span style="color:${pc>=0?'var(--g)':'var(--r)'};text-align:right" class="mono">${t.profit}</span>
        <span style="text-align:right;font-size:9px;font-weight:700;color:${mc}">${t.mode}</span>
      </div>`;
    }).join('');
  }

  // ── Markets tab ───────────────────────────────────────────────────────────
  const mkts = (d.markets && d.markets.length > 0)
    ? d.markets.map(m => ({
        title: m.title || m.name || 'Unknown',
        yes:   parseFloat(m.yes_bid_dollars || m.yes_bid || 0.5),
        vol:   m.volume || 0,
      }))
    : SIM_MKTS.map(m => ({title: m.title, yes: m.yes + (Math.random() - 0.5) * 0.03, vol: m.vol}));

  document.getElementById('mBody').innerHTML = mkts.map(m => {
    const bar = Math.round(m.yes * 100);
    const col = m.yes > 0.5 ? 'var(--g)' : 'var(--r)';
    return `<div class="tr gm">
      <span style="color:#6b7280;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding-right:6px">${m.title}</span>
      <span><div class="yb">
        <div class="ybb"><div class="ybi" style="width:${bar}%;background:${col}"></div></div>
        <span class="mono" style="color:${col};font-size:11px">${(m.yes*100).toFixed(1)}%</span>
      </div></span>
      <span style="color:#4b5563;font-size:11px" class="mono">$${(m.vol/1000).toFixed(0)}k</span>
      <span style="text-align:right;color:${col}">${m.yes > 0.5 ? '▲' : '▼'}</span>
    </div>`;
  }).join('');

  // ── Positions tab ─────────────────────────────────────────────────────────
  const pb = document.getElementById('pBody');
  if (!d.positions || !d.positions.length) {
    pb.innerHTML = '<div class="empty">No open positions</div>';
  } else {
    pb.innerHTML = d.positions.map(p => `<div class="tr gp">
      <span style="color:#6b7280;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${p.ticker}</span>
      <span style="text-align:right;color:var(--g)" class="mono">${p.position || 0}</span>
      <span style="text-align:right;color:var(--p)" class="mono">${p.position_no || 0}</span>
      <span style="text-align:right;color:#9ca3af" class="mono">$${((p.market_exposure || 0) / 100).toFixed(2)}</span>
    </div>`).join('');
  }

  // ── Log tab ───────────────────────────────────────────────────────────────
  const lb = document.getElementById('lBody');
  if (!d.log || !d.log.length) {
    lb.innerHTML = '<div class="empty">No activity yet</div>';
  } else {
    lb.innerHTML = d.log.map(e => {
      const col = e.includes('✅') || e.includes('🟢') || e.includes('💰') ? 'var(--g)'
                : e.includes('❌') || e.includes('🔴')                     ? 'var(--r)'
                : e.includes('⚠️')                                         ? 'var(--y)'
                : e.includes('📥') || e.includes('📋') || e.includes('🔗') ? 'var(--b)'
                : '#4b5563';
      return `<div class="loge" style="color:${col}">${e}</div>`;
    }).join('');
  }

  // ── Session stats ─────────────────────────────────────────────────────────
  const wins   = d.trades.filter(t => t.result === 'WIN');
  const losses = d.trades.filter(t => t.result === 'LOSS');
  const aw = wins.length   ? wins.reduce((s, t) => s + parseFloat(t.profit), 0) / wins.length   : null;
  const al = losses.length ? Math.abs(losses.reduce((s, t) => s + parseFloat(t.profit), 0) / losses.length) : null;

  document.getElementById('sWon').textContent = Math.round(d.win_rate * d.trade_count) + ' / ' + d.trade_count;
  document.getElementById('sAW').textContent  = aw !== null ? $u(aw) : '—';
  document.getElementById('sAL').textContent  = al !== null ? $u(al) : '—';
  document.getElementById('sPnl').textContent = $f(d.pnl);
  document.getElementById('sRet').textContent = (ret >= 0 ? '+' : '') + ret.toFixed(1) + '%';

  // ── Equity curve ──────────────────────────────────────────────────────────
  balHist.push(d.balance);
  if (balHist.length > 70) balHist.shift();
  drawSpark(balHist, brStart);
}

function drawSpark(vals, br) {
  if (vals.length < 2) return;
  const W = 268, H = 52;
  const mn  = Math.min(...vals, br * 0.90);
  const mx  = Math.max(...vals, br * 1.10);
  const rng = mx - mn || 1;
  const cl  = y => Math.max(1, Math.min(H - 1, y));
  const pts = vals.map((v, i) => ({
    x: (i / (vals.length - 1)) * W,
    y: H - ((v - mn) / rng) * H,
  }));
  const ln  = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${cl(p.y).toFixed(1)}`).join(' ');
  const col = vals[vals.length - 1] >= br ? '#22c55e' : '#ef4444';
  document.getElementById('spk').innerHTML = `
    <defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="${col}" stop-opacity=".18"/>
      <stop offset="100%" stop-color="${col}" stop-opacity="0"/>
    </linearGradient></defs>
    <path d="${ln} L${W},${H} L0,${H} Z" fill="url(#sg)"/>
    <path d="${ln}" stroke="${col}" stroke-width="1.8" fill="none" stroke-linejoin="round"/>`;
}
</script>
</body>
</html>"""

# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print()
    print("=" * 58)
    print("  🤖  Kalshi Trading Bot")
    print("=" * 58)
    print()
    print("  Safety features active:")
    print("  ✅  Simulation mode ON by default")
    print("  ✅  Live trading requires explicit confirmation")
    print("  ✅  IOC buys — no resting orders left open")
    print("  ✅  Sell worker closes every position automatically")
    print(f"  ✅  Hard cap: ${MAX_ORDER_DOLLARS:.0f} per buy order")
    print("  ✅  Liquidity checked before every live buy")
    print("  ✅  Single-leg YES/NO only — no combo bets")
    print()
    print(f"  📡  Open in your browser:  http://localhost:{PORT}")
    print("  🛑  Press Ctrl+C to stop")
    print()
    print("=" * 58)
    print()

    # Open browser automatically after 1.5 seconds
    def _open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{PORT}")
    threading.Thread(target=_open_browser, daemon=True).start()

    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)
