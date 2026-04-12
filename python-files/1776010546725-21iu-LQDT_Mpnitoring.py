import requests
import json
from datetime import datetime, timedelta, timezone

# ------------------------------------------------------------------
# НАСТРОЙКИ
# ------------------------------------------------------------------
TOKEN = "t.hcReCrvzwgX_FDwrPE97KiTqnVpX3zrhehjVMln0eJcdBNboX7NfzGrlz_JV7bCBR3j9jUi5iVg1I94Y0-L1ug"

# Актуальные FIGI (получены из твоего API)
FIGI_LQDT = "TCS60A1014L8"

OFZ_TICKER = "SU26238RMFS4"
OFZ_YIELD_ALARM = 22.0
LQDT_DROP_ALARM = -0.5
LQDT_DROP_CRITICAL = -2.0

BASE_URL = "https://invest-public-api.tinkoff.ru/rest"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


# ------------------------------------------------------------------
# ФУНКЦИИ API ТИНЬКОФФ (для LQDT)
# ------------------------------------------------------------------
def api_post(endpoint, body):
    try:
        r = requests.post(f"{BASE_URL}/{endpoint}", json=body, headers=HEADERS, timeout=10)
        return r.json()
    except Exception as e:
        print(f"   ❌ Ошибка API: {e}")
        return {}


def get_lqdt_prices():
    """Получает свечи LQDT по прямому FIGI"""
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=10)

    body = {
        "figi": FIGI_LQDT,
        "from": from_date.isoformat().replace('+00:00', 'Z'),
        "to": to_date.isoformat().replace('+00:00', 'Z'),
        "interval": "CANDLE_INTERVAL_DAY"
    }

    resp = api_post("tinkoff.public.invest.api.contract.v1.MarketDataService/GetCandles", body)
    candles = resp.get("candles", [])

    if not candles:
        print(f"   [!] Нет свечей для LQDT по FIGI {FIGI_LQDT}")
        return []

    prices = []
    for c in candles:
        close = float(c["close"]["units"]) + float(c["close"]["nano"]) / 1e9
        prices.append({
            "date": c["time"][:10],
            "price": round(close, 6)
        })
    return prices


# ------------------------------------------------------------------
# ФУНКЦИЯ ПАРСИНГА МОСБИРЖИ (для ОФЗ)
# ------------------------------------------------------------------
def get_ofz_yield_moex():
    """Парсит доходность ОФЗ с публичного API Мосбиржи (без токена)"""
    url = f"https://iss.moex.com/iss/engines/stock/markets/bonds/securities/{OFZ_TICKER}.json"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        marketdata = data.get("marketdata", {}).get("data", [])
        columns = data.get("marketdata", {}).get("columns", [])

        # Ищем столбец YIELD
        if "YIELD" in columns:
            idx = columns.index("YIELD")
            if marketdata and marketdata[0][idx] is not None:
                ytm = marketdata[0][idx]
                return round(ytm, 2)

        # Запасной вариант - YIELDDATE
        if "YIELDDATE" in columns:
            idx = columns.index("YIELDDATE")
            if marketdata and marketdata[0][idx] is not None:
                ytm = marketdata[0][idx]
                return round(ytm, 2)

        print("   [!] Доходность не найдена в ответе Мосбиржи")
        return None

    except Exception as e:
        print(f"   ❌ Ошибка парсинга Мосбиржи: {e}")
        return None


# ------------------------------------------------------------------
# АНАЛИЗ И ВЕРДИКТ
# ------------------------------------------------------------------
def analyze():
    print("=" * 50)
    print(f"📊 МОНИТОРИНГ LQDT - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("=" * 50)

    alerts = []
    critical = []

    # 1. Доходность ОФЗ (через Мосбиржу)
    ofz_yield = get_ofz_yield_moex()
    if ofz_yield:
        print(f"\n📈 Доходность ОФЗ {OFZ_TICKER}: {ofz_yield}%")
        if ofz_yield > OFZ_YIELD_ALARM:
            msg = f"⚠️ ТРЕВОГА: Доходность ОФЗ {ofz_yield}% > {OFZ_YIELD_ALARM}%"
            alerts.append(msg)
            print(f"   {msg}")
        else:
            print(f"   ✅ Норма (ниже {OFZ_YIELD_ALARM}%)")
    else:
        print("\n❌ Не удалось получить доходность ОФЗ")

    # 2. Динамика LQDT (через API Тинькофф)
    prices = get_lqdt_prices()
    if len(prices) >= 4:
        print(f"\n📉 Динамика LQDT:")
        today = prices[-1]["price"]
        yesterday = prices[-2]["price"]
        day3 = prices[-3]["price"]

        change_1d = round((today - yesterday) / yesterday * 100, 3)
        change_3d = round((today - day3) / day3 * 100, 3)

        print(f"   Сегодня: {today} ₽")
        print(f"   Вчера: {yesterday} ₽ ({change_1d:+.3f}%)")
        print(f"   3 дня назад: {day3} ₽ ({change_3d:+.3f}%)")

        if change_1d <= LQDT_DROP_ALARM:
            msg = f"⚠️ ТРЕВОГА: LQDT упал на {change_1d:.3f}% за день"
            alerts.append(msg)
            print(f"   {msg}")
        if change_3d <= LQDT_DROP_CRITICAL:
            msg = f"🚨 КРИТИЧЕСКИ: LQDT упал на {change_3d:.3f}% за 3 дня"
            critical.append(msg)
            print(f"   {msg}")
        if change_1d > LQDT_DROP_ALARM and change_3d > LQDT_DROP_CRITICAL:
            print(f"   ✅ Динамика в норме")
    else:
        print("\n❌ Недостаточно данных по LQDT")

    # 3. Вердикт
    print("\n" + "=" * 50)
    print("📋 ВЕРДИКТ:")
    print("=" * 50)

    if critical:
        print("🔴🔴🔴 КРИТИЧЕСКАЯ СИТУАЦИЯ!")
        print("   Рекомендация: ПРОДАТЬ ВСЕ LQDT СЕГОДНЯ")
        for msg in critical:
            print(f"   - {msg}")
    elif len(alerts) >= 2:
        print("🟡🟡 ПОВЫШЕННАЯ ТРЕВОЖНОСТЬ")
        print("   Рекомендация: Продать 50% LQDT, остальное мониторить ежедневно")
        for msg in alerts:
            print(f"   - {msg}")
    elif len(alerts) == 1:
        print("🟢 ВНИМАНИЕ (один сигнал)")
        print("   Рекомендация: Мониторить ежедневно, но пока держать")
        for msg in alerts:
            print(f"   - {msg}")
    else:
        print("🟢🟢🟢 ВСЁ СПОКОЙНО")
        print("   Рекомендация: Держать LQDT, ничего не делать")
        print("   Ожидаемая доходность: ~1.2% в месяц")

    print("\n" + "=" * 50)
    print("Следующая проверка: через 24 часа")
    print("=" * 50)


# ------------------------------------------------------------------
# ЗАПУСК
# ------------------------------------------------------------------
if __name__ == "__main__":
    if TOKEN == "ТВОЙ_ТОКЕН_С_ПОЛНЫМ_ДОСТУПОМ":
        print("❌ ВСТАВЬ СВОЙ ТОКЕН В ПЕРЕМЕННУЮ TOKEN!")
        exit(1)
    analyze()