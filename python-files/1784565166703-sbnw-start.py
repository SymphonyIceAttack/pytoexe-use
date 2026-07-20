#!/usr/bin/python3
import asyncio
import csv
import re
from playwright.async_api import async_playwright

BASE_URL = (
    "https://ostrovok.ru/hotel/russia/novosibirsk/"
    "?dates=18.06.2026-19.06.2026&guests=2&search=yes&q=2721&sort=price&page={page}"
)

MAX_PAGES = 10
OUTPUT_CSV = "hotels.csv"


def parse_price(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 999_999_999


async def scrape_page(page, url: str) -> list[dict]:
    await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    await asyncio.sleep(7)

    hotels = await page.evaluate("""
        () => {
            const results = [];
            // Группируем ссылки по href — каждые 5 ссылок = 1 отель
            const linkGroups = {};
            document.querySelectorAll('a[href*="/hotel/russia/novosibirsk/"]').forEach(a => {
                const href = a.getAttribute('href');
                if (!linkGroups[href]) linkGroups[href] = [];
                const text = a.innerText.trim();
                if (text) linkGroups[href].push(text);
            });

            for (const [href, texts] of Object.entries(linkGroups)) {
                let name    = null;
                let rating  = null;
                let reviews = null;
                let score   = null;
                let price   = null;

                for (const t of texts) {
                    // Цена: содержит ₽
                    if (!price && t.includes('₽')) {
                        price = t.split('\\n')[0].trim();
                    }
                    // Рейтинг: "Отлично\\n2045 отзывов\\n8,4"
                    else if (!rating && /отзыв/i.test(t)) {
                        const parts = t.split('\\n');
                        rating  = parts[0] || null;   // "Отлично"
                        reviews = parts[1] || null;   // "2045 отзывов"
                        score   = parts[2] || null;   // "8,4"
                    }
                    // Название отеля — первая непустая строка без служебных слов
                    else if (!name && t.length > 3 && !t.includes('номера')) {
                        name = t;
                    }
                }

                if (name && price) {
                    results.push({ name, price, rating, reviews, score, href });
                }
            }
            return results;
        }
    """)
    return hotels


async def main():
    all_hotels: list[dict] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        )

        for page_num in range(1, MAX_PAGES + 1):
            url = BASE_URL.format(page=page_num)
            print(f"📄 Страница {page_num} ...", end=" ", flush=True)

            hotels = await scrape_page(page, url)

            if not hotels:
                print("пусто, останавливаемся.")
                break

            # Стоп если страница дублирует первую (пагинация кончилась)
            if all_hotels and hotels[0]["name"] == all_hotels[0]["name"]:
                print("дубликат первой страницы, останавливаемся.")
                break

            print(f"найдено {len(hotels)} отелей")
            all_hotels.extend(hotels)
            await asyncio.sleep(2)

        await browser.close()

    # --- Дедупликация ---
    seen, unique = set(), []
    for h in all_hotels:
        if h["name"] not in seen:
            seen.add(h["name"])
            unique.append(h)

    # --- Сортировка по цене ---
    for h in unique:
        h["price_int"] = parse_price(h["price"])
    unique.sort(key=lambda x: x["price_int"])

    # --- Сохраняем CSV ---
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "rank", "name", "price", "price_int",
            "score", "rating", "reviews", "url"
        ])
        writer.writeheader()
        for i, h in enumerate(unique, 1):
            writer.writerow({
                "rank":      i,
                "name":      h["name"],
                "price":     h["price"],
                "price_int": h["price_int"],
                "score":     h.get("score", ""),
                "rating":    h.get("rating", ""),
                "reviews":   h.get("reviews", ""),
                "url":       "https://ostrovok.ru" + h["href"],
            })

    print(f"\n💾 CSV сохранён: {OUTPUT_CSV}  ({len(unique)} отелей)")

    # --- Топ-10 в терминал ---
    print(f"\n{'='*72}")
    print(f"  ТОП-10  |  Новосибирск, 18–19 июня 2026, 2 гостя")
    print(f"{'='*72}")
    print(f"{'#':<4} {'Цена':>12}  {'Оценка':>6}  {'Отель'}")
    print(f"{'-'*72}")
    for h in unique[:10]:
        score = h.get("score") or "—"
        print(f"{h['rank']:<4} {h['price']:>12}  {score:>6}  {h['name']}")
    print(f"{'='*72}")
    print(f"Всего уникальных отелей собрано: {len(unique)}")

asyncio.run(main())
