import tkinter as tk
from tkinter import messagebox
import webbrowser
import os

# -------------------
# ESTADO
# -------------------
score = 0
unlocked = False
acabar_clicks = 0

# -------------------
# ACABAR
# -------------------
def acabar():
    global acabar_clicks
    acabar_clicks += 1

    if acabar_clicks == 1:
        try:
            os.startfile("music.mp4")
        except:
            print("music.mp4 no encontrado")
    else:
        root.destroy()

# -------------------
# FLAPPY BIRD (EMBED)
# -------------------
def open_flappy():
    global score

    game = tk.Toplevel(root)
    game.title("Flappy Bird")

    tk.Label(game, text="Flappy Bird (embed externo)").pack(pady=10)

    def open_game():
        webbrowser.open("https://jewkesy.github.io/Flappy/")

    tk.Button(game, text="Abrir juego", command=open_game).pack(pady=5)

    score_label = tk.Label(game, text="Score: 0")
    score_label.pack(pady=10)

    def add_point():
        global score, unlocked
        score += 1
        score_label.config(text=f"Score: {score}")

        if score >= 10 and not unlocked:
            unlocked = True
            game.destroy()
            show_unlock()

    tk.Button(game, text="+1 (simular score)", command=add_point).pack(pady=5)

# -------------------
# DESBLOQUEO
# -------------------
def show_unlock():
    btn_felicitacion.pack(pady=10)

# -------------------
# FELICITACIÓN
# -------------------
def felicitacion():
    msgs = ["msg1", "msg2", "msg3", "msg4", "msg5", "msg6", "msg7"]

    for m in msgs:
        messagebox.showinfo("Felicitación", m)

# -------------------
# UI PRINCIPAL
# -------------------
root = tk.Tk()
root.title("App Flappy System")
root.geometry("300x300")

tk.Label(root, text="Sistema bloqueado").pack(pady=10)

tk.Button(root, text="Desbloquear felicitación", command=open_flappy).pack(pady=10)

tk.Button(root, text="Acabar", command=acabar).pack(pady=10)

btn_felicitacion = tk.Button(root, text="Ver felicitación", command=felicitacion)

root.mainloop()