"""
ATI.SU — Монитор грузов с GUI и автозвонком
=============================================
Требования:
    pip install playwright
    playwright install chromium

Запуск:
    python ati_monitor.py

Tkinter входит в стандартную библиотеку Python.
"""

import asyncio
import json
import re
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from tkinter import (
    Tk, Frame, Label, Entry, Button, Text, Scrollbar,
    StringVar, BooleanVar, OptionMenu, END, DISABLED, NORMAL,
    messagebox, ttk
)


# ─────────────────────────────────────────────────────────────────────
#  BACKEND
# ─────────────────────────────────────────────────────────────────────

SEEN_IDS_FILE = "seen_ids.json"


def load_seen_ids() -> set:
    try:
        with open(SEEN_IDS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_seen_ids(ids: set):
    with open(SEEN_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, ensure_ascii=False)


def copy_to_clipboard_sys(text: str):
    try:
        if sys.platform == "win32":
            subprocess.run("clip", input=text.encode("utf-16"), check=True)
        elif sys.platform == "darwin":
            subprocess.run("pbcopy", input=text.encode("utf-8"), check=True)
        else:
            try:
                subprocess.run(["xclip", "-selection", "clipboard"],
                               input=text.encode("utf-8"), check=True)
            except FileNotFoundError:
                subprocess.run(["xsel", "--clipboard", "--input"],
                               input=text.encode("utf-8"), check=True)
    except Exception:
        pass


def make_call(phone: str, call_method: str) -> str:
    clean = re.sub(r"[^\d+]", "", phone)
    if not clean.startswith("+"):
        clean = "+7" + clean.lstrip("7").lstrip("8")
    copy_to_clipboard_sys(clean)
    if call_method == "tel":
        webbrowser.open(f"tel:{clean}")
    return clean


def price_ok(price_str: str, price_min: int, price_max: int) -> bool:
    if price_min == 0 and price_max == 0:
        return True
    digits = re.sub(r"[^\d]", "", price_str)
    if not digits:
        return True
    price = int(digits)
    if price_min and price < price_min:
        return False
    if price_max and price > price_max:
        return False
    return True


async def get_phone_from_card(context, cargo_url: str):
    page = None
    try:
        page = await context.new_page()
        await page.goto(cargo_url, timeout=30_000)
        await page.wait_for_load_state("domcontentloaded")

        show_btn = page.locator(
            "button:has-text('Показать телефон'), "
            "button:has-text('Показать контакты'), "
            "a:has-text('Показать телефон')"
        ).first
        if await show_btn.count() > 0:
            await show_btn.click()
            await page.wait_for_timeout(2000)

        phone_el = page.locator(
            "[class*='phone'], [class*='Phone'], "
            "[data-testid*='phone'], a[href^='tel:']"
        ).first
        if await phone_el.count() > 0:
            text = await phone_el.inner_text()
            return text.strip()

        body = await page.inner_text("body")
        match = re.search(
            r"(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", body
        )
        if match:
            return match.group(0)
    except Exception:
        pass
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
    return None


async def search_cargos(page, city_from: str, city_to: str) -> list:
    await page.goto("https://ati.su/loads", timeout=30_000)
    await page.wait_for_load_state("domcontentloaded")
    await page.wait_for_timeout(2000)

    for selector, value in [
        (
            "input[placeholder*='Откуда'], input[placeholder*='откуда'], "
            "input[name*='from'], input[aria-label*='Откуда']",
            city_from
        ),
        (
            "input[placeholder*='Куда'], input[placeholder*='куда'], "
            "input[name*='to'], input[aria-label*='Куда']",
            city_to
        ),
    ]:
        try:
            inp = page.locator(selector).first
            await inp.fill("")
            await inp.fill(value)
            await page.wait_for_timeout(1000)
            suggestion = page.locator(
                "[class*='suggest'] li, [class*='autocomplete'] li, [role='option']"
            ).first
            if await suggestion.count() > 0:
                await suggestion.click()
                await page.wait_for_timeout(500)
        except Exception:
            pass

    try:
        btn = page.locator(
            "button:has-text('Найти'), button[type='submit'], input[type='submit']"
        ).first
        await btn.click()
        await page.wait_for_load_state("networkidle", timeout=15_000)
        await page.wait_for_timeout(2000)
    except Exception:
        pass

    cargos = []
    try:
        cards = await page.locator(
            "a[href*='/loads/'], [class*='load-item'], [class*='cargo-item']"
        ).all()
        for card in cards[:30]:
            try:
                href = await card.get_attribute("href") or ""
                if "/loads/" not in href:
                    continue
                if not href.startswith("http"):
                    href = "https://ati.su" + href
                id_match = re.search(r"/loads/(\d+)", href)
                if not id_match:
                    continue
                cargo_id = id_match.group(1)
                title = (await card.inner_text()).strip()[:120].replace("\n", " ")
                price_match = re.search(r"[\d\s]{3,}[\s]*(руб|₽|р\.)", title)
                price_str = price_match.group(0) if price_match else ""
                cargos.append({
                    "id":    cargo_id,
                    "title": title,
                    "price": price_str,
                    "url":   href,
                })
            except Exception:
                continue
    except Exception:
        pass

    return cargos


async def monitor_loop(config: dict, log_fn, stop_event: threading.Event):
    from playwright.async_api import async_playwright
    seen_ids = load_seen_ids()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not config["show_browser"])
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        search_page = await context.new_page()
        iteration = 0

        while not stop_event.is_set():
            iteration += 1
            ts = datetime.now().strftime("%H:%M:%S")
            log_fn(f"\n[{ts}] Итерация #{iteration}...", "info")

            try:
                cargos = await search_cargos(
                    search_page, config["city_from"], config["city_to"]
                )
                log_fn(f"  Найдено на странице: {len(cargos)}", "info")

                for cargo in cargos:
                    cid = cargo["id"]
                    if cid in seen_ids:
                        continue
                    if cargo["price"] and not price_ok(
                        cargo["price"], config["price_min"], config["price_max"]
                    ):
                        seen_ids.add(cid)
                        continue

                    log_fn(f"\n  НОВЫЙ ГРУЗ #{cid}", "new")
                    log_fn(f"  {cargo['title'][:100]}", "new")
                    log_fn(f"  {cargo['url']}", "new")

                    phone = await get_phone_from_card(context, cargo["url"])
                    if phone:
                        clean = make_call(phone, config["call_method"])
                        log_fn(f"  Звоним: {clean}", "phone")
                    else:
                        log_fn("  Телефон не найден — открываю карточку", "err")
                        webbrowser.open(cargo["url"])

                    seen_ids.add(cid)

                save_seen_ids(seen_ids)

            except Exception as e:
                log_fn(f"  Ошибка: {e}", "err")

            log_fn(
                f"  Следующая проверка через {config['check_interval']} сек.", "info"
            )

            for _ in range(config["check_interval"] * 2):
                if stop_event.is_set():
                    break
                await asyncio.sleep(0.5)

        await browser.close()
        log_fn("\nМониторинг остановлен.", "info")


# ─────────────────────────────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────────────────────────────

BG       = "#1a1a2e"
CARD     = "#16213e"
ACCENT   = "#0f3460"
GREEN    = "#00d4aa"
RED_CLR  = "#e94560"
GOLD     = "#ffd700"
FG       = "#e8e8f0"
FG2      = "#8888aa"
ENTRY_BG = "#0d1b2a"
FONT     = ("Consolas", 10)
FONT_SM  = ("Consolas", 9)
FONT_BIG = ("Consolas", 13, "bold")


def make_entry(parent, textvariable=None, width=20):
    return Entry(
        parent, textvariable=textvariable, width=width,
        bg=ENTRY_BG, fg=FG, insertbackground=FG,
        relief="flat", bd=4, font=FONT,
        highlightthickness=1,
        highlightbackground=ACCENT,
        highlightcolor=GREEN,
    )


def section_frame(parent, title):
    outer = Frame(
        parent, bg=CARD,
        highlightthickness=1, highlightbackground=ACCENT,
    )
    outer.pack(fill="x", pady=(0, 10))
    Label(
        outer, text=title, bg=ACCENT, fg=FG2,
        font=FONT_SM, anchor="w", padx=8, pady=3,
    ).pack(fill="x")
    inner = Frame(outer, bg=CARD, padx=12, pady=8)
    inner.pack(fill="x")
    return inner


def form_row(parent, label_text, widget, hint=""):
    row = Frame(parent, bg=CARD)
    row.pack(fill="x", pady=3)
    Label(row, text=label_text, bg=CARD, fg=FG2,
          font=FONT_SM, width=17, anchor="w").pack(side="left")
    widget.pack(side="left")
    if hint:
        Label(row, text=hint, bg=CARD, fg=FG2,
              font=("Consolas", 8)).pack(side="left", padx=6)


class App:
    def __init__(self, root: Tk):
        self.root = root
        root.title("ATI.SU — Монитор грузов")
        root.configure(bg=BG)
        root.resizable(True, True)
        root.minsize(640, 560)

        # ── Заголовок ─────────────────────────────────────────
        hdr = Frame(root, bg=ACCENT, pady=12)
        hdr.pack(fill="x")
        Label(hdr, text="ATI.SU  |  Монитор грузов",
              bg=ACCENT, fg=GREEN, font=FONT_BIG).pack()
        Label(hdr, text="автоматический поиск и звонок при новом грузе",
              bg=ACCENT, fg=FG2, font=FONT_SM).pack()

        # ── Тело ──────────────────────────────────────────────
        body = Frame(root, bg=BG, padx=18, pady=14)
        body.pack(fill="both", expand=True)

        col_l = Frame(body, bg=BG)
        col_r = Frame(body, bg=BG)
        col_l.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        col_r.grid(row=0, column=1, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        # ── Маршрут ───────────────────────────────────────────
        s1 = section_frame(col_l, "  МАРШРУТ")
        self.city_from = StringVar(value="Москва")
        self.city_to   = StringVar(value="Санкт-Петербург")
        form_row(s1, "Город отправки", make_entry(s1, self.city_from))
        form_row(s1, "Город доставки", make_entry(s1, self.city_to))

        # ── Цена ──────────────────────────────────────────────
        s2 = section_frame(col_l, "  ФИЛЬТР ПО ЦЕНЕ (руб.)")
        self.price_min = StringVar(value="0")
        self.price_max = StringVar(value="0")
        form_row(s2, "Минимум", make_entry(s2, self.price_min, 12), "0 = без ограничений")
        form_row(s2, "Максимум", make_entry(s2, self.price_max, 12), "0 = без ограничений")

        # ── Параметры ─────────────────────────────────────────
        s3 = section_frame(col_r, "  ПАРАМЕТРЫ МОНИТОРИНГА")
        self.interval = StringVar(value="60")
        form_row(s3, "Интервал (сек)", make_entry(s3, self.interval, 8),
                 "минимум 10")

        self.call_method = StringVar(value="tel")
        om_row = Frame(s3, bg=CARD)
        om_row.pack(fill="x", pady=3)
        Label(om_row, text="Метод звонка", bg=CARD, fg=FG2,
              font=FONT_SM, width=17, anchor="w").pack(side="left")
        om = OptionMenu(om_row, self.call_method, "tel", "clip")
        om.configure(
            bg=ENTRY_BG, fg=FG, activebackground=ACCENT,
            activeforeground=FG, relief="flat", bd=0,
            font=FONT_SM, highlightthickness=1,
            highlightbackground=ACCENT,
        )
        om["menu"].configure(bg=ENTRY_BG, fg=FG, font=FONT_SM,
                             activebackground=ACCENT, activeforeground=FG)
        om.pack(side="left")
        Label(om_row, text="tel=звонок  clip=только буфер",
              bg=CARD, fg=FG2, font=("Consolas", 8)).pack(side="left", padx=8)

        self.show_browser = BooleanVar(value=False)
        cb_row = Frame(s3, bg=CARD)
        cb_row.pack(fill="x", pady=3)
        Label(cb_row, text="Показать браузер", bg=CARD, fg=FG2,
              font=FONT_SM, width=17, anchor="w").pack(side="left")
        style = ttk.Style()
        style.configure("Dark.TCheckbutton",
                         background=CARD, foreground=FG2)
        ttk.Checkbutton(cb_row, variable=self.show_browser,
                        style="Dark.TCheckbutton").pack(side="left")
        Label(cb_row, text="(отладка)", bg=CARD, fg=FG2,
              font=("Consolas", 8)).pack(side="left", padx=6)

        # ── Кнопки ────────────────────────────────────────────
        btn_row = Frame(body, bg=BG)
        btn_row.grid(row=1, column=0, columnspan=2,
                     pady=(10, 4), sticky="w")

        self.start_btn = Button(
            btn_row, text="▶  ЗАПУСТИТЬ",
            bg=GREEN, fg="#000000",
            activebackground="#00ffcc", activeforeground="#000000",
            relief="flat", font=("Consolas", 11, "bold"),
            padx=18, pady=7, cursor="hand2",
            command=self.start_monitoring,
        )
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = Button(
            btn_row, text="■  ОСТАНОВИТЬ",
            bg=RED_CLR, fg="#ffffff",
            activebackground="#ff6b6b", activeforeground="#ffffff",
            relief="flat", font=("Consolas", 11, "bold"),
            padx=18, pady=7, cursor="hand2",
            state=DISABLED,
            command=self.stop_monitoring,
        )
        self.stop_btn.pack(side="left")

        self.status_lbl = Label(
            btn_row, text="●  Остановлен",
            bg=BG, fg=RED_CLR, font=FONT_SM,
        )
        self.status_lbl.pack(side="left", padx=16)

        # ── Лог ───────────────────────────────────────────────
        log_wrap = Frame(root, bg=BG, padx=18, pady=(0, 14))
        log_wrap.pack(fill="both", expand=True)

        Label(log_wrap, text="  ЛОГ", bg=BG, fg=FG2,
              font=FONT_SM, anchor="w").pack(fill="x")

        log_border = Frame(
            log_wrap, bg=CARD,
            highlightthickness=1, highlightbackground=ACCENT,
        )
        log_border.pack(fill="both", expand=True)

        sb = Scrollbar(log_border)
        sb.pack(side="right", fill="y")

        self.log_text = Text(
            log_border, bg=ENTRY_BG, fg=FG,
            font=("Consolas", 9),
            relief="flat", bd=0,
            state=DISABLED,
            yscrollcommand=sb.set,
            wrap="word", height=10,
        )
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)
        sb.config(command=self.log_text.yview)

        self.log_text.tag_config("new",   foreground=GREEN)
        self.log_text.tag_config("err",   foreground=RED_CLR)
        self.log_text.tag_config("phone", foreground=GOLD)
        self.log_text.tag_config("info",  foreground=FG2)

        self._stop_event = None
        self._thread     = None

    # ── Лог ───────────────────────────────────────────────────
    def log(self, text: str, tag: str = "info"):
        def _insert():
            self.log_text.configure(state=NORMAL)
            self.log_text.insert(END, text + "\n", tag)
            self.log_text.see(END)
            self.log_text.configure(state=DISABLED)
        self.root.after(0, _insert)

    # ── Запуск ────────────────────────────────────────────────
    def start_monitoring(self):
        errors = []
        if not self.city_from.get().strip():
            errors.append("Укажите город отправки")
        if not self.city_to.get().strip():
            errors.append("Укажите город доставки")
        try:
            interval = int(self.interval.get())
            if interval < 10:
                errors.append("Интервал — не менее 10 секунд")
        except ValueError:
            errors.append("Интервал должен быть числом")
            interval = 60
        try:
            pmin = int(self.price_min.get())
            pmax = int(self.price_max.get())
            if pmin < 0 or pmax < 0:
                errors.append("Цены не могут быть отрицательными")
            if pmax and pmin > pmax:
                errors.append("Минимальная цена больше максимальной")
        except ValueError:
            errors.append("Цены должны быть числами")
            pmin = pmax = 0

        if errors:
            messagebox.showerror("Ошибка настроек", "\n".join(errors))
            return

        config = {
            "city_from":      self.city_from.get().strip(),
            "city_to":        self.city_to.get().strip(),
            "price_min":      pmin,
            "price_max":      pmax,
            "check_interval": interval,
            "call_method":    self.call_method.get(),
            "show_browser":   self.show_browser.get(),
        }

        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(config, self._stop_event),
            daemon=True,
        )
        self._thread.start()

        self.start_btn.configure(state=DISABLED)
        self.stop_btn.configure(state=NORMAL)
        self.status_lbl.configure(text="●  Работает", fg=GREEN)
        self.log(
            f"Запуск: {config['city_from']} → {config['city_to']} | "
            f"цена {config['price_min'] or '—'}…{config['price_max'] or '—'} руб. | "
            f"интервал {config['check_interval']} сек.",
            "new"
        )

    def _run_loop(self, config, stop_event):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(monitor_loop(config, self.log, stop_event))
        except Exception as e:
            self.log(f"Критическая ошибка: {e}", "err")
        finally:
            loop.close()
            self.root.after(0, self._on_stopped)

    def _on_stopped(self):
        self.start_btn.configure(state=NORMAL)
        self.stop_btn.configure(state=DISABLED)
        self.status_lbl.configure(text="●  Остановлен", fg=RED_CLR)

    # ── Остановка ─────────────────────────────────────────────
    def stop_monitoring(self):
        if self._stop_event:
            self._stop_event.set()
        self.stop_btn.configure(state=DISABLED)
        self.status_lbl.configure(text="●  Остановка…", fg=GOLD)
        self.log("Отправлен сигнал остановки…", "info")


if __name__ == "__main__":
    root = Tk()
    App(root)
    root.mainloop()
