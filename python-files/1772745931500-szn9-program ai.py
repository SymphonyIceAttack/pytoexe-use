import tkinter as tk
import random
import winsound
import time
import webbrowser

def sprawdz_wiadomosc(event=None):
    kod_blokady = "75♪3MPľ7▒TP]¸∟Îě↓5═Úh54"
    # .strip() usuwa zbędne spacje z początku i końca
    user_input = entry.get().strip()

    # 1. Sprawdzenie, czy pole jest puste
    if not user_input:
        chat_history.config(state=tk.NORMAL)
        chat_history.insert(tk.END, "Bot: ślepy jesteś nic nie napisałeś\n\n", "bot_text")
        chat_history.config(state=tk.DISABLED)
        chat_history.see(tk.END)
        return

    # 2. Sprawdzenie tajnego kodu
    if user_input == kod_blokady:
        winsound.MessageBeep(winsound.MB_ICONHAND)
        root.update()
        time.sleep(10)
        webbrowser.open("http://www.youtube.com/watch?v=dQw4w9WgXcQ")
        root.destroy()
        return

    # 3. Losowe odpowiedzi (jeśli coś zostało wpisane)
    odpowiedzi = [
        "TAK NAPEWNO Xd",
        "No jasne, akurat ci uwierzę... xd",
        "Chciałbyś! XD",
        "Rel.",
        "XDDDD",
        "No i prawidłowo, nieźle cię odkleiło.",
        "Nie no, bez przesady, weź leki.",
        "Może w innym uniwersum, marzycielu xd",
        "Skończ już gadać głupoty.",
        "Niezła odklejka, szanuję. xd",
        "Twoja stara xd",
        "Nudne to już jest, zmień płytę."
    ]

    reakcja = random.choice(odpowiedzi)

    chat_history.config(state=tk.NORMAL)
    chat_history.insert(tk.END, f"Ty: {user_input}\n", "user_text")
    chat_history.insert(tk.END, f"Bot: {reakcja}\n\n", "bot_text")
    chat_history.config(state=tk.DISABLED)
    
    entry.delete(0, tk.END)
    chat_history.see(tk.END)

# --- UI Setup ---
root = tk.Tk()
root.title("Chatbot Xd v6.0")
root.geometry("400x550")
root.configure(bg="#121212")

chat_history = tk.Text(root, state=tk.DISABLED, bg="#1e1e1e", fg="#ffffff", wrap=tk.WORD, font=("Consolas", 10))
chat_history.tag_config("user_text", foreground="#888888")
chat_history.tag_config("bot_text", foreground="#00ff00", font=("Consolas", 10, "bold"))
chat_history.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

entry = tk.Entry(root, font=("Consolas", 12), bg="#333333", fg="white", insertbackground="white")
entry.pack(padx=10, pady=5, fill=tk.X)
entry.bind("<Return>", sprawdz_wiadomosc)

send_button = tk.Button(root, text="WYŚLIJ POCISK", command=sprawdz_wiadomosc, bg="#ff0000", fg="white", font=("Consolas", 10, "bold"))
send_button.pack(pady=10)

entry.focus_set()
root.mainloop()