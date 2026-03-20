import tkinter as tk
import os
from tkinter import messagebox
from PIL import Image, ImageTk  # Pillow do obrazków

# ===== OPCJONALNY Discord RPC =====
try:
    from pypresence import Presence
    RPC_AVAILABLE = True
except ImportError:
    RPC_AVAILABLE = False

DISCORD_CLIENT_ID = ""  # <-- TU wpisz swój client_id z Discord Developer Portal jeśli chcesz RPC

if RPC_AVAILABLE and DISCORD_CLIENT_ID:
    try:
        rpc = Presence(DISCORD_CLIENT_ID)
        rpc.connect()
        rpc.update(state="Panel By Me", details="Korzystam z launchera Phantom")
        print("[Discord RPC] Połączono!")
    except Exception as e:
        print(f"[Discord RPC] Nie udało się połączyć: {e}")
else:
    print("[Discord RPC] Wyłączony lub brak client_id")

# ===== USER =====
def get_current_user():
    try:
        return os.getlogin()
    except:
        return os.environ.get("USERNAME", "")

# ===== APP PATHS =====
def znajdz_minecraft_launcher(): return "MC_OFFICIAL"
def znajdz_discord(): return "DISCORD_OFFICIAL"
def znajdz_steam(): return "STEAM_OFFICIAL"

def znajdz_roblox():
    user = get_current_user()
    base = fr"C:\Users\{user}\AppData\Local\Roblox\Versions"
    if not os.path.exists(base):
        return None
    for root, dirs, files in os.walk(base):
        if "RobloxPlayerBeta.exe" in files:
            return os.path.join(root, "RobloxPlayerBeta.exe")
    return None

def znajdz_spotify():
    user = get_current_user()
    paths = [
        fr"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
        r"C:\Program Files\Spotify\Spotify.exe",
        r"C:\Program Files (x86)\Spotify\Spotify.exe",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

# ===== COLORS =====
T = {
    "bg": "#0d0d0d",
    "card": "#161616",
    "border": "#242424",
    "border_h": "#4ade80",
    "text": "#f0f0f0",
    "sub": "#555555",
    "accent": "#4ade80",
    "err": "#f87171",
}

W, H_MAIN = 460, 560

# ===== LAUNCHER =====
class PhantomLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Phantom Launcher")
        self.root.resizable(False, False)
        self.root.configure(bg=T["bg"])
        self.root.attributes("-alpha", 0.97)

        self.canvas = tk.Canvas(root, highlightthickness=0, bg=T["bg"])
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.current_scroll = 0
        self.max_scroll = 0

        # Trzymamy obrazki, żeby Tkinter ich nie wyrzucał
        self.images = []

        self._show_main()

    def _on_mousewheel(self, event):
        delta = int(-1*(event.delta/120)) * 20
        new_scroll = max(0, min(self.current_scroll + delta, self.max_scroll))
        move = new_scroll - self.current_scroll
        self.current_scroll = new_scroll
        self.canvas.move("all", 0, -move)

    def _show_main(self):
        self.root.geometry(f"{W}x{H_MAIN}")
        c = self.canvas
        c.delete("all")

        c.create_rectangle(0, 0, W, H_MAIN, fill=T["bg"], outline="")

        # TOP BAR
        self._rr(c, 0, 0, W, 85, 0, "#111111")
        c.create_line(0, 85, W, 85, fill=T["border"])

        # ---- Ikona Phantom ----
        try:
            icon_img = Image.open("Neon ghost logo with terminal prompt.png").resize((44,44), Image.ANTIALIAS)
        except Exception:
            icon_img = Image.new('RGBA', (44,44), (74,222,128,255))  # placeholder jeśli plik nie istnieje
        self.icon_tk = ImageTk.PhotoImage(icon_img)
        self.images.append(self.icon_tk)
        c.create_image(40, 40, image=self.icon_tk)

        c.create_text(82, 30, text="Phantom Launcher",
                      anchor="w", font=("Segoe UI", 13, "bold"), fill=T["text"])
        c.create_text(82, 52,
                      text="Twórca DC stoskacper123_43702",
                      anchor="w", font=("Segoe UI", 9), fill=T["sub"])

        # APPS
        apps = [
            ("Roblox", znajdz_roblox()),
            ("Minecraft", znajdz_minecraft_launcher()),
            ("Steam", znajdz_steam()),
            ("Spotify", znajdz_spotify()),
            ("Discord", znajdz_discord()),
        ]

        y = 108
        for name, path in apps:
            self._card(c, name, path, y)
            y += 100

        footer_y = y + 10
        c.create_line(25, footer_y, W - 25, footer_y, fill=T["border"])
        c.create_text(W // 2, footer_y + 20,
                      text="Phantom OS  --  Wszystkie systemy online",
                      font=("Segoe UI", 8), fill=T["sub"])

        self.max_scroll = max(0, (footer_y + 40) - H_MAIN)

    def _card(self, c, name, path, y):
        exists = path is not None
        h = 82

        bg = self._rr(c, 25, y, W - 25, y + h, 12, T["card"], T["border"], 1)
        self._rr(c, 42, y + 14, 86, y + h - 14, 10, "#1e1e1e")

        ico_map = {"Roblox": "R", "Minecraft": "M", "Steam": "S", "Spotify": "S", "Discord": "D"}
        c.create_text(64, y + h // 2, text=ico_map.get(name, name[0]),
                      font=("Consolas", 16, "bold"), fill=T["accent'])

        txt = c.create_text(102, y + 24, text=name,
                            anchor="w", font=("Segoe UI", 13, "bold"), fill=T["text'])

        scol = T["accent"] if exists else T["err"]
        stxt = "Gotowy" if exists else "Nie znaleziono"

        c.create_oval(102, y + 47, 112, y + 57, fill=scol, outline="")
        c.create_text(118, y + 52, text=stxt,
                      anchor="w", font=("Segoe UI", 9), fill=scol)

        arr = c.create_text(W - 42, y + h // 2, text=">",
                            font=("Segoe UI", 14, "bold"), fill=T["sub'])

        hit = self._rr(c, 25, y, W - 25, y + h, 12, "", "", 0)

        def on_enter(e):
            c.config(cursor="hand2")
            c.itemconfig(bg, outline=T["border_h'])
            c.itemconfig(arr, fill=T["accent'])
            c.itemconfig(txt, fill=T["accent'])

        def on_leave(e):
            c.config(cursor="")
            c.itemconfig(bg, outline=T["border'])
            c.itemconfig(arr, fill=T["sub'])
            c.itemconfig(txt, fill=T["text'])

        for item in [hit, bg, txt, arr]:
            c.tag_bind(item, "<Enter>", on_enter)
            c.tag_bind(item, "<Leave>", on_leave)
            c.tag_bind(item, "<Button-1>", lambda e, p=path, n=name: self._launch(p, n))

    def _launch(self, path, name):
        try:
            if path == "MC_OFFICIAL":
                os.system("start minecraft:")
            elif path == "DISCORD_OFFICIAL":
                os.system("start discord:")
            elif path == "STEAM_OFFICIAL":
                os.system("start steam:")
            elif path and os.path.exists(path):
                os.startfile(path)
            else:
                messagebox.showwarning("Phantom", f"Nie znaleziono: {name}")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def _rr(self, c, x1, y1, x2, y2, r, fill, outline="", w=0):
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2,
               x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return c.create_polygon(pts, smooth=True, fill=fill, outline=outline, width=w)


if __name__ == "__main__":
    root = tk.Tk()
    app = PhantomLauncher(root)
    root.mainloop()