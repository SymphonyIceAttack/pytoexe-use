
import asyncio
import threading
import time
import subprocess
import requests
import re
from datetime import datetime
from pathlib import Path

import pyautogui
import keyboard
import polars as pl

from tsetmc.market_watch import MarketWatch
from tsetmc.instruments import Instrument

# ============================================================
# تنظیمات
# ============================================================

SYMBOL = ""

POLL_INTERVAL_MS = 100
CLICK_DELAY_MS = 800

CLICK_COUNT = 1
CLICK_INTERVAL_MS = 50

# کلیدها
POSITION_KEY = "f2"       # ثبت موقعیت موس
TEST_CLICK_KEY = "f3"     # یک کلیک آزمایشی روی موقعیت ذخیره‌شده
ARM_KEY = "f8"            # ARM / DISARM
STOP_KEY = "f9"           # توقف کامل

LOG_FILE = "click_log.csv"

# آدرس TSETMC برای اندازه‌گیری تأخیر شبکه
PING_HOST = "cdn.tsetmc.com"

# هر چند ثانیه یک بار Ping/HTTP Delay اندازه‌گیری شود
NETWORK_CHECK_INTERVAL_SEC = 10

# ============================================================

running = True
armed = False
click_position = None
click_in_progress = False
trigger_lock = threading.Lock()

log_lock = threading.Lock()


def log_event(event, extra=""):
    """ثبت رویداد با زمان دقیق تا میلی‌ثانیه."""
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    line = f"{stamp},{event},{extra}\n"

    with log_lock:
        new_file = not Path(LOG_FILE).exists()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            if new_file:
                f.write("timestamp,event,details\n")
            f.write(line)

    print(f"[{stamp}] {event} {extra}")



def measure_network():
    """هر ۱۰ ثانیه RTT پینگ ویندوز و زمان پاسخ HTTP به TSETMC را اندازه می‌گیرد."""
    try:
        # ICMP ping در ویندوز
        t0 = time.perf_counter_ns()
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "2000", PING_HOST],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        ping_ms = None
        # استخراج زمان از خروجی ping؛ نمونه: time=32ms یا time<1ms
        m = re.search(r"time[=<]\s*(\d+)\s*ms", result.stdout, re.I)
        if m:
            ping_ms = float(m.group(1))
        elif result.returncode == 0:
            ping_ms = (time.perf_counter_ns() - t0) / 1_000_000

        # RTT واقعی درخواست HTTPS به CDN TSETMC
        http_ms = None
        try:
            t1 = time.perf_counter_ns()
            r = requests.get(
                "https://cdn.tsetmc.com/",
                timeout=3,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            http_ms = (time.perf_counter_ns() - t1) / 1_000_000
            r.close()
        except Exception:
            pass

        ping_text = f"{ping_ms:.1f} ms" if ping_ms is not None else "N/A"
        http_text = f"{http_ms:.1f} ms" if http_ms is not None else "N/A"

        print(f"🌐 TSETMC Network | Ping: {ping_text} | HTTP delay: {http_text}")
        log_event(
            "NETWORK",
            f"ping_ms={ping_text};http_delay_ms={http_text}"
        )

    except Exception as e:
        print("خطا در اندازه‌گیری شبکه:", e)
        log_event("NETWORK_ERROR", str(e))


def network_monitor():
    """مانیتور شبکه در Thread جدا تا پایش بازار را متوقف نکند."""
    while running:
        try:
            measure_network()
        except Exception as e:
            print("خطای مانیتور شبکه:", e)
            log_event("NETWORK_ERROR", str(e))

        for _ in range(NETWORK_CHECK_INTERVAL_SEC * 10):
            if not running:
                return
            time.sleep(0.1)


def save_click_position():
    global click_position

    x, y = pyautogui.position()
    click_position = (x, y)

    print()
    print(f"📍 موقعیت ذخیره شد: X={x}, Y={y}")
    log_event("POSITION_SAVED", f"x={x};y={y}")


def test_click():
    """فقط یک کلیک آزمایشی؛ هیچ ارتباطی با تریگر بازار ندارد."""
    if click_position is None:
        print("❌ ابتدا موس را روی محل موردنظر ببرید و F2 بزنید.")
        return

    x, y = click_position

    print(f"🧪 TEST CLICK روی X={x}, Y={y}")
    log_event("TEST_CLICK_START", f"x={x};y={y}")

    pyautogui.click(x, y)

    log_event("TEST_CLICK_DONE", f"x={x};y={y}")


def toggle_arm():
    global armed

    # بدون موقعیت، ARM نشود و هیچ Thread جدیدی ساخته نشود.
    if not armed and click_position is None:
        print("\n⚠️ ابتدا موس را روی محل کلیک ببرید و F2 بزنید.")
        log_event("ARM_REFUSED", "position_not_set")
        return

    # ARM/DISARM به صورت idempotent:
    # اگر دوباره در حالت ARM کلید زده شود، برنامه دوباره راه نمی‌افتد.
    if armed:
        armed = False
        print("\n🔴 ARM = OFF")
        log_event("ARM_OFF")
    else:
        armed = True
        print("\n🟢 ARM = ON")
        log_event("ARM_ON")


def emergency_stop():
    global running
    running = False
    print("\n⛔ STOP")
    log_event("STOP")


async def resolve_symbol(symbol):
    symbol = symbol.strip()

    if not symbol:
        raise ValueError("نام نماد یا InsCode وارد نشده است.")

    if symbol.isdigit():
        return symbol

    print(f"در حال جستجوی نماد: {symbol}")

    instrument = await Instrument.from_search(symbol)

    if instrument is None:
        raise RuntimeError(f"نماد «{symbol}» پیدا نشد.")

    return str(instrument.ins_code)


def get_status_from_row(row):
    for col in ("c_etaval_title", "cEtavalTitle"):
        if col in row.columns:
            value = row[col][0]
            if value is not None:
                return str(value).strip()
    return None


def delayed_click():
    global click_in_progress

    try:
        if click_position is None:
            print("❌ موقعیت کلیک با F2 تعیین نشده.")
            log_event("TRIGGER_ABORTED", "position_not_set")
            return

        trigger_time = time.perf_counter_ns()

        log_event(
            "TRIGGER",
            "ممنوع->ممنوع-محفوظ"
        )

        print(
            f"⏳ تأخیر {CLICK_DELAY_MS} ms "
            f"| تعداد کلیک {CLICK_COUNT}"
        )

        time.sleep(CLICK_DELAY_MS / 1000.0)

        if not running or not armed:
            log_event("CLICK_ABORTED", "not_running_or_disarmed")
            return

        x, y = click_position

        for i in range(CLICK_COUNT):
            before = time.perf_counter_ns()

            pyautogui.click(x, y)

            after = time.perf_counter_ns()

            elapsed_from_trigger_ms = (
                after - trigger_time
            ) / 1_000_000

            click_duration_ms = (
                after - before
            ) / 1_000_000

            log_event(
                f"CLICK_{i + 1}",
                f"x={x};y={y};"
                f"from_trigger_ms={elapsed_from_trigger_ms:.3f};"
                f"click_duration_ms={click_duration_ms:.3f}"
            )

            if i < CLICK_COUNT - 1:
                time.sleep(CLICK_INTERVAL_MS / 1000.0)

    finally:
        with trigger_lock:
            click_in_progress = False


async def market_loop(inscode):
    global running, click_in_progress

    market_watch = MarketWatch()

    print("\nMarketWatch در حال شروع است...")
    await market_watch.start()

    print("🟢 MarketWatch فعال شد.")
    print("F2=ثبت موقعیت | F3=کلیک تستی | F8=ARM | F9=STOP")
    print(f"Log: {Path(LOG_FILE).resolve()}\n")

    previous_status = None

    while running:
        try:
            await asyncio.wait_for(
                market_watch.update_event.wait(),
                timeout=POLL_INTERVAL_MS / 1000.0
            )
        except asyncio.TimeoutError:
            pass

        if not running:
            break

        try:
            df = market_watch.df

            if df is None:
                continue

            row = df.filter(
                pl.col("ins_code") == inscode
            )

            if row.height == 0:
                continue

            status = get_status_from_row(row)

            if status is None:
                continue

            if previous_status is None:
                previous_status = status
                print("وضعیت اولیه:", status)
                continue

            if status != previous_status:
                print(
                    f"{time.strftime('%H:%M:%S')} "
                    f"{previous_status} -> {status}"
                )

                # فقط این جهت:
                # ممنوع -> ممنوع-محفوظ
                if (
                    armed
                    and previous_status == "ممنوع"
                    and status == "ممنوع-محفوظ"
                ):
                    with trigger_lock:
                        if not click_in_progress:
                            click_in_progress = True
                            threading.Thread(
                                target=delayed_click,
                                daemon=True
                            ).start()

                previous_status = status

        except Exception as e:
            print("خطای پردازش:", e)


async def main():
    global running

    print("=" * 58)
    print("             TSETMC AUTO CLICKER")
    print("=" * 58)

    symbol = SYMBOL.strip()

    if not symbol:
        symbol = input("نام نماد یا InsCode: ").strip()

    inscode = await resolve_symbol(symbol)

    print()
    print(f"InsCode: {inscode}")
    print(f"Polling: {POLL_INTERVAL_MS} ms")
    print(f"Click delay: {CLICK_DELAY_MS} ms")
    print(f"Click count: {CLICK_COUNT}")
    print(f"Click interval: {CLICK_INTERVAL_MS} ms")
    print()
    print("F2 = ذخیره موقعیت موس")
    print("F3 = یک کلیک آزمایشی")
    print("F8 = ARM / DISARM")
    print("F9 = STOP")
    print(f"Ping/HTTP delay: هر {NETWORK_CHECK_INTERVAL_SEC} ثانیه")
    print()
    print("وضعیت اولیه: DISARM")
    print("برای شروع: F2 → F3 (اختیاری برای تست) → F8")
    print()

    keyboard.add_hotkey(POSITION_KEY, save_click_position)
    keyboard.add_hotkey(TEST_CLICK_KEY, test_click)
    keyboard.add_hotkey(ARM_KEY, toggle_arm)
    keyboard.add_hotkey(STOP_KEY, emergency_stop)

    # مانیتور شبکه مستقل از MarketWatch
    threading.Thread(
        target=network_monitor,
        daemon=True
    ).start()

    await market_loop(inscode)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        running = False
    finally:
        keyboard.unhook_all()
