#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dota 2 Counter Finder
----------------------
Вводишь одного или нескольких героев вражеской команды (через запятую) —
программа идёт на dotabuff.com (контрпики) и dota2counters.com (предметы),
и выдаёт:
  - объединённый список героев-контрпиков против всей введённой группы
  - core-айтем билд (предметы, которые нужны против всей группы)

Установка зависимостей (один раз):
    pip install requests beautifulsoup4

Запуск как скрипт:
    python dota_counter.py

Сборка в exe (Windows, один раз):
    pip install pyinstaller
    pyinstaller --onefile --console dota_counter.py
    exe появится в папке dist/

Программа не закрывается после ответа — просто вводишь следующих героев.
Ctrl+C или "exit" — выход.
"""

import re
import sys
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

MANUAL_SLUGS = {
    "антимаг": "anti-mage", "анти маг": "anti-mage", "antimage": "anti-mage",
    "мясник": "pudge", "лич кинг": "wraith-king", "крипп": "meepo",
    "цм": "crystal-maiden", "кристал маиден": "crystal-maiden",
    "нюкропос": "necrophos", "некрофос": "necrophos",
    "лд": "lone-druid", "нп": "natures-prophet", "пророк": "natures-prophet",
    "сф": "shadow-fiend", "тень": "shadow-fiend",
    "дп": "death-prophet", "фв": "faceless-void",
    "спс": "spirit-breaker", "разбиватель душ": "spirit-breaker",
    "др": "dragon-knight", "рыцарь дракон": "dragon-knight",
    "тарас": "tiny", "тини": "tiny",
    "квп": "queen-of-pain", "кв": "queen-of-pain",
    "нс": "night-stalker", "втв": "outworld-destroyer", "од": "outworld-destroyer",
}


def to_slug(name: str) -> str:
    name = name.strip().lower()
    if name in MANUAL_SLUGS:
        return MANUAL_SLUGS[name]
    name = name.replace("'", "").replace(".", "")
    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"[^a-z0-9\-]", "", name)
    return name


def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def parse_table_after(soup: BeautifulSoup, keyword: str):
    header = soup.find(string=re.compile(re.escape(keyword), re.I))
    if not header:
        return []
    node = header.find_parent()
    table = node.find_next("table") if node else None
    if not table:
        return []
    rows = []
    for tr in table.select("tbody tr"):
        link = tr.select_one("a[href*='/heroes/']")
        if not link:
            continue
        hero_name = link.get_text(strip=True)
        tds = tr.find_all("td")
        pct = tds[-2].get_text(strip=True) if len(tds) >= 2 else "0%"
        wr = tds[-1].get_text(strip=True) if len(tds) >= 1 else ""
        rows.append((hero_name, pct, wr))
    return rows


def get_counters(slug: str, top_n: int = 10):
    url = f"https://www.dotabuff.com/heroes/{slug}/counters"
    soup = get_soup(url)
    return parse_table_after(soup, "is countered by")[:top_n]


def get_items(slug: str):
    url = f"https://dota2counters.com/heroes/{slug}/"
    soup = get_soup(url)
    header = soup.find(string=re.compile("Find Items To Counter", re.I))
    items = []
    if header:
        node = header.find_parent()
        for el in node.find_all_next():
            if el.name == "h2":
                break
            if el.name == "img" and el.get("alt"):
                alt = el["alt"].strip()
                if alt:
                    items.append(alt)
    seen, unique = set(), []
    for it in items:
        if it not in seen:
            seen.add(it)
            unique.append(it)
    return unique


def pct_to_float(pct: str) -> float:
    try:
        return float(pct.replace("%", "").replace(",", "."))
    except ValueError:
        return 0.0


def run(hero_names):
    """hero_names — список имён вражеских героев."""
    per_hero_counters = {}
    per_hero_items = {}

    for raw in hero_names:
        slug = to_slug(raw)
        print(f"\nСобираю данные по: {raw.strip().title()} ({slug})...")
        try:
            per_hero_counters[raw] = get_counters(slug)
        except Exception as e:
            print(f"  Не удалось получить контрпики: {e}")
            per_hero_counters[raw] = []
        try:
            per_hero_items[raw] = get_items(slug)
        except Exception as e:
            print(f"  Не удалось получить предметы: {e}")
            per_hero_items[raw] = []

    # --- Агрегация контрпиков ---
    counter_score = defaultdict(lambda: [0, 0.0, set()])  # counter_hero -> [кол-во целей, сумма %, кто именно]
    for enemy, rows in per_hero_counters.items():
        for name, pct, wr in rows:
            entry = counter_score[name]
            entry[0] += 1
            entry[1] += pct_to_float(pct)
            entry[2].add(enemy.strip().title())

    ranked = sorted(counter_score.items(), key=lambda kv: (-kv[1][0], -kv[1][1]))

    print("\n" + "=" * 50)
    print("КОГО ПИКАТЬ (контрпики против всей группы)")
    print("=" * 50)
    if ranked:
        for hero, (count, total_pct, targets) in ranked[:12]:
            vs = ", ".join(sorted(targets))
            print(f"  - {hero}  [контрит {count} героев: {vs}]")
    else:
        print("  нет данных")

    # --- Агрегация предметов (core-билд) ---
    item_score = defaultdict(lambda: [0, set()])
    for enemy, items in per_hero_items.items():
        for it in items:
            entry = item_score[it]
            entry[0] += 1
            entry[1].add(enemy.strip().title())

    ranked_items = sorted(item_score.items(), key=lambda kv: -kv[1][0])

    print("\n" + "=" * 50)
    print("CORE ITEM BUILD (против всей группы)")
    print("=" * 50)
    core = [x for x in ranked_items if x[1][0] >= 2]
    situational = [x for x in ranked_items if x[1][0] == 1]

    if core:
        print("Core (эффективны сразу против нескольких героев):")
        for item, (count, targets) in core:
            print(f"  - {item}  [против: {', '.join(sorted(targets))}]")
    if situational:
        print("\nСитуативно (по одному герою):")
        for item, (count, targets) in situational:
            print(f"  - {item}  [против: {', '.join(sorted(targets))}]")
    if not core and not situational:
        print("  нет данных")
    print()


def split_heroes(line: str):
    if "," in line:
        parts = [p.strip() for p in line.split(",")]
    else:
        parts = line.split()
    return [p for p in parts if p]


def main():
    print("Dota 2 Counter Finder")
    print("Вводи героев вражеской команды через запятую (например: pudge, anti-mage, tinker)")
    print("Команда 'exit' или Ctrl+C — выход.\n")

    if len(sys.argv) > 1:
        line = " ".join(sys.argv[1:])
        run(split_heroes(line))

    while True:
        try:
            line = input("Враги> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nПока.")
            break
        if not line:
            continue
        if line.lower() in ("exit", "quit", "выход"):
            break
        heroes = split_heroes(line)
        if heroes:
            run(heroes)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nОшибка: {e}")
        input("Нажми Enter, чтобы закрыть...")
