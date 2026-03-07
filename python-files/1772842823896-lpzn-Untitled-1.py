#!/usr/bin/env python3
"""
Money Clicker - terminal-only Python clicker game
Save file: money_clicker_save.json
Commands: c (click), shop, stats, save, load, help, q (quit)
"""

import threading
import time
import json
import os
import math

SAVE_FILE = "money_clicker_save.json"


def fmt(m):
    return f"${m:,.2f}"


class Game:
    def __init__(self):
        self.lock = threading.Lock()
        self.money = 0.0
        self.per_click = 1.0
        self.auto_income = 0.0  # income per second
        self.click_count = 0
        self.start_time = time.time()
        # owned counts for dynamic shop pricing
        self.owned = {
            "cursor": 0,        # +1 per click
            "autoclicker": 0,   # +0.5 per second
            "multiplier": 0,    # multiply per_click by 2 (stacking)
        }
        self.stop_event = threading.Event()
        self.autothread = threading.Thread(target=self._auto_income_loop, daemon=True)
        self.autothread.start()

    def _auto_income_loop(self):
        last = time.time()
        while not self.stop_event.is_set():
            now = time.time()
            elapsed = now - last
            if elapsed >= 0.2:
                with self.lock:
                    # add pro-rated auto income
                    self.money += self.auto_income * elapsed
                last = now
            time.sleep(0.05)

    def click(self):
        with self.lock:
            self.money += self.per_click
            self.click_count += 1
            return self.per_click

    def buy(self, item):
        with self.lock:
            cost = self._cost(item)
            if self.money < cost:
                return False, cost
            self.money -= cost
            if item == "cursor":
                self.per_click += 1.0
                self.owned["cursor"] += 1
            elif item == "autoclicker":
                self.auto_income += 0.5
                self.owned["autoclicker"] += 1
            elif item == "multiplier":
                self.per_click *= 2.0
                self.owned["multiplier"] += 1
            return True, cost

    def _cost(self, item):
        # exponential price scaling
        if item == "cursor":
            base = 10.0
            factor = 1.15
            n = self.owned["cursor"]
            return base * (factor ** n)
        if item == "autoclicker":
            base = 50.0
            factor = 1.17
            n = self.owned["autoclicker"]
            return base * (factor ** n)
        if item == "multiplier":
            base = 1000.0
            factor = 3.0
            n = self.owned["multiplier"]
            return base * (factor ** n)
        return math.inf

    def stats(self):
        with self.lock:
            uptime = time.time() - self.start_time
            return {
                "money": self.money,
                "per_click": self.per_click,
                "auto_income": self.auto_income,
                "click_count": self.click_count,
                "uptime": uptime,
                "owned": dict(self.owned),
            }

    def save(self, filename=SAVE_FILE):
        with self.lock:
            data = {
                "money": self.money,
                "per_click": self.per_click,
                "auto_income": self.auto_income,
                "click_count": self.click_count,
                "start_time": self.start_time,
                "owned": self.owned,
            }
        with open(filename, "w") as f:
            json.dump(data, f)
        return filename

    def load(self, filename=SAVE_FILE):
        if not os.path.exists(filename):
            return False, "no save"
        with open(filename, "r") as f:
            data = json.load(f)
        with self.lock:
            self.money = float(data.get("money", 0.0))
            self.per_click = float(data.get("per_click", 1.0))
            self.auto_income = float(data.get("auto_income", 0.0))
            self.click_count = int(data.get("click_count", 0))
            self.start_time = float(data.get("start_time", time.time()))
            self.owned = dict(data.get("owned", self.owned))
        return True, filename

    def stop(self):
        self.stop_event.set()
        self.autothread.join(timeout=1.0)


def print_help():
    print("Commands:")
    print("  c            - click (gain money)")
    print("  shop         - open shop")
    print("  stats        - show stats")
    print("  save         - save game")
    print("  load         - load game")
    print("  help         - show this")
    print("  q            - quit and save")


def shop_menu(game: Game):
    items = [("cursor", "Cursor (+1 per click)"),
             ("autoclicker", "Auto-Clicker (+0.5 money/sec)"),
             ("multiplier", "Mega (double per-click)")]
    print("Shop:")
    for key, desc in items:
        cost = game._cost(key)
        owned = game.owned.get(key, 0)
        print(f"  {key:12} - {desc:30} cost {fmt(cost)} (owned: {owned})")
    choice = input("Buy which (key) or cancel: ").strip().lower()
    if choice == "" or choice == "cancel":
        return
    if choice not in [k for k, _ in items]:
        print("Unknown item.")
        return
    ok, cost = game.buy(choice)
    if ok:
        print(f"Purchased {choice} for {fmt(cost)}.")
    else:
        print(f"Not enough money. Cost: {fmt(cost)}.")


def main():
    game = Game()
    print("Money Clicker (terminal)")
    print_help()
    try:
        while True:
            cmd = input("> ").strip().lower()
            if cmd in ("c", "click"):
                amount = game.click()
                print(f"Clicked! +{fmt(amount)} (total {fmt(game.stats()['money'])})")
            elif cmd == "shop":
                shop_menu(game)
            elif cmd == "stats":
                s = game.stats()
                print(f"Money: {fmt(s['money'])}")
                print(f"Per click: {fmt(s['per_click'])}")
                print(f"Auto income: {fmt(s['auto_income'])} / sec")
                print(f"Clicks: {s['click_count']}")
                print(f"Owned: {s['owned']}")
                print(f"Uptime: {int(s['uptime'])}s")
            elif cmd == "save":
                fn = game.save()
                print(f"Saved to {fn}")
            elif cmd == "load":
                ok, msg = game.load()
                if ok:
                    print("Loaded.")
                else:
                    print("Load failed:", msg)
            elif cmd in ("help", "?"):
                print_help()
            elif cmd in ("q", "quit", "exit"):
                game.save()
                print("Game saved. Exiting.")
                break
            elif cmd == "":
                continue
            else:
                print("Unknown command. Type 'help'.")
    except KeyboardInterrupt:
        print("\nInterrupted. Saving and exiting.")
        game.save()
    finally:
        game.stop()


if __name__ == "__main__":
    main()