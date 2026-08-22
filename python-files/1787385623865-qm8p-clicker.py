import tkinter as tk
from tkinter import ttk


# ============================================================
# THEMES
# ============================================================

THEMES = {
    "Midnight": {
        "bg": "#09090b",
        "panel": "#111114",
        "text": "#f4f4f5",
        "muted": "#8b8b93",
        "button": "#1b1b20",
    },

    "Carbon": {
        "bg": "#151515",
        "panel": "#1e1e1e",
        "text": "#eeeeee",
        "muted": "#8a8a8a",
        "button": "#292929",
    },

    "Mono Blue": {
        "bg": "#0a1118",
        "panel": "#111a24",
        "text": "#edf6ff",
        "muted": "#8191a3",
        "button": "#192737",
    },

    "Soft Purple": {
        "bg": "#100d15",
        "panel": "#19141f",
        "text": "#f4efff",
        "muted": "#998fa5",
        "button": "#241b2e",
    },
}


# ============================================================
# MAIN APP
# ============================================================

class Clicker(tk.Tk):

    def __init__(self):
        super().__init__()

        # Window
        self.title("Click")
        self.geometry("560x700")
        self.minsize(500, 620)
        self.resizable(True, True)

        # Game variables
        self.score = 0

        self.click_power = 1
        self.auto_power = 0

        self.click_cost = 25
        self.auto_cost = 100

        self.current_theme = "Midnight"

        # Build everything
        self.build_ui()

        # Apply initial theme
        self.apply_theme()

        # Start passive income
        self.after(1000, self.tick)


    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        # ---------------- HEADER ----------------

        self.header = tk.Frame(self)

        self.header.pack(
            fill="x",
            padx=32,
            pady=(25, 5)
        )


        # App title

        self.title_label = tk.Label(
            self.header,
            text="CLICK",
            font=("Segoe UI", 18, "bold")
        )

        self.title_label.pack(side="left")


        # Theme dropdown

        self.theme_var = tk.StringVar(
            value=self.current_theme
        )

        self.theme_box = ttk.Combobox(
            self.header,
            textvariable=self.theme_var,
            values=list(THEMES.keys()),
            state="readonly",
            width=13
        )

        self.theme_box.pack(side="right")

        self.theme_box.bind(
            "<<ComboboxSelected>>",
            self.change_theme
        )


        # ---------------- SCORE ----------------

        self.score_label = tk.Label(
            self,
            text="0",
            font=("Segoe UI", 64, "bold")
        )

        self.score_label.pack(
            pady=(75, 5)
        )


        # Stats

        self.info_label = tk.Label(
            self,
            text="+1 per click  •  +0/sec",
            font=("Segoe UI", 11)
        )

        self.info_label.pack()


        # ---------------- CLICK BUTTON ----------------

        self.click_button = tk.Button(
            self,
            text="CLICK",
            command=self.click,

            font=("Segoe UI", 16, "bold"),

            relief="flat",
            bd=0,

            width=15,
            height=3,

            cursor="hand2"
        )

        self.click_button.pack(
            pady=40
        )


        # ---------------- UPGRADES TITLE ----------------

        self.upgrades_label = tk.Label(
            self,
            text="UPGRADES",
            font=("Segoe UI", 10, "bold")
        )

        self.upgrades_label.pack(
            anchor="w",
            padx=42,
            pady=(0, 8)
        )


        # ---------------- CLICK POWER UPGRADE ----------------

        self.click_upgrade = tk.Button(
            self,

            command=self.buy_click_upgrade,

            relief="flat",
            bd=0,

            anchor="w",

            padx=18,
            pady=14,

            font=("Segoe UI", 10, "bold"),

            cursor="hand2"
        )

        self.click_upgrade.pack(
            fill="x",
            padx=32,
            pady=4
        )


        # ---------------- PASSIVE UPGRADE ----------------

        self.auto_upgrade = tk.Button(
            self,

            command=self.buy_auto_upgrade,

            relief="flat",
            bd=0,

            anchor="w",

            padx=18,
            pady=14,

            font=("Segoe UI", 10, "bold"),

            cursor="hand2"
        )

        self.auto_upgrade.pack(
            fill="x",
            padx=32,
            pady=4
        )


        # ---------------- STATUS ----------------

        self.status_label = tk.Label(
            self,
            text="Click to begin.",
            font=("Segoe UI", 9)
        )

        self.status_label.pack(
            pady=20
        )


        # ---------------- KEYBOARD ----------------

        # Spacebar also clicks

        self.bind(
            "<space>",
            lambda event: self.click()
        )


    # ========================================================
    # THEME SYSTEM
    # ========================================================

    def change_theme(self, event=None):

        self.current_theme = self.theme_var.get()

        self.apply_theme()


    def apply_theme(self):

        theme = THEMES[self.current_theme]


        # Main window

        self.configure(
            bg=theme["bg"]
        )


        # Header

        self.header.configure(
            bg=theme["bg"]
        )


        # Text

        self.title_label.configure(
            bg=theme["bg"],
            fg=theme["text"]
        )

        self.score_label.configure(
            bg=theme["bg"],
            fg=theme["text"]
        )

        self.info_label.configure(
            bg=theme["bg"],
            fg=theme["muted"]
        )

        self.upgrades_label.configure(
            bg=theme["bg"],
            fg=theme["text"]
        )

        self.status_label.configure(
            bg=theme["bg"],
            fg=theme["muted"]
        )


        # Buttons

        for button in (
            self.click_button,
            self.click_upgrade,
            self.auto_upgrade
        ):

            button.configure(
                bg=theme["panel"],
                fg=theme["text"],

                activebackground=theme["button"],
                activeforeground=theme["text"]
            )


        # Combobox styling

        style = ttk.Style(self)

        style.theme_use("clam")

        style.configure(
            "TCombobox",

            fieldbackground=theme["panel"],
            background=theme["panel"],
            foreground=theme["text"],

            borderwidth=0
        )


        self.refresh_ui()


    # ========================================================
    # CLICKING
    # ========================================================

    def click(self):

        self.score += self.click_power

        self.status_label.configure(
            text=""
        )

        self.refresh_ui()


    # ========================================================
    # CLICK POWER UPGRADE
    # ========================================================

    def buy_click_upgrade(self):

        if self.score >= self.click_cost:

            # Spend clicks

            self.score -= self.click_cost

            # Increase clicking power

            self.click_power += 1

            # Make next upgrade more expensive

            self.click_cost = int(
                self.click_cost * 1.65
            )

            self.status_label.configure(
                text="Click power upgraded."
            )

        else:

            self.status_label.configure(
                text="Not enough clicks."
            )


        self.refresh_ui()


    # ========================================================
    # PASSIVE CLICK UPGRADE
    # ========================================================

    def buy_auto_upgrade(self):

        if self.score >= self.auto_cost:

            # Spend clicks

            self.score -= self.auto_cost

            # Increase passive income

            self.auto_power += 1

            # Increase next price

            self.auto_cost = int(
                self.auto_cost * 1.8
            )

            self.status_label.configure(
                text="Passive clicks upgraded."
            )

        else:

            self.status_label.configure(
                text="Not enough clicks."
            )


        self.refresh_ui()


    # ========================================================
    # UPDATE DISPLAY
    # ========================================================

    def refresh_ui(self):

        # Main number

        self.score_label.configure(
            text=f"{self.score:,}"
        )


        # Stats

        self.info_label.configure(
            text=(
                f"+{self.click_power} per click"
                f"  •  "
                f"+{self.auto_power}/sec"
            )
        )


        # Click upgrade

        self.click_upgrade.configure(
            text=(
                f"  +1 CLICK POWER"
                f"                         "
                f"{self.click_cost:,}"
            )
        )


        # Passive upgrade

        self.auto_upgrade.configure(
            text=(
                f"  +1 PASSIVE / SEC"
                f"                         "
                f"{self.auto_cost:,}"
            )
        )


    # ========================================================
    # PASSIVE INCOME TIMER
    # ========================================================

    def tick(self):

        if self.auto_power > 0:

            self.score += self.auto_power

            self.refresh_ui()


        # Run again after 1 second

        self.after(
            1000,
            self.tick
        )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app = Clicker()

    app.mainloop()