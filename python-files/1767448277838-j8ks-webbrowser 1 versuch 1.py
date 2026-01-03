import tkinter as tk
import time
import webbrowser

fenster = tk.Tk()
fenster.title("Webbrowser")
fenster.geometry("400x200")
print("Starte...")


eingabe = tk.Entry(fenster, width=30)
eingabe.pack(pady=10)


def anzeigen():
    text = eingabe.get()
    print("Eingabe:", text)
    print("Verabreite...")
    time.sleep(1)
    print("Zertigikat erfolg")
    time.sleep(0.400)
    print("Öffne...")
    webbrowser.open(f"https://www.{text}")
    print(f"Webseite:https://www.{text} wurde geöffnet")
    time.sleep(1)


button = tk.Button(fenster, text="Öffnen", command=anzeigen)
button.pack(pady=10)

fenster.mainloop()
