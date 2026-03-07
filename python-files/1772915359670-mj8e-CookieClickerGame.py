#!/usr/bin/env python3
"""
Simple Cookie Clicker - single-file tkinter game

Controls:
- Click the big cookie button to get cookies.
- Buy items from the shop to increase CPS (cookies per second).
- Game auto-saves to cookiesave.json on exit.
"""

import json
import math
import os
import tkinter as tk
from tkinter import ttk

SAVE_FILE = "cookiesave.json"
TICK_MS = 100  # update interval in milliseconds

ITEMS = [
    {"id": "cursor", "name": "Cursor", "base_cost": 15, "cps": 0.1},
    {"id": "grandma", "name": "Grandma", "base_cost": 100, "cps": 1},
    {"id": "farm", "name": "Farm", "base_cost": 1100, "cps": 8},
    {"id": "mine", "name": "Mine", "base_cost": 12000, "cps": 47},
    {"id": "factory", "name": "Factory", "base_cost": 130000, "cps": 260},
]


class Game:
    def __init__(self):
        self.cookies = 0.0
        self.total_cookies = 0.0
        self.click_value = 1.0
        self.items_owned = {it["id"]: 0 for it in ITEMS}
        self.last_save = None
        self.load()

    def cps(self):
        return sum(self.items_owned[it["id"]] * it["cps"] for it in ITEMS)

    def buy_cost(self, item):
        # exponential scaling: base_cost * 1.15^n
        n = self.items_owned[item["id"]]
        return math.ceil(item["base_cost"] * (1.15 ** n))

    def can_buy(self, item):
        return self.cookies >= self.buy_cost(item)

    def buy(self, item):
        cost = self.buy_cost(item)
        if self.cookies >= cost:
            self.cookies -= cost
            self.items_owned[item["id"]] += 1
            return True
        return False

    def click(self):
        self.cookies += self.click_value
        self.total_cookies += self.click_value

    def tick(self, dt):
        # dt in seconds
        gain = self.cps() * dt
        self.cookies += gain
        self.total_cookies += gain

    def save(self):
        data = {
            "cookies": self.cookies,
            "total_cookies": self.total_cookies,
            "click_value": self.click_value,
            "items_owned": self.items_owned,
        }
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def load(self):
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            self.cookies = float(data.get("cookies", 0.0))
            self.total_cookies = float(data.get("total_cookies", 0.0))
            self.click_value = float(data.get("click_value", 1.0))
            saved_items = data.get("items_owned", {})
            for k in self.items_owned:
                self.items_owned[k] = int(saved_items.get(k, 0))
        except Exception:
            pass


class CookieClickerApp(tk.Tk):
    def __init__(self, game):
        super().__init__()
        self.title("Cookie Clicker")
        self.game = game
        self._build_ui()
        self._last_tick = None
        self._running = True
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(TICK_MS, self._update_loop)

    def _build_ui(self):
        main = ttk.Frame(self, padding=10)
        main.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)
        # Cookie display and button
        top = ttk.Frame(main)
        top.grid(row=0, column=0, sticky="ew")
        self.cookies_var = tk.StringVar()
        self.cps_var = tk.StringVar()
        ttk.Label(top, textvariable=self.cookies_var, font=("TkDefaultFont", 18)).grid(row=0, column=0, sticky="w")
        ttk.Label(top, textvariable=self.cps_var).grid(row=1, column=0, sticky="w")
        self.cookie_btn = ttk.Button(main, text="🍪 Click Cookie 🍪", command=self.on_click)
        self.cookie_btn.grid(row=1, column=0, sticky="ew", pady=8)

        # Shop
        shop_frame = ttk.LabelFrame(main, text="Shop")
        shop_frame.grid(row=2, column=0, sticky="nsew")
        shop_frame.columnconfigure(1, weight=1)
        self.item_vars = {}
        for i, item in enumerate(ITEMS):
            name = item["name"]
            var = tk.StringVar()
            self.item_vars[item["id"]] = var
            ttk.Label(shop_frame, text=name).grid(row=i, column=0, sticky="w", padx=4, pady=2)
            btn = ttk.Button(shop_frame, textvariable=var, command=lambda it=item: self.buy_item(it))
            btn.grid(row=i, column=1, sticky="ew", padx=4, pady=2)

        # Footer: total cookies and save button
        footer = ttk.Frame(main)
        footer.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        self.total_var = tk.StringVar()
        ttk.Label(footer, textvariable=self.total_var).grid(row=0, column=0, sticky="w")
        ttk.Button(footer, text="Save", command=self.game.save).grid(row=0, column=1, sticky="e")

        self.update_ui(initial=True)

    def format_cookies(self, v):
        if v >= 1e9:
            return f"{v/1e9:.2f}B"
        if v >= 1e6:
            return f"{v/1e6:.2f}M"
        if v >= 1e3:
            return f"{v/1e3:.2f}k"
        return f"{v:.1f}".rstrip("0").rstrip(".")

    def update_ui(self, initial=False):
        self.cookies_var.set(f"Cookies: {self.format_cookies(self.game.cookies)}")
        self.cps_var.set(f"CPS: {self.format_cookies(self.game.cps())}")
        self.total_var.set(f"Total: {self.format_cookies(self.game.total_cookies)}")
        for item in ITEMS:
            cost = self.game.buy_cost(item)
            owned = self.game.items_owned[item["id"]]
            self.item_vars[item["id"]].set(f"{owned} — Cost: {self.format_cookies(cost)}")
        if not initial:
            self.update_idletasks()

    def on_click(self):
        self.game.click()
        self.update_ui()

    def buy_item(self, item):
        if self.game.buy(item):
            self.update_ui()

    def _update_loop(self):
        if not self._running:
            return
        # compute dt
        dt = TICK_MS / 1000.0
        self.game.tick(dt)
        self.update_ui()
        self.after(TICK_MS, self._update_loop)

    def on_close(self):
        self._running = False
        self.game.save()
        self.destroy()


def main():
    game = Game()
    app = CookieClickerApp(game)
    app.mainloop()


if __name__ == "__main__":
    main()