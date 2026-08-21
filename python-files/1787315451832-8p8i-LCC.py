import random
import tkinter as tk
from tkinter import messagebox
from dataclasses import dataclass
import json
import os

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# ============================================================
# CONFIGURATION
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BACKGROUND = "#0B1120"
PANEL = "#111827"
PANEL_LIGHT = "#1F2937"

GREEN = "#22C55E"
RED = "#EF4444"
BLUE = "#3B82F6"
YELLOW = "#F59E0B"
PURPLE = "#8B5CF6"

TEXT = "#F8FAFC"
TEXT_MUTED = "#94A3B8"

STARTING_MONEY = 25_000
MAX_DAYS = 1000

# ============================================================
# SAUVEGARDE WINDOWS
# ============================================================

APP_NAME = "BusinessEmpire"

if os.name == "nt":

    SAVE_DIR = os.path.join(
        os.environ.get(
            "APPDATA",
            os.path.expanduser("~")
        ),
        APP_NAME
    )

else:

    SAVE_DIR = os.path.join(
        os.path.expanduser("~"),
        f".{APP_NAME}"
    )

# Création automatique du dossier
try:
    os.makedirs(
        SAVE_DIR,
        exist_ok=True
    )
except Exception:
    pass

SAVE_FILE = os.path.join(
    SAVE_DIR,
    "sauvegarde.json"
)


# ============================================================
# PRODUIT
# ============================================================

@dataclass
class Product:

    name: str
    production_cost: float
    sale_price: float
    stock: int = 0
    total_sold: int = 0


# ============================================================
# JEU
# ============================================================

class BusinessGame(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title("Business Empire")

        self.geometry(
            "1400x850"
        )

        self.minsize(
            900,
            600
        )

        self.configure(
            fg_color=BACKGROUND
        )

        # ====================================================
        # PLEIN ÉCRAN
        # ====================================================

        self.fullscreen = True

        self.attributes(
            "-fullscreen",
            True
        )

        self.bind(
            "<F11>",
            self.toggle_fullscreen
        )

        self.bind(
            "<Escape>",
            self.exit_fullscreen
        )

        # ====================================================
        # VARIABLES
        # ====================================================

        self.day = 1
        self.money = STARTING_MONEY

        self.employees = 3
        self.reputation = 50
        self.level = 1

        self.total_revenue = 0
        self.total_expenses = 0
        self.total_profit = 0

        self.daily_revenue = 0
        self.daily_expenses = 0
        self.daily_profit = 0

        self.market_demand = 1.0

        self.event_message = (
            "🏢 Bienvenue dans Business Empire !"
        )

        # ====================================================
        # PRODUITS
        # ====================================================

        self.products = {

            "Smartphone": Product(
                "Smartphone",
                180,
                450
            ),

            "Ordinateur": Product(
                "Ordinateur",
                400,
                900
            ),

            "Casque VR": Product(
                "Casque VR",
                120,
                350
            ),

            "Montre connectée": Product(
                "Montre connectée",
                70,
                220
            ),

            "Tablette": Product(
                "Tablette",
                150,
                400
            ),

            "Console": Product(
                "Console",
                300,
                750
            ),

            "Téléviseur 4K": Product(
                "Téléviseur 4K",
                500,
                1200
            ),

            "Drone": Product(
                "Drone",
                250,
                700
            ),

            "PC Gaming": Product(
                "PC Gaming",
                650,
                1500
            ),

            "Écouteurs": Product(
                "Écouteurs",
                45,
                150
            )
        }

        # ====================================================
        # HISTORIQUES
        # ====================================================

        self.money_history = [
            STARTING_MONEY
        ]

        self.revenue_history = [
            0
        ]

        self.profit_history = [
            0
        ]

        self.transaction_history = []

        # ====================================================
        # INTERFACE
        # ====================================================

        self.grid_columnconfigure(
            0,
            weight=0
        )

        self.grid_columnconfigure(
            1,
            weight=1
        )

        self.grid_rowconfigure(
            0,
            weight=1
        )

        self.create_sidebar()
        self.create_main()

        self.refresh_ui()

        # ====================================================
        # VÉRIFICATION SAUVEGARDE
        # ====================================================

        self.after(
            700,
            self.check_save_at_start
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )


    # ========================================================
    # PLEIN ÉCRAN
    # ========================================================

    def toggle_fullscreen(
        self,
        event=None
    ):

        self.fullscreen = not self.fullscreen

        self.attributes(
            "-fullscreen",
            self.fullscreen
        )


    def exit_fullscreen(
        self,
        event=None
    ):

        self.fullscreen = False

        self.attributes(
            "-fullscreen",
            False
        )


    # ========================================================
    # SIDEBAR
    # ========================================================

    def create_sidebar(self):

        self.sidebar = ctk.CTkFrame(
            self,
            width=250,
            corner_radius=0,
            fg_color="#080D18"
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.sidebar.grid_propagate(False)

        # ====================================================
        # TITRE
        # ====================================================

        ctk.CTkLabel(
            self.sidebar,
            text="LCC",
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            ),
            text_color="#60A5FA"
        ).pack(
            padx=18,
            pady=(20, 2),
            anchor="w"
        )

        ctk.CTkLabel(
            self.sidebar,
            text="Logistique Compiuter Craft",
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            ),
            text_color=TEXT_MUTED
        ).pack(
            padx=18,
            pady=(0, 10),
            anchor="w"
        )

        # ====================================================
        # STATISTIQUES
        # ====================================================

        self.day_label = self.create_card(
            "JOUR",
            "1"
        )

        self.money_label = self.create_card(
            "TRÉSORERIE",
            "25 000 €"
        )

        self.revenue_label = self.create_card(
            "CHIFFRE D'AFFAIRES",
            "0 €"
        )

        self.profit_label = self.create_card(
            "BÉNÉFICE",
            "0 €"
        )

        self.employee_label = self.create_card(
            "EMPLOYÉS",
            "3"
        )

        self.reputation_label = self.create_card(
            "RÉPUTATION",
            "50 / 100"
        )

        self.level_label = self.create_card(
            "NIVEAU",
            "1"
        )

        # ====================================================
        # OBJECTIF
        # ====================================================

        ctk.CTkLabel(
            self.sidebar,
            text="OBJECTIF",
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            ),
            text_color=TEXT_MUTED
        ).pack(
            padx=18,
            pady=(10, 2),
            anchor="w"
        )

        ctk.CTkLabel(
            self.sidebar,
            text="Atteindre 100 000 €\nde trésorerie.",
            justify="left",
            font=ctk.CTkFont(
                size=12
            ),
            text_color=TEXT
        ).pack(
            padx=18,
            anchor="w"
        )

        # ====================================================
        # SAUVEGARDE
        # ====================================================

        ctk.CTkLabel(
            self.sidebar,
            text="SAUVEGARDE",
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            ),
            text_color=TEXT_MUTED
        ).pack(
            padx=18,
            pady=(10, 3),
            anchor="w"
        )

        ctk.CTkButton(
            self.sidebar,
            text="💾 Sauvegarder",
            height=32,
            fg_color=GREEN,
            hover_color="#16A34A",
            text_color="#04130A",
            command=self.save_game
        ).pack(
            fill="x",
            padx=15,
            pady=2
        )

        ctk.CTkButton(
            self.sidebar,
            text="📂 Charger",
            height=32,
            fg_color=BLUE,
            hover_color="#2563EB",
            command=self.load_game
        ).pack(
            fill="x",
            padx=15,
            pady=2
        )

        ctk.CTkButton(
            self.sidebar,
            text="📍 Emplacement",
            height=30,
            fg_color="#374151",
            hover_color="#4B5563",
            command=self.show_save_location
        ).pack(
            fill="x",
            padx=15,
            pady=2
        )

        ctk.CTkButton(
            self.sidebar,
            text="🗑️ Supprimer",
            height=30,
            fg_color="#374151",
            hover_color="#4B5563",
            command=self.delete_save
        ).pack(
            fill="x",
            padx=15,
            pady=2
        )

        # ====================================================
        # NOUVELLE PARTIE
        # ====================================================

        ctk.CTkButton(
            self.sidebar,
            text="Nouvelle entreprise",
            height=36,
            corner_radius=9,
            fg_color=PANEL_LIGHT,
            hover_color="#334155",
            command=self.reset_game
        ).pack(
            side="bottom",
            fill="x",
            padx=15,
            pady=15
        )


    def create_card(
        self,
        title,
        value
    ):

        frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=PANEL,
            corner_radius=9
        )

        frame.pack(
            fill="x",
            padx=12,
            pady=2
        )

        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(
                size=8,
                weight="bold"
            ),
            text_color=TEXT_MUTED
        ).pack(
            padx=10,
            pady=(5, 0),
            anchor="w"
        )

        label = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            ),
            text_color=TEXT
        )

        label.pack(
            padx=10,
            pady=(0, 5),
            anchor="w"
        )

        return label


    # ========================================================
    # ZONE PRINCIPALE
    # ========================================================

    def create_main(self):

        self.main_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=BACKGROUND,
            corner_radius=0
        )

        self.main_scroll.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=10,
            pady=10
        )

        self.main_scroll.grid_columnconfigure(
            0,
            weight=1
        )

        self.create_header()
        self.create_products()
        self.create_middle()
        self.create_history()
        self.create_event()


    # ========================================================
    # HEADER
    # ========================================================

    def create_header(self):

        header = ctk.CTkFrame(
            self.main_scroll,
            fg_color="transparent"
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 10)
        )

        header.grid_columnconfigure(
            0,
            weight=1
        )

        ctk.CTkLabel(
            header,
            text="MON ENTREPRISE",
            font=ctk.CTkFont(
                size=25,
                weight="bold"
            )
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.header_money = ctk.CTkLabel(
            header,
            text="25 000 €",
            font=ctk.CTkFont(
                size=25,
                weight="bold"
            ),
            text_color=GREEN
        )

        self.header_money.grid(
            row=0,
            column=1,
            sticky="e"
        )


    # ========================================================
    # PRODUITS
    # ========================================================

    def create_products(self):

        frame = ctk.CTkFrame(
            self.main_scroll,
            fg_color=PANEL,
            corner_radius=14
        )

        frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 10)
        )

        ctk.CTkLabel(
            frame,
            text="📦 PRODUITS",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        ).pack(
            padx=12,
            pady=(9, 5),
            anchor="w"
        )

        self.product_rows = {}

        for product_name, product in self.products.items():

            row = ctk.CTkFrame(
                frame,
                fg_color=PANEL_LIGHT,
                corner_radius=8,
                height=38
            )

            row.pack(
                fill="x",
                padx=10,
                pady=2
            )

            row.pack_propagate(False)

            ctk.CTkLabel(
                row,
                text=product.name,
                width=160,
                anchor="w",
                font=ctk.CTkFont(
                    size=11,
                    weight="bold"
                )
            ).pack(
                side="left",
                padx=8
            )

            stock_label = ctk.CTkLabel(
                row,
                text="Stock : 0",
                width=100,
                anchor="w",
                text_color=TEXT_MUTED
            )

            stock_label.pack(
                side="left"
            )

            price_label = ctk.CTkLabel(
                row,
                text="Prix : 0 €",
                width=110,
                anchor="w"
            )

            price_label.pack(
                side="left"
            )

            sell_button = ctk.CTkButton(
                row,
                text="VENDRE",
                width=80,
                height=28,
                fg_color=GREEN,
                hover_color="#16A34A",
                text_color="#04130A",
                command=lambda p=product_name:
                self.sell_product(p)
            )

            sell_button.pack(
                side="right",
                padx=4
            )

            produce_button = ctk.CTkButton(
                row,
                text="PRODUIRE",
                width=85,
                height=28,
                fg_color=PURPLE,
                hover_color="#7C3AED",
                command=lambda p=product_name:
                self.produce(p)
            )

            produce_button.pack(
                side="right",
                padx=4
            )

            self.product_rows[
                product_name
            ] = {
                "stock": stock_label,
                "price": price_label
            }


    # ========================================================
    # GRAPHIQUE + GESTION
    # ========================================================

    def create_middle(self):

        container = ctk.CTkFrame(
            self.main_scroll,
            fg_color="transparent"
        )

        container.grid(
            row=2,
            column=0,
            sticky="ew"
        )

        container.grid_columnconfigure(
            0,
            weight=3
        )

        container.grid_columnconfigure(
            1,
            weight=2
        )

        # ====================================================
        # GRAPHIQUE
        # ====================================================

        chart_frame = ctk.CTkFrame(
            container,
            fg_color=PANEL,
            corner_radius=15
        )

        chart_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        self.figure = Figure(
            figsize=(7, 4),
            dpi=100,
            facecolor=PANEL
        )

        self.ax = self.figure.add_subplot(
            111
        )

        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=chart_frame
        )

        self.canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        # ====================================================
        # GESTION
        # ====================================================

        panel = ctk.CTkFrame(
            container,
            fg_color=PANEL,
            corner_radius=15
        )

        panel.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        ctk.CTkLabel(
            panel,
            text="⚙️ GESTION",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        ).pack(
            padx=15,
            pady=(15, 8),
            anchor="w"
        )

        ctk.CTkLabel(
            panel,
            text="PERSONNEL",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            )
        ).pack(
            padx=15,
            anchor="w"
        )

        employee_frame = ctk.CTkFrame(
            panel,
            fg_color=PANEL_LIGHT
        )

        employee_frame.pack(
            fill="x",
            padx=12,
            pady=4
        )

        self.employee_value = ctk.CTkLabel(
            employee_frame,
            text="3 employés"
        )

        self.employee_value.pack(
            side="left",
            padx=8,
            pady=7
        )

        ctk.CTkButton(
            employee_frame,
            text="+ EMPLOYÉ",
            width=105,
            height=30,
            command=self.hire_employee
        ).pack(
            side="right",
            padx=5
        )

        # ====================================================
        # MARKETING
        # ====================================================

        ctk.CTkLabel(
            panel,
            text="MARKETING",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            )
        ).pack(
            padx=15,
            pady=(8, 0),
            anchor="w"
        )

        ctk.CTkButton(
            panel,
            text="📢 Marketing — 1 000 €",
            height=38,
            fg_color=BLUE,
            hover_color="#2563EB",
            command=self.marketing
        ).pack(
            fill="x",
            padx=12,
            pady=4
        )

        # ====================================================
        # DÉVELOPPEMENT
        # ====================================================

        ctk.CTkLabel(
            panel,
            text="DÉVELOPPEMENT",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            )
        ).pack(
            padx=15,
            pady=(8, 0),
            anchor="w"
        )

        ctk.CTkButton(
            panel,
            text="🚀 Améliorer — 3 000 €",
            height=38,
            fg_color=PURPLE,
            hover_color="#7C3AED",
            command=self.upgrade
        ).pack(
            fill="x",
            padx=12,
            pady=4
        )

        # ====================================================
        # JOUR SUIVANT
        # ====================================================

        ctk.CTkButton(
            panel,
            text="JOUR SUIVANT  →",
            height=46,
            fg_color=GREEN,
            hover_color="#16A34A",
            text_color="#04130A",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            command=self.next_day
        ).pack(
            fill="x",
            padx=12,
            pady=(12, 15)
        )


    # ========================================================
    # HISTORIQUE
    # ========================================================

    def create_history(self):

        frame = ctk.CTkFrame(
            self.main_scroll,
            fg_color=PANEL,
            corner_radius=14
        )

        frame.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(10, 0)
        )

        ctk.CTkLabel(
            frame,
            text="📜 JOURNAL DE L'ENTREPRISE",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            )
        ).pack(
            padx=12,
            pady=(8, 4),
            anchor="w"
        )

        self.history = ctk.CTkTextbox(
            frame,
            height=100,
            fg_color="#0B1120"
        )

        self.history.pack(
            fill="both",
            padx=8,
            pady=(0, 8)
        )

        self.history.configure(
            state="disabled"
        )


    # ========================================================
    # MESSAGE
    # ========================================================

    def create_event(self):

        self.event_label = ctk.CTkLabel(
            self.main_scroll,
            text=self.event_message,
            height=42,
            corner_radius=10,
            fg_color=PANEL,
            text_color="#CBD5E1"
        )

        self.event_label.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(10, 5)
        )


    # ========================================================
    # PRODUIRE
    # ========================================================

    def produce(
        self,
        product_name
    ):

        product = self.products[
            product_name
        ]

        quantity = self.employees * 2

        cost = (
            quantity *
            product.production_cost
        )

        if cost > self.money:

            messagebox.showwarning(
                "Fonds insuffisants",
                "Tu n'as pas assez d'argent."
            )

            return

        self.money -= cost

        product.stock += quantity

        self.daily_expenses += cost
        self.total_expenses += cost

        self.add_history(
            f"Jour {self.day} : production "
            f"de {quantity} {product.name} "
            f"(-{self.money_format(cost)})"
        )

        self.event_message = (
            f"🏭 {quantity} {product.name} produits."
        )

        self.refresh_ui()


    # ========================================================
    # VENDRE
    # ========================================================

    def sell_product(
        self,
        product_name
    ):

        product = self.products[
            product_name
        ]

        if product.stock <= 0:

            messagebox.showwarning(
                "Stock vide",
                f"Tu n'as plus de {product.name}."
            )

            return

        demand = int(
            random.randint(1, 5) *
            self.market_demand
        )

        quantity = min(
            product.stock,
            max(1, demand)
        )

        revenue = (
            quantity *
            product.sale_price
        )

        product.stock -= quantity

        product.total_sold += quantity

        self.money += revenue

        self.daily_revenue += revenue
        self.total_revenue += revenue

        self.add_history(
            f"Jour {self.day} : vente de "
            f"{quantity} {product.name} "
            f"(+{self.money_format(revenue)})"
        )

        self.event_message = (
            f"🛒 Vente de {quantity} "
            f"{product.name} : "
            f"+{self.money_format(revenue)}"
        )

        self.refresh_ui()


    # ========================================================
    # EMPLOYÉ
    # ========================================================

    def hire_employee(self):

        cost = 2000

        if self.money < cost:

            messagebox.showwarning(
                "Fonds insuffisants",
                "Il faut 2 000 €."
            )

            return

        self.money -= cost

        self.employees += 1

        self.daily_expenses += cost
        self.total_expenses += cost

        self.add_history(
            f"Jour {self.day} : recrutement "
            f"d'un employé (-2 000 €)"
        )

        self.event_message = (
            "👨‍💼 Un nouvel employé rejoint "
            "l'entreprise."
        )

        self.refresh_ui()


    # ========================================================
    # MARKETING
    # ========================================================

    def marketing(self):

        cost = 1000

        if self.money < cost:

            messagebox.showwarning(
                "Fonds insuffisants",
                "Il faut 1 000 €."
            )

            return

        self.money -= cost

        self.reputation = min(
            100,
            self.reputation + 10
        )

        self.market_demand += 0.15

        self.daily_expenses += cost
        self.total_expenses += cost

        self.add_history(
            f"Jour {self.day} : campagne "
            f"marketing (-1 000 €)"
        )

        self.event_message = (
            "📢 Campagne marketing réussie !"
        )

        self.refresh_ui()


    # ========================================================
    # AMÉLIORATION
    # ========================================================

    def upgrade(self):

        cost = 3000

        if self.money < cost:

            messagebox.showwarning(
                "Fonds insuffisants",
                "Il faut 3 000 €."
            )

            return

        self.money -= cost

        self.level += 1

        self.reputation = min(
            100,
            self.reputation + 5
        )

        self.daily_expenses += cost
        self.total_expenses += cost

        self.add_history(
            f"Jour {self.day} : entreprise "
            f"améliorée (-3 000 €)"
        )

        self.event_message = (
            f"🚀 L'entreprise passe "
            f"au niveau {self.level} !"
        )

        self.refresh_ui()


    # ========================================================
    # JOUR SUIVANT
    # ========================================================

    def next_day(self):

        if self.day >= MAX_DAYS:

            self.end_game()

            return

        self.day += 1

        self.daily_revenue = 0
        self.daily_expenses = 0
        self.daily_profit = 0

        # ====================================================
        # SALAIRES
        # ====================================================

        salaries = self.employees * 150

        if salaries <= self.money:

            self.money -= salaries

            self.daily_expenses += salaries
            self.total_expenses += salaries

            self.add_history(
                f"Jour {self.day} : salaires "
                f"(-{self.money_format(salaries)})"
            )

        else:

            self.reputation = max(
                0,
                self.reputation - 5
            )

            self.event_message = (
                "⚠️ Tu n'as pas assez d'argent "
                "pour payer les salaires."
            )

        # ====================================================
        # DEMANDE
        # ====================================================

        self.market_demand = max(
            0.4,
            self.market_demand +
            random.uniform(-0.08, 0.08)
        )

        # ====================================================
        # ÉVÉNEMENT
        # ====================================================

        event = self.random_event()

        if event:
            self.event_message = event

        # ====================================================
        # BÉNÉFICE
        # ====================================================

        self.daily_profit = (
            self.daily_revenue -
            self.daily_expenses
        )

        self.total_profit += self.daily_profit

        # ====================================================
        # HISTORIQUE
        # ====================================================

        self.money_history.append(
            self.money
        )

        self.revenue_history.append(
            self.daily_revenue
        )

        self.profit_history.append(
            self.daily_profit
        )

        self.add_history(
            f"Jour {self.day} terminé : "
            f"CA {self.money_format(self.daily_revenue)} | "
            f"bénéfice "
            f"{self.money_signed(self.daily_profit)}"
        )

        # ====================================================
        # AUTOSAVE
        # ====================================================

        self.auto_save()

        self.refresh_ui()

        if self.day >= MAX_DAYS:

            self.after(
                300,
                self.end_game
            )


    # ========================================================
    # ÉVÉNEMENTS
    # ========================================================

    def random_event(self):

        if random.random() > 0.30:
            return None

        event = random.choice([
            "boom",
            "crisis",
            "order",
            "machine",
            "social"
        ])

        # BOOM

        if event == "boom":

            self.market_demand += 0.30

            self.reputation = min(
                100,
                self.reputation + 5
            )

            return (
                "🚀 BOOM ! Un influenceur "
                "parle de ton entreprise !"
            )

        # CRISE

        if event == "crisis":

            loss = random.randint(
                500,
                2000
            )

            loss = min(
                loss,
                self.money
            )

            self.money -= loss

            self.daily_expenses += loss
            self.total_expenses += loss

            self.reputation = max(
                0,
                self.reputation - 8
            )

            return (
                f"⚠️ CRISE ! Coût imprévu : "
                f"{self.money_format(loss)}"
            )

        # GROSSE COMMANDE

        if event == "order":

            product = random.choice(
                list(self.products.values())
            )

            quantity = random.randint(
                5,
                15
            )

            if product.stock >= quantity:

                revenue = (
                    quantity *
                    product.sale_price
                )

                product.stock -= quantity

                product.total_sold += quantity

                self.money += revenue

                self.daily_revenue += revenue
                self.total_revenue += revenue

                return (
                    f"📦 GROSSE COMMANDE ! "
                    f"{quantity} {product.name} "
                    f"vendus pour "
                    f"{self.money_format(revenue)}."
                )

            return (
                "📦 Un gros client voulait "
                "commander, mais ton stock "
                "est insuffisant."
            )

        # PANNE

        if event == "machine":

            cost = random.randint(
                300,
                1200
            )

            cost = min(
                cost,
                self.money
            )

            self.money -= cost

            self.daily_expenses += cost
            self.total_expenses += cost

            return (
                f"🔧 PANNE ! Réparation : "
                f"{self.money_format(cost)}."
            )

        # RÉSEAUX SOCIAUX

        self.reputation = min(
            100,
            self.reputation + 5
        )

        self.market_demand += 0.10

        return (
            "📱 Ton entreprise devient "
            "virale sur les réseaux sociaux !"
        )


    # ========================================================
    # JOURNAL
    # ========================================================

    def add_history(
        self,
        text
    ):

        self.transaction_history.append(
            text
        )

        if len(
            self.transaction_history
        ) > 50:

            self.transaction_history.pop(0)


    # ========================================================
    # ACTUALISATION
    # ========================================================

    def refresh_ui(self):

        self.day_label.configure(
            text=f"{self.day} / {MAX_DAYS}"
        )

        self.money_label.configure(
            text=self.money_format(
                self.money
            )
        )

        self.header_money.configure(
            text=self.money_format(
                self.money
            )
        )

        self.revenue_label.configure(
            text=self.money_format(
                self.total_revenue
            )
        )

        self.profit_label.configure(
            text=self.money_signed(
                self.total_profit
            ),
            text_color=(
                GREEN
                if self.total_profit >= 0
                else RED
            )
        )

        self.employee_label.configure(
            text=str(
                self.employees
            )
        )

        self.employee_value.configure(
            text=f"{self.employees} employés"
        )

        self.reputation_label.configure(
            text=f"{self.reputation} / 100"
        )

        self.level_label.configure(
            text=str(
                self.level
            )
        )

        self.event_label.configure(
            text=self.event_message
        )

        # ====================================================
        # PRODUITS
        # ====================================================

        for name, product in self.products.items():

            row = self.product_rows[name]

            row["stock"].configure(
                text=f"Stock : {product.stock}"
            )

            row["price"].configure(
                text=(
                    f"Prix : "
                    f"{self.money_format(product.sale_price)}"
                )
            )

        # ====================================================
        # JOURNAL
        # ====================================================

        self.history.configure(
            state="normal"
        )

        self.history.delete(
            "1.0",
            tk.END
        )

        for line in reversed(
            self.transaction_history[-15:]
        ):

            self.history.insert(
                tk.END,
                line + "\n"
            )

        self.history.configure(
            state="disabled"
        )

        self.update_chart()


    # ========================================================
    # GRAPHIQUE
    # ========================================================

    def update_chart(self):

        self.ax.clear()

        self.ax.set_facecolor(
            PANEL
        )

        days = list(
            range(
                1,
                len(
                    self.money_history
                ) + 1
            )
        )

        self.ax.plot(
            days,
            self.money_history,
            color=GREEN,
            linewidth=2.5
        )

        minimum = min(
            self.money_history
        )

        self.ax.fill_between(
            days,
            self.money_history,
            minimum * 0.98,
            color=GREEN,
            alpha=0.12
        )

        self.ax.set_title(
            "Évolution de la trésorerie",
            color=TEXT,
            fontsize=14,
            fontweight="bold",
            loc="left"
        )

        self.ax.grid(
            color="#334155",
            linestyle="--",
            alpha=0.35
        )

        self.ax.tick_params(
            axis="both",
            colors=TEXT_MUTED
        )

        for spine in self.ax.spines.values():

            spine.set_visible(False)

        self.figure.tight_layout()

        self.canvas.draw()


    # ========================================================
    # DONNÉES DE SAUVEGARDE
    # ========================================================

    def get_save_data(self):

        data = {

            "day": self.day,
            "money": self.money,

            "employees": self.employees,
            "reputation": self.reputation,
            "level": self.level,

            "total_revenue": self.total_revenue,
            "total_expenses": self.total_expenses,
            "total_profit": self.total_profit,

            "daily_revenue": self.daily_revenue,
            "daily_expenses": self.daily_expenses,
            "daily_profit": self.daily_profit,

            "market_demand": self.market_demand,

            "event_message": self.event_message,

            "money_history": self.money_history,
            "revenue_history": self.revenue_history,
            "profit_history": self.profit_history,

            "transaction_history":
                self.transaction_history,

            "products": {}
        }

        for name, product in self.products.items():

            data["products"][name] = {

                "name": product.name,

                "production_cost":
                    product.production_cost,

                "sale_price":
                    product.sale_price,

                "stock":
                    product.stock,

                "total_sold":
                    product.total_sold
            }

        return data


    # ========================================================
    # SAUVEGARDE MANUELLE
    # ========================================================

    def save_game(self):

        temp_file = SAVE_FILE + ".tmp"

        try:

            os.makedirs(
                SAVE_DIR,
                exist_ok=True
            )

            data = self.get_save_data()

            with open(
                temp_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

                file.flush()

                os.fsync(
                    file.fileno()
                )

            os.replace(
                temp_file,
                SAVE_FILE
            )

            self.event_message = (
                "💾 Partie sauvegardée !"
            )

            self.refresh_ui()

            messagebox.showinfo(
                "Sauvegarde",
                "Ta partie a été sauvegardée avec succès.\n\n"
                f"Emplacement :\n{SAVE_FILE}"
            )

        except Exception as error:

            try:

                if os.path.exists(
                    temp_file
                ):
                    os.remove(
                        temp_file
                    )

            except Exception:
                pass

            messagebox.showerror(
                "Erreur de sauvegarde",
                "Impossible de sauvegarder la partie.\n\n"
                f"Erreur : {error}\n\n"
                f"Emplacement prévu :\n{SAVE_FILE}"
            )


    # ========================================================
    # AUTOSAVE
    # ========================================================

    def auto_save(self):

        temp_file = SAVE_FILE + ".tmp"

        try:

            os.makedirs(
                SAVE_DIR,
                exist_ok=True
            )

            data = self.get_save_data()

            with open(
                temp_file,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

                file.flush()

                os.fsync(
                    file.fileno()
                )

            os.replace(
                temp_file,
                SAVE_FILE
            )

            return True

        except Exception as error:

            print(
                f"Erreur autosave : {error}"
            )

            try:

                if os.path.exists(
                    temp_file
                ):
                    os.remove(
                        temp_file
                    )

            except Exception:
                pass

            return False


    # ========================================================
    # EMPLACEMENT SAUVEGARDE
    # ========================================================

    def show_save_location(self):

        messagebox.showinfo(
            "Emplacement de la sauvegarde",
            "Ta sauvegarde se trouve ici :\n\n"
            f"{SAVE_FILE}"
        )


    # ========================================================
    # CHARGEMENT
    # ========================================================

    def load_game(
        self,
        show_message=True
    ):

        try:

            os.makedirs(
                SAVE_DIR,
                exist_ok=True
            )

        except Exception:
            pass

        if not os.path.exists(
            SAVE_FILE
        ):

            if show_message:

                messagebox.showinfo(
                    "Aucune sauvegarde",
                    "Aucune sauvegarde n'a été trouvée."
                )

            return False

        try:

            with open(
                SAVE_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

            self.day = data.get(
                "day",
                1
            )

            self.money = data.get(
                "money",
                STARTING_MONEY
            )

            self.employees = data.get(
                "employees",
                3
            )

            self.reputation = data.get(
                "reputation",
                50
            )

            self.level = data.get(
                "level",
                1
            )

            self.total_revenue = data.get(
                "total_revenue",
                0
            )

            self.total_expenses = data.get(
                "total_expenses",
                0
            )

            self.total_profit = data.get(
                "total_profit",
                0
            )

            self.daily_revenue = data.get(
                "daily_revenue",
                0
            )

            self.daily_expenses = data.get(
                "daily_expenses",
                0
            )

            self.daily_profit = data.get(
                "daily_profit",
                0
            )

            self.market_demand = data.get(
                "market_demand",
                1.0
            )

            self.event_message = data.get(
                "event_message",
                "Partie chargée."
            )

            self.money_history = data.get(
                "money_history",
                [STARTING_MONEY]
            )

            self.revenue_history = data.get(
                "revenue_history",
                [0]
            )

            self.profit_history = data.get(
                "profit_history",
                [0]
            )

            self.transaction_history = data.get(
                "transaction_history",
                []
            )

            # =================================================
            # PRODUITS
            # =================================================

            saved_products = data.get(
                "products",
                {}
            )

            for name, saved in saved_products.items():

                if name not in self.products:
                    continue

                product = self.products[name]

                product.stock = saved.get(
                    "stock",
                    0
                )

                product.total_sold = saved.get(
                    "total_sold",
                    0
                )

                product.production_cost = saved.get(
                    "production_cost",
                    product.production_cost
                )

                product.sale_price = saved.get(
                    "sale_price",
                    product.sale_price
                )

            self.event_message = (
                "📂 Partie chargée avec succès !"
            )

            self.refresh_ui()

            if show_message:

                messagebox.showinfo(
                    "Chargement",
                    "Ta partie a été chargée."
                )

            return True

        except Exception as error:

            messagebox.showerror(
                "Erreur de chargement",
                "Le fichier de sauvegarde est "
                "incorrect ou endommagé.\n\n"
                f"{error}"
            )

            return False


    # ========================================================
    # SUPPRIMER SAUVEGARDE
    # ========================================================

    def delete_save(self):

        try:

            os.makedirs(
                SAVE_DIR,
                exist_ok=True
            )

        except Exception:
            pass

        if not os.path.exists(
            SAVE_FILE
        ):

            messagebox.showinfo(
                "Sauvegarde",
                "Aucune sauvegarde n'existe."
            )

            return

        answer = messagebox.askyesno(
            "Supprimer",
            "Voulez-vous vraiment supprimer "
            "la sauvegarde ?"
        )

        if not answer:
            return

        try:

            os.remove(
                SAVE_FILE
            )

            # Supprime également un éventuel
            # fichier temporaire
            temp_file = SAVE_FILE + ".tmp"

            if os.path.exists(
                temp_file
            ):

                os.remove(
                    temp_file
                )

            self.event_message = (
                "🗑️ Sauvegarde supprimée."
            )

            self.refresh_ui()

            messagebox.showinfo(
                "Sauvegarde",
                "La sauvegarde a été supprimée."
            )

        except Exception as error:

            messagebox.showerror(
                "Erreur",
                f"Impossible de supprimer :\n{error}"
            )


    # ========================================================
    # SAUVEGARDE AU DÉMARRAGE
    # ========================================================

    def check_save_at_start(self):

        if not os.path.exists(
            SAVE_FILE
        ):
            return

        answer = messagebox.askyesno(
            "Sauvegarde trouvée",
            "Une sauvegarde a été trouvée.\n\n"
            "Veux-tu continuer ta partie ?\n\n"
            "Oui = Charger\n"
            "Non = Nouvelle entreprise"
        )

        if answer:

            self.load_game(
                show_message=False
            )


    # ========================================================
    # RESET
    # ========================================================

    def reset_game(self):

        answer = messagebox.askyesno(
            "Nouvelle entreprise",
            "Commencer une nouvelle entreprise ?\n\n"
            "La partie actuelle sera perdue."
        )

        if not answer:
            return

        self.day = 1
        self.money = STARTING_MONEY

        self.employees = 3
        self.reputation = 50
        self.level = 1

        self.total_revenue = 0
        self.total_expenses = 0
        self.total_profit = 0

        self.daily_revenue = 0
        self.daily_expenses = 0
        self.daily_profit = 0

        self.market_demand = 1.0

        self.event_message = (
            "🏢 Une nouvelle entreprise "
            "vient d'être créée !"
        )

        self.money_history = [
            STARTING_MONEY
        ]

        self.revenue_history = [
            0
        ]

        self.profit_history = [
            0
        ]

        self.transaction_history = []

        # ====================================================
        # PRODUITS PAR DÉFAUT
        # ====================================================

        initial_products = {

            "Smartphone": (
                180,
                450
            ),

            "Ordinateur": (
                400,
                900
            ),

            "Casque VR": (
                120,
                350
            ),

            "Montre connectée": (
                70,
                220
            ),

            "Tablette": (
                150,
                400
            ),

            "Console": (
                300,
                750
            ),

            "Téléviseur 4K": (
                500,
                1200
            ),

            "Drone": (
                250,
                700
            ),

            "PC Gaming": (
                650,
                1500
            ),

            "Écouteurs": (
                45,
                150
            )
        }

        for name, product in self.products.items():

            cost, price = initial_products[
                name
            ]

            product.production_cost = cost

            product.sale_price = price

            product.stock = 0

            product.total_sold = 0

        # Sauvegarde immédiatement
        # la nouvelle partie
        self.auto_save()

        self.refresh_ui()


    # ========================================================
    # FIN DU JEU
    # ========================================================

    def end_game(self):

        if self.money >= 100_000:

            title = "🏆 EMPIRE PROSPÈRE"

            result = (
                "Félicitations !\n"
                "Ton entreprise est devenue "
                "un véritable empire."
            )

        elif self.money > STARTING_MONEY:

            title = "📈 PARTIE TERMINÉE"

            result = (
                "Ton entreprise a réussi "
                "à progresser."
            )

        else:

            title = "📉 PARTIE TERMINÉE"

            result = (
                "La gestion de l'entreprise "
                "a été difficile."
            )

        messagebox.showinfo(
            title,
            f"{result}\n\n"
            f"Trésorerie : "
            f"{self.money_format(self.money)}\n"
            f"Chiffre d'affaires : "
            f"{self.money_format(self.total_revenue)}\n"
            f"Bénéfice : "
            f"{self.money_signed(self.total_profit)}\n"
            f"Réputation : "
            f"{self.reputation}/100"
        )


    # ========================================================
    # FERMETURE
    # ========================================================

    def on_close(self):

        # Sauvegarde automatique avant fermeture
        self.auto_save()

        self.destroy()


    # ========================================================
    # ARGENT
    # ========================================================

    @staticmethod
    def money_format(
        value
    ):

        formatted = (
            f"{value:,.2f}"
            .replace(",", " ")
            .replace(".", ",")
        )

        return f"{formatted} €"


    @staticmethod
    def money_signed(
        value
    ):

        sign = "+"

        if value < 0:
            sign = "-"

        formatted = (
            f"{abs(value):,.2f}"
            .replace(",", " ")
            .replace(".", ",")
        )

        return f"{sign}{formatted} €"


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":

    app = BusinessGame()

    app.mainloop()
