import tkinter as tk

score = 0

def klik():
    global score
    score += 1
    label.config(text="Skóre: " + str(score))

okno = tk.Tk()
okno.title("Klikací hra")

label = tk.Label(okno, text="Skóre: 0", font=("Arial", 20))
label.pack()

button = tk.Button(okno, text="Klikni na mě!", command=klik)
button.pack()

okno.mainloop()
