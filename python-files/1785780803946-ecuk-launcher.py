import ctypes
import json
import os
import urllib.request
import tkinter as tk
from PIL import Image, ImageTk

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

BG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bg.png")
LICENSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "license.dat")
SERVER_URL = os.environ.get(
    "LAUNCHER_SERVER", "http://127.0.0.1:5441")

W, H = 903, 494
TITLEBAR_H = 34
DARK = "#0e1220"
RADIUS = 30
BLUR = 14


class Launcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Launcher")
        self.root.overrideredirect(True)
        self.root.geometry(f"{W}x{H}")
        self.root.configure(bg=DARK)

        self.init_x = self.init_y = 0

        self.build_ui()

    def build_ui(self):
        self.canvas = tk.Canvas(self.root, width=W, height=H,
                                highlightthickness=0, bg=DARK)
        self.canvas.place(x=0, y=0)

        self.bg_img = self.make_rounded_bg()
        self.canvas.create_image(0, 0, image=self.bg_img, anchor="nw")

        self.canvas.bind("<Button-1>", self.drag_start)
        self.canvas.bind("<B1-Motion>", self.drag_move)

        self.build_key_field()

        self.canvas.create_text(W - 27, TITLEBAR_H // 2 + 1, text="\u2715",
                                font=("Segoe UI", 11), fill="#c8cedd",
                                tags=("xbtn",))
        self.canvas.tag_bind("xbtn", "<ButtonPress>", lambda e: self.close())
        self.canvas.tag_bind("xbtn", "<Enter>",
                             lambda e: self.canvas.itemconfigure(
                                 "xbtn", fill="#ffffff"))
        self.canvas.tag_bind("xbtn", "<Leave>",
                             lambda e: self.canvas.itemconfigure(
                                 "xbtn", fill="#c8cedd"))

        self.root.update_idletasks()
        self.apply_rounded_region()

    def build_key_field(self):
        c = self.canvas
        cx = W // 2
        cy = H // 2
        card_w, card_h = 460, 190
        self.card_img = self.make_card_img(cx - card_w // 2,
                                           cy - card_h // 2, card_w, card_h)
        c.create_image(cx - card_w // 2, cy - card_h // 2,
                       image=self.card_img, anchor="nw")

        c.create_text(cx, cy - 14, text="\U0001f511  Введите свой ключ",
                      font=("Segoe UI", 17, "bold"), fill="#ffffff")

        self.build_key_entry()

    def build_key_entry(self):
        c = self.canvas
        cx = W // 2
        cy = H // 2

        # подложка поля: белая, со скруглением
        self.entry_bg = self.make_round_rect(340, 48, "#fdfdfd",
                                             pos=(cx - 170, cy + 26),
                                             radius=8)
        self.entry_bg_focus = self.make_round_rect(
            340, 48, "#ffffff", outline="#6a7bff",
            pos=(cx - 170, cy + 26), radius=8)
        self.entry_bg_id = c.create_image(cx - 170, cy + 26,
                                          image=self.entry_bg, anchor="nw")

        self.key_entry = tk.Entry(self.root, bg="#fdfdfd", fg="#1a1a2e",
                                  relief="flat", insertbackground="#1a1a2e",
                                  font=("Segoe UI", 13), justify="left",
                                  highlightthickness=0, bd=0)
        self.entry_id = c.create_window(cx - 160, cy + 32, anchor="nw",
                                        window=self.key_entry, width=320,
                                        height=36)

        self.placeholder = "Введите ключ"
        self.key_entry.insert(0, self.placeholder)
        self.key_entry.config(fg="#8a8fa3")
        self.key_entry.bind("<FocusIn>", self.entry_focus_in)
        self.key_entry.bind("<FocusOut>", self.entry_focus_out)
        self.key_entry.bind("<Return>", self.activate)

        self.status_id = c.create_text(cx, cy + 86, text="",
                                       font=("Segoe UI", 10, "bold"),
                                       fill="#9aa3c0")

    def entry_focus_in(self, event=None):
        c = self.canvas
        if hasattr(self, "entry_bg_id"):
            c.itemconfigure(self.entry_bg_id, image=self.entry_bg_focus)
        if self.key_entry.get() == self.placeholder:
            self.key_entry.delete(0, "end")
            self.key_entry.config(fg="#1a1a2e")

    def entry_focus_out(self, event=None):
        c = self.canvas
        if hasattr(self, "entry_bg_id"):
            c.itemconfigure(self.entry_bg_id, image=self.entry_bg)
        if not self.key_entry.get():
            self.key_entry.insert(0, self.placeholder)
            self.key_entry.config(fg="#8a8fa3")
        else:
            self.key_entry.config(fg="#1a1a2e")

    def make_card_img(self, x, y, w, h):
        from PIL import Image, ImageDraw, ImageEnhance
        ss = 3
        w2, h2 = w * ss, h * ss
        crop = self.bg_pil.crop((x, y, x + w, y + h)).resize(
            (w2, h2), Image.LANCZOS)
        dark = ImageEnhance.Brightness(crop.copy()).enhance(0.5)

        mask = Image.new("L", (w2, h2), 0)
        d = ImageDraw.Draw(mask)
        d.rounded_rectangle([0, 0, w2 - 1, h2 - 1], radius=18 * ss,
                            fill=255)

        base = Image.composite(dark, crop, mask).resize((w, h),
                                                        Image.LANCZOS)
        d2 = ImageDraw.Draw(base)
        d2.rounded_rectangle([0, 0, w - 1, h - 1], radius=18,
                             outline="#3a4570", width=1)
        return ImageTk.PhotoImage(base)

    def make_round_rect(self, w, h, fill, outline=None,
                        base=(16, 21, 38), pos=None, radius=None):
        from PIL import Image, ImageDraw
        ss = 3
        w2, h2 = w * ss, h * ss
        r = (h // 2 if radius is None else radius) * ss
        x0, y0 = pos or (0, 0)
        crop = self.bg_pil.crop((x0, y0, x0 + w, y0 + h)).resize(
            (w2, h2), Image.LANCZOS)
        overlay = Image.new("RGB", (w2, h2), fill)

        mask = Image.new("L", (w2, h2), 0)
        dm = ImageDraw.Draw(mask)
        dm.rounded_rectangle([0, 0, w2 - 1, h2 - 1], radius=r,
                             fill=255)

        im = Image.composite(overlay, crop, mask).resize((w, h),
                                                         Image.LANCZOS)
        d = ImageDraw.Draw(im)
        if outline:
            d.rounded_rectangle([0, 0, w - 1, h - 1],
                                radius=(radius or h // 2), outline=outline,
                                width=1)
        return ImageTk.PhotoImage(im)

    def make_glass_card(self, cx, cy, w, h):
        try:
            from PIL import ImageFilter, ImageEnhance, ImageDraw
            x0, y0 = cx - w // 2, cy - h // 2
            im = Image.open(BG_PATH).convert("RGB")
            im = im.resize((W, H), Image.LANCZOS)
            crop = im.crop((x0, y0, x0 + w, y0 + h))

            crop = crop.filter(ImageFilter.GaussianBlur(10))
            crop = ImageEnhance.Brightness(crop).enhance(0.55)

            mask = Image.new("L", (w, h), 0)
            d = ImageDraw.Draw(mask)
            d.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=255)

            base = Image.new("RGB", (w, h), (16, 21, 38))
            base.paste(crop, (0, 0), mask)
            return ImageTk.PhotoImage(base)
        except Exception:
            return None
    def make_rounded_bg(self):
        from PIL import ImageFilter, ImageDraw
        import random
        im = Image.open(BG_PATH).convert("RGB")
        im = im.resize((W, H), Image.LANCZOS)

        # 1) денойз: убирает цифровой шум и артефакты сжатия
        im = im.filter(ImageFilter.MedianFilter(size=3))

        # 2) размытие фона
        im = im.filter(ImageFilter.GaussianBlur(BLUR))

        # 3) сглаживание бандинга градиентов: мягкий разброс ±1 по каналам
        px = im.load()
        for y in range(H):
            for x in range(0, W, 1):
                r, g, b = px[x, y]
                d = random.randint(-1, 1)
                px[x, y] = (
                    max(0, min(255, r + d)),
                    max(0, min(255, g + d)),
                    max(0, min(255, b + d)),
                )

        # 4) лёгкая резкость для чёткости деталей
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=60,
                                               threshold=2))
        self.bg_pil = im

        mask = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(mask)
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=RADIUS, fill=255)

        dark = Image.new("RGB", (W, H), DARK)
        dark.paste(im, (0, 0), mask)
        return ImageTk.PhotoImage(dark)

    def apply_rounded_region(self):
        try:
            from PIL import ImageDraw
            hwnd = int(self.root.frame(), 16)
            dpi = 1.0
            try:
                dpi = ctypes.windll.user32.GetDpiForWindow(hwnd) / 96.0
            except Exception:
                pass
            rw = int(W * dpi)
            rh = int(H * dpi)
            radius = int(RADIUS * dpi)
            mask = Image.new("L", (rw, rh), 0)
            d = ImageDraw.Draw(mask)
            d.rounded_rectangle([0, 0, rw - 1, rh - 1], radius=radius,
                                fill=255)
            bmp = self._mask_to_hrgn(mask, rw, rh)
            ctypes.windll.user32.SetWindowRgn(hwnd, bmp, True)
        except Exception:
            pass

    def _mask_to_hrgn(self, mask, w, h):
        from ctypes import c_int
        px = mask.load()
        regions = []
        gdi32 = ctypes.windll.gdi32
        for y in range(h):
            x = 0
            while x < w:
                if px[x, y] > 128:
                    x0 = x
                    while x < w and px[x, y] > 128:
                        x += 1
                    regions.append((x0, y, x - x0, 1))
                else:
                    x += 1
        hrgn = gdi32.CreateRectRgn(0, 0, 0, 0)
        for (x0, y, rw, rh) in regions:
            r = gdi32.CreateRectRgn(x0, y, x0 + rw, y + rh)
            gdi32.CombineRgn(hrgn, hrgn, r, 2)
            gdi32.DeleteObject(r)
        return hrgn

    def activate(self, event=None):
        key = self.key_entry.get().strip().upper()
        self.set_status("", "#9aa3c0")

        if not key:
            self.set_status("Введите ключ", "#ff8080")
            return

        hwid = self.get_hwid()

        payload = json.dumps({"key": key, "hwid": hwid}).encode("utf-8")
        req = urllib.request.Request(
            SERVER_URL + "/api/activate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            self.set_status("Сервер недоступен", "#ff8080")
            return

        if data.get("ok"):
            self.save_license(key)
            self.show_activated()
        else:
            self.set_status(data.get("msg", "?"), "#ff8080")

    def save_license(self, key):
        try:
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                f.write(f"{key}\n")
        except Exception:
            pass

    def load_license(self):
        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                return f.read().strip().upper()
        except Exception:
            return None

    def check_saved_license(self):
        key = self.load_license()
        if not key:
            return
        hwid = self.get_hwid()
        payload = json.dumps({"key": key, "hwid": hwid}).encode("utf-8")
        req = urllib.request.Request(
            SERVER_URL + "/api/verify",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return
        if data.get("ok"):
            self.show_activated()

    def show_activated(self):
        self.canvas.itemconfigure("key_title", text="\u2713  Аккаунт активирован")
        self.canvas.itemconfigure(self.entry_bg_id, state="hidden")
        self.canvas.itemconfigure(self.entry_id, state="hidden")
        self.canvas.itemconfigure(self.status_id, text="",
                                  fill="#9aa3c0")
        self.canvas.create_text(W // 2, self.status_y, text="Добро пожаловать!",
                                font=("Segoe UI", 11, "bold"),
                                fill="#6ee88a", tags=("welcome",))

    def get_hwid(self):
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography"
            ) as k:
                guid, _ = winreg.QueryValueEx(k, "MachineGuid")
                return str(guid).strip().lower()
        except Exception:
            return "unknown-hwid"

    def set_status(self, text, color):
        if not hasattr(self, "status_id"):
            return
        self.canvas.itemconfigure(self.status_id, text=text, fill=color)

    def close(self):
        self.root.destroy()

    def drag_start(self, event):
        self.init_x = event.x_root
        self.init_y = event.y_root
        self.win_x = self.root.winfo_x()
        self.win_y = self.root.winfo_y()

    def drag_move(self, event):
        dx = event.x_root - self.init_x
        dy = event.y_root - self.init_y
        self.root.geometry(f"+{self.win_x + dx}+{self.win_y + dy}")


if __name__ == "__main__":
    root = tk.Tk()
    Launcher(root)
    root.mainloop()