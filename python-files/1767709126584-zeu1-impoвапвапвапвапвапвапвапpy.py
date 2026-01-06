import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os  # Для работы с текущей директорией

# ======= цвета =======
winbg = "#1e272e"
cardbg = "#2f3640"
headerbg = "#0097a7"
textcolor = "#ecf0f1"

btnbg = "#00acc1"
btnhover = "#26c6da"
btnactive = "#00838f"

success = "#2ecc71"
error = "#e74c3c"

# ======= запрещённые слова =======
words = ["паспорт", "пароль", "номер карты", "секрет", "confidential"]

# ======= лог =======
def log(word):
    try:
        # Лог создается в той же папке, что и .pyw
        log_path = os.path.join(os.path.dirname(__file__), "dlp_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} — Найдено: {word}\n")
    except Exception as e:
        print(f"Ошибка при записи лога: {e}")  # На случай отладки через IDE

# ======= проверка текста =======
def checktext():
    status.config(text="🔍 Проверяю...", fg=textcolor)
    root.update()

    # Получаем текст, убираем пробелы и переводим в нижний регистр
    t = text.get("1.0", "end").strip().lower()

    # Список запрещённых слов, найденных в тексте
    found_words = [w for w in words if w.lower() in t]

    if found_words:
        status.config(text="⛔ Найдены запрещённые слова", fg=error)
        # Логируем каждое слово
        for w in found_words:
            log(w)
        # Показываем все найденные слова
        messagebox.showerror("DLP — Утечка данных", "Найдены запрещённые слова:\n- " + "\n- ".join(found_words))
    else:
        status.config(text="✅ Нарушений нет", fg=success)
        messagebox.showinfo("DLP", "Текст безопасен")

# ======= горячие клавиши =======
def hotkeys(event):
    if not (event.state & 0x4):  # Проверка, что нажата Ctrl
        return
    # Ctrl+A
    if event.keycode == 65:
        text.tag_add("sel", "1.0", "end")
        return "break"
    # Ctrl+C
    if event.keycode == 67:
        text.event_generate("<<Copy>>")
        return "break"
    # Ctrl+V
    if event.keycode == 86:
        text.event_generate("<<Paste>>")
        return "break"

# ======= hover кнопки =======
def onenter(e):
    btn.config(bg=btnhover)
def onleave(e):
    btn.config(bg=btnbg)

# ======= главное окно =======
root = tk.Tk()
root.title("DLP • Контроль утечек данных")
root.configure(bg=winbg)

w, h = 930, 645
x = (root.winfo_screenwidth() - w) // 2
y = (root.winfo_screenheight() - h) // 2
root.geometry(f"{w}x{h}+{x}+{y}")
root.resizable(False, False)

# ======= верхний заголовок =======
head = tk.Frame(root, bg=headerbg, height=60)
head.pack(fill="x")
tk.Label(head, text="🛡 DLP-система", bg=headerbg, fg="white", font=("Arial",16,"bold")).pack(side="left", padx=15, pady=10)
tk.Label(head, text="by Makar M.", bg=headerbg, fg="#e0f7fa", font=("Arial",10)).pack(side="left", padx=10)

# ======= карточка =======
card = tk.Frame(root, bg=cardbg)
card.pack(padx=20, pady=20, fill="both", expand=True)

tk.Label(card, text="Проверка текста на утечку данных", bg=cardbg, fg=textcolor, font=("Arial",13,"bold")).pack(pady=(15,5))
tk.Label(card, text="Введите текст или вставьте:", bg=cardbg, fg=textcolor).pack()

# ======= текстовое поле =======
text = tk.Text(card, height=16, font=("Segoe UI",13), bg="#353b48", fg=textcolor, insertbackground=textcolor, relief="flat", wrap="word")
text.pack(fill="x", padx=15, pady=10)
text.focus_set()
text.bind("<KeyPress>", hotkeys)

# ======= кнопка =======
btn = tk.Button(card, text="🔎 Проверить текст", command=checktext, bg=btnbg, fg="white", activebackground=btnactive, relief="flat", font=("Arial",11), padx=20, pady=6)
btn.pack(pady=5)
btn.bind("<Enter>", onenter)
btn.bind("<Leave>", onleave)

# ======= статус =======
status = tk.Label(card, text="ℹ Ожидание проверки", bg=cardbg, fg=textcolor, font=("Arial",10,"italic"))
status.pack(pady=(10,15))

# ======= запускаем GUI =======
root.mainloop()
