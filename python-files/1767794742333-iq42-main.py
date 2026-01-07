import tkinter as tk
from PIL import Image, ImageTk
import os

# ===== SÉCURITÉ =====
import security

# ===== MODULES =====
from articles import Articles
from arrivages import Arrivages
from ventes import Ventes
from resume import Resume
from rapport import Rapport

# ===== CONFIG =====
APP_TITLE = "TOPIC TELECOM"
BG_IMAGE = "background.png"   # ton image EXACTE

# zones alignées SUR L’IMAGE (NE PAS CHANGER)
BTN_X1 = 60
BTN_X2 = 420
BTN_H  = 70
BTN_Y  = [190, 270, 350, 430, 510, 590]  # Articles → Quitter


class Main(tk.Tk):
    def __init__(self):
        super().__init__()

        # ===== SÉCURITÉ AVANT TOUT =====
        security.security_check(self)

        self.title(APP_TITLE)
        self.state("zoomed")
        self.configure(bg="black")

        self.update()
        w, h = self.winfo_width(), self.winfo_height()

        # ===== CANVAS =====
        self.canvas = tk.Canvas(self, width=w, height=h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # ===== IMAGE PLEIN ÉCRAN =====
        img = Image.open(BG_IMAGE).resize((w, h), Image.LANCZOS)
        self.bg = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, image=self.bg, anchor="nw")

        # ===== ZONES INVISIBLES (MENU IMAGE) =====
        self.zone(BTN_Y[0], lambda e: Articles(self))
        self.zone(BTN_Y[1], lambda e: Arrivages(self))
        self.zone(BTN_Y[2], lambda e: Ventes(self))
        self.zone(BTN_Y[3], lambda e: Resume(self))
        self.zone(BTN_Y[4], lambda e: Rapport(self))
        self.zone(BTN_Y[5], lambda e: self.destroy())

        # ===== BOUTON ACTIVER LICENCE (VISIBLE & TEMPORAIRE) =====
        self.check_licence_button()

    def check_licence_button(self):
        data = security.load_data()

        if not data.get("licensed", False):
            self.btn_licence = tk.Button(
                self,
                text="🔑 Activer licence",
                bg="#f5b000",
                fg="black",
                font=("Arial", 11, "bold"),
                cursor="hand2",
                command=self.activate_licence
            )
            # position sur le côté droit (toujours visible)
            self.btn_licence.place(relx=0.985, y=20, anchor="ne")

    def activate_licence(self):
        security.activate_license(self)
        data = security.load_data()

        if data.get("licensed", False):
            self.btn_licence.destroy()

    def zone(self, y, action):
        r = self.canvas.create_rectangle(
            BTN_X1, y,
            BTN_X2, y + BTN_H,
            outline="", fill=""
        )
        self.canvas.tag_bind(r, "<Button-1>", action)
        self.canvas.tag_bind(r, "<Enter>", lambda e: self.config(cursor="hand2"))
        self.canvas.tag_bind(r, "<Leave>", lambda e: self.config(cursor=""))


if __name__ == "__main__":
    Main().mainloop()
