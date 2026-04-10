import tkinter as tk
from tkinter import messagebox

units = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
teens = ["عشرة", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر",
         "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"]
tens = ["", "", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون",
        "سبعون", "ثمانون", "تسعون"]
hundreds = ["", "مائة", "مائتان", "ثلاثمائة", "أربعمائة",
            "خمسمائة", "ستمائة", "سبعمائة", "ثمانمائة", "تسعمائة"]

# ✅ conversion de 0 إلى 999 (corrigée)
def convert_0_999(n):
    words = []

    # centaines
    if n >= 100:
        words.append(hundreds[n // 100])
        n %= 100

    # 10 → 19
    if 10 <= n < 20:
        words.append(teens[n - 10])

    else:
        # unités + dizaines (ordre correct)
        if n >= 20:
            if n % 10 != 0:
                words.append(units[n % 10])
            words.append(tens[n // 10])

        elif n > 0:
            words.append(units[n])

    return " و ".join(words)

# ✅ conversion complète
def number_to_arabic(n):
    n = int(n)

    if n == 0:
        return "صفر"

    parts = []

    millions = n // 1_000_000
    thousands = (n % 1_000_000) // 1000
    remainder = n % 1000

    # millions
    if millions:
        if millions == 1:
            parts.append("مليون")
        elif millions == 2:
            parts.append("مليونان")
        elif 3 <= millions <= 10:
            parts.append(convert_0_999(millions) + " ملايين")
        else:
            parts.append(convert_0_999(millions) + " مليون")

    # thousands
    if thousands:
        if thousands == 1:
            parts.append("ألف")
        elif thousands == 2:
            parts.append("ألفان")
        elif 3 <= thousands <= 10:
            parts.append(convert_0_999(thousands) + " آلاف")
        else:
            parts.append(convert_0_999(thousands) + " ألف")

    # reste
    if remainder:
        parts.append(convert_0_999(remainder))

    return " و ".join(parts)

# ✅ bouton convertir
def convertir():
    try:
        num = entry.get()
        if not num.isdigit():
            raise ValueError
        result = number_to_arabic(int(num))
        label_result.config(text=result)
    except:
        label_result.config(text="⚠️ أدخل رقم صحيح")

# ✅ bouton copier
def copier():
    text = label_result.cget("text")
    if text:
        app.clipboard_clear()
        app.clipboard_append(text)
        messagebox.showinfo("تم", "تم النسخ")

# 🎨 interface
app = tk.Tk()
app.title("Convertisseur Nombre → Arabe PRO")
app.geometry("400x260")

tk.Label(app, text="أدخل الرقم:", font=("Arial", 12)).pack(pady=5)

entry = tk.Entry(app, font=("Arial", 14), justify="center")
entry.pack(pady=5)

tk.Button(app, text="تحويل", command=convertir).pack(pady=5)

label_result = tk.Label(app, text="", wraplength=350, font=("Arial", 12), fg="blue")
label_result.pack(pady=10)

tk.Button(app, text="نسخ", command=copier).pack()

app.mainloop()