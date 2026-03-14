import tkinter as tk
from tkinter import ttk as tkk
from random import randint


#Level Modus spannender machen mit Endboss-Leveln und Versuche Anzahl ändern
#WASD Support
#Score System
#High Score Menü
#Möglichkeit verschiedene Spielerprofile/-namen anzulegen


#Startvariabeln Spiel
min_wert = 0
max_wert = 10
anzahl_versuche = 5
i = 0
level = 1
level_mode = False
current_frame = None

#Allgemeine Einstellungen Fenster
root = tk.Tk()
root.title("NumGuesser")
root.geometry("500x500")
root.resizable(width=True, height=True)
root.minsize(500, 500)
root.bind("<Return>", lambda event: return_key())
root.bind("<Escape>", lambda event: esc_key())
root.bind("<r>", lambda event: r_key())


#Tastenbelegung
def return_key(event=None):
    if current_frame in (game_frame, level_frame):
        game()

def esc_key(event=None):
    if current_frame in (game_frame, level_frame, fast_frame, custom_frame, modus_frame):
        back_to_menue()

def r_key(event=None):
    if current_frame == game_frame:
        restart()


#Funktionen
def show_frame(frame):
    global current_frame

    menue_frame.pack_forget()
    game_frame.pack_forget()
    fast_frame.pack_forget()
    modus_frame.pack_forget()
    custom_frame.pack_forget()
    level_frame.pack_forget()

    frame.pack()
    current_frame = frame

#Modi starten
def start_fast():
    show_frame(fast_frame)

def start_modus():
    show_frame(modus_frame)

def start_custom():
    show_frame(custom_frame)


#Button Funktionen

def restart():
    global y, i
    i = 0
    show_frame(game_frame)
    anzahl_game_label.config(text=f"Versuche: {anzahl_versuche}", font=("Arial", 15, "bold"), fg="black")
    game_label.config(text=f"zwischen {min_wert} und {max_wert}")
    game_entry.config(state="normal")
    game_entry.delete(0, tk.END)
    game_button.config(state="normal")
    error_game_var.set("")
    hint_game_var.set("")
    y = randint(min_wert, max_wert)


def back():
   show_frame(modus_frame)

def back_to_menue():
    global i, level_mode
    i = 0
    show_frame(menue_frame)
    level_mode = False
    error_game_var.set("")

#Level Modus
def start_level():
    global level_mode, level

    level_mode = True
    level = 1

    start_game()

def start_game():
    global y, max_wert, anzahl_versuche, i

    i = 0
    show_frame(level_frame)
    level_entry.focus_set()
    level_entry.config(state="normal")
    level_entry.delete(0, tk.END)
    level_confirm_button.config(state="normal")
    next_level_button.config(state="disabled")
    error_level_var.set("")
    hint_level_var.set("")


    if level_mode:
        max_wert = 10 + level * 5
        anzahl_versuche = 5

        level_var.set("Level: " + str(level))
        y = randint(min_wert, max_wert)
        bereich_level_label.config(text=f"Bereich: {min_wert} - {max_wert}")
        anzahl_level_label.config(text=f"Versuche: {anzahl_versuche}", font=("Arial", 15, "bold"), fg="black")


def next_level():
    global level

    level += 1
    start_game()
    show_frame(level_frame)

#Game Funktionen
def game():
    global i


    if i < anzahl_versuche:
        if not level_mode:
            guess = game_entry.get()
        else:
            guess = level_entry.get()

        #Eingabewert auf Int überprüfen
        try:
            value = int(guess)
        except ValueError:
            if not level_mode:
                error_game_var.set("Fehler! Bitte gib eine ganze Zahl zwischen " + str(min_wert) + " und " + str(max_wert) + " ein")
                game_entry.delete(0, tk.END)
                return
            else:
                error_level_var.set("Fehler! Bitte gib eine ganze Zahl zwischen " + str(min_wert) + " und " + str(max_wert) + " ein")
                level_entry.delete(0, tk.END)
                return

        if not min_wert <= value <= max_wert:
            if not level_mode:
                error_game_var.set("Fehler! Die Zahl muss zwischen " + str(min_wert) + " und " + str(max_wert) + " liegen")
                game_entry.delete(0, tk.END)
                return
            else:
                error_level_var.set("Fehler! Die Zahl muss zwischen " + str(min_wert) + " und " + str(max_wert) + " liegen")
                level_entry.delete(0, tk.END)
                return
        i += 1
        anzahl_game_label.config(text=f"Versuche: {anzahl_versuche - i}", font=("Arial", 15, "bold"), fg="black")
        anzahl_level_label.config(text=f"Versuche: {anzahl_versuche - i}", font=("Arial", 15, "bold"), fg="black")

        #Hinweis geben und Wert überprüfen
        if value == y:
            if not level_mode:
                hint_game_var.set("Du hast richtig geraten!")
                game_entry.config(state="disabled")
                i = 0
            if level_mode:
                hint_level_var.set("Du hast richtig geraten!")
                next_level_button.config(state="normal")
                level_entry.config(state="disabled")
                level_confirm_button.config(state="disabled")
                i = 0
            return

        elif value > int(y) and i < anzahl_versuche:
            if not level_mode:
                hint_game_var.set("Die Zahl ist kleiner als " + str(value))
                game_entry.delete(0, tk.END)
            else:
                hint_level_var.set("Die Zahl ist kleiner als " + str(value))
                level_entry.delete(0, tk.END)

        elif int(value) < int(y) and i < anzahl_versuche:
            if not level_mode:
                hint_game_var.set("Die Zahl ist größer als " + str(value))
                game_entry.delete(0, tk.END)
            else:
                hint_level_var.set("Die Zahl ist größer als " + str(value))
                level_entry.delete(0, tk.END)

        else:
            if not level_mode:
                hint_game_var.set("Du hast verloren! Die gesuchte Zahl war " + str(y))
                i = 0
                game_button.config(state="disabled")
            else:
                hint_level_var.set("Du hast verloren! Die gesuchte Zahl war " + str(y))
                i=0
                level_confirm_button.config(state="disabled")

        return

    #Eingabe im Eingabefeld löschen
    game_entry.delete(0, tk.END)
    level_entry.delete(0, tk.END)

def easy():
    global min_wert, max_wert, anzahl_versuche, y, level_mode
    level_mode = False
    min_wert = 0
    max_wert = 10
    y = randint(min_wert, max_wert)
    anzahl_versuche = 3
    show_frame(game_frame)
    bereich_game_label.config(text=f"Bereich: {min_wert} - {max_wert}")
    anzahl_game_label.config(text=f"Versuche: {anzahl_versuche}")
    game_entry.delete(0, tk.END)
    game_entry.focus_set()
    game_button.config(state="normal")
    error_game_var.set("")
    hint_game_var.set("")


def medium():
    global min_wert, max_wert, anzahl_versuche, y, level_mode
    level_mode = False
    min_wert = 0
    max_wert = 20
    anzahl_versuche = 4
    y = randint(min_wert, max_wert)
    show_frame(game_frame)
    bereich_game_label.config(text=f"Bereich: {min_wert} - {max_wert}")
    anzahl_game_label.config(text=f"Versuche: {anzahl_versuche}")
    game_entry.delete(0, tk.END)
    game_entry.focus_set()
    game_button.config(state="normal")
    error_game_var.set("")
    hint_game_var.set("")

def difficult():
    global min_wert, max_wert, anzahl_versuche, y, level_mode

    level_mode = False
    min_wert = 0
    max_wert = 30
    anzahl_versuche = 5
    y = randint(min_wert, max_wert)
    show_frame(game_frame)
    bereich_game_label.config(text=f"Bereich: {min_wert} - {max_wert}")
    anzahl_game_label.config(text=f"Versuche: {anzahl_versuche}")
    game_entry.delete(0, tk.END)
    game_entry.focus_set()
    game_button.config(state="normal")
    error_game_var.set("")
    hint_game_var.set("")


#Benutzerdefinierter Modus
def evolve():
    global min_wert, max_wert, anzahl_versuche, y, level_mode

    level_mode = False
    min_hint_var.set("")
    max_hint_var.set("")
    anzahl_versuche_hint_var.set("")

    eingabe1 = min_wert_entry.get()
    eingabe2 = max_wert_entry.get()
    eingabe3 = anzahl_versuche_entry.get()

    fehler = False #Kontrollvariable

    #Untergrenze festlegen
    try:
        value1 = int(eingabe1)
        min_wert = int(min_wert_entry.get())
    except ValueError:
        min_hint_var.set("Fehler! Bitte gib nur ganze Zahlen ein")
        fehler = True

    #Obergrenze festlegen
    try:
        value2 = int(eingabe2)
        max_wert = int(max_wert_entry.get())
    except ValueError:
        max_hint_var.set("Fehler! Bitte gib nur ganze Zahlen ein")
        fehler = True

    #Obergrenze > Untergrenze?
    if not fehler:
        if int(eingabe2) <= int(eingabe1):
            max_hint_var.set("Fehler! Die Obergrenze muss größer sein als die Untergrenze")
            fehler = True


    #Anzahl der Versuche festlegen
    try:
        value3 = int(eingabe3)
        anzahl_versuche = int(anzahl_versuche_entry.get())
    except ValueError:
        anzahl_versuche_hint_var.set("Fehler! Bitte gib nur ganze positive Zahlen ein")
        fehler = True

    #Auf Fehler überprüfen, ansonsten Frame wechseln
    if not fehler:
        show_frame(game_frame)
        bereich_game_label.config(text=f"Bereich: {min_wert} - {max_wert}")
        anzahl_game_label.config(text=f"Versuche: {anzahl_versuche}")
        game_entry.delete(0, tk.END)
        game_entry.focus_set()
        game_button.config(state="normal")
        error_game_var.set("")
        hint_game_var.set("")
        y = randint(min_wert, max_wert)
    return


#Startmenü
menue_frame = tk.Frame(root)

titel_menue = tk.Label(menue_frame, text="NumGuesser", font=("Arial", 25, "bold"), fg="black")
titel_menue.pack(pady=20)

start_button = tkk.Button(menue_frame, text="Spielen", padding=10, width=20, command=start_modus)
start_button.pack(pady=8)

quit_button = tkk.Button(menue_frame, text="Beenden", padding=10, width=20, command=exit)
quit_button.pack(pady=8)

version_menue = tk.Label(root, text="V2.1", font=("Arial", 5, "bold"), fg="black")
version_menue.pack(side="bottom", anchor="e", padx=10, pady=10)

menue_frame.pack()


#Game
game_frame = tk.Frame(root)

game_label = tk.Label(game_frame, text="Rate eine Zahl", font=("Arial", 25, "bold"), fg="black")
game_label.pack()

bereich_game_label = tk.Label(game_frame, text=f"Bereich: {min_wert} - {max_wert}", font=("Arial", 15, "bold"), fg="black")
bereich_game_label.pack()

anzahl_game_label = tk.Label(game_frame, text=f"Versuche: {anzahl_versuche}", font=("Arial", 15, "bold"), fg="black")
anzahl_game_label.pack()

game_entry = tkk.Entry(game_frame, width=20, justify="center")
game_entry.pack(pady=(60,0))

error_game_var = tk.StringVar()
error_game_var.set("")

error_game_label = tk.Label(game_frame, textvariable=error_game_var, font=("Arial", 10, "bold"), fg="black")
error_game_label.pack()

game_button = tkk.Button(game_frame, text="Bestätigen", padding=10, width=20, command=game)
game_button.pack(pady=8)

restart_button = tkk.Button(game_frame, text="Neues Spiel", padding=10, width=20, command=restart)
restart_button.pack(pady=8)

hint_game_var = tk.StringVar()
hint_game_var.set("")

hint_game_label = tk.Label(game_frame, textvariable=hint_game_var, font=("Arial", 15), fg="black")
hint_game_label.pack(pady=16)

back_button = tkk.Button(game_frame, text="Zurück zum Menü", padding=10, width=20,command=back_to_menue)
back_button.pack(pady=8)


#Level Game
level_frame = tk.Frame(root)

level_label = tk.Label(level_frame, text="Rate eine Zahl", font=("Arial", 25, "bold"), fg="black")
level_label.pack()

bereich_level_label = tk.Label(level_frame, text=f"Bereich: {min_wert} - {max_wert}", font=("Arial", 15, "bold"), fg="black")
bereich_level_label.pack()

anzahl_level_label = tk.Label(level_frame, text=f"Versuche: {anzahl_versuche}", font=("Arial", 15, "bold"), fg="black")
anzahl_level_label.pack()

level_entry = tkk.Entry(level_frame, width=20, justify="center")
level_entry.pack(pady=(60,0))

error_level_var = tk.StringVar()
error_level_var.set("")

error_level_label = tk.Label(level_frame, textvariable=error_level_var, font=("Arial", 10, "bold"), fg="black")
error_level_label.pack()

level_confirm_button = tkk.Button(level_frame, text="Bestätigen", padding=10, width=20, command=game)
level_confirm_button.pack(pady=8)

next_level_button = tkk.Button(level_frame, text="Nächstes Level", padding=10, width=20, command=next_level)
next_level_button.pack(pady=8)

hint_level_var = tk.StringVar()
hint_level_var.set("")

hint_level_label = tk.Label(level_frame, textvariable=hint_level_var, font=("Arial", 15), fg="black")
hint_level_label.pack(pady=16)

back_button = tkk.Button(level_frame, text="Zurück zum Menü", padding=10, width=20,command=back_to_menue)
back_button.pack(pady=8)

level_var = tk.StringVar()
level_var.set("Level: 1")

level_label = tk.Label(level_frame, textvariable=level_var, font=("Arial", 12))
level_label.pack()


#Modus
modus_frame = tk.Frame(root)
titel_modi = tk.Label(modus_frame, text="Spielmodus", font=("Arial", 25, "bold"), fg="black")
titel_modi.pack(pady=20)

fast_button = tkk.Button(modus_frame, text="Schnelles Spiel", padding=10, width=25,command=start_fast)
fast_button.pack(pady=8)

level_button = tkk.Button(modus_frame, text="Level Up", padding=10, width=25, command=start_level)
level_button.pack(pady=8)

custom_button = tkk.Button(modus_frame, text="Benutzerdefiniert", padding=10, width=25, command=start_custom)
custom_button.pack(pady=8)

back_button = tkk.Button(modus_frame, text="Zurück zum Menü", padding=10, width=25,command=back_to_menue)
back_button.pack(pady=(32,0))


#Schnelles Spiel
fast_frame = tk.Frame(root)

titel_settings = tk.Label(fast_frame, text="Schwierigkeit wählen", font=("Arial", 25, "bold"), fg="black")
titel_settings.pack(pady=20)

easy_button = tkk.Button(fast_frame, text="Einfach - 0-10, 3 Versuche", padding=10, width=25,command=easy)
easy_button.pack(pady=8)

medium_button = tkk.Button(fast_frame, text="Mittel - 0-20, 4 Versuche", padding=10, width=25, command=medium)
medium_button.pack(pady=8)

difficult_button = tkk.Button(fast_frame, text="Schwer - 0-30, 5 Versuche", padding=10, width=25, command=difficult)
difficult_button.pack(pady=8)

back_button = tkk.Button(fast_frame, text="Zurück", padding=10, width=25,command=back)
back_button.pack(pady=(32,0))


#Benutzerdefiniert
custom_frame = tk.Frame(root)

titel_custom = tk.Label(custom_frame, text="Benutzerdefiniert", font=("Arial", 25, "bold"), fg="black")
titel_custom.pack(pady=20)

min_wert_label = tk.Label(custom_frame, text="Untergrenze", font=("Arial", 10, "bold"), fg="black")
min_wert_label.pack()

min_wert_entry = tkk.Entry(custom_frame, width=20, justify="center")
min_wert_entry.pack()

min_hint_var = tk.StringVar()
min_hint_var.set("")

min_hint_label = tk.Label(custom_frame, textvariable=min_hint_var, font=("Arial", 10), fg="black")
min_hint_label.pack(pady=(0,8))


max_wert_label = tk.Label(custom_frame, text="Obergrenze", font=("Arial", 10, "bold"), fg="black")
max_wert_label.pack()

max_wert_entry = tkk.Entry(custom_frame, width=20, justify="center")
max_wert_entry.pack()

max_hint_var = tk.StringVar()
max_hint_var.set("")

max_hint_label = tk.Label(custom_frame, textvariable=max_hint_var, font=("Arial", 10), fg="black")
max_hint_label.pack(pady=(0,8))


anzahl_versuche_label = tk.Label(custom_frame, text="Anzahl der Versuche", font=("Arial", 10, "bold"), fg="black")
anzahl_versuche_label.pack()

anzahl_versuche_entry = tkk.Entry(custom_frame, width=20, justify="center")
anzahl_versuche_entry.pack()

anzahl_versuche_hint_var = tk.StringVar()
anzahl_versuche_hint_var.set("")

anzahl_versuche_hint_label = tk.Label(custom_frame, textvariable=anzahl_versuche_hint_var, font=("Arial", 10), fg="black")
anzahl_versuche_hint_label.pack(pady=(0,8))


entry_button2 = tkk.Button(custom_frame, text="Bestätigen", padding=10, width=25, command=evolve)
entry_button2.pack(pady=8)

back_button = tkk.Button(custom_frame, text="Zurück", padding=10, width=25,command=back)
back_button.pack(pady=(32,0))

root.mainloop()