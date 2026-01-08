import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

RAID_DATA = {
    "Wooden Door": {
        "C4": (1, 2200),
        "Rocket": (1, 1400),
        "Explosive Ammo": (18, 450),
        "Satchel": (2, 960)
    },
    "Sheet Metal Door": {
        "C4": (1, 2200),
        "Rocket": (2, 2800),
        "Explosive Ammo": (63, 1575),
        "Satchel": (4, 1920)
    },
    "Garage Door": {
        "C4": (2, 4400),
        "Rocket": (3, 4200),
        "Explosive Ammo": (150, 3750),
        "Satchel": (9, 4320)
    },
    "Armored Door": {
        "C4": (2, 4400),
        "Rocket": (4, 5600),
        "Explosive Ammo": (200, 5000),
        "Satchel": (12, 5760)
    },
    "Stone Wall": {
        "C4": (2, 4400),
        "Rocket": (4, 5600),
        "Explosive Ammo": (185, 4625),
        "Satchel": (10, 4800)
    },
    "Metal Wall": {
        "C4": (4, 8800),
        "Rocket": (8, 11200),
        "Explosive Ammo": (400, 10000),
        "Satchel": (23, 11040)
    },
    "HQM Wall": {
        "C4": (8, 17600),
        "Rocket": (15, 21000),
        "Explosive Ammo": (799, 19975),
        "Satchel": (46, 22080)
    }
}

def calculate():
    target = target_var.get()
    amount = amount_var.get()

    available = []
    if c4_var.get(): available.append("C4")
    if rocket_var.get(): available.append("Rocket")
    if ammo_var.get(): available.append("Explosive Ammo")
    if satchel_var.get(): available.append("Satchel")

    if not available or amount <= 0:
        messagebox.showerror("Ошибка", "Проверь ввод данных")
        return

    results = []
    for expl in available:
        count, sulfur = RAID_DATA[target][expl]
        results.append((expl, count * amount, sulfur * amount))

    best = min(results, key=lambda x: x[2])

    text = f"🎯 Цель: {target} x{amount}\n\n"
    for r in results:
        text += f"{r[0]} → {r[1]} | 💰 {r[2]} серы\n"

    text += f"\n✅ Самый выгодный вариант:\n🔥 {best[0]} → {best[1]} | {best[2]} серы"

    result_label.configure(text=text)

# ===== ОКНО =====
app = ctk.CTk()
app.title("Rust Raid Calculator")
app.geometry("520x560")
app.resizable(False, False)

# ===== ЗАГОЛОВОК =====
ctk.CTkLabel(app, text="🧨 Rust Raid Calculator",
             font=ctk.CTkFont(size=24, weight="bold")).pack(pady=15)

# ===== ВЫБОР ЦЕЛИ =====
ctk.CTkLabel(app, text="Тип объекта").pack()
target_var = ctk.StringVar(value="Stone Wall")
ctk.CTkComboBox(app, values=list(RAID_DATA.keys()),
                variable=target_var, width=250).pack(pady=5)

# ===== КОЛИЧЕСТВО =====
ctk.CTkLabel(app, text="Количество").pack()
amount_var = ctk.IntVar(value=1)
ctk.CTkEntry(app, textvariable=amount_var, width=120).pack(pady=5)

# ===== ВЗРЫВЧАТКА =====
ctk.CTkLabel(app, text="Доступная взрывчатка").pack(pady=10)

c4_var = ctk.BooleanVar(value=True)
rocket_var = ctk.BooleanVar(value=True)
ammo_var = ctk.BooleanVar(value=True)
satchel_var = ctk.BooleanVar(value=True)

for text, var in [
    ("C4", c4_var),
    ("Rocket", rocket_var),
    ("Explosive Ammo", ammo_var),
    ("Satchel", satchel_var)
]:
    ctk.CTkCheckBox(app, text=text, variable=var).pack(anchor="w", padx=150)

# ===== КНОПКА =====
ctk.CTkButton(app, text="Рассчитать рейд",
              height=45, width=220,
              command=calculate).pack(pady=20)

# ===== РЕЗУЛЬТАТ =====
result_label = ctk.CTkLabel(app, text="",
                            justify="left",
                            font=ctk.CTkFont(size=14))
result_label.pack(pady=10)

app.mainloop()
