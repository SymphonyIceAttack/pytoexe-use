import requests
import csv
import json
import urllib.parse
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import time
import os
import glob

session = requests.Session()

API_KEY = "1Y80lmpolCnHfWKmh1ei50yWWYU8ovq"

MAX_OVERPAY = 0.05
COMMISSION = 0.136

WEARS = [
    "Factory New",
    "Minimal Wear",
    "Field-Tested",
]

# ================== SETS SYSTEM ==================

SETS_FOLDER = "SETS"

def load_sets():
    files = glob.glob(f"{SETS_FOLDER}/*.json")
    sets = []

    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
                data["file"] = f
                sets.append(data)
        except:
            continue

    return sets


def choose_set():
    sets = load_sets()

    print("\nAVAILABLE SETS:\n")

    for i, s in enumerate(sets):
        print(f"{i+1} - {s['name']} | sell={s['sell_price']}₽ | skins={len(s['skins'])}")

    choice = int(input("\nSelect set: ")) - 1
    return sets[choice]

# ================== INPUT ==================

TRADE_URL = input("Trade URL покупателя: ").strip()

parsed = urlparse(TRADE_URL)
params = parse_qs(parsed.query)

partner = params.get("partner", [""])[0]
token = params.get("token", [""])[0]

ORDER_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

# ================== ORDER FOLDER ==================

ORDER_FOLDER = os.path.join("orders", ORDER_ID)
os.makedirs(ORDER_FOLDER, exist_ok=True)

LOG_FILE = os.path.join(ORDER_FOLDER, "log.txt")
ORDER_JSON = os.path.join(ORDER_FOLDER, "order.json")
PURCHASES_CSV = os.path.join(ORDER_FOLDER, "purchases.csv")
FAILED_FILE = os.path.join(ORDER_FOLDER, "failed_skins.txt")
SUMMARY_FILE = os.path.join(ORDER_FOLDER, "summary.txt")

# ================== LOG ==================

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ================== SEARCH ==================

def find_best_lot(base_skin):
    all_lots = []

    variants = [base_skin, f"Souvenir {base_skin}"]

    for variant in variants:
        for wear in WEARS:
            full_name = f"{variant} ({wear})"

            try:
                url = (
                    "https://market.csgo.com/api/v2/search-item-by-hash-name-specific"
                    f"?key={API_KEY}&hash_name={urllib.parse.quote(full_name)}"
                )

                data = session.get(url, timeout=15).json()

                if not data.get("data"):
                    continue

                for lot in data["data"]:
                    fv = lot.get("extra", {}).get("float")
                    if fv is None:
                        continue

                    all_lots.append({
                        "name": lot["market_hash_name"],
                        "price": int(lot["price"]),
                        "float": float(fv),
                        "id": lot["id"]
                    })

            except Exception as e:
                log(f"SEARCH ERROR {base_skin}: {e}", "WARN")

    if not all_lots:
        return None

    all_lots.sort(key=lambda x: x["price"])

    min_price = all_lots[0]["price"]
    max_price = int(min_price * (1 + MAX_OVERPAY))

    candidates = [x for x in all_lots if x["price"] <= max_price]
    candidates.sort(key=lambda x: x["float"])

    return {
        "lots": candidates[:10],
        "min_price": min_price,
        "max_price": max_price
    }

# ================== BUY ==================

def buy_lot(lot):
    url = (
        "https://market.csgo.com/api/v2/buy-for"
        f"?key={API_KEY}"
        f"&id={lot['id']}"
        f"&price={lot['price']}"
        f"&partner={partner}"
        f"&token={token}"
        f"&chance_to_transfer=90"
    )

    try:
        r = session.get(url, timeout=30).json()
    except Exception as e:
        return False, str(e)

    return (r.get("success"), r.get("error"))

# ================== MAIN ==================

manual = input("Manual skins? (y/n): ").lower() == "y"
skins = []

SELL_PRICE = 0

state = {
    "order_id": ORDER_ID,
    "set_name": "No Name",
    "sell_price": SELL_PRICE,
    "cart": {},
    "purchased": [],
    "failed": [],
    "max_cost": 0,
    "total_cost": 0
}

if manual:
    print("Enter skins line by line. Empty line to stop.")
    while True:
        s = input("> ").strip()
        if not s:
            break
        skins.append(s)
else:
    set_data = choose_set()
    skins = set_data["skins"]

    SELL_PRICE = float(set_data["sell_price"])
    state["set_name"] = set_data["name"]

    log(f"SELECTED SET: {set_data['name']}")
    log(f"SELL PRICE: {SELL_PRICE}")

state["sell_price"] = SELL_PRICE

failed_skins = []

# ================== SEARCH PHASE ==================

log("SEARCH START")

for skin in skins:
    res = find_best_lot(skin)

    if not res:
        failed_skins.append(skin)
        continue

    state["cart"][skin] = res

state["max_cost"] = sum(
    v["max_price"] for v in state["cart"].values()
) / 100

log(f"ITEMS: {len(state['cart'])}")
log(f"COST: {state['max_cost']:.2f}₽")

if input("BUY? (y/n): ").lower() != "y":
    exit()

# ================== CSV ==================

with open(PURCHASES_CSV, "w", newline="", encoding="utf-8") as f:
    csv.writer(f, delimiter=";").writerow(
        ["time", "skin", "id", "price", "status"]
    )

# ================== BUY PHASE ==================

real_cost = 0

for skin, data in state["cart"].items():

    log(f"BUY {skin}")

    success = False

    # TOP10
    for lot in data["lots"]:

        ok, err = buy_lot(lot)

        if ok:
            state["purchased"].append(skin)
            log(f"OK TOP10 {skin}", "OK")
            real_cost += lot["price"]
            success = True
            break

        time.sleep(1)

    # RETRY
    if not success:
        log(f"RETRY {skin}", "WARN")

        for _ in range(1):
            retry = find_best_lot(skin)
            if not retry:
                break

            for lot in retry["lots"]:
                ok, err = buy_lot(lot)
                if ok:
                    state["purchased"].append(skin)
                    real_cost += lot["price"]
                    success = True
                    break
                if not ok:
                    log(f"FAIL {skin} {err}", "WARN")

            if success:
                break

    # FALLBACK
    if not success:
        fallback_price = int(data["max_price"])
        lot_name = data["lots"][0]["name"]

        url = (
             "https://market.csgo.com/api/v2/buy-for" 
            f"?key={API_KEY}" 
            f"&hash_name={urllib.parse.quote(lot_name)}" 
            f"&price={fallback_price}" 
            f"&partner={partner}" 
            f"&token={token}" 
            f"&chance_to_transfer=90"
        )

        r = session.get(url, timeout=30).json()

        if r.get("success"):
            state["purchased"].append(skin)

            dataBuy = r.get("data")

            if dataBuy:
                real_cost += dataBuy["price"]
            else:
                real_cost += fallback_price

            log(f"FALLBACK OK {skin}", "OK")
        else:
            state["failed"].append(skin)
            log(f"FALLBACK FAIL {skin}", "ERROR")

state["total_cost"] = real_cost / 100

# ================== SAVE ==================

with open(ORDER_JSON, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

with open(FAILED_FILE, "w", encoding="utf-8") as f:
    for s in state["failed"]:
        f.write(s + "\n")

# ================== SUMMARY ==================

revenue = SELL_PRICE * (1 - COMMISSION)
profit = revenue - state["total_cost"]

with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
    f.write(f"SET: {state['set_name']}\n")
    f.write(f"TOTAL COST: {state['total_cost']:.2f}\n")
    f.write(f"SELL: {SELL_PRICE:.2f}\n")
    f.write(f"PROFIT: {profit:.2f}\n")

log("DONE")